import sqlite3

conn = sqlite3.connect('users.db')
cursor = conn.cursor()

tables = [
    'student_course_mapping',
    'teacher_course',
    'coursecontent',
    'student',
    'students',
    'teacher',
    'users',
    'department'
]

try:
    for table in tables:
        cursor.execute(f"DELETE FROM {table}")
        cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")  # Reset autoincrement

    conn.commit()
    print("✅ All data cleared successfully.")
except Exception as e:
    print("❌ Error:", e)
finally:
    conn.close()
