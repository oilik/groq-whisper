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

def translate_text(text, target_language):
    prompt = f"Translate the following text to {target_language}:\n\n{text}\n\nTranslation:"
    
    try:
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that translates text accurately."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=4000,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error occurred during translation: {str(e)}")
        raise

def copy_to_clipboard(text):
    pyperclip.copy(text)
    st.success("Copied to clipboard!")

def main():
    st.set_page_config(page_title="Groq Whisper: M4A Transcription & Translation", layout="wide")
    st.title("Groq Whisper: M4A Transcription & Translation")

    # Initialize session state variables
    if 'transcription' not in st.session_state:
        st.session_state.transcription = None
    if 'translation' not in st.session_state:
        st.session_state.translation = None
    if 'transcription_language' not in st.session_state:
        st.session_state.transcription_language = None
    if 'target_language' not in st.session_state:
        st.session_state.target_language = None

    # Display debug information
    st.sidebar.subheader("Debug Information")
    debug_info = st.sidebar.empty()

    # Language selection for transcription
    transcription_language = st.selectbox(
        "Select transcription language", 
        list(LANGUAGES.keys()),
        key="transcription_language_select"
    )
    st.session_state.transcription_language = transcription_language

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
                
                st.session_state.transcription = transcription
                st.success("Transcription completed!")

                # Update debug information
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
            
            # Filter out the transcription language from target language options
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
                        translated_text = translate_text(st.session_state.transcription, target_language)
                    
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