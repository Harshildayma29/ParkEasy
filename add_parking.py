"""Add a demonstration parking location to the SQLite database."""
from pathlib import Path
import sqlite3

path = Path(__file__).resolve().parent / 'data' / 'parking.db'
if not path.exists():
    print('Run python server.py first to create the database.')
    raise SystemExit(1)

name = input('Parking name: ').strip()
area = input('Ahmedabad area: ').strip()
try:
    bike = int(input('Total bike spaces: '))
    car = int(input('Total car spaces: '))
    bike_price = int(input('Bike price per hour (₹): '))
    car_price = int(input('Car price per hour (₹): '))
except ValueError:
    print('Please enter whole numbers for spaces and prices.')
    raise SystemExit(1)
if not name or not area or min(bike,car,bike_price,car_price) < 0:
    print('Enter a name, area, and nonnegative numbers.')
    raise SystemExit(1)
with sqlite3.connect(path) as db:
    db.execute('''INSERT INTO parking
        (name,area,total_2w,total_4w,available_2w,available_4w,price_2w,price_4w)
        VALUES (?,?,?,?,?,?,?,?)''',
        (name,area,bike,car,bike,car,bike_price,car_price))
print('Parking location added successfully.')
