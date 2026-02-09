from flask import Flask, request, jsonify, render_template, render_template_string,redirect,url_for,session, flash
import whisper
import os
import base64
import tempfile
from flask import send_file, abort
import io
import pyttsx3

import pandas as pd
from io import BytesIO

from datetime import datetime
import subprocess
import sqlite3
import fitz  
from gtts import gTTS
from langdetect import detect
from googletrans import Translator


app = Flask(__name__)
app.secret_key = 'vvvc' 
UPLOAD_FOLDER = 'recordings'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

model = whisper.load_model("base")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/studentlogin')
def student_login():
    return render_template('studentlogin.html') 

@app.route('/teacherlogin')
def teacher_login():
    return render_template('teacherlogin.html') 

# Route to show the student add form
@app.route('/studentadd', methods=['GET', 'POST'])
def studentadd():
    if 'username' not in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            from datetime import datetime

            register_number = request.form['register_number']
            name = request.form['name']
            dname = request.form['dname']
            year = int(request.form.get('year_of_joining'))
            phone = int(request.form.get('phone_number'))

            if not year or not phone:
                return "Year of Joining or Phone Number is missing", 400

            year = int(year)
            phone = int(phone)

            # Get current year
            current_year = datetime.now().year
            year_diff = current_year - year  # year is already converted to int above

            # Determine class level
            if year_diff == 0:
                class_level = "I"
            elif year_diff == 1:
                class_level = "II"
            elif year_diff == 2:
                class_level = "III"
            else:
                class_level = "Alumni"  # or handle future/invalid cases
            class_name = f"{class_level} {dname}"
            graduate = request.form['graduate']
            dob = request.form['dob']
            propic = request.files.get('profile_picture')
            idcard = request.files.get('idcard_image')
            pwd = request.files.get('pwd_certificate_image')

            propic = propic.read() if propic and propic.filename != '' else None
            idcard = idcard.read() if idcard and idcard.filename != '' else None
            pwd = pwd.read() if pwd and pwd.filename != '' else None

            username = register_number[:2] + register_number[-2:]
            dob_day = datetime.strptime(dob, "%Y-%m-%d").day
            dob_year = datetime.strptime(dob, "%Y-%m-%d").year
            password = f"{dob_day:02d}{dob_year % 100:02d}"

            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()

            # Get did from department table
            cursor.execute("SELECT did FROM department WHERE dname = ?", (dname,))
            result = cursor.fetchone()
            if not result:
                return "Department not found", 404
            did = result[0]

            # Insert student
            cursor.execute("""
                INSERT INTO student (
                    register_number, name, class, department, year_of_joining, phone_number,
                    profile_picture, idcard_image, pwd, username, password, graduate, dob
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (register_number, name, class_name, dname, year, phone, propic, idcard, pwd, username, password, graduate, dob))

            # Insert login credentials
            cursor.execute("""
                INSERT INTO users (username, password)
                VALUES (?, ?)
            """, (username, password))

            conn.commit()
            conn.close()
            return redirect('/adashboard')

        except Exception as e:
            return f"Error: {e}", 500

    # For GET method – load department names for the form
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT dname FROM department")
    departments = [row[0] for row in cursor.fetchall()]
    conn.close()

    return render_template("studentadd.html", username=session.get('username'), departments=departments)

@app.route('/teacheradd')
def teacheradd():
    if 'username' not in session:
        return redirect(url_for('admin_login'))
    
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT dname FROM department")
    departments = [row[0] for row in cursor.fetchall()]
    conn.close()

    return render_template("teacheradd.html", username=session.get('username'), departments=departments)

@app.route('/teacheradd', methods=['POST'])
def register_teacher():
    try:
        tid = request.form['tid']
        tname = request.form['name']
        dname = request.form['dname']
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        # Get the did based on selected dname
        cursor.execute("SELECT did FROM department WHERE dname = ?", (dname,))
        result = cursor.fetchone()
        if not result:
            return "Department not found", 404
        did = result[0]

        # Insert into teacher table
        cursor.execute("""
            INSERT INTO teacher (tid, tname, designation, did, dname, exp, propic, idcard, username, password)
            VALUES (?, ?, NULL, ?, ?, NULL, NULL, NULL, ?, ?)
        """, (tid, tname, did, dname, username, password))

        # Insert into users table
        cursor.execute("""
            INSERT INTO users (username, password)
            VALUES (?, ?)
        """, (username, password))

        conn.commit()
        conn.close()
        return redirect('/adashboard')

    except Exception as e:
        return f"Error: {e}", 500

@app.route('/teacherstudentmapping', methods=['GET', 'POST'])
def teacherstudentmapping():
    if 'username' not in session:
        return redirect(url_for('tlogin'))

    tid = session.get('tid')

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        courseid = request.form.get('courseid')
        student_ids = request.form.getlist('student_ids')

        for sid in student_ids:
            cursor.execute("""
                INSERT OR IGNORE INTO student_course_mapping (courseid, register_number, tid)
                VALUES (?, ?, ?)
            """, (courseid, sid, tid))
        
        conn.commit()
        conn.close()
        return redirect(url_for('tdashboard'))

    # Fetch teacher's courses
    cursor.execute("SELECT courseid, coursetitle FROM teacher_course WHERE tid = ?", (tid,))
    teacher_courses = cursor.fetchall()

    # Fetch all students
    cursor.execute("SELECT register_number, name FROM student")
    students = cursor.fetchall()

    conn.close()
    return render_template("teacherstudentmapping.html", teacher_courses=teacher_courses, students=students, username=session.get('username'))

@app.route('/coursecontent', methods=['GET'])
def coursecontent():
    if 'tid' not in session:
        return redirect(url_for('tlogin'))

    tid = session['tid']

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Get courses mapped to this teacher
    cursor.execute("SELECT coursetitle FROM teacher_course WHERE tid=?", (tid,))
    courses = [row[0] for row in cursor.fetchall()]

    # Get uploaded course content
    cursor.execute("SELECT rowid, topic FROM coursecontent WHERE tid=?", (tid,))
    uploaded_contents = cursor.fetchall()

    conn.close()
    
    return render_template('coursecontent.html', username=session.get('username'), courses=courses, uploaded_contents=uploaded_contents)

@app.route('/upload_course_content', methods=['POST'])
def upload_course_content():
    try:
        if 'username' not in session:
            flash("Session expired. Please log in again.")
            return redirect('/')

        # DB connect
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        # Teacher ID
        cursor.execute("SELECT tid FROM teacher WHERE username = ?", (session['username'],))
        tid_row = cursor.fetchone()
        if not tid_row:
            flash("Teacher ID not found.")
            return redirect('/coursecontent')
        tid = tid_row[0]

        # Form fields
        course_title = request.form['course']
        unit = request.form['unit']
        topic = request.form['topic']
        language = request.form['language']   # ENGLISH or TAMIL

        # Course ID
        cursor.execute("SELECT courseid FROM teacher_course WHERE tid = ? AND coursetitle = ?", (tid, course_title))
        course_row = cursor.fetchone()
        if not course_row:
            flash("Course ID not found.")
            return redirect('/coursecontent')
        courseid = course_row[0]

        # Files
        pdf_data = request.files['pdf_file'].read() if 'pdf_file' in request.files and request.files['pdf_file'].filename else None
        mp3_data = None  
        if language.upper() == "ENGLISH" and pdf_data:
            try:
                import fitz, os, time
                from gtts import gTTS  
  
                pdf_doc = fitz.open(stream=pdf_data, filetype="pdf")
                text = "".join([page.get_text() for page in pdf_doc])
 
            # fallback if PDF has no text
                if not text.strip():
                    text = "No readable text found in PDF."

            # gTTS with Indian female slow English
                tts = gTTS(text=text, lang="en", tld="co.in")
                temp_file = "temp_audio.mp3"
                tts.save(temp_file)

            # Wait until file exists & is not empty
                for _ in range(10):
                    if os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
                        break
                    time.sleep(0.2)

                if os.path.exists(temp_file):
                    with open(temp_file, "rb") as f:
                        mp3_data = f.read()
                    os.remove(temp_file)

            except Exception as tts_err:
                print("TTS Conversion Error:", str(tts_err))
                mp3_data = None
            
        elif language.upper() == "TAMIL":
             mp3_data = request.files['audio_file'].read() if 'audio_file' in request.files and request.files['audio_file'].filename else None

        # Mock test
        mocktest_data = request.files['mocktest_file'].read() if 'mocktest_file' in request.files and request.files['mocktest_file'].filename else None

        # Insert row
        cursor.execute("""
            INSERT INTO coursecontent (tid, courseid, coursetitle, unit, topic, content, audio, mocktest)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (tid, courseid, course_title, unit, topic, pdf_data, mp3_data, mocktest_data))

        conn.commit()
        conn.close()

        flash("Course content uploaded successfully!")
        return redirect('/coursecontent')

    except Exception as e:
        print("Upload Error:", str(e))
        flash("Error uploading course content.")
        return redirect('/coursecontent')



