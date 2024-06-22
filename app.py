import streamlit as st
import os
import tempfile
from groq import Groq
import json
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Get Groq API key from environment variable
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    st.error("GROQ_API_KEY environment variable not found. Please set your API key.")
    st.stop()

# Initialize Groq API
client = Groq(api_key=GROQ_API_KEY)

# Supported languages list
LANGUAGES = {
    "English": "en",
    "Turkish": "tr",
    "German": "de",
    "French": "fr",
    "Spanish": "es",
    "Italian": "it",
    "Dutch": "nl"
}

def transcribe_audio(audio_file, language):
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".m4a") as tmp_file:
        tmp_file.write(audio_file.read())
        tmp_file_path = tmp_file.name

    logger.debug(f"Temporary file created: {tmp_file_path}")

    # Transcribe using Groq API
    with open(tmp_file_path, "rb") as file:
        file_content = file.read()
        logger.debug(f"File size: {len(file_content)} bytes")

        # Prepare API request parameters
        request_params = {
            "file": (tmp_file_path, file_content),
            "model": "whisper-large-v3",
            "prompt": "Transcribe the following audio",
            "response_format": "json",
            "language": language,
            "temperature": 0.0
        }
        logger.debug(f"API request parameters: {json.dumps(request_params, default=str)}")

        # Send API request
        try:
            transcription = client.audio.transcriptions.create(**request_params)
            logger.debug(f"API response received: {transcription}")
        except Exception as e:
            logger.error(f"Error occurred during API request: {str(e)}")
            raise
    
    # Delete temporary file
    os.unlink(tmp_file_path)
    logger.debug(f"Temporary file deleted: {tmp_file_path}")
    
    return transcription.text

def main():
    st.title("M4A File Transcription and Translation App")

    # Display debug information
    st.sidebar.subheader("Debug Information")
    debug_info = st.sidebar.empty()

    # Language selection for transcription
    transcription_language = st.selectbox(
        "Select transcription language", 
        list(LANGUAGES.keys()),
        key="transcription_language_select"
    )

    # File upload widget
    uploaded_file = st.file_uploader("Upload your M4A file", type=["m4a"])

    if uploaded_file is not None:
        st.audio(uploaded_file, format="audio/m4a")
        st.write(f"Uploaded file: {uploaded_file.name}, Size: {uploaded_file.size} bytes")

        # Update debug information
        debug_info.json({
            "file_name": uploaded_file.name,
            "file_size": uploaded_file.size,
            "transcription_language": transcription_language
        })

        if st.button("Start Transcription"):
            try:
                with st.spinner("Transcribing audio... This may take a few minutes."):
                    logger.debug("Initializing transcription process")
                    transcription = transcribe_audio(uploaded_file, LANGUAGES[transcription_language])
                    logger.debug("Transcription process completed successfully")
                
                st.success("Transcription completed!")
                st.markdown("### Transcription Result")
                st.markdown(transcription)

                # Update debug information
                debug_info.json({
                    "file_name": uploaded_file.name,
                    "file_size": uploaded_file.size,
                    "transcription_language": transcription_language,
                    "transcription_length": len(transcription),
                    "transcription_word_count": len(transcription.split())
                })

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                logger.exception("Error in transcription process")

if __name__ == "__main__":
    main()