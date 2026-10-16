"""Core parking lot logic for Lot Manager v2.

The parking spaces are stored in a hand-built singly linked list. Completed
parking sessions are saved as JSON so the revenue report survives restarts.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, date
from pathlib import Path
import json
import math
from typing import Iterator


RATES_PER_HOUR = {"Bike": 10.0, "Car": 20.0, "Truck": 60.0, "Other": 30.0}
DATA_FILE = Path(__file__).with_name("parking_data.json")


@dataclass
class Slot:
    number: int
    vehicle_number: str | None = None
    vehicle_type: str | None = None
    entry_time: str | None = None
    next: Slot | None = None

    @property
    def is_free(self) -> bool:
        return self.vehicle_number is None


@dataclass
class Session:
    vehicle_number: str
    vehicle_type: str
    slot_number: int
    entry_time: str
    exit_time: str
    billed_hours: int
    fee: float


class ParkingLot:
    """A parking lot whose slots are maintained as a singly linked list."""

    def __init__(self, capacity: int = 10, data_file: Path = DATA_FILE):
        if capacity < 0:
            raise ValueError("Capacity cannot be negative.")
        self.head: Slot | None = None
        self.tail: Slot | None = None
        self.capacity = 0
        self.waiting: list[dict[str, str]] = []
        self.sessions: list[Session] = []
        self.data_file = Path(data_file)
        for _ in range(capacity):
            self.add_slot(save=False)
        self.load()

    def __iter__(self) -> Iterator[Slot]:
        current = self.head
        while current:
            yield current
            current = current.next

    @property
    def occupied_count(self) -> int:
        return sum(not slot.is_free for slot in self)

    @property
    def free_count(self) -> int:
        return self.capacity - self.occupied_count

    def find_vehicle(self, vehicle_number: str) -> Slot | None:
        key = vehicle_number.strip().upper()
        return next((s for s in self if s.vehicle_number == key), None)

    def add_slot(self, save: bool = True) -> Slot:
        slot = Slot(number=self.capacity + 1)
        if self.tail:
            self.tail.next = slot
        else:
            self.head = slot
        self.tail = slot
        self.capacity += 1
        if save:
            self.save()
        return slot

    def remove_last_slot(self) -> int:
        if not self.tail:
            raise ValueError("There are no slots to remove.")
        if not self.tail.is_free:
            raise ValueError("The last slot is occupied; release it before removing it.")
        removed = self.tail.number
        if self.head is self.tail:
            self.head = self.tail = None
        else:
            previous = self.head
            while previous and previous.next is not self.tail:
                previous = previous.next
            assert previous is not None
            previous.next = None
            self.tail = previous
        self.capacity -= 1
        self.save()
        return removed

    def park(self, vehicle_number: str, vehicle_type: str) -> Slot | None:
        number = vehicle_number.strip().upper()
        if not number:
            raise ValueError("Enter a vehicle number.")
        if vehicle_type not in RATES_PER_HOUR:
            raise ValueError("Choose a valid vehicle type.")
        if self.find_vehicle(number):
            raise ValueError("That vehicle is already parked.")
        if any(v["vehicle_number"] == number for v in self.waiting):
            raise ValueError("That vehicle is already in the waiting queue.")
        slot = next((s for s in self if s.is_free), None)
        if slot is None:
            self.waiting.append({"vehicle_number": number, "vehicle_type": vehicle_type})
            self.save()
            return None
        slot.vehicle_number = number
        slot.vehicle_type = vehicle_type
        slot.entry_time = datetime.now().isoformat(timespec="seconds")
        self.save()
        return slot

    def add_to_waiting(self, vehicle_number: str, vehicle_type: str) -> None:
        number = vehicle_number.strip().upper()
        if not number:
            raise ValueError("Enter a vehicle number.")
        if vehicle_type not in RATES_PER_HOUR:
            raise ValueError("Choose a valid vehicle type.")
        if self.find_vehicle(number) or any(v["vehicle_number"] == number for v in self.waiting):
            raise ValueError("That vehicle is already parked or waiting.")
        self.waiting.append({"vehicle_number": number, "vehicle_type": vehicle_type})
        self.save()

    def exit_vehicle(self, vehicle_number: str) -> Session:
        number = vehicle_number.strip().upper()
        slot = self.find_vehicle(number)
        if slot is None:
            raise ValueError("Vehicle not found in the parking lot.")
        assert slot.entry_time and slot.vehicle_type
        entered = datetime.fromisoformat(slot.entry_time)
        exited = datetime.now()
        minutes = max(0, math.ceil((exited - entered).total_seconds() / 60))
        billed_hours = max(1, math.ceil(minutes / 60))
        fee = billed_hours * RATES_PER_HOUR[slot.vehicle_type]
        session = Session(number, slot.vehicle_type, slot.number, slot.entry_time,
                          exited.isoformat(timespec="seconds"), billed_hours, fee)
        slot.vehicle_number = slot.vehicle_type = slot.entry_time = None
        self.sessions.append(session)

        # First-come-first-served: put the first waiting vehicle into the freed slot.
        if self.waiting:
            next_vehicle = self.waiting.pop(0)
            slot.vehicle_number = next_vehicle["vehicle_number"]
            slot.vehicle_type = next_vehicle["vehicle_type"]
            slot.entry_time = datetime.now().isoformat(timespec="seconds")
        self.save()
        return session

    def cancel_waiting(self, vehicle_number: str) -> None:
        key = vehicle_number.strip().upper()
        for index, vehicle in enumerate(self.waiting):
            if vehicle["vehicle_number"] == key:
                self.waiting.pop(index)
                self.save()
                return
        raise ValueError("Vehicle not found in the waiting queue.")

    def daily_revenue(self, for_date: date | None = None) -> tuple[float, int]:
        target = for_date or date.today()
        matching = [s for s in self.sessions if datetime.fromisoformat(s.exit_time).date() == target]
        return sum(s.fee for s in matching), len(matching)

    def save(self) -> None:
        payload = {
            "version": 2,
            "capacity": self.capacity,
            "slots": [{"number": s.number, "vehicle_number": s.vehicle_number,
                       "vehicle_type": s.vehicle_type, "entry_time": s.entry_time} for s in self],
            "waiting": self.waiting,
            "sessions": [asdict(s) for s in self.sessions],
        }
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        temp_file = self.data_file.with_suffix(".tmp")
        temp_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        temp_file.replace(self.data_file)

    def load(self) -> None:
        if not self.data_file.exists():
            return
        try:
            payload = json.loads(self.data_file.read_text(encoding="utf-8"))
            if payload.get("version") != 2:
                return
            self.head = self.tail = None
            self.capacity = 0
            for item in payload.get("slots", []):
                slot = self.add_slot(save=False)
                slot.number = int(item["number"])
                slot.vehicle_number = item.get("vehicle_number")
                slot.vehicle_type = item.get("vehicle_type")
                slot.entry_time = item.get("entry_time")
            self.waiting = payload.get("waiting", [])
            self.sessions = [Session(**item) for item in payload.get("sessions", [])]
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
            # Preserve a damaged save file for manual recovery; start a fresh lot.
            self.head = self.tail = None
            self.capacity = 0
            self.waiting = []
            self.sessions = []