def extract_text_from_pdf_blob(blob):
    pdf_stream = io.BytesIO(blob)
    doc = fitz.open(stream=pdf_stream, filetype="pdf")
    return "\n".join(page.get_text() for page in doc)

def detect_language(text):
    translator = Translator()
    detection = translator.detect(text)
    return detection.lang  # e.g., 'en', 'ta', etc.

def speak_text_auto_language(text, filename="output.mp3"):
    lang = detect_language(text)
    tts = gTTS(text=text, lang=lang)
    tts.save(filename)
    return filename

def convert_pdf_to_audio_auto_lang(pdf_blob, output_file="auto_audio.mp3"):
    text = extract_text_from_pdf_blob(pdf_blob)
    return speak_text_auto_language(text, output_file)
    
# download course content
@app.route("/download/<filetype>/<int:rowid>")
def download_file(filetype, rowid):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    if filetype == "pdf":
        cursor.execute("SELECT content FROM coursecontent WHERE rowid = ?", (rowid,))
        file_data = cursor.fetchone()
        mime_type = "application/pdf"
        filename = "transcript.pdf"
    else:
        conn.close()
        return "Invalid file type", 400

    conn.close()

    if file_data and file_data[0]:
        return send_file(
            io.BytesIO(file_data[0]),
            mimetype=mime_type,
            as_attachment=False,
            download_name=filename
        )
    else:
        return "File not found", 404

def convert_pdf_blob_to_audio(pdf_blob, output_path='output.mp3'):
    try:
        # Load PDF from bytes
        pdf_stream = io.BytesIO(pdf_blob)
        doc = fitz.open(stream=pdf_stream, filetype='pdf')

        # Extract text from all pages
        full_text = ""
        for page in doc:
            full_text += page.get_text()

        if not full_text.strip():
            raise ValueError("No text found in PDF.")

        # Convert text to speech using gTTS
        tts = gTTS(text=full_text, lang='en')
        tts.save(output_path)
        return output_path
    except Exception as e:
        print("Error generating audio:", e)
        return None

