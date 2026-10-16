# Lot Manager v2

A small desktop parking-lot manager built with Python and Tkinter. It uses a
hand-written singly linked list for parking spaces, saves state between runs,
keeps a first-in-first-out waiting queue, and records completed sessions for a
daily revenue summary.

## Features

- Park vehicles in the first free slot and prevent duplicate vehicle numbers.
- Calculate exit fees by vehicle type and round parking time up to a full hour.
- Add or remove slots while the app is open; occupied slots cannot be removed.
- Add vehicles to a FIFO waiting queue. The first waiting vehicle takes a slot
  when a parked vehicle exits.
- Save occupied slots, the queue, and completed sessions in `parking_data.json`.
- Review today's revenue and completed session history.
- View the parking spaces as a linked list, with nodes and next arrows.
- Use only Python's standard library; no package installation is required.

## Requirements

- Python 3.10 or later
- Tkinter (included with most Python installations; some Linux distributions
  package it separately)

## Run

Open a terminal in this folder and run:

```bash
python app.py
```

The app starts with 10 free slots. Its saved data file is created beside the
Python files the first time the lot changes.

## Rates

| Vehicle type | Rate per hour |
|---|---:|
| Bike | ₹10 |
| Car | ₹20 |
| Truck | ₹60 |
| Other | ₹30 |

Any started hour is billed as a full hour. A parking session shorter than one
hour is billed for one hour.

## Project structure

```text
lot-manager-v2/
├── app.py             Tkinter interface
├── lot_manager.py     Linked list, queue, billing, and JSON persistence
├── README.md          Setup and feature guide
└── .gitignore         Keeps local parking data out of Git
```

## Data structure notes

Every space is a `Slot` node containing its number, current vehicle details,
and a reference to the next node. `ParkingLot` owns the `head` and `tail`
references and performs traversal, insertion, deletion, and search. The
waiting area is a FIFO queue, so the earliest waiting vehicle is assigned the
next space that becomes available.

Completed sessions store the vehicle, slot, entry and exit times, billed hours,
and fee. The daily revenue card totals sessions by their exit date.

## GitHub publishing checklist

- Keep real parking data out of the repository. `.gitignore` excludes
  `parking_data.json`.
- Add screenshots of the parking table, linked-list view, and receipt dialog.
- In your repository description, note which parts you implemented and any
  changes you make after this starter version.
- Add a license if you want others to reuse the code.

## Future improvements

- Add automated tests for list operations, waiting order, persistence, and
  billing boundaries.
- Add a date selector and CSV export to the revenue report.
- Add a search field and validation for local vehicle registration formats.
- Move from JSON storage to SQLite when keeping a larger session history.
