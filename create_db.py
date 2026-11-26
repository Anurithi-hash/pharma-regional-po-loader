import sqlite3

conn = sqlite3.connect("regional_po.db")

cursor = conn.cursor()

with open("sql/create.tables.sql", "r") as f:
    cursor.executescript(f.read())

conn.commit()
conn.close()

print("Database created successfully")