@app.route('/play_audio/<int:rowid>')
def play_audio(rowid):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT audio FROM coursecontent WHERE rowid = ?", (rowid,))
    row = cursor.fetchone()
    conn.close()

    if row and row[0]:
        return send_file(io.BytesIO(row[0]), mimetype="audio/mpeg")
    else:
        return "No audio available", 404

@app.route("/download/audio/<int:rowid>")
def download_audio(rowid):
    # Step 1: Connect and fetch PDF blob
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM coursecontent WHERE rowid = ?", (rowid,))
    row = cursor.fetchone()
    conn.close()

    if not row or not row[0]:
        return abort(404, "Transcript PDF not found")

    pdf_blob = row[0]

    # Step 2: Extract text from PDF blob using PyMuPDF
    try:
        pdf_stream = io.BytesIO(pdf_blob)
        doc = fitz.open("pdf", pdf_stream)
        text = "\n".join([page.get_text() for page in doc])
    except Exception as e:
        return abort(500, f"PDF processing failed: {e}")

    if not text.strip():
        return abort(400, "No readable text found in the PDF")

    # Step 3: Convert text to audio using pyttsx3
    try:
        engine = pyttsx3.init()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
            temp_audio_path = temp_audio.name

        engine.save_to_file(text, temp_audio_path)
        engine.runAndWait()

        # Step 4: Read audio and return as response
        with open(temp_audio_path, "rb") as f:
            audio_bytes = f.read()

        os.remove(temp_audio_path)  # Clean up temp file

        return send_file(
            io.BytesIO(audio_bytes),
            mimetype="audio/mpeg",
            download_name="transcript_audio.mp3",
            as_attachment=False
        )

    except Exception as e:
        return abort(500, f"Audio generation failed: {e}")
        
@app.route('/delete_course_content/<int:rowid>')
def delete_course_content(rowid):
    if 'tid' not in session:
        return redirect(url_for('tlogin'))

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM coursecontent WHERE rowid=?", (rowid,))
    conn.commit()
    conn.close()

    return redirect(url_for('coursecontent'))

@app.route('/api/departments')
def get_departments_by_graduate():
    graduate_type = request.args.get('graduate', '').upper()
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT dname FROM department WHERE graduate = ?", (graduate_type,))
    departments = [row[0] for row in cursor.fetchall()]
    conn.close()
    return jsonify(departments)

@app.route('/show-timage')
def show_timage():
    if 'username' not in session:
        return "User not logged in. <a href='/'>Go Back</a>"

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    # ✅ Use parameterized query to avoid SQL injection and fix syntax error
    cursor.execute("SELECT propic FROM teacher WHERE username = ?", (session['username'],))
    result = cursor.fetchone()
    conn.close()

    if result and result[0]:
        image_base64 = base64.b64encode(result[0]).decode('utf-8')
        html = f'''
        <h3>Teacher Profile Picture</h3>
        <img src="data:image/jpeg;base64,{image_base64}" style="max-width:300px;" /><br>
        <a href="/">Go Back</a>
        '''
        return render_template_string(html)
    else:
        return "No image found for this teacher. <a href='/'>Go Back</a>"
    
@app.route('/show-image')
def show_image():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT profile_picture FROM students")
    result = cursor.fetchone()
    conn.close()

    if result and result[0]:
        image_base64 = base64.b64encode(result[0]).decode('utf-8')
        html = f'<h3>Student ID  Profile Picture</h3><img src="data:image/jpeg;base64,{image_base64}" /><br><a href="/">Go Back</a>'
        return render_template_string(html)
    else:
        return f"No image found for student ID  <a href='/'>Go Back</a>"
    
@app.route('/submit-audio', methods=['POST'])
def submit_audio():
    audio = request.files.get('audio_data')
    if not audio:
        return jsonify({'error': 'No audio received'}), 400
    # Generate timestamp-based filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    webm_filename = f"recording_{timestamp}.webm"
    webm_path = os.path.join(UPLOAD_FOLDER, webm_filename)
    audio.save(webm_path)
    print(f"✅ Saved file to: {webm_path}")

    # Convert to wav using ffmpeg subprocess
    wav_filename = f"recording_{timestamp}.wav"
    wav_path = os.path.join(UPLOAD_FOLDER, wav_filename)

    try:
        print("🔄 Converting to WAV...")
        subprocess.run([
            "c:\ffmpeg\bin\ffmpeg", "-y", "-i", webm_path, wav_path
        ], check=True)

        print("🔍 Transcribing using Whisper...")
        result = model.transcribe(wav_path)
        transcript = result["text"]
        print("📝 Transcript:", transcript)
        return f"Transcribed Text: {transcript}"

    except subprocess.CalledProcessError as ffmpeg_error:
        print("❌ FFmpeg conversion failed:", ffmpeg_error)
        return f"FFmpeg conversion failed: {ffmpeg_error}", 500
    except Exception as e:
        print("❌ Exception occurred while processing audio:", e)
        return f"Internal Server Error: {e}", 500

def fetch_profile_picture():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute("SELECT profile_picture FROM students")
    result = cursor.fetchone()
    conn.close()
    if result and result[0]:
        image_base64 = base64.b64encode(result[0]).decode('utf-8')
        html = f'<img src="data:image/jpeg;base64,{image_base64}" />'
        return render_template_string(html)
    else:
        return "❌ No image found"

@app.route('/coursecontentupload', methods=['GET'])
def show_upload_form():
    return render_template('coursecontentupload.html')  # template must have flash block

