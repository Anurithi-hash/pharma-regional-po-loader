import sqlite3
import pandas as pd

conn = sqlite3.connect("regional_po.db")

df = pd.read_sql(
    "SELECT * FROM etl_file_audit_log",
    conn
)

print(df)

conn.close()