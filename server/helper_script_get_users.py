import sqlite3
conn = sqlite3.connect("smart_home.db")
cur = conn.cursor()
cur.execute("SELECT userId, email, password, role FROM users;")
rows = cur.fetchall()
print(rows)