@app.route('/coursecontentupload', methods=['POST'])
def upload():
    try:
        coursetitle = request.form['coursetitle']
        unit = request.form['unit']
        topic = request.form['topic']
        content = request.files['content']
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        if content and content.filename != '':
            file_data = content.read()
            cursor.execute("""
                    insert into coursecontent (coursetitle, unit, topic, content) values (?, ?, ?, ?) """, (coursetitle, unit, topic, file_data))
            conn.commit()
            return redirect('/adashboard')
        else:
            flash('No file selected.','error')
            return redirect('/coursecontentupload')
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()
    
@app.route('/api/courses')
def get_courses():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT coursetitle FROM coursecontent")
    courses = [row[0] for row in cursor.fetchall()]
    conn.close()
    return jsonify(courses)

@app.route('/api/units')
def get_units():
    course = request.args.get('course')
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT unit FROM coursecontent WHERE coursetitle = ?", (course,))
    units = [row[0] for row in cursor.fetchall()]
    print(units)
    conn.close()
    return jsonify(units)

@app.route('/api/topics')
def get_topics():
    course = request.args.get('course')
    unit = request.args.get('unit')
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT topic FROM coursecontent WHERE coursetitle = ? AND unit = ?", (course, unit))
    topics = [row[0] for row in cursor.fetchall()]
    print(topics)
    conn.close()
    return jsonify(topics)

@app.route('/get-audio')
def get_audio():
    course = request.args.get("course")
    unit = request.args.get("unit")
    topic = request.args.get("topic")

    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT audio
        FROM coursecontent
        WHERE coursetitle = ? AND unit = ? AND topic = ?
        LIMIT 1
    """, (course, unit, topic))

    row = cur.fetchone()
    conn.close()

    if not row or not row["audio"]:
        abort(404, "No audio found for this selection")

    audio_bytes = row["audio"]

    return send_file(
        io.BytesIO(audio_bytes),
        mimetype="audio/mpeg",
        as_attachment=False,
        download_name=f"{course}_{unit}_{topic}.mp3"
    )

@app.route("/api/audio")
def api_audio():
    course = request.args.get("course")
    unit   = request.args.get("unit")
    topic  = request.args.get("topic")

    if not course or not unit or not topic:
        abort(400, "Missing course, unit, or topic")

    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Adjust column names if yours differ. Assumes:
    # table: coursecontent
    # columns: coursetitle (TEXT), unit (TEXT), topic (TEXT), audio (BLOB/mp3)
    cur.execute("""
        SELECT audio
        FROM coursecontent
        WHERE coursetitle = ? AND unit = ? AND topic = ?
        LIMIT 1
    """, (course, unit, topic))
    row = cur.fetchone()
    conn.close()

    if not row or row["audio"] is None:
        abort(404, "Audio not found for the selected course/unit/topic")

    audio_bytes = row["audio"]  # stored as BLOB
    # If you stored Base64 text instead, decode it here.

    return send_file(
        io.BytesIO(audio_bytes),
        mimetype="audio/mpeg",             # mp3
        as_attachment=False,
        download_name=f"{course}_{unit}_{topic}.mp3",
        conditional=True
    )

@app.route('/read-pdf-fixed')
def read_selected_pdf():
    course = request.args.get('course')
    unit = request.args.get('unit')
    topic = request.args.get('topic')

    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT content FROM coursecontent
            WHERE coursetitle = ? AND unit = ? AND topic = ?
        """, (course, unit, topic))
        row = cursor.fetchone()
        conn.close()

        if not row or not row[0]:
            return jsonify({'error': 'PDF not found'}), 404

        # Write PDF to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(row[0])
            temp_pdf_path = temp_pdf.name

        # Read PDF using PyMuPDF
    
        with fitz.open(temp_pdf_path) as doc:
            text = "\n".join(page.get_text() for page in doc)

        os.unlink(temp_pdf_path)
        return jsonify({'text': text})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
        
