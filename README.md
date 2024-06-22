# Groq Whisper: M4A File Transcription and Translation App

This Streamlit application allows users to upload M4A audio files, transcribe them using the Groq API with the Whisper model, and translate the transcriptions to multiple languages.

## Features

- Upload M4A audio files
- Transcribe audio in multiple languages using Groq's Whisper implementation
- Translate transcriptions to various languages using Google's Gemini model
- Copy transcriptions and translations to clipboard
- User-friendly interface with Streamlit
- Debug information display
- Error handling and logging

## Requirements

- Python 3.7+
- Streamlit
- Groq API
- Google GenerativeAI API
- pyperclip

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/oilik/groq-whisper.git
   cd groq-whisper
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Set up your API keys as environment variables:
   ```
   export GROQ_API_KEY=your_groq_api_key_here
   export GOOGLE_API_KEY=your_google_api_key_here
   ```

## Usage

Run the Streamlit app:

```
streamlit run app.py
```

Then, open your web browser and go to the URL displayed in the terminal (usually `http://localhost:8501`).

## How it works

1. Upload an M4A file through the Streamlit interface.
2. Select the language of the audio content for transcription.
3. Click "Start Transcription" to begin the process.
4. The app will use the Groq API to transcribe the audio using the Whisper model.
5. Once complete, the transcription will be displayed on the page.
6. Select a target language and click "Translate" to translate the transcription.
7. The translation will be displayed, and you can copy both the transcription and translation to your clipboard.

## Key Components

- `transcribe_audio()`: Handles audio file transcription using Groq's Whisper model.
- `translate_text()`: Translates text using Google's Gemini model.
- `copy_to_clipboard()`: Allows users to easily copy text to their clipboard.
- Error handling and logging throughout the application for better debugging.

## Supported Languages

The app supports transcription and translation for multiple languages, including:
- English
- Turkish
- German
- French
- Spanish
- Italian
- Dutch

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[MIT License](LICENSE)