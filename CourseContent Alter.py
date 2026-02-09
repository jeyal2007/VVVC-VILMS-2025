import sqlite3

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

try:
     cursor.execute("""
        CREATE TABLE coursecontent (
            tid TEXT, 
            courseid TEXT,
            coursetitle TEXT,
            unit TEXT,
            topic TEXT,
            content BLOB,
            mocktest BLOB
        )
    """)

except Exception as e:
    print("❌ Error during migration:", e)
finally:
    conn.close()
