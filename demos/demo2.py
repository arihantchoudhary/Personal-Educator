from open_ai import GPT
import streamlit as st
from pdf2image import convert_from_bytes
from PyPDF2 import PdfReader
import os

if 'pdf_uploaded' not in st.session_state:
    st.session_state.pdf_uploaded = False

# Check for API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key or not api_key.startswith("sk-"):
    st.error("Please set a valid OpenAI API key in your .env file. The key should start with 'sk-' and can be found at https://platform.openai.com/account/api-keys")
    st.stop()

uploaded_file = st.file_uploader("Choose a PDF file", type=['pdf'])

if uploaded_file is not None:
    pdf_bytes = uploaded_file.read()
    st.session_state.pdf_uploaded = True


if st.session_state.get("pdf_uploaded"):
    pages = convert_from_bytes(pdf_bytes)
    st.write(f"Total pages: {len(pages)}")
    st.session_state.pages = {}
    cols = st.columns(len(pages))
    for i, (page, col) in enumerate(zip(pages, cols)):
        with col:
            st.image(page, caption=f"Page {i+1}")
            st.write(f"Page {i+1}")
            st.session_state.pages[i+1] = page

    st.write(st.session_state.pages)


    with open(uploaded_file.name, "wb") as f:
        f.write(pdf_bytes)

    pdf = PdfReader(uploaded_file.name)
    page_ocrs = {}
    for i in range(len(pages)):
        page = pdf.pages[i]
        text = page.extract_text()
        page_ocrs[i+1] = text

    st.session_state.page_ocrs = page_ocrs

    selected_pages = st.multiselect(
        "Select pages to display their OCR", 
        list(page_ocrs.keys())
    )

    for i in selected_pages:
        with st.expander(f"Page {i} OCR"):
            st.write(page_ocrs[i])

    try:
        gpt = GPT(
            api_key=api_key,
            system_prompt="You are an intelligent AI assistant focused on education. Your responses should be informative, clear, and helpful. When explaining concepts, use examples and analogies to make them more understandable.",
            model="gpt-4",
            temperature=0.7,
            max_tokens=1000
        )
        
        with st.spinner("Generating educational transcripts..."):
            page_transcripts = {}
            for page, text in page_ocrs.items():
                transcript = gpt.generate_response(
                    user_prompt=f"Please provide a natural lecture transcript for presenting this slide content:\n\n{text}"
                )
                if transcript:  # Only add if we got a valid response
                    page_transcripts[page] = transcript
                else:
                    st.error(f"Failed to generate transcript for page {page}")
                    continue

            if page_transcripts:  # Only show if we have any transcripts
                st.session_state.page_transcripts = page_transcripts

                selected_pages = st.multiselect(
                    "Select pages to display their transcripts", 
                    list(page_transcripts.keys())
                )

                for i in selected_pages:
                    with st.expander(f"Page {i} Transcript"):
                        st.write(page_transcripts[i])
            else:
                st.error("Failed to generate any transcripts. Please check your API key and try again.")
    except Exception as e:
        st.error(f"An error occurred while generating transcripts: {str(e)}")
    
    if "page_transcripts" in st.session_state:
        selected_pages = st.multiselect(
            "Select pages to display their transcripts", 
            list(st.session_state.page_transcripts.keys())
        )

        for i in selected_pages:
            with st.expander(f"Page {i} Transcript"):
                st.write(st.session_state.page_transcripts[i])
