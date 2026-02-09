from flask import Flask, render_template, request
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'recordings'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit-audio', methods=['POST'])
def submit_audio():
    audio = request.files['audio_data']
    if audio:
        filepath = os.path.join(UPLOAD_FOLDER, audio.filename)
        audio.save(filepath)
        return 'Audio submitted successfully!'
    return 'No audio received.', 400

if __name__ == '__main__':
    app.run(debug=True)
