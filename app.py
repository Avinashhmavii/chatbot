import streamlit as st
import os
import tempfile
from groq import Groq
from PyPDF2 import PdfReader
from docx import Document
import pandas as pd

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "processed_text" not in st.session_state:
    st.session_state.processed_text = ""

# Updated list of verified available models
MODEL_OPTIONS = [
    "llama3-70b-8192",          # Meta's Llama 3 70B
    "llama3-8b-8192",           # Meta's Llama 3 8B
    "deepseek-r1-distill-qwen-32b",       # deepseek
    "gemma2-9b-it",              # Google's Gemma 9B
    "whisper-large-v3",          # Meta's Llama 2 70B
]

# Streamlit app configuration
st.set_page_config(page_title="Groq Chat Assistant", page_icon="🤖")

# Sidebar configuration
with st.sidebar:
    st.title("Groq Settings")
    groq_api_key = st.text_input("Enter Groq API Key", type="password")
    selected_model = st.selectbox("Choose a Model", MODEL_OPTIONS)
    
    st.markdown("---")
    st.markdown("### File Upload Settings")
    uploaded_files = st.file_uploader(
        "Upload files (PDF, Word, CSV, Excel)",
        type=["pdf", "docx", "csv", "xlsx"],
        accept_multiple_files=True
    )

# Process uploaded files (keep the same as before)
def process_files(uploaded_files):
    all_text = ""
    for file in uploaded_files:
        file_type = file.name.split(".")[-1]
        
        try:
            if file_type == "pdf":
                reader = PdfReader(file)
                text = "".join([page.extract_text() for page in reader.pages])
            elif file_type == "docx":
                doc = Document(file)
                text = "\n".join([para.text for para in doc.paragraphs])
            elif file_type == "csv":
                df = pd.read_csv(file)
                text = df.to_string()
            elif file_type == "xlsx":
                df = pd.read_excel(file)
                text = df.to_string()
            else:
                text = f"Unsupported file type: {file_type}"
            
            all_text += f"\n\nFile: {file.name}\n{text}"
        
        except Exception as e:
            all_text += f"\n\nError processing {file.name}: {str(e)}"
    
    return all_text
# Process files when uploaded
if uploaded_files:
    st.session_state.processed_text = process_files(uploaded_files)

# Main chat interface
st.title("💬 Chat Assistant")
st.caption("🚀 A chatbot powered by Groq LLMs")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input and processing
if prompt := st.chat_input("Ask me anything..."):
    if not groq_api_key:
        st.error("Please enter your Groq API key in the sidebar")
        st.stop()
    
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Prepare context
    context = f"""
    User Question: {prompt}
    
    Uploaded Files Context: {st.session_state.processed_text}
    
    Please answer the question based on the provided context and your general knowledge.
    """
    
    try:
        # Initialize Groq client
        client = Groq(api_key=groq_api_key)
        
        # Create chat completion
        response = client.chat.completions.create(
            messages=[{"role": m["role"], "content": context + m["content"]} 
                     for m in st.session_state.messages],
            model=selected_model,
            temperature=0.5,
            max_tokens=2048
        )
        
        # Get AI response
        ai_response = response.choices[0].message.content
        
        # Add AI response to chat history
        st.session_state.messages.append({"role": "assistant", "content": ai_response})
        
        # Display AI response
        with st.chat_message("assistant"):
            st.markdown(ai_response)
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
