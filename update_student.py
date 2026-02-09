import sqlite3

# Connect to database
conn = sqlite3.connect('users.db')
cursor = conn.cursor()

# Update query
cursor.execute(
    "UPDATE student SET name = ? WHERE register_number = ?",
    ('Venba K', 100)
)

# Commit changes
conn.commit()

# Close connection
conn.close()

print("Student name updated successfully")
