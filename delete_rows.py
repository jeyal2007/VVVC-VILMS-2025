import sqlite3

conn = sqlite3.connect('users.db')
cursor = conn.cursor()

try:
    cursor.execute("DELETE FROM student_assignment")
    conn.commit()
    print("✅ table rows are deleted successfully.")
except Exception as e:
    print("❌ Error:", e)
finally:
    conn.close()
