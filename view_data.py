"""View stored demo data: python view_data.py"""
from pathlib import Path
import sqlite3

path = Path(__file__).resolve().parent / 'data' / 'parking.db'
if not path.exists():
    print('Database not created. Run python server.py first.')
    raise SystemExit(1)
with sqlite3.connect(path) as db:
    for table in ('users', 'parking', 'bookings'):
        print('\n---', table.upper(), '---')
        cursor = db.execute('SELECT * FROM ' + table)
        columns = [item[0] for item in cursor.description]
        for row in cursor.fetchall():
            safe = dict(zip(columns, row))
            safe.pop('password_hash', None)
            print(safe)
