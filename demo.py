import streamlit as st
from pathlib import Path
import os
from open_ai import GPT

# Configure page layout with 3 columns and custom theme
st.set_page_config(layout="wide", page_title="Intel's Personal Educator")

# Custom CSS for styling
st.markdown("""
    <style>
    /* Modern color palette */
    :root {
        --primary-color: #2C3E50;
        --secondary-color: #34495E;
        --accent-color: #3498DB;
        --background-color: #F8F9FA;
        --text-color: #2C3E50;
        --border-radius: 8px;
        --glow-color: rgba(52, 152, 219, 0.5);
    }

    /* Overall app styling */
    .stApp {
        background-color: var(--background-color);
        color: var(--text-color);
    }

    /* Title styling */
    .title {
        color: var(--primary-color);
        font-size: 32px;
        text-align: center;
        font-weight: 600;
        margin-bottom: 2rem;
        text-transform: uppercase;
        letter-spacing: 2px;
    }

    /* Header styling */
    .header {
        color: var(--secondary-color);
        font-size: 16px;
        font-weight: 500;
        margin-bottom: 1rem;
        border-bottom: 2px solid var(--accent-color);
        padding-bottom: 4px;
    }

    /* Chat message styling */
    .assistant-message {
        background-color: white;
        padding: 12px;
        border-radius: var(--border-radius);
        margin: 8px 0;
        color: var(--text-color);
        font-size: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 3px solid var(--accent-color);
    }

    .st-emotion-cache-1vbkxwb p {
        background-color: white;
        padding: 12px;
        border-radius: var(--border-radius);
        margin: 8px 0;
        color: var(--text-color);
        font-size: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 3px solid var(--secondary-color);
    }

    /* Chat container styling */
    .st-emotion-cache-1v0mbdj {
        padding: 1rem;
        border-radius: var(--border-radius);
        background-color: var(--background-color);
    }

    /* Chat input box styling */
    .st-emotion-cache-1x8cf1d {
        font-size: 10px;
        border-radius: var(--border-radius);
        border: 1px solid var(--accent-color);
        padding: 8px;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        font-size: 12px;
        background-color: white !important;
        border-radius: var(--border-radius);
    }

    /* File uploader styling */
    .st-emotion-cache-1gulkj5 {
        font-size: 10px;
        border-radius: var(--border-radius);
    }

    /* Panel styling */
    .element-container, .stTextInput, .stSelectbox, .stFileUploader {
        font-size: 10px !important;
        background-color: white;
        padding: 12px;
        border-radius: var(--border-radius);
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 8px;
    }

    /* Success/Info messages */
    .st-emotion-cache-16idsys p, .st-emotion-cache-1eqh5x p {
        font-size: 10px !important;
        border-radius: var(--border-radius);
    }

    /* Button styling */
    .stButton > button {
        background-color: var(--accent-color);
        color: white;
        border-radius: var(--border-radius);
        border: none;
        padding: 0.5rem 1rem;
        font-size: 10px;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        background-color: var(--secondary-color);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transform: translateY(-1px);
    }

    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: var(--background-color);
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb {
        background: var(--accent-color);
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: var(--secondary-color);
    }

    /* Make all text elements consistent */
    .stMarkdown, .stText, p, label {
        font-size: 10px !important;
        color: var(--text-color);
    }

    /* Row widget styling */
    .row-widget {
        background-color: white;
        padding: 8px;
        border-radius: var(--border-radius);
        margin-bottom: 8px;
    }

    /* Add subtle hover effect */
    .element-container {
        transition: all 0.3s ease;
    }

    .element-container:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    /* Chat input focus state */
    .st-emotion-cache-1x8cf1d:focus {
        border-color: var(--accent-color);
        box-shadow: 0 0 5px rgba(52, 152, 219, 0.3);
    }
    </style>
""", unsafe_allow_html=True)

# Display title
st.markdown("<h1 class='title'>Intel's Personal Educator</h1>", unsafe_allow_html=True)

# Add column width controls in an expander
with st.expander("Layout Settings"):
    left_width = st.slider("Left Panel Width", min_value=1, max_value=5, value=1, key="left_width")
    center_width = st.slider("Center Panel Width", min_value=1, max_value=5, value=3, key="center_width")
    right_width = st.slider("Right Panel Width", min_value=1, max_value=5, value=1, key="right_width")

# Initialize GPT with a more specific system prompt
gpt = GPT(system_prompt="""You are an intelligent AI assistant focused on education. 
Your responses should be informative, clear, and helpful. When explaining concepts, 
use examples and analogies to make them more understandable.""")

# Create three columns with adjustable widths
left_col, center_col, right_col = st.columns([
    st.session_state.get("left_width", 1),
    st.session_state.get("center_width", 3),
    st.session_state.get("right_width", 1)
])

# Left panel - Document upload
with left_col:
    st.markdown("<h2 class='header'>📄 Documents</h2>", unsafe_allow_html=True)
    uploaded_files = st.file_uploader("Upload Documents", accept_multiple_files=True)
    
    if uploaded_files:
        for file in uploaded_files:
            # Save uploaded files
            save_path = Path("uploads") / file.name
            save_path.parent.mkdir(exist_ok=True)
            
            with open(save_path, "wb") as f:
                f.write(file.getvalue())
            
            st.success(f"Uploaded: {file.name}")
            
            # Create video.mp4 after upload (placeholder)
            with open("video.mp4", "wb") as f:
                # Here you would add actual video generation logic
                pass

# Center panel - Video player
with center_col:
    st.markdown("<h2 class='header'>🎥 Video Player</h2>", unsafe_allow_html=True)
    
    if uploaded_files:  # Only show video section after files are uploaded
        video_path = "video.mp4"
        if os.path.exists(video_path):
            st.video(video_path)
        else:
            st.info("Generating video from your documents...")
    else:
        st.info("Upload documents to generate a video presentation.")

# Right panel - Chatbot
with right_col:
    st.markdown("<h2 class='header'>💬 Chat</h2>", unsafe_allow_html=True)
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                st.markdown(f"<div class='assistant-message'>{message['content']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask a question..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get GPT response
        with st.chat_message("assistant"):
            response = gpt.generate_response(prompt)
            st.markdown(f"<div class='assistant-message'>{response}</div>", unsafe_allow_html=True)
            
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
