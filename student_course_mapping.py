import sqlite3

conn = sqlite3.connect('users.db')
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS student_course_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    courseid TEXT NOT NULL,
    register_number TEXT NOT NULL,
    tid TEXT NOT NULL,
    assigned_on DATE DEFAULT (DATE('now')),
    FOREIGN KEY (courseid) REFERENCES teacher_course(courseid),
    FOREIGN KEY (register_number) REFERENCES student(register_number),
    FOREIGN KEY (tid) REFERENCES teacher(tid),
    UNIQUE(courseid, register_number)
);

''')

conn.commit()
conn.close()
