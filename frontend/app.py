import os
import requests
import streamlit as st
from dotenv import load_dotenv
# Load environment variables
load_dotenv()
API_URL = os.getenv("API_URL")

# API_URL = "http://localhost:5509"
# Custom CSS remains the same
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        .main-container {
            display: flex;
            flex-direction: column;
            height: 100vh;
            overflow: hidden;
            position: relative;
        }
        
        .fixed-header {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: white;
            padding: 1rem;
            z-index: 999;
            text-align: center;
            border-bottom: 1px solid #eee;
            height: 60px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .messages-container {
            flex: 1;
            padding: 1rem;
            margin-top: 60px;
            margin-bottom: 80px;
            overflow-y: auto;
            scrollbar-width: none;
            -ms-overflow-style: none;
        }
        
        .messages-container::-webkit-scrollbar {
            display: none;
        }
        
        .message {
            margin: 8px 0;
            padding: 8px;
            border-radius: 8px;
        }
        
        .user-message {
            background: #f0f0f0;
            margin-left: 20%;
            margin-right: 2%;
            text-align: right;
        }
        
        .bot-message {
            background: #e3f2fd;
            margin-right: 20%;
            margin-left: 2%;
        }
        
        .css-1d391kg {
            padding-top: 0;
        }
        
        .stButton > button {
            height: 38px;
            margin-top: 0 !important;
            background-color: black;
            color: white;
            border-radius: 8px;
        }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'session_id' not in st.session_state:
    st.session_state.session_id = ""
if 'model_name' not in st.session_state:
    st.session_state.model_name = ""
if 'groq_api_key' not in st.session_state:
    st.session_state.groq_api_key = ""
if 'processing' not in st.session_state:
    st.session_state.processing = False

def send_message(user_input):
    if user_input and not st.session_state.processing:
        st.session_state.processing = True
        
        # Add user message immediately
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        payload = {
            "session_id": st.session_state.session_id if st.session_state.session_id else None,
            "question": user_input
        }
        params = {}
        if st.session_state.model_name:
            params["model"] = st.session_state.model_name
        if st.session_state.groq_api_key:
            params["groq_api_key"] = st.session_state.groq_api_key

        try:
            response = requests.post(f"{API_URL}/chat", json=payload, params=params)
            if response.status_code == 200:
                data = response.json()
                bot_response = data["response"]
                st.session_state.messages.append({"role": "bot", "content": bot_response})
            else:
                st.error(f"Error: {response.json()['detail']}")
        except Exception as e:
            st.error(f"Request failed: {e}")
        finally:
            st.session_state.processing = False
            # Force a rerun to update the UI
            st.rerun()

def process_file(file, code):
    try:
        with st.spinner("Processing file..."):
            files = {"file": (file.name, file.getvalue())}
            data = {"code": code} if code else {}
            response = requests.post(f"{API_URL}/process", files=files, data=data)

            if response.status_code == 200:
                st.success(response.json().get("message", "File processed successfully!"))
            else:
                st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
    except Exception as e:
        st.error(f"Request failed: {e}")

# Sidebar for navigation and settings
st.sidebar.title("Navigation")
task_option = st.sidebar.radio("Choose a task:", ["Chat with Bot", "Process File"])

if task_option == "Chat with Bot":
    st.session_state.session_id = st.sidebar.text_input("Session ID (optional):", value=st.session_state.session_id)
    st.session_state.model_name = st.sidebar.text_input("Model Name (optional):", value=st.session_state.model_name)
    st.session_state.groq_api_key = st.sidebar.text_input("Groq API Key (optional):", type="password", value=st.session_state.groq_api_key)

    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    st.markdown('<div class="fixed-header"><h1>AI AssistPro</h1></div>', unsafe_allow_html=True)
    st.markdown('<div class="messages-container">', unsafe_allow_html=True)

    # Display messages
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f'<div class="message user-message">🧑‍💻 {message["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="message bot-message">🤖 {message["content"]}</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Chat input
    user_input = st.chat_input("Ask your question...")
    if user_input:
        send_message(user_input)

elif task_option == "Process File":
    st.markdown('<div style="padding: 1rem;">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload a file:", type=["txt", "csv", "pdf"])
    code = st.sidebar.text_input("Code (optional):", type="password")
    if st.button("Process File"):
        if uploaded_file:
            process_file(uploaded_file, code)
        else:
            st.warning("Please upload a file.")
    st.markdown('</div>', unsafe_allow_html=True)