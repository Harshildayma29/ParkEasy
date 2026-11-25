"""ParkEasy: a small Python web server with SQLite (no pip installs needed).

Run: python server.py
The HTML, CSS, JS, and SQLite database are all inside this folder.
"""

from datetime import datetime
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
import hashlib
import hmac
import json
import mimetypes
import os
import re
import secrets
import sqlite3
import webbrowser

ROOT = Path(__file__).resolve().parent
DB_FILE = ROOT / "data" / "parking.db"
SECRET_FILE = ROOT / "data" / ".session_key"
HOST = "127.0.0.1"
PORT = 5000

# Sample data only: prices and spaces are invented for our college demonstration.
PARKING_AREAS = [
    ("Riverfront Parking", "Ashram Road", 35, 20, 19, 10, 10, 30),
    ("CG Road Parking", "Navrangpura", 30, 18, 14, 9, 15, 40),
    ("Vastrapur Lake Parking", "Vastrapur", 25, 16, 11, 8, 10, 35),
    ("Maninagar Parking", "Maninagar", 40, 22, 20, 14, 10, 30),
    ("Science City Parking", "Science City Road", 30, 18, 17, 7, 15, 50),
    ("Law Garden Parking", "Ellis Bridge", 22, 15, 7, 6, 10, 40),
    ("Bopal Parking", "Bopal", 30, 16, 18, 11, 10, 35),
    ("Naroda Parking", "Naroda", 36, 18, 27, 12, 10, 30),
    # Extra Ahmedabad neighborhoods: all capacities and prices are demo values.
    ("Satellite Parking", "Satellite", 40, 22, 29, 13, 15, 40),
    ("Prahlad Nagar Parking", "Prahlad Nagar", 32, 26, 24, 12, 20, 50),
    ("Thaltej Parking", "Thaltej", 28, 20, 18, 9, 15, 45),
    ("Chandkheda Parking", "Chandkheda", 45, 25, 37, 18, 10, 35),
    ("Motera Parking", "Motera", 50, 35, 39, 22, 15, 45),
    ("Gota Parking", "Gota", 36, 18, 20, 11, 10, 35),
    ("Paldi Parking", "Paldi", 29, 14, 19, 7, 10, 40),
    ("Naranpura Parking", "Naranpura", 24, 13, 13, 9, 10, 30),
    ("Shahibaug Parking", "Shahibaug", 32, 20, 25, 12, 15, 45),
    ("Nikol Parking", "Nikol", 40, 22, 34, 17, 10, 35),
    ("Sola Parking", "Sola", 48, 26, 38, 19, 15, 45),
    ("Kankaria Parking", "Kankaria", 56, 30, 43, 14, 10, 40),
    ("Memnagar Parking", "Memnagar", 30, 19, 23, 15, 10, 35),
    ("Ambawadi Parking", "Ambawadi", 32, 19, 25, 11, 15, 45),
    ("Jodhpur Parking", "Jodhpur", 24, 18, 18, 10, 10, 40),
    ("Shyamal Parking", "Shyamal", 37, 21, 30, 15, 15, 45),
    ("Ranip Parking", "Ranip", 30, 18, 24, 13, 10, 30),
    ("Odhav Parking", "Odhav", 35, 20, 27, 14, 10, 35),
    ("South Bopal Parking", "South Bopal", 30, 18, 25, 12, 15, 40),
    ("Sabarmati Parking", "Sabarmati", 38, 24, 28, 16, 10, 35),
    # More illustrative Ahmedabad parking entries.
    ('University Road Parking', 'University Area', 42, 24, 28, 15, 10, 40),
    ('Gurukul Road Parking', 'Gurukul', 34, 20, 23, 12, 10, 40),
    ('Drive In Road Parking', 'Drive In Road', 38, 21, 30, 9, 15, 45),
    ('Judges Bungalow Parking', 'Bodakdev', 36, 24, 24, 16, 15, 50),
    ('Sindhu Bhavan Parking', 'Sindhu Bhavan Road', 50, 30, 32, 19, 20, 60),
    ('Iscon Cross Road Parking', 'SG Highway', 46, 28, 35, 18, 15, 50),
    ('Vaishnodevi Circle Parking', 'Vaishnodevi', 48, 27, 36, 15, 10, 40),
    ('Tragad Parking', 'Tragad', 32, 20, 21, 12, 10, 35),
    ('New Ranip Parking', 'New Ranip', 40, 22, 29, 13, 10, 35),
    ('Chandlodia Parking', 'Chandlodia', 38, 21, 24, 14, 10, 35),
    ('Vejalpur Parking', 'Vejalpur', 34, 20, 26, 11, 10, 35),
    ('Jivraj Park Parking', 'Jivraj Park', 36, 19, 27, 12, 10, 35),
    ('Anjali Cross Road Parking', 'Vasna', 30, 18, 19, 10, 10, 40),
    ('Danilimda Parking', 'Danilimda', 33, 17, 23, 11, 10, 30),
    ('Amraiwadi Parking', 'Amraiwadi', 39, 20, 28, 12, 10, 35),
    ('Rakhial Parking', 'Rakhial', 35, 18, 25, 9, 10, 30),
    ('Bapunagar Parking', 'Bapunagar', 43, 24, 32, 16, 10, 35),
    ('India Colony Parking', 'India Colony', 29, 16, 20, 9, 10, 30),
    ('Hansol Parking', 'Hansol', 41, 23, 27, 14, 10, 40),
    ('Airport Road Parking', 'Airport Road', 52, 32, 33, 20, 15, 50),
]


