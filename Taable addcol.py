import sqlite3

# Connect to the database (creates if it doesn't exist)
conn = sqlite3.connect('users.db')  # Use correct path if needed

# Create a cursor object
cursor = conn.cursor()

# Define the CREATE TABLE command
create_table_sql = """
ALTER TABLE coursecontent ADD COLUMN audio BLOB;
"""

# Execute the command
cursor.execute(create_table_sql)

# Commit and close
conn.commit()
conn.close()

print("✅ audio column was added successfully.")
