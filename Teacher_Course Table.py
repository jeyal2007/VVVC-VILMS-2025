import sqlite3

conn = sqlite3.connect('users.db')
c = conn.cursor()

c.execute('''
    CREATE TABLE teacher_course (
    tid TEXT,
    courseid TEXT,
    coursetitle TEXT,
    syllabus BLOB,
    assignment1 TEXT,
    assignment2 TEXT,
    quiz1 BLOB,
    quiz2 BLOB,
    quiz3 BLOB);
''')
conn.commit()
conn.close()
