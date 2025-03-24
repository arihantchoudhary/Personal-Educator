import streamlit as st
import pdfplumber
from PIL import Image
from open_ai import GPT
import os
import io
from pdf2image import convert_from_bytes
import cv2
import ffmpeg
import numpy as np
import tempfile

class PDFProcessor:
    def __init__(self):
        self.initialize_session_state()
        
    def initialize_session_state(self):
        """Initialize Streamlit session state variables"""
        if 'uploaded_file_data' not in st.session_state:
            st.session_state.uploaded_file_data = None
            st.session_state.extracted_content = None

            
    def extract_content(self, pdf_bytes):
        """Extract text, tables and images from PDF"""
        extracted_content = {}
        
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for i, page in enumerate(pdf.pages):
                page_content = []
                
                # Extract text
                if text := page.extract_text():
                    st.write(text)
                    page_content.append(text)
                
                # Extract tables 
                if tables := page.extract_tables():
                    page_content.append(tables)
                    
                # Extract images
                if images := page.images:
                    page_content.append(images)
                    
                extracted_content[f'slide_{i+1}.pdf'] = page_content
                
        return extracted_content

    def accept_file(self):
        """Handle file upload through Streamlit"""
        uploaded_file = st.file_uploader("Choose a PDF file", type=['pdf'])
        
        if uploaded_file is not None:
            return uploaded_file.read()
        return None

    def generate_slide_videos(self, gpt_instance):
        """Generate videos for each slide with audio narration and combine them"""
        if not st.session_state.extracted_content:
            st.warning("Please upload a PDF first")
            return

        st.write("### Generating slide videos...")
        
        # Convert PDF pages to images
        with st.spinner("Converting PDF pages to images..."):
            slides = convert_from_bytes(st.session_state.uploaded_file_data)
        
        # Create temporary directory for intermediate files
        with tempfile.TemporaryDirectory() as temp_dir:
            slide_videos = []
            
            for i, (slide_name, content) in enumerate(st.session_state.extracted_content.items()):
                st.write(f"Processing {slide_name}...")
                
                # Extract text content from the slide
                slide_text = next((item for item in content if isinstance(item, str)), "")
                
                if slide_text:
                    # Generate transcript
                    with st.spinner(f"Generating transcript for {slide_name}..."):
                        transcript = gpt_instance.generate_response(
                            user_prompt=f"""Here is the content from {slide_name}:
                            
                            {slide_text}
                            
                            Please provide a natural lecture transcript for presenting this slide content.""",
                            temperature=0.7
                        )
                    
                    # Generate audio from transcript
                    with st.spinner(f"Generating audio for {slide_name}..."):
                        speech_file = gpt_instance.client.audio.speech.create(
                            model="tts-1",
                            voice="onyx",
                            input=transcript
                        )
                        
                        # Save audio to temporary file
                        audio_path = f"{temp_dir}/slide_{i}_audio.mp3"
                        with open(audio_path, 'wb') as f:
                            f.write(speech_file.content)
                    
                    # Save slide image
                    image_path = f"{temp_dir}/slide_{i}.png"
                    slides[i].save(image_path, 'PNG')
                    
                    # Create video for this slide
                    with st.spinner(f"Creating video for {slide_name}..."):
                        # Get audio duration using ffmpeg
                        probe = ffmpeg.probe(audio_path)
                        audio_duration = float(probe['streams'][0]['duration'])
                        
                        # Read the image
                        img = cv2.imread(image_path)
                        height, width = img.shape[:2]
                        
                        # Create video writer
                        video_path = f"{temp_dir}/slide_{i}.mp4"
                        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                        out = cv2.VideoWriter(video_path, fourcc, 30, (width, height))
                        
                        # Write the same image for duration * fps frames
                        for _ in range(int(audio_duration * 30)):  # 30 fps
                            out.write(img)
                        
                        out.release()
                        
                        # Combine video and audio using ffmpeg
                        final_slide_path = f"{temp_dir}/slide_{i}_with_audio.mp4"
                        stream = ffmpeg.input(video_path)
                        audio = ffmpeg.input(audio_path)
                        stream = ffmpeg.output(stream, audio, final_slide_path, vcodec='copy', acodec='aac')
                        ffmpeg.run(stream, overwrite_output=True)
                        
                        slide_videos.append(final_slide_path)
                        
                        # Display progress
                        st.subheader(f"📝 {slide_name}")
                        st.text("Original Content:")
                        st.text(slide_text)
                        st.text("Professor's Transcript:")
                        st.write(transcript)
                        st.audio(speech_file.content, format='audio/mp3')
                        st.image(image_path)
            
            # Combine all videos using ffmpeg
            with st.spinner("Combining all slides into final video..."):
                # Create a file with input filenames
                concat_file = f"{temp_dir}/concat.txt"
                with open(concat_file, 'w') as f:
                    for video_path in slide_videos:
                        f.write(f"file '{video_path}'\n")
                
                # Use ffmpeg to concatenate videos
                final_path = "lecture.mp4"
                stream = ffmpeg.input(concat_file, format='concat', safe=0)
                stream = ffmpeg.output(stream, final_path, c='copy')
                ffmpeg.run(stream, overwrite_output=True)
            
            # Display final video
            st.write("### Final Lecture Video")
            st.video(final_path)

    def process(self):
        """Main processing function"""
        if pdf_bytes := self.accept_file():
            st.session_state.uploaded_file_data = pdf_bytes
            st.session_state.extracted_content = self.extract_content(pdf_bytes)
            
            # Initialize GPT instance
            gpt = GPT(system_prompt="You are an experienced professor giving a lecture.")
            
            # Generate videos
            self.generate_slide_videos(gpt)

# Initialize and run
pdf_processor = PDFProcessor()
pdf_processor.process()