@app.route('/add-student', methods=['POST'])
def save_student():
    try:
        name = request.form['name']
        register_number = request.form['register_number']
        dob=request.form['dob']
        student_class = request.form['class']
        department = request.form['department']
        year_of_joining = request.form['year_of_joining']
        phone_number = request.form['phone_number']
        graduate=request.form['graduate']
        profile_picture = request.files['profile_picture'].read()
        idcard_image = request.files['idcard_image'].read()
        pwd_certificate_image = request.files['pwd_certificate_image'].read()
        username = register_number[:2]+register_number[-2:]
        dob_day = datetime.strptime(dob, "%Y-%m-%d").day
        dob_year = datetime.strptime(dob, "%Y-%m-%d").year
        password = f"{dob_day:02d}{dob_year % 100:02d}"
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        # Check if student already exists
        cursor.execute("SELECT register_number FROM students WHERE register_number= ?", (register_number,))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Student already exists'}), 409

        # Insert new user
        cursor.execute("""
            INSERT INTO students (
                name, register_number, class, department, year_of_joining,
                phone_number, profile_picture, idcard_image, pwd_certificate_image,username,password,graduate,dob
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name, register_number, student_class, department, year_of_joining,
            phone_number, profile_picture, idcard_image, pwd_certificate_image,username,password,graduate,dob
        ))
        conn.commit()
        return redirect('/adashboard')
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

@app.route('/department-register', methods=['POST'])
def deptregister():
    conn = None  # define conn before the try block
    try:
        did = request.form['did']
        dname = request.form['dname']
        graduate = request.form['graduate']

        if not did or not dname or not graduate:
            return jsonify({'success': False, 'message': 'Department ID, Name and type of Graduate are required'}), 400

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        # Check if department already exists
        cursor.execute("SELECT did FROM department WHERE did = ?", (did,))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Department already exists'}), 409

        # Insert new department
        cursor.execute("INSERT INTO department (did, dname, graduate) VALUES (?, ?, ?)", (did, dname, graduate))
        conn.commit()
        return redirect('/adashboard')

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

    finally:
        if conn:
            conn.close()


@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM student WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        session['username'] = username 
        session['password'] = password
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Invalid credentials'})


@app.route('/api/tlogin', methods=['POST'])
def api_tlogin():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM teacher WHERE username=? AND password=?", (username, password))
    teacher = c.fetchone()
    conn.close()

    if teacher:
        session['tid'] = teacher[0] 
        session['username'] = teacher[8] 
        session['dname'] = teacher[4] 
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "message": "Invalid credentials"}), 401
    
@app.route('/adminlogin')
def admin_login():
    return render_template('adminlogin.html')

@app.route('/api/alogin', methods=['POST'])
def api_alogin():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if username=='admin' and password=='vvvcinsight':
        session['username'] = username 
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Invalid credentials'})

@app.route('/sdashboard')
def sdashboard():
    if 'username' not in session:
        return redirect(url_for('student_login'))

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM student WHERE username=?", (session['username'],))
    student = cursor.fetchone()

    conn.close()

    # Prepare profile image
    profile_picture = None
    if student[7]:
        import base64
        profile_picture = base64.b64encode(student[7]).decode('utf-8') if student[4] else None
        
    return render_template('sdashboard.html',
                           student=student,
                           profile_picture=profile_picture,
                           username=student[1])

@app.route('/tdashboard')
def tdashboard():
    if 'username' not in session:
        return redirect(url_for('teacher_login'))

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM teacher WHERE username=?", (session['username'],))
    teacher = cursor.fetchone()

    cursor.execute("SELECT courseid, coursetitle FROM teacher_course WHERE tid=?", (teacher[0],))
    uploaded_courses = cursor.fetchall()  # List of (courseid, coursetitle)

    cursor.execute("SELECT DISTINCT dname FROM department")
    departments = [row[0] for row in cursor.fetchall()]

    conn.close()

    # Prepare profile image
    profile_image = None
    idcard_image = None
    if teacher[4]:
        import base64
        profile_image = base64.b64encode(teacher[6]).decode('utf-8') if teacher[6] else None
        idcard_image = base64.b64encode(teacher[7]).decode('utf-8') if teacher[7] else None

    return render_template('tdashboard.html',
                           teacher=teacher,
                           tid=teacher[0],
                           did=teacher[3],
                           departments=departments,
                           profile_image=profile_image,
                           idcard_image=idcard_image, 
                           uploaded_courses=uploaded_courses,                          
                           username=session['username'])

@app.route('/upload_course', methods=['POST'])
def upload_course():
    if 'username' not in session:
        return redirect(url_for('teacher_login'))
    try:
        tid = session.get('tid')  
        courseid = request.form['courseid']
        coursetitle = request.form['coursetitle']
        syllabus_file = request.files['syllabus']
        syllabus = syllabus_file.read() if syllabus_file and syllabus_file.filename != '' else None
        assignment1 = request.form['assignment1']
        assignment2 = request.form['assignment2']
        quiz1 = request.files["quiz_file1"].read() if "quiz_file1" in request.files and request.files["quiz_file1"] else None
        quiz2 = request.files["quiz_file2"].read() if "quiz_file2" in request.files and request.files["quiz_file2"] else None
        quiz3 = request.files["quiz_file3"].read() if "quiz_file3" in request.files and request.files["quiz_file3"] else None

        conn = sqlite3.connect('users.db')
        cur = conn.cursor()
        cur.execute("INSERT INTO teacher_course (tid, courseid, coursetitle, syllabus, assignment1, assignment2,quiz1, quiz2, quiz3) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (tid, courseid, coursetitle, syllabus, assignment1, assignment2,quiz1, quiz2, quiz3))
        conn.commit()
        conn.close()
        flash("Course uploaded successfully!", "success")
        return redirect(url_for('tdashboard'))
    except Exception as e:
        return f"Error uploading course: {e}", 500

@app.route('/tassignment')
def tassignment():
    if 'username' not in session:
        return redirect(url_for('tdashboard'))  # redirect to login if session not set
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM teacher WHERE username=?", (session['username'],))
    teacher = cursor.fetchone()
    tid=teacher[0]

    cursor.execute("SELECT courseid, coursetitle FROM teacher_course WHERE tid=?", (teacher[0],))
    uploaded_courses = cursor.fetchall()  # List of (courseid, coursetitle)

    cursor.execute("SELECT DISTINCT dname FROM department")
    departments = [row[0] for row in cursor.fetchall()]

    conn.close()
    return render_template("tassignment.html", username=session['username'],teacher=teacher,tid=tid,teacher_course=uploaded_courses)

@app.route('/get_assignment_data/<courseid>')
def get_assignment_data(courseid):
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("""
        SELECT assignment1, assignment2, int_prac, ext_prac 
        FROM teacher_course 
        WHERE courseid = ?
    """, (courseid,))
    row = cur.fetchone()
    conn.close()

    if row:
        return jsonify({
            "assignment1": row[0],
            "assignment2": row[1],
            "int_prac": row[2],
            "ext_prac": row[3]
        })
    else:
        return jsonify({
            "assignment1": "",
            "assignment2": "",
            "int_prac": "",
            "ext_prac": ""
        })

@app.route('/tquiz')
def tquiz():
    if 'username' not in session:
        return redirect(url_for('tdashboard'))  # redirect to login if session not set
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute("SELECT tid FROM teacher WHERE username=?", (session['username'],))
    teacher = cursor.fetchone()
    tid=teacher[0]

    cursor.execute("SELECT courseid, coursetitle FROM teacher_course WHERE tid=?", (teacher[0],))
    uploaded_courses = cursor.fetchall()  # List of (courseid, coursetitle)

    cursor.execute("SELECT DISTINCT dname FROM department")
    departments = [row[0] for row in cursor.fetchall()]

    conn.close()
    return render_template("tquiz.html", username=session['username'],tid=tid,teacher_course=uploaded_courses)


@app.route('/tasseval')
def tasseval():
    if 'username' not in session:
        return redirect('/')

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT courseid, coursetitle 
        FROM teacher_course 
        WHERE tid = (SELECT tid FROM teacher WHERE username = ?)
    """, (session['username'],))
    teacher_courses = cursor.fetchall()
    conn.close()

    return render_template("tasseval.html", teacher_courses=teacher_courses)

