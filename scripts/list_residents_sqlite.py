import sqlite3
from pathlib import Path
DB = Path(__file__).resolve().parents[1] / 'db.sqlite3'
conn = sqlite3.connect(DB)
cur = conn.cursor()
try:
    cur.execute('SELECT id, profile_name, email, is_default FROM dashboard_resident')
    rows = cur.fetchall()
    for r in rows:
        print(r)
except Exception as e:
    print('Error:', e)
finally:
    conn.close()
