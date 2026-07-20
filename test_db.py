import sqlite3

connection = sqlite3.connect("chat.db")

cursor = connection.cursor()

cursor.execute("SELECT id, role, content FROM messages")

rows = cursor.fetchall()

for row in rows:
    print(row)

connection.close()