# Get students by course
@app.route('/students_by_course')
def students_by_course():
    courseid = request.args.get('courseid')  # 🔑 use courseid, not coursetitle
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.register_number, s.name
        FROM student_course_mapping scm
        JOIN student s ON scm.register_number = s.register_number
        WHERE scm.courseid = ?
    """, (courseid,))
    students = [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]
    conn.close()
    return jsonify(students)

@app.route('/assignments_by_student')
def assignments_by_student():
    courseid = request.args.get('courseid')
    studentid = request.args.get('studentid')   

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, assno, answer
        FROM student_assignment
        WHERE courseid = ? AND register_no = ? 
        ORDER BY assno ASC
    """, (courseid, studentid))

    label_map = {
        3: "Internal Practical",
        4: "External Practical"
    }

    assignments = []
    for row in cursor.fetchall():
        assno = row[1]
        if (assno==1 or assno==2):
           label = f"{label_map.get(assno, 'Assignment')} {assno}"
        else:
            label = f"{label_map.get(assno, 'Assignment')} {assno-2}"
        assignments.append({
            "id": row[0],
            "assno": assno,
            "label": label
        })

    conn.close()
    print(f"Assignments fetched for {studentid} in {courseid}: {assignments}")
    return jsonify(assignments)



@app.route('/play_tassignment_audio/<int:assignment_id>')
def play_tassignment_audio(assignment_id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT answer FROM student_assignment WHERE id = ?", (assignment_id,))
    row = cursor.fetchone()
    conn.close()

    if row and row[0]:
        return send_file(io.BytesIO(row[0]), mimetype="audio/mpeg")
    else:
        return "No audio available", 404

@app.route('/update_assignment_marks', methods=['POST'])
def update_assignment_marks():
    data = request.json
    studentId = data['studentId']
    updates = data['updates']

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    try:
        for u in updates:
            cursor.execute("""
                UPDATE student_assignment
                SET score = ?
                WHERE id = ? AND register_no = ?
            """, (u['score'], u['assignmentId'], studentId))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(e)
        return jsonify({'success': False})
    finally:
        conn.close()

# Get assignments of a student in a course
@app.route('/student_assignments')
def student_assignments():
    course = request.args.get('course')
    student_id = request.args.get('student')

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT rowid, title 
        FROM student_assignment sa
        JOIN coursecontent cc ON sa.courseid = cc.courseid
        WHERE cc.coursetitle = ? AND sa.sid = ?
    """, (course, student_id))
    assignments = [{"id": row[0], "title": row[1]} for row in cursor.fetchall()]
    conn.close()
    return jsonify(assignments)

@app.route('/play_assignment_audio/<int:assign_id>')
def play_assignment_audio(assign_id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT answer FROM student_assignment WHERE rowid = ?", (assign_id,))
    row = cursor.fetchone()
    conn.close()

    if row and row[0]:
        return send_file(io.BytesIO(row[0]), mimetype="audio/mpeg")
    else:
        return "No audio available", 404

@app.route('/edit_assignment_course', methods=['POST'])
def edit_assignment_course():
    try:
        tid = request.form.get("tid")
        courseid = request.form.get("courseid")
        assignment1 = request.form.get("assignment1")
        assignment2 = request.form.get("assignment2")
        int_prac = request.form.get("int_prac")
        ext_prac = request.form.get("ext_prac")

        if not courseid:
            return "Course ID is required", 400

        conn = sqlite3.connect("users.db")
        cur = conn.cursor()

        # update if row exists
        cur.execute("""
            UPDATE teacher_course
            SET assignment1 = ?, assignment2 = ?, int_prac = ?, ext_prac = ?
            WHERE courseid = ? AND tid = ?
        """, (assignment1, assignment2, int_prac, ext_prac, courseid, tid))

        conn.commit()
        conn.close()

        return redirect(url_for("tassignment"))

    except Exception as e:
        return f"Error: {str(e)}", 500
    
@app.route('/update_teacher', methods=['POST'])
def update_teacher():
    if 'username' not in session:
        return redirect(url_for('teacher_login'))

    username = session['username']
    tname = request.form.get('tname')
    designation = request.form.get('designation')
    dname = request.form.get('dname')
    exp = request.form.get('exp') 
    
    profile_file = request.files.get('profile_pic')
    idcard_file = request.files.get('id_card')

    propic = profile_file.read() if profile_file and profile_file.filename != '' else None
    idcard = idcard_file.read() if idcard_file and idcard_file.filename != '' else None
    

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Get did for the selected department name
    cursor.execute("SELECT did FROM department WHERE dname = ?", (dname,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return "Invalid department", 400
    did = row[0]

    # Prepare update query
    update_query = """
        UPDATE teacher
        SET tname = ?, designation = ?, did = ?, dname = ?, exp = ?
    """
    params = [tname, designation, did, dname, exp]

    if propic:
        update_query += ", propic = ?"
        params.append(propic)

    if idcard:
        update_query += ", idcard = ?"
        params.append(idcard)

    update_query += " WHERE username = ?"
    params.append(username)

    cursor.execute(update_query, tuple(params))
    conn.commit()
    conn.close()

    return redirect(url_for('tdashboard'))


@app.route('/adashboard')
def adashboard():
    if 'username' not in session:
        return redirect(url_for('admin_login'))
    departments = get_departments()
    return render_template("adashboard.html", username=session['username'], departments=departments)
def get_departments():
    conn = sqlite3.connect('users.db')  # Use your actual DB name
    cursor = conn.cursor()
    cursor.execute("SELECT distinct dname FROM department")  # Change column name if different
    departments = [row[0] for row in cursor.fetchall()]
    conn.close()
    return departments

@app.route('/department-register', methods=['GET', 'POST'])
def departmentregister():
    if 'username' not in session:
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        did = request.form['did']
        dname = request.form['dname']
        graduate = request.form['graduate']

        # Save into the database
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('INSERT INTO department (did, dname, graduate) VALUES (?, ?, ?)', (did, dname, graduate))
        conn.commit()
        conn.close()

        flash('Department registered successfully!')
        return redirect(url_for('departmentregister'))

    return render_template('departmentregister.html',username=session.get('username') )
 
@app.route('/logout')
def logout():
    session.pop('username', None)
    return render_template('index.html')

@app.route('/tlogout')
def tlogout():
    session.pop('username', None)
    return render_template('index.html')

@app.route('/alogout')
def alogout():
    session.pop('username', None)
    return render_template('index.html')

@app.route('/scourse')
def scourse():
    if 'username' not in session:
        return redirect(url_for('student_login'))  # redirect to login if session not set
    return render_template("scourse.html", username=session['username'])

@app.route('/mocktest')
def mocktest():
    if 'username' not in session:
        return redirect(url_for('student_login'))
    
    username = session.get('username')
    password = session.get('password')

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("""SELECT register_number, name, class, department FROM student WHERE username = ? AND password = ? """, (username,password,))
    students = cursor.fetchall()
    
    # Join to get courseid and coursetitle assigned to student
    cursor.execute("""
        SELECT tc.courseid, tc.coursetitle
        FROM student_course_mapping sc
        JOIN teacher_course tc ON sc.courseid = tc.courseid
        WHERE sc.register_number = ?
    """, (students[0][0],))
    student_courses = cursor.fetchall()
    conn.close()
    return render_template("mocktest.html", students=students, username=session['username'],password=session['password'],student_courses=student_courses)

@app.route('/getunits')
def getunits():
    courseid = request.args.get('courseid')
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT unit FROM coursecontent WHERE courseid = ?", (courseid,))
    units = [row[0] for row in cursor.fetchall()]
    conn.close()
    return jsonify({'unit': units})

@app.route('/gettopics')
def gettopics():
    courseid = request.args.get('courseid')
    unit = request.args.get('unit')
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT topic FROM coursecontent WHERE courseid = ? AND unit = ?", (courseid, unit))
    topics = [row[0] for row in cursor.fetchall()]
    print(topics)
    conn.close()
    return jsonify({'topics': topics})

@app.route('/get_mocktest')
def get_mocktest():
    courseid = request.args.get('courseid')
    unit = request.args.get('unit')
    topic = request.args.get('topic')

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT mocktest FROM coursecontent 
        WHERE coursetitle = ? AND unit = ? AND topic = ?
    """, (courseid, unit, topic))

    row = cursor.fetchone()
    conn.close()

    if row and row[0]:
        excel_data = row[0]
        df = pd.read_excel(BytesIO(excel_data), skiprows=0)

        print("Columns in Excel:", df.columns.tolist())  

        rows = []
        for _, r in df.iterrows():
            rows.append({
                "qno": r.get("S. NO.", ""),
                "question": r.get("QUESTION", ""),
                "option_a": r.get("OPTION A", ""),
                "option_b": r.get("OPTION B", ""),
                "option_c": r.get("OPTION C", ""),
                "option_d": r.get("OPTION D", ""),
                "answer": r.get("Ans", "")             })

        return jsonify({"rows": rows})
    else:
        return jsonify({"rows": []})

