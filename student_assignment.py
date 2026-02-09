import sqlite3

def create_table():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    # Create the table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_assignment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            register_no TEXT NOT NULL,
            courseid TEXT NOT NULL,
            assno INTEGER NOT NULL,
            question TEXT NOT NULL,
            answer BLOB NOT NULL,
            submitdate DATE NOT NULL,
            remarks TEXT(50),
            score INTEGER,
            FOREIGN KEY (register_no, courseid) REFERENCES student_course_mapping(register_no, courseid),
            FOREIGN KEY (courseid) REFERENCES teacher_course(courseid),
            FOREIGN KEY (question) REFERENCES teacher_course(assignment1) -- simplified reference to teacher_course question
        )
    """)

    conn.commit()
    conn.close()
    print("✅ student_assignment table created successfully!")

if __name__ == "__main__":
    create_table()
