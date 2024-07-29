import streamlit as st
import os
import tempfile
from groq import Groq
import json
import logging
import pyperclip

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# --- Constants ---
LANGUAGES = {
    "English": "en",
    "Turkish": "tr",
    "German": "de",
    "French": "fr",
    "Spanish": "es",
    "Italian": "it",
    "Dutch": "nl"
}

# --- API Configuration ---
def configure_apis():
    # Groq API
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    if not GROQ_API_KEY:
        st.error("GROQ_API_KEY environment variable not found. Please set your API key.")
        st.stop()
    groq_client = Groq(api_key=GROQ_API_KEY)
    return groq_client

# --- Transcription ---
def transcribe_audio(groq_client, audio_file, language="en"):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".m4a") as tmp_file:
        tmp_file.write(audio_file.read())
        tmp_file_path = tmp_file.name

    logger.debug(f"Temporary file created: {tmp_file_path}")

    try:
        with open(tmp_file_path, "rb") as file:
            file_content = file.read()
            logger.debug(f"File size: {len(file_content)} bytes")

            request_params = {
                "file": (tmp_file_path, file_content),
                "model": "whisper-large-v3",
                "prompt": "Transcribe the following audio",
                "response_format": "json",
                "language": language,
                "temperature": 0.0
            }
            logger.debug(f"API request parameters: {json.dumps(request_params, default=str)}")

            transcription = groq_client.audio.transcriptions.create(**request_params)
            logger.debug(f"API response received: {transcription}")
    except Exception as e:
        logger.error(f"Error occurred during API request: {str(e)}")
        raise
    finally:
        os.unlink(tmp_file_path)
        logger.debug(f"Temporary file deleted: {tmp_file_path}")
    
    return transcription.text

# --- Utility Functions ---
def copy_to_clipboard(text):
    pyperclip.copy(text)
    st.success("Copied to clipboard!")

# --- Main Application ---
def main():
    st.set_page_config(page_title="Groq Whisper: M4A/MP3 Transcription", layout="wide")
    st.title("Groq Whisper: M4A/MP3 Transcription")

    # Initialize APIs
    groq_client = configure_apis()

    # Initialize session state
    if 'transcription' not in st.session_state: st.session_state.transcription = None
    if 'transcription_language' not in st.session_state: st.session_state.transcription_language = None
    
    # --- Sidebar: Debug Information ---
    st.sidebar.subheader("Debug Information")
    debug_info = st.sidebar.empty()

    # --- Language Selection ---
    st.session_state.transcription_language = st.selectbox("Select transcription language", list(LANGUAGES.keys()), key="transcription_language_select")

    # --- File Upload ---
    uploaded_file = st.file_uploader("Upload your M4A or MP3 file", type=["m4a", "mp3"])

    if uploaded_file:
        file_format = uploaded_file.name.split(".")[-1]
        st.audio(uploaded_file, format=f"audio/{file_format}")
        st.write(f"Uploaded file: {uploaded_file.name}, Size: {uploaded_file.size} bytes")

        debug_info.json({"file_name": uploaded_file.name, "file_size": uploaded_file.size, "transcription_language": st.session_state.transcription_language})

        if st.button("Start Transcription"):
            try:
                with st.spinner("Transcribing audio... This may take a few minutes."):
                    logger.debug("Initializing transcription process")
                    st.session_state.transcription = transcribe_audio(groq_client, uploaded_file, LANGUAGES[st.session_state.transcription_language])
                    logger.debug("Transcription process completed successfully")
                st.success("Transcription completed!")

                debug_info.json({"file_name": uploaded_file.name, "file_size": uploaded_file.size, 
                                 "transcription_language": st.session_state.transcription_language,
                                 "transcription_length": len(st.session_state.transcription),
                                 "transcription_word_count": len(st.session_state.transcription.split())})
            except Exception as e:
                st.error(f"An error occurred during transcription: {str(e)}")
                logger.exception("Error in transcription process")

        # --- Display Transcription Result ---
        if st.session_state.transcription:
            st.markdown("### Transcription Result")
            st.text_area("Transcription", st.session_state.transcription, height=200)
            if st.button("Copy Transcription", key="copy_transcription"): copy_to_clipboard(st.session_state.transcription)

if __name__ == "__main__":
    main()