@app.route('/assignment')
def assignment():
    if 'username' not in session:
        return redirect(url_for('student_login'))
    
    username = session.get('username')
    password = session.get('password')

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("""SELECT register_number, name, class, department FROM student WHERE username = ? AND password = ? """, (username,password,))
    students = cursor.fetchall()
    
    # Join to get courseid and coursetitle assigned to student
    cursor.execute("""
        SELECT tc.courseid, tc.coursetitle
        FROM student_course_mapping sc
        JOIN teacher_course tc ON sc.courseid = tc.courseid
        WHERE sc.register_number = ?
    """, (students[0][0],))
    student_courses = cursor.fetchall()
    conn.close()

    return render_template("assignment.html",students=students, student_courses=student_courses, username=session.get('username'))

@app.route('/get_assignment')
def get_assignment():
    courseid = request.args.get('courseid')
    assno = request.args.get('assno')

    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    query_map = {
        "1": "assignment1",
        "2": "assignment2",
        "3": "int_prac",
        "4": "ext_prac"
    }

    field = query_map.get(assno)
    if not field:
        return jsonify({"assignment": ""})

    c.execute(f"SELECT {field} FROM teacher_course WHERE courseid=?", (courseid,))
    row = c.fetchone()
    conn.close()

    return jsonify({"assignment": row[0] if row else ""})

