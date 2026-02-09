import sqlite3

# Connect to the database (creates if it doesn't exist)
conn = sqlite3.connect('users.db')  # Use correct path if needed

# Create a cursor object
cursor = conn.cursor()

# Define the CREATE TABLE command
create_table_sql = """
DELETE FROM teacher_course
WHERE courseid = '007';
"""

# Execute the command
cursor.execute(create_table_sql)

# Commit and close
conn.commit()
conn.close()

print("✅ courseid=007 record of Teacher_course table deleted successfully.")
