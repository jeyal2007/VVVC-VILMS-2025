import sqlite3

conn = sqlite3.connect('users.db')
cursor = conn.cursor()

try:
    cursor.execute("DROP TABLE IF EXISTS students")
    conn.commit()
    print("✅ 'students' table dropped successfully.")
except Exception as e:
    print("❌ Error:", e)
finally:
    conn.close()
