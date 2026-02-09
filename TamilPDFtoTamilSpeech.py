import fitz  # PyMuPDF
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
import os

# Load Tamil PDF
pdf_path = "Tamil.pdf"
doc = fitz.open(pdf_path)

# Extract all text
full_text = ""
for page in doc:
    text = page.get_text()
    full_text += text.strip() + " "

# Safety check
if not full_text.strip():
    raise ValueError("No text found in PDF.")

# Convert text to speech in Tamil
tts = gTTS(text=full_text, lang='ta', slow=True)
mp3_path = "tamil_audio.mp3"
tts.save(mp3_path)

# Play the audio (optional)
audio = AudioSegment.from_mp3(mp3_path)
play(audio)

print("✔ Tamil audio generated and played successfully.")
