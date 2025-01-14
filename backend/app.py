import os
import uuid
import uvicorn
import psycopg2
from psycopg2 import sql
from utils import Chat
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.graphs import Neo4jGraph
from langchain_community.vectorstores import Neo4jVector
from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Query
from data_processing import embedding_model, process_file, process_batches, clear_database

# Disable parallelism in tokenizers
os.environ["TOKENIZERS_PARALLELISM"] = "false"
# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
PG_HOST = os.getenv("PG_HOST")
PG_PORT = os.getenv("PG_PORT")
PG_DBNAME = os.getenv("PG_DBNAME")
PG_USER = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")


# Initialize components
embeddModel = embedding_model()

graph = Neo4jGraph(
    url=NEO4J_URI,
    username=NEO4J_USERNAME,
    password=NEO4J_PASSWORD
)

vector_index = Neo4jVector.from_existing_graph(
    embeddModel,
    search_type="hybrid",
    node_label="Document",
    text_node_properties=["text"],
    embedding_node_property="embedding"
)

# Connect to PostgreSQL
def get_db_connection():
    conn = psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DBNAME,
        user=PG_USER,
        password=PG_PASSWORD
    )
    return conn

# Function to create the database if it doesn't exist
def create_database():
    try:
        conn = get_db_connection()
        conn.autocommit = True
        print(f"Database '{PG_DBNAME}' connected successfully.")
        conn.close()
    except Exception as e:
        print(f"Error connecting to database: {e}")

# Function to create the table
def create_table():
    create_table_query = """
    CREATE TABLE IF NOT EXISTS agentpro_db (
        session_id UUID PRIMARY KEY,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(create_table_query)
        conn.commit()
        cursor.close()
        conn.close()
        print("Table created successfully or already exists.")
    except Exception as e:
        print(f"Error creating table: {e}")

# Initialize FastAPI app
app = FastAPI()

# Request and Response Models
class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    question: str

class ChatResponse(BaseModel):
    response: str

# Model for process request with optional code (defaults to None)
class ProcessRequest(BaseModel):
    file_path: str
    code: Optional[int] = None  # Default to None if not provided

@app.post("/chat", response_model=ChatResponse)
def ask_question(request: ChatRequest, model: Optional[str] = Query(None), groq_api_key: Optional[str] = Query(None)):
    """Endpoint to handle chatbot queries."""
    try:
        DEFAULT_MODEL = "llama-3.1-8b-instant"
        model_name = model if model else DEFAULT_MODEL
        
        if not model_name:
            raise HTTPException(status_code=400, detail="Model is required and not provided.")
        # If the user provides the groq_api_key in the query, use it, else use the default one from the .env file
        api_key_to_use = groq_api_key if groq_api_key else GROQ_API_KEY
        
        if not api_key_to_use:
            raise HTTPException(status_code=400, detail="Groq API key is required and not provided.")

        # Generate a new session ID if none is provided
        session_id = request.session_id or str(uuid.uuid4())

        # Process the question using Chat with the selected API key
        response = Chat(
            graph=graph,
            llm=ChatGroq(groq_api_key=api_key_to_use, model_name = model_name, temperature = 0),  # Pass the API key here
            embedding=embeddModel,
            vector_index=vector_index,
            question=request.question,
        )
        print(response)
        # Insert session data into PostgreSQL
        conn = get_db_connection()
        cursor = conn.cursor()
        query = sql.SQL("INSERT INTO agentpro_db (session_id, question, answer, timestamp) VALUES (%s, %s, %s, %s)")
        cursor.execute(query, (session_id, request.question, response, datetime.now()))
        conn.commit()
        cursor.close()
        conn.close()

        return ChatResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    """Root endpoint."""
    return {"message": "Welcome to the ChatBot API!"}

@app.post("/process")
async def process_data(file: UploadFile = File(...), code: Optional[str] = Form(None)):  # Explicitly get `code` from form-data
    """Endpoint to process file, clear database, and process batches."""
    try:
        # Save the uploaded file temporarily
        file_path = f"{file.filename}"
        with open(file_path, "wb") as f:
            f.write(await file.read())

        # Clear the database if a code is provided
        print(code)
        if code is not None:
            print("Clearing database with code...")
            clear_database(code)

        # Process the file
        documents = process_file(file_path)
        # Process documents in batches
        process_batches(documents)
        os.remove(file_path)
        return {"message": "Task completed successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Startup event to create the database and table
@app.on_event("startup")
def startup_event():
    """Runs at application startup."""
    create_database()  # Ensure the database exists
    create_table()  # Create the table during startup

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=5507, reload=True)
