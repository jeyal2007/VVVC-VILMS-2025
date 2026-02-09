import sqlite3

# Connect to the database (creates if it doesn't exist)
conn = sqlite3.connect('users.db')  # Use correct path if needed

# Create a cursor object
cursor = conn.cursor()

# Define the CREATE TABLE command
create_table_sql = """
CREATE TABLE coursecontent(
    tid TEXT, 
    courseid TEXT,
    coursetitle TEXT,
    unit text,
    topic text,
    content BLOB,
    mocktext BLOB,
    assignment TEXT
    quiz BLOB
);

"""

# Execute the command
cursor.execute(create_table_sql)

# Commit and close
conn.commit()
conn.close()

print("✅ Teacher table created successfully.")
