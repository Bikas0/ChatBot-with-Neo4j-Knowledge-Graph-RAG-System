import os
import csv
import time
import magic
import pymupdf4llm
from typing import List
from langchain_groq import ChatGroq
from langchain_community.graphs import Neo4jGraph
from langchain_community.vectorstores import Neo4jVector
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_experimental.graph_transformers import LLMGraphTransformer
from neo4j import GraphDatabase
from dotenv import load_dotenv
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document

# Load environment variables
load_dotenv()
GROQ_API_KEYS = [
    os.getenv("GROQ_API_KEY"),
    os.getenv("GROQ_API_KEY_2"),
    os.getenv("GROQ_API_KEY_3"),
    os.getenv("GROQ_API_KEY_4"),
    os.getenv("GROQ_API_KEY_5"),
    os.getenv("GROQ_API_KEY_6"),
]

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

def embedding_model():
    model = HuggingFaceEmbeddings(model_name="GeneralTextEmbeddingModel")
    return model

# Initialize embeddings and Neo4j driver
embeddModel = embedding_model()
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
graph = Neo4jGraph(url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD)


def get_llm(api_key: str):
    """Initialize ChatGroq LLM with an API key."""
    return ChatGroq(groq_api_key=api_key, model_name="llama-3.1-8b-instant")


def clear_database(CODE):
    """Clear all nodes and relationships in the Neo4j database."""
    if CODE == str(7179):
        with driver.session() as session:
            try:
                session.write_transaction(lambda tx: tx.run("MATCH (n) DETACH DELETE n"))
                print("Database cleared successfully.")
            except Exception as e:
                print(f"Error clearing database: {e}")
    else:
        print("Your password is incorrect")


def process_pdf(pdf_path: str) -> List[Document]:
    """Convert PDF to a list of Documents."""
    raw_text = pymupdf4llm.to_markdown(pdf_path)
    return split_text_into_chunks(raw_text)


def process_csv(csv_path: str) -> List[Document]:
    """Convert CSV to a list of Documents."""
    with open(csv_path, mode="r") as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader)  # Read header
        rows = [",".join(row) for row in reader]
    text_data = "\n".join([",".join(header)] + rows)
    return split_text_into_chunks(text_data)


def split_text_into_chunks(text: str) -> List[Document]:
    """Split text into smaller chunks for processing."""
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=50)
    chunks = text_splitter.split_text(text)
    return [Document(page_content=chunk) for chunk in chunks]


def detect_file_type(file_path: str) -> str:
    """Detect the MIME type of a file."""
    mime = magic.Magic(mime=True)
    return mime.from_file(file_path)


def process_file(file_path: str) -> List[Document]:
    """Determine file type and process accordingly."""
    file_type = detect_file_type(file_path)
    if file_type == "text/plain" or file_type == "text/csv":
        return process_csv(file_path)
    elif file_type == "application/pdf":
        return process_pdf(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


def add_documents_to_graph(documents: List[Document], transformer: LLMGraphTransformer):
    """Add processed documents to the Neo4j graph."""
    try:
        batch_graph_docs = transformer.convert_to_graph_documents(documents)
        graph.add_graph_documents(
            batch_graph_docs,
            baseEntityLabel=True,
            include_source=True,
        )
        Neo4jVector.from_existing_graph(
            embeddModel,
            search_type="hybrid",
            node_label="Document",
            text_node_properties=["text"],
            embedding_node_property="embedding",
        )
        print(f"Processed batch with {len(batch_graph_docs)} documents.")
    except Exception as e:
        print(f"Error processing documents: {e}")


def process_batches(documents: List[Document]):
    """Process document batches using multiple API keys."""
    num_keys = len(GROQ_API_KEYS)
    for i, document_batch in enumerate(documents):
        print(f"Processing batch {i + 1}/{len(documents)}...")
        api_key_index = i % num_keys  # Round-robin API key selection
        transformer = LLMGraphTransformer(llm=get_llm(GROQ_API_KEYS[api_key_index]))
        add_documents_to_graph([document_batch], transformer)
        time.sleep(10)  # Wait for 10 seconds before using the next API key
