import sqlite3

# connect to your database
conn = sqlite3.connect("users.db")
c = conn.cursor()

# describe table structure (like DESC in MySQL)
table_name = "student_assignment"
c.execute(f"PRAGMA table_info({table_name})")

columns = c.fetchall()

print("Table structure for", table_name)
print("CID | Name | Type | NotNull | Default | PK")
for col in columns:
    print(col)

conn.close()
