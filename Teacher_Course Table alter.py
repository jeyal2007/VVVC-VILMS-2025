import sqlite3

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# Add new columns
columns_to_add = [
    "assignment1 BLOB",
    "assignment2 BLOB",
    "quiz1 BLOB",
    "quiz2 BLOB",
    "quiz3 BLOB"
]

for col in columns_to_add:
    try:
        cursor.execute(f"ALTER TABLE teacher_course ADD COLUMN {col}")
        print(f"✅ Added column: {col}")
    except sqlite3.OperationalError as e:
        print(f"⚠️ Could not add column {col}: {e}")

conn.commit()
conn.close()
