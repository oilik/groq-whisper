import streamlit as st
import os
import tempfile
from groq import Groq
import google.generativeai as genai
import json
import logging
import pyperclip

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Constants
LANGUAGES = {
    "English": "en",
    "Turkish": "tr",
    "German": "de",
    "French": "fr",
    "Spanish": "es",
    "Italian": "it",
    "Dutch": "nl"
}

# API Configuration
def configure_apis():
    # Groq API
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    if not GROQ_API_KEY:
        st.error("GROQ_API_KEY environment variable not found. Please set your API key.")
        st.stop()
    groq_client = Groq(api_key=GROQ_API_KEY)

    # Google API
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    genai.configure(api_key=GOOGLE_API_KEY)

    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
    }

    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

    MODEL_NAME = "gemini-1.5-flash-001"

    google_model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        generation_config=generation_config,
        safety_settings=safety_settings,
    )

    return groq_client, google_model

# Transcription
def transcribe_audio(groq_client, audio_file, language):
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

# Translation
def translate_text(google_model, text, transcription_language, target_language):
    system_instruction = [
        f"You are a helpful language translator.",
        f"Your mission is to translate text from {transcription_language} to {target_language}.",
        "Ensure that the translation maintains the original meaning, tone, and style as much as possible.",
        "If there are any cultural nuances or idiomatic expressions, try to find appropriate equivalents in the target language."
    ]

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash-latest",
        system_instruction=system_instruction,
    )
    
    prompt = f"""{text}"""
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error occurred during translation: {str(e)}")
        raise

# Utility functions
def copy_to_clipboard(text):
    pyperclip.copy(text)
    st.success("Copied to clipboard!")

# Main application
def main():
    st.set_page_config(page_title="Groq Whisper: M4A Transcription & Translation", layout="wide")
    st.title("Groq Whisper: M4A Transcription & Translation")

    # Initialize APIs
    groq_client, google_model = configure_apis()

    # Initialize session state
    for key in ['transcription', 'translation', 'transcription_language', 'target_language']:
        if key not in st.session_state:
            st.session_state[key] = None

    # Debug information
    st.sidebar.subheader("Debug Information")
    debug_info = st.sidebar.empty()

    # Language selection
    transcription_language = st.selectbox(
        "Select transcription language", 
        list(LANGUAGES.keys()),
        key="transcription_language_select"
    )
    st.session_state.transcription_language = transcription_language

    # File upload
    uploaded_file = st.file_uploader("Upload your M4A file", type=["m4a"])

    if uploaded_file:
        st.audio(uploaded_file, format="audio/m4a")
        st.write(f"Uploaded file: {uploaded_file.name}, Size: {uploaded_file.size} bytes")

        debug_info.json({
            "file_name": uploaded_file.name,
            "file_size": uploaded_file.size,
            "transcription_language": transcription_language
        })

        if st.button("Start Transcription"):
            try:
                with st.spinner("Transcribing audio... This may take a few minutes."):
                    logger.debug("Initializing transcription process")
                    transcription = transcribe_audio(groq_client, uploaded_file, LANGUAGES[transcription_language])
                    logger.debug("Transcription process completed successfully")
                
                st.session_state.transcription = transcription
                st.success("Transcription completed!")

                debug_info.json({
                    "file_name": uploaded_file.name,
                    "file_size": uploaded_file.size,
                    "transcription_language": transcription_language,
                    "transcription_length": len(transcription),
                    "transcription_word_count": len(transcription.split())
                })
            except Exception as e:
                st.error(f"An error occurred during transcription: {str(e)}")
                logger.exception("Error in transcription process")

        # Display transcription result
        if st.session_state.transcription:
            st.markdown("### Transcription Result")
            st.text_area("Transcription", st.session_state.transcription, height=200)
            if st.button("Copy Transcription", key="copy_transcription"):
                copy_to_clipboard(st.session_state.transcription)

            # Translation section
            st.markdown("### Translate Transcription")
            
            target_languages = [lang for lang in LANGUAGES.keys() if lang != st.session_state.transcription_language]
            
            col1, col2 = st.columns([1, 6])
            
            with col1:
                translate_button = st.button("Translate", key="translate_button")
            
            with col2:
                target_language = st.selectbox(
                    "",
                    target_languages,
                    key="translation_language_select",
                    label_visibility="collapsed"  
                )
            
            st.session_state.target_language = target_language

            if translate_button:
                try:
                    with st.spinner("Translating... This may take a moment."):
                        translated_text = translate_text(google_model, st.session_state.transcription, transcription_language, target_language)
                    
                    st.session_state.translation = translated_text
                except Exception as e:
                    st.error(f"An error occurred during translation: {str(e)}")
                    logger.exception("Error in translation process")

            # Display translation result
            if st.session_state.translation:
                st.markdown("### Translation Result")
                st.text_area("Translation", st.session_state.translation, height=200)
                if st.button("Copy Translation", key="copy_translation"):
                    copy_to_clipboard(st.session_state.translation)

if __name__ == "__main__":
    main()