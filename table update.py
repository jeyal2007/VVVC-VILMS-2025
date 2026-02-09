import sqlite3

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute("""
    UPDATE coursecontent
    SET coursetitle = ? 
    WHERE coursetitle = ?
""", ("Algorithms", "Data Structures & Algorithms"))

conn.commit()
conn.close()
