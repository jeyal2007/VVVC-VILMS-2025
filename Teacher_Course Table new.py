import sqlite3

conn = sqlite3.connect('users.db')
c = conn.cursor()

c.execute('''
    DROP TABLE IF EXISTS coursecontent;
''')

conn.commit()
conn.close()
