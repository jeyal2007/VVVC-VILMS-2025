from flask import Flask, request, send_file, abort
from googletrans import Translator
from gtts import gTTS
import fitz  # PyMuPDF
import io
import os

app = Flask(__name__)

def extract_text_from_pdf_blob(blob):
    pdf_stream = io.BytesIO(blob)
    doc = fitz.open(stream=pdf_stream, filetype="pdf")
    return "\n".join(page.get_text() for page in doc)

def translate_to_tamil(text):
    translator = Translator()
    translated = translator.translate(text, dest='ta')
    return translated.text

def speak_tamil_text(text, filename="output.mp3"):
    tts = gTTS(text=text, lang='ta')
    tts.save(filename)
    return filename

def convert_pdf_to_tamil_audio(pdf_blob, output_file="tamil_audio.mp3"):
    extracted_text = extract_text_from_pdf_blob(pdf_blob)
    if not extracted_text.strip():
        raise ValueError("No text found in the PDF.")
    tamil_text = translate_to_tamil(extracted_text)
    return speak_tamil_text(tamil_text, output_file)

@app.route("/", methods=["GET", "POST"])
def upload_pdf():
    if request.method == "POST":
        file = request.files.get("pdf_file")
        if file and file.filename.endswith(".pdf"):
            try:
                pdf_blob = file.read()
                output_audio_path = convert_pdf_to_tamil_audio(pdf_blob)
                return send_file(output_audio_path, as_attachment=True)
            except Exception as e:
                return f"<h2 style='color:red;'>Error: {e}</h2>"
        else:
            return "<h2 style='color:red;'>Invalid file. Please upload a PDF.</h2>"

    return '''
        <!DOCTYPE html>
        <html>
        <head><title>PDF to Tamil Audio</title></head>
        <body style="background-color:#e0f7fa; text-align:center; padding:50px;">
            <h1>Upload PDF to Convert to Tamil Audio 🎧</h1>
            <form method="POST" enctype="multipart/form-data">
                <input type="file" name="pdf_file" accept=".pdf" required>
                <br><br>
                <input type="submit" value="Convert & Download">
            </form>
        </body>
        </html>
    '''

if __name__ == "__main__":
    app.run(debug=True)
