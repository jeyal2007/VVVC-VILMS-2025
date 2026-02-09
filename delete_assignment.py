import sqlite3

# Connect to your database
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# Delete all records from student_assignment
cursor.execute("DELETE FROM student_assignment")

# Commit changes and close connection
conn.commit()
conn.close()

print("✅ All records deleted from student_assignment.")
