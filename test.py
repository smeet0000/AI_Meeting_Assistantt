from dotenv import load_dotenv
load_dotenv()
from utils.audio_processor import process_input
from core.transcriber import transcribe_all
import os

# print('KEY LOADED:',os.getenv('SARVAM_API_KEY'))
# print('CWD: ',os.getcwd())

source = 'https://youtu.be/U0EI7XFkkV4?si=1L4QKqCg55Gh1GxP'
language = 'hinglish'


chunks = process_input(source= source)
transcript = transcribe_all(chunks=chunks,language=language)

print('\n======Transcript======')
print(transcript)