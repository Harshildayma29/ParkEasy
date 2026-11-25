# ParkEasy Premium — Ahmedabad Smart Parking (College Project)

**Run:** `python server.py` and open http://127.0.0.1:5000. Python standard library only, no installation needed.

## Features
- Responsive premium light UI, dark blue hero, mobile-friendly parking cards.
- 48 illustrative Ahmedabad area parking entries; separate bike / car space counts and hourly rates.
- Search, area filter, available-only filter, vehicle type selector.
- Availability dashboard: total free/total capacity and top-10 horizontal bar graph (two decimals).
- User registration/login, Indian number plate entry, duration 1–8 hours, dynamic fee calculation.
- Demo checkout methods: UPI simulation / card simulation / pay at parking; no real processing.
- Booking receipt with order ID, payment status, and demo reference; print receipt.
- Booking history, cancellations, automatic space restoration, SQLite storage.

## Payment semantics
For **Demo UPI** / **Demo Card**, checkout marks the booking `paid_demo` (a simulation, no actual transaction). **Cash at parking** marks the booking `pay_on_arrival` (no money collected). Never provide banking credentials in this project.

## Probability explanation
`availability_percentage = (available_spots / total_spots) * 100`, rounded to 2 decimal places for display. This is an accurate percentage of **stored sample occupancy counts**, not a real-time occupancy estimate or independently trained AI prediction. The source data are fabricated for a college prototype.

## Use existing records
Copy your older `data/parking.db` before running. The program adds payment status and demo transaction reference columns without deleting earlier records. Existing older paid-demo statuses cannot be proven and remain `pending`.

## Tech / subjects
Design Thinking (empathize, define, ideate, prototype, test), Probability/Statistics (occupancy ratio), Web Tech (HTML/CSS/JS), Python (standard library HTTP), AI concepts (future model extension; **no trained AI model implemented**). SQLite database for records. See DESIGN_THINKING.md and FACULTY_NOTES.md.