@app.route('/get_question')
def get_question():
    courseid = request.args.get('courseid')
    field = request.args.get('field')  # assignment1, assignment2, int_prac, ext_prac

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute(f"SELECT {field} FROM teacher_course WHERE courseid=?", (courseid,))
    row = c.fetchone()
    conn.close()

    question_text = row[0] if row else ""
    return jsonify({'question': question_text})
def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/get_pending_assignments')
def get_pending_assignments():
    courseid = request.args.get('courseid')
    register_no = request.args.get('register_no')

    conn = get_db_connection()
    # Fetch all assignments from teacher_course
    course = conn.execute("SELECT assignment1, assignment2 FROM teacher_course WHERE courseid = ?", (courseid,)).fetchone()

    # Fetch submitted assignments
    submitted = conn.execute(
        "SELECT assno FROM student_assignment WHERE register_no=? AND courseid=?",
        (register_no, courseid)
    ).fetchall()
    submitted_numbers = [row['assno'] for row in submitted]

    pending = []
    if course['assignment1'] and 1 not in submitted_numbers:
        pending.append({"assno": 1, "type": "Assignment", "question": course['assignment1']})
    if course['assignment2'] and 2 not in submitted_numbers:
        pending.append({"assno": 2, "type": "Assignment", "question": course['assignment2']})

    conn.close()
    return jsonify({"pending": pending})

@app.route('/get_pending_practicals')
def get_pending_practicals():
    courseid = request.args.get('courseid')
    register_no = request.args.get('register_no')

    conn = get_db_connection()

    # Fetch the teacher_course row for the given courseid
    course = conn.execute(
        "SELECT int_prac, ext_prac FROM teacher_course WHERE courseid = ?",
        (courseid,)
    ).fetchone()

    if not course:
        conn.close()
        return jsonify({"error": f"No course found for courseid={courseid}"}), 404

    # Fetch submitted assignments for this student and course
    submitted = conn.execute(
        "SELECT assno FROM student_assignment WHERE register_no=? AND courseid=?",
        (register_no, courseid)
    ).fetchall()
    submitted_numbers = [row['assno'] for row in submitted]

    pending = []

    # Internal Practical = assno 3
    if course['int_prac'] and 3 not in submitted_numbers:
        pending.append({
            "assno": 3,
            "type": "Internal Practical",
            "question": course['int_prac']
        })

    # External Practical = assno 4
    if course['ext_prac'] and 4 not in submitted_numbers:
        pending.append({
            "assno": 4,
            "type": "External Practical",
            "question": course['ext_prac']
        })

    conn.close()

    return jsonify({"pending": pending})


@app.route('/submit_assignment', methods=['POST'])
def submit_assignment():
    register_no = request.form['register_no']
    courseid = request.form['courseid']
    assno = request.form['assno']
    question = request.form['question']
    submitdate = request.form['submitdate']
    audio_file = request.files['audio_data']

    # read binary
    audio_blob = audio_file.read()

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO student_assignment 
        (register_no, courseid, assno, question, answer, submitdate, remarks, score)
        VALUES (?, ?, ?, ?, ?, ?, NULL, NULL)
    """, (register_no, courseid, assno, question, audio_blob, submitdate))
    conn.commit()
    conn.close()

    return "Assignment submitted successfully!"

@app.route('/get_quiz')
def get_quiz():
    courseid = request.args.get('courseid')
    test = request.args.get('test')
 
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    if test=="Quiz I":
        cursor.execute("""
            SELECT quiz1 FROM teacher_course WHERE courseid = ? """, (courseid))

    if test=="Quiz II":
        cursor.execute("""
            SELECT quiz2 FROM teacher_course WHERE courseid = ? """, (courseid))
    
    if test=="Quiz III":
        cursor.execute("""
            SELECT quiz3 FROM teacher_course WHERE courseid = ? """, (courseid))

    row = cursor.fetchone()
    conn.close()    
    if row and row[0]:
        excel_data = row[0]
        df = pd.read_excel(BytesIO(excel_data), skiprows=0)

        print("Columns in Excel:", df.columns.tolist())  

        rows = []
        for _, r in df.iterrows():
            rows.append({
                "qno": r.get("S. NO.", ""),
                "question": r.get("QUESTION", ""),
                "option_a": r.get("OPTION A", ""),
                "option_b": r.get("OPTION B", ""),
                "option_c": r.get("OPTION C", ""),
                "option_d": r.get("OPTION D", "")
            })

        return jsonify({"rows": rows})
    else:
        return jsonify({"rows": []})


@app.route('/quiz')
def quiz():
    if 'username' not in session:
        return redirect(url_for('student_login'))
    
    username = session.get('username')
    password = session.get('password')

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("""SELECT register_number, name, class, department FROM student WHERE username = ? AND password = ? """, (username,password,))
    students = cursor.fetchall()
    
    # Join to get courseid and coursetitle assigned to student
    cursor.execute("""
        SELECT tc.courseid, tc.coursetitle
        FROM student_course_mapping sc
        JOIN teacher_course tc ON sc.courseid = tc.courseid
        WHERE sc.register_number = ?
    """, (students[0][0],))
    student_courses = cursor.fetchall()
    conn.close()
    return render_template("quiz.html", students=students, username=session['username'],password=session['password'],student_courses=student_courses)

if __name__ == '__main__':
    app.run(debug=True)