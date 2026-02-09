import sqlite3

# Connect to the database (creates if it doesn't exist)
conn = sqlite3.connect('users.db')  # Use correct path if needed

# Create a cursor object
cursor = conn.cursor()

# Define the CREATE TABLE command
create_table_sql = """
CREATE TABLE IF NOT EXISTS teacher (
    tid TEXT NOT NULL PRIMARY KEY,
    tname TEXT NOT NULL,
    designation TEXT,
    did INTEGER(9) NOT NULL,
    dname TEXT,
    exp INTEGER,
    propic BLOB,
    idcard BLOB,
    username TEXT NOT NULL,
    password TEXT NOT NULL
);
"""

# Execute the command
cursor.execute(create_table_sql)

# Commit and close
conn.commit()
conn.close()

print("✅ Teacher table created successfully.")