def database():
    """Open a database connection for one operation/request."""
    db = sqlite3.connect(DB_FILE, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def setup_database():
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    with database() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS parking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                area TEXT NOT NULL,
                total_2w INTEGER NOT NULL,
                total_4w INTEGER NOT NULL,
                available_2w INTEGER NOT NULL,
                available_4w INTEGER NOT NULL,
                price_2w INTEGER NOT NULL,
                price_4w INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                parking_id INTEGER NOT NULL REFERENCES parking(id),
                vehicle_type TEXT NOT NULL CHECK(vehicle_type IN ('2W','4W')),
                hours INTEGER NOT NULL CHECK(hours BETWEEN 1 AND 8),
                amount INTEGER NOT NULL,
                payment_method TEXT NOT NULL,
                status TEXT NOT NULL,
                booked_at TEXT NOT NULL,
                number_plate TEXT NOT NULL DEFAULT '',
                payment_status TEXT NOT NULL DEFAULT 'pending',
                transaction_ref TEXT NOT NULL DEFAULT ''
            );
        """)
        # Upgrade earlier project databases without deleting existing bookings.
        columns = {row["name"] for row in db.execute("PRAGMA table_info(bookings)")}
        if "number_plate" not in columns:
            db.execute("ALTER TABLE bookings ADD COLUMN number_plate TEXT NOT NULL DEFAULT ''")
        if "payment_status" not in columns:
            db.execute("ALTER TABLE bookings ADD COLUMN payment_status TEXT NOT NULL DEFAULT 'pending'")
        if "transaction_ref" not in columns:
            db.execute("ALTER TABLE bookings ADD COLUMN transaction_ref TEXT NOT NULL DEFAULT ''")
        # Rename old labels in existing databases while preserving IDs and bookings.
        db.execute("UPDATE parking SET name=REPLACE(name, ' Demo Parking', ' Parking') WHERE name LIKE '% Demo Parking'")
        # Add missing sample locations without overwriting or deleting saved records.
        # This also works when users bring their parking.db from the older project.
        for place in PARKING_AREAS:
            already_added = db.execute(
                "SELECT 1 FROM parking WHERE name=? AND area=? LIMIT 1",
                (place[0], place[1])
            ).fetchone()
            if not already_added:
                db.execute("""INSERT INTO parking
                    (name,area,total_2w,total_4w,available_2w,available_4w,price_2w,price_4w)
                    VALUES (?,?,?,?,?,?,?,?)""", place)
    if not SECRET_FILE.exists():
        SECRET_FILE.write_text(secrets.token_hex(32), encoding="utf-8")


def password_hash(password):
    """Store a salted hash, not the actual password."""
    salt = os.urandom(16)
    result = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return f"{salt.hex()}:{result.hex()}"


def verify_password(password, saved):
    try:
        salt, expected = saved.split(":", 1)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 200_000)
        return hmac.compare_digest(actual, bytes.fromhex(expected))
    except (ValueError, TypeError):
        return False


def signed_cookie(user_id):
    key = bytes.fromhex(SECRET_FILE.read_text(encoding="utf-8"))
    identifier = str(user_id)
    signature = hmac.new(key, identifier.encode(), "sha256").hexdigest()
    return identifier + "." + signature


class ParkEasyHandler(BaseHTTPRequestHandler):
    def reply(self, status, payload, cookie=None):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        if cookie is not None:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(data)

    def serve_file(self, file):
        if not file.is_file():
            return self.send_error(HTTPStatus.NOT_FOUND, "File not found")
        content = file.read_bytes()
        media = mimetypes.guess_type(file.name)[0] or "application/octet-stream"
        if media.startswith("text/") or media == "application/javascript":
            media += "; charset=utf-8"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", media)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def user(self):
        """Read the locally signed login cookie."""
        try:
            cookies = SimpleCookie()
            cookies.load(self.headers.get("Cookie", ""))
            value = cookies["parkeasy_session"].value
            identifier, signature = value.split(".", 1)
            if not identifier.isdecimal():
                return None
            if not hmac.compare_digest(signed_cookie(identifier), value):
                return None
            with database() as db:
                row = db.execute("SELECT id,name FROM users WHERE id=?", (int(identifier),)).fetchone()
                return dict(row) if row else None
        except (KeyError, ValueError):
            return None

    def json_body(self):
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 16_384:
                return None
            data = json.loads(self.rfile.read(size).decode("utf-8"))
            return data if isinstance(data, dict) else None
        except (ValueError, UnicodeError):
            return None

    def do_GET(self):
        path = urlsplit(self.path).path
        pages = {"/": "index.html", "/login": "login.html", "/register": "register.html", "/payment": "payment.html"}
        if path in pages:
            return self.serve_file(ROOT / "templates" / pages[path])
        if path.startswith("/static/"):
            asset = path[len("/static/"):]
            # Only known, flat static assets may be served. Never expose the database.
            if asset in {"style.css", "script.js", "auth.js", "payment.js"}:
                return self.serve_file(ROOT / "static" / asset)
            return self.send_error(HTTPStatus.NOT_FOUND, "File not found")
        if path == "/api/parking":
            with database() as db:
                items = [dict(row) for row in db.execute("SELECT * FROM parking ORDER BY name")]
            for place in items:
                for suffix in ("2w", "4w"):
                    total = place["total_" + suffix]
                    free = place["available_" + suffix]
                    place["chance_" + suffix] = round(100 * free / total, 2) if total else 0
            return self.reply(200, items)
        if path == "/api/me":
            return self.reply(200, {"user": self.user()})
        if path == "/api/bookings":
            user = self.user()
            if not user:
                return self.reply(401, {"error": "Please log in first."})
            with database() as db:
                rows = db.execute("""SELECT b.id,p.name,p.area,b.vehicle_type,b.hours,b.amount,
                    b.payment_method,b.payment_status,b.transaction_ref,b.status,b.booked_at,b.number_plate
                    FROM bookings b JOIN parking p ON p.id=b.parking_id
                    WHERE b.user_id=? ORDER BY b.id DESC""", (user["id"],)).fetchall()
            return self.reply(200, [dict(row) for row in rows])
        return self.send_error(HTTPStatus.NOT_FOUND, "Page not found")

    def do_POST(self):
        path = urlsplit(self.path).path
        if path == "/api/logout":
            return self.reply(200, {"message": "Logged out."}, "parkeasy_session=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax")
        # Cancelling a booking needs no JSON body.
        match = re.fullmatch(r"/api/bookings/(\d+)/cancel", path)
        if match:
            user = self.user()
            if not user:
                return self.reply(401, {"error": "Please log in to cancel a booking."})
            booking_id = int(match.group(1))
            with database() as db:
                db.execute("BEGIN IMMEDIATE")
                booking = db.execute("""SELECT parking_id,vehicle_type FROM bookings
                    WHERE id=? AND user_id=? AND status='booked'""", (booking_id, user["id"])).fetchone()
                if not booking:
                    return self.reply(404, {"error": "Active booking not found."})
                suffix = "2w" if booking["vehicle_type"] == "2W" else "4w"
                db.execute("UPDATE bookings SET status='cancelled' WHERE id=?", (booking_id,))
                db.execute(f"UPDATE parking SET available_{suffix}=available_{suffix}+1 WHERE id=?",
                           (booking["parking_id"],))
            return self.reply(200, {"message": "Booking cancelled; space restored."})
        data = self.json_body()
        if data is None:
            return self.reply(400, {"error": "Please send valid information."})
        if path == "/api/register":
            name = str(data.get("name", "")).strip()
            email = str(data.get("email", "")).strip().lower()
            password = str(data.get("password", ""))
            if not (2 <= len(name) <= 80 and re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email)
                    and len(email) <= 200 and 8 <= len(password) <= 128):
                return self.reply(400, {"error": "Enter your name, valid email, and password (8+ characters)."})
            try:
                with database() as db:
                    row = db.execute("INSERT INTO users(name,email,password_hash) VALUES (?,?,?)",
                                     (name, email, password_hash(password)))
                    new_id = row.lastrowid
            except sqlite3.IntegrityError:
                return self.reply(409, {"error": "Email already registered. Please log in."})
            return self.reply(201, {"message": "Account created."},
                              f"parkeasy_session={signed_cookie(new_id)}; Path=/; HttpOnly; SameSite=Lax")
        if path == "/api/login":
            email = str(data.get("email", "")).strip().lower()
            password = str(data.get("password", ""))
            with database() as db:
                account = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
            if not account or not verify_password(password, account["password_hash"]):
                return self.reply(401, {"error": "Incorrect email or password."})
            return self.reply(200, {"message": "Logged in."},
                              f"parkeasy_session={signed_cookie(account['id'])}; Path=/; HttpOnly; SameSite=Lax")
        user = self.user()
        if not user:
            return self.reply(401, {"error": "Please log in to book parking."})
        if path == "/api/book":
            try:
                parking_id = int(data.get("parking_id"))
                hours = int(data.get("hours"))
            except (TypeError, ValueError):
                return self.reply(400, {"error": "Invalid parking selection."})
            vehicle = data.get("vehicle_type")
            method = data.get("payment_method")
            plate = re.sub(r"[\s-]", "", str(data.get("number_plate", ""))).upper()
            # Supports modern and older Indian registration formats, including BH series.
            if not (re.fullmatch(r"[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{1,4}", plate)
                    or re.fullmatch(r"[0-9]{2}BH[0-9]{4}[A-Z]{1,2}", plate)):
                return self.reply(400, {"error": "Enter a valid Indian registration, e.g. GJ01AB1234."})
            if vehicle not in ("2W", "4W") or hours not in range(1, 9) or method not in (
                    "Cash at parking", "Demo UPI", "Demo Card"):
                return self.reply(400, {"error": "Choose a vehicle, 1–8 hours, and payment option."})
            suffix = "2w" if vehicle == "2W" else "4w"
            with database() as db:
                db.execute("BEGIN IMMEDIATE")
                p = db.execute("SELECT * FROM parking WHERE id=?", (parking_id,)).fetchone()
                if not p or p["available_" + suffix] == 0:
                    return self.reply(409, {"error": "No parking spaces available."})
                duplicate = db.execute("SELECT id FROM bookings WHERE number_plate=? AND status='booked' LIMIT 1", (plate,)).fetchone()
                if duplicate:
                    return self.reply(409, {"error": "This vehicle number already has an active booking. Cancel it first."})
                amount = hours * p["price_" + suffix]
                payment_status = "pay_on_arrival" if method == "Cash at parking" else "paid_demo"
                transaction_ref = "" if method == "Cash at parking" else "DEMO-" + secrets.token_hex(5).upper()
                db.execute(f"UPDATE parking SET available_{suffix}=available_{suffix}-1 WHERE id=?", (parking_id,))
                cursor = db.execute("""INSERT INTO bookings
                    (user_id,parking_id,vehicle_type,hours,amount,payment_method,status,booked_at,number_plate,payment_status,transaction_ref)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)""", (user["id"], parking_id, vehicle, hours, amount,
                    method, "booked", datetime.now().strftime("%Y-%m-%d %H:%M"), plate, payment_status, transaction_ref))
            return self.reply(201, {"message": "Booking confirmed (simulation only).", "booking_id": cursor.lastrowid,
                                    "amount": amount, "number_plate": plate, "payment_status": payment_status,
                                    "transaction_ref": transaction_ref})
        return self.send_error(HTTPStatus.NOT_FOUND, "Action not found")


if __name__ == "__main__":
    setup_database()
    print("\n" + "=" * 52, flush=True)
    print(" ParkEasy - Student Parking Finder", flush=True)
    print(" Open in browser: http://127.0.0.1:5000/", flush=True)
    print(" Press Ctrl+C in this terminal to stop the website.", flush=True)
    print("=" * 52 + "\n", flush=True)
    try:
        with ThreadingHTTPServer((HOST, PORT), ParkEasyHandler) as server:
            if os.environ.get("PARKEASY_NO_BROWSER") != "1":
                webbrowser.open(f"http://{HOST}:{PORT}/")
            server.serve_forever()
    except OSError as exc:
        print("\nCould not start: " + str(exc), flush=True)
        print("Another app may already be using port 5000. Close it and retry.", flush=True)
        raise SystemExit(1)
    except KeyboardInterrupt:
        print("\nParkEasy stopped.")
