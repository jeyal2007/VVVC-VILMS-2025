import sqlite3

conn = sqlite3.connect('users.db')
cursor = conn.cursor()

try:
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('admin', 'vvvcinsight'))
    conn.commit()
    print("✅ Admin user inserted successfully.")
except Exception as e:
    print("❌ Error:", e)
finally:
    conn.close()
