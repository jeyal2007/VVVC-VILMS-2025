import sqlite3

# Connect to the database (creates if it doesn't exist)
conn = sqlite3.connect('users.db')  # Use correct path if needed

# Create a cursor object
cursor = conn.cursor()

# Define the CREATE TABLE command
create_table_sql = """
CREATE TABLE student (
    register_number TEXT PRIMARY KEY,
    name TEXT,
    class TEXT,
    department TEXT,
    year_of_joining INTEGER,
    phone_number INTEGER,
    profile_picture BLOB,
    idcard_image BLOB,
    pwd BLOB,
    username TEXT,
    password TEXT,
    graduate TEXT,
    dob DATE
);

"""

# Execute the command
cursor.execute(create_table_sql)

# Commit and close
conn.commit()
conn.close()

print("✅ Student table created successfully.")
