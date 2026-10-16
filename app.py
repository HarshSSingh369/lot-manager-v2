"""Tkinter interface for Lot Manager v2."""

import tkinter as tk
from tkinter import messagebox, ttk

from lot_manager import ParkingLot, RATES_PER_HOUR


class LotManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Lot Manager v2")
        self.geometry("1050x720")
        self.minsize(850, 600)
        self.configure(bg="#f4f7fb")
        self.lot = ParkingLot()
        self._style()
        self._build()
        self.refresh()

    def _style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#f4f7fb")
        style.configure("Card.TFrame", background="white")
        style.configure("TLabel", background="#f4f7fb", foreground="#172033", font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 22, "bold"), foreground="#152746")
        style.configure("Metric.TLabel", font=("Segoe UI", 18, "bold"), foreground="#152746", background="white")
        style.configure("MetricName.TLabel", font=("Segoe UI", 9), foreground="#62718a", background="white")
        style.configure("TButton", padding=(10, 7), font=("Segoe UI", 9, "bold"))
        style.configure("Treeview", rowheight=27, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))

    def _build(self):
        outer = ttk.Frame(self, padding=20)
        outer.pack(fill="both", expand=True)
        header = ttk.Frame(outer)
        header.pack(fill="x", pady=(0, 14))
        ttk.Label(header, text="Lot Manager v2", style="Title.TLabel").pack(side="left")
        ttk.Label(header, text="Linked-list parking • saved sessions • FIFO waiting queue").pack(side="right", pady=9)

        metrics = ttk.Frame(outer)
        metrics.pack(fill="x", pady=(0, 14))
        self.metric_values = {}
        for key, label in (("total", "TOTAL SLOTS"), ("free", "FREE"), ("occupied", "OCCUPIED"),
                           ("waiting", "WAITING"), ("revenue", "TODAY'S REVENUE")):
            card = ttk.Frame(metrics, style="Card.TFrame", padding=(14, 10))
            card.pack(side="left", fill="x", expand=True, padx=(0, 8))
            value = ttk.Label(card, text="0", style="Metric.TLabel")
            value.pack(anchor="w")
            ttk.Label(card, text=label, style="MetricName.TLabel").pack(anchor="w")
            self.metric_values[key] = value

        controls = ttk.Frame(outer, style="Card.TFrame", padding=12)
        controls.pack(fill="x", pady=(0, 12))
        self.vehicle_entry = ttk.Entry(controls, width=18)
        self.vehicle_entry.pack(side="left", padx=(0, 8))
        self.vehicle_entry.insert(0, "Vehicle number")
        self.vehicle_entry.bind("<FocusIn>", self._clear_placeholder)
        self.vehicle_type = tk.StringVar(value="Car")
        ttk.Combobox(controls, textvariable=self.vehicle_type, values=list(RATES_PER_HOUR),
                     state="readonly", width=10).pack(side="left", padx=(0, 8))
        ttk.Button(controls, text="Park vehicle", command=self.park).pack(side="left", padx=3)
        ttk.Button(controls, text="Add to queue", command=self.queue_vehicle).pack(side="left", padx=3)
        self.exit_entry = ttk.Entry(controls, width=17)
        self.exit_entry.pack(side="left", padx=(14, 6))
        self.exit_entry.insert(0, "Vehicle to exit")
        self.exit_entry.bind("<FocusIn>", self._clear_placeholder)
        ttk.Button(controls, text="Exit & bill", command=self.exit_vehicle).pack(side="left", padx=3)
        ttk.Button(controls, text="＋ Slot", command=self.add_slot).pack(side="right", padx=3)
        ttk.Button(controls, text="− Last slot", command=self.remove_slot).pack(side="right", padx=3)

        self.tabs = ttk.Notebook(outer)
        self.tabs.pack(fill="both", expand=True)
        parking_tab = ttk.Frame(self.tabs, padding=12)
        queue_tab = ttk.Frame(self.tabs, padding=12)
        list_tab = ttk.Frame(self.tabs, padding=12)
        history_tab = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(parking_tab, text="Parking spaces")
        self.tabs.add(queue_tab, text="Waiting queue")
        self.tabs.add(list_tab, text="Linked list")
        self.tabs.add(history_tab, text="Revenue history")

        self.slot_tree = self._tree(parking_tab, ("slot", "status", "vehicle", "type", "since"),
                                     ("Slot", "Status", "Vehicle", "Type", "Parked since"))
        self.queue_tree = self._tree(queue_tab, ("position", "vehicle", "type"),
                                      ("Position", "Vehicle", "Type"))
        self.linked_list = tk.Text(list_tab, wrap="word", font=("Consolas", 11),
                                   bg="#152746", fg="#e8f0ff", relief="flat", padx=18, pady=18)
        self.linked_list.pack(fill="both", expand=True)
        self.history_tree = self._tree(history_tab, ("date", "vehicle", "slot", "hours", "fee"),
                                        ("Exit time", "Vehicle", "Slot", "Hours billed", "Fee"))

        footer = ttk.Frame(outer)
        footer.pack(fill="x", pady=(10, 0))
        self.status = ttk.Label(footer, text="Ready")
        self.status.pack(side="left")
        ttk.Label(footer, text="Rates per hour: Bike ₹10 • Car ₹20 • Truck ₹60 • Other ₹30").pack(side="right")

    @staticmethod
    def _tree(parent, keys, labels):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)
        tree = ttk.Treeview(frame, columns=keys, show="headings")
        for key, label in zip(keys, labels):
            tree.heading(key, text=label)
            tree.column(key, width=120, anchor="w")
        scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        return tree

    def _clear_placeholder(self, event):
        if event.widget.get() in ("Vehicle number", "Vehicle to exit"):
            event.widget.delete(0, "end")

    def _say(self, text):
        self.status.configure(text=text)

    def _error(self, error):
        messagebox.showwarning("Lot Manager", str(error), parent=self)

    def park(self):
        try:
            slot = self.lot.park(self.vehicle_entry.get(), self.vehicle_type.get())
            self._say(f"Parked in slot {slot.number}." if slot else "Lot full; vehicle added to the end of the waiting queue.")
            self.vehicle_entry.delete(0, "end")
            self.refresh()
        except ValueError as exc:
            self._error(exc)

    def queue_vehicle(self):
        try:
            self.lot.add_to_waiting(self.vehicle_entry.get(), self.vehicle_type.get())
            self._say("Vehicle added to the waiting queue.")
            self.vehicle_entry.delete(0, "end")
            self.refresh()
        except ValueError as exc:
            self._error(exc)

    def exit_vehicle(self):
        try:
            session = self.lot.exit_vehicle(self.exit_entry.get())
            self.exit_entry.delete(0, "end")
            self._say(f"{session.vehicle_number} exited. Fee: ₹{session.fee:.2f} for {session.billed_hours} billed hour(s).")
            messagebox.showinfo("Parking receipt",
                f"Vehicle: {session.vehicle_number}\nType: {session.vehicle_type}\nSlot: {session.slot_number}\n"
                f"Hours billed: {session.billed_hours}\nRate: ₹{RATES_PER_HOUR[session.vehicle_type]:.2f}/hour\n"
                f"Total: ₹{session.fee:.2f}", parent=self)
            self.refresh()
        except ValueError as exc:
            self._error(exc)

    def add_slot(self):
        slot = self.lot.add_slot()
        self._say(f"Added slot {slot.number}.")
        self.refresh()

    def remove_slot(self):
        try:
            removed = self.lot.remove_last_slot()
            self._say(f"Removed slot {removed}.")
            self.refresh()
        except ValueError as exc:
            self._error(exc)

    def refresh(self):
        revenue, exits = self.lot.daily_revenue()
        self.metric_values["total"].configure(text=str(self.lot.capacity))
        self.metric_values["free"].configure(text=str(self.lot.free_count))
        self.metric_values["occupied"].configure(text=str(self.lot.occupied_count))
        self.metric_values["waiting"].configure(text=str(len(self.lot.waiting)))
        self.metric_values["revenue"].configure(text=f"₹{revenue:,.0f}")
        self.slot_tree.delete(*self.slot_tree.get_children())
        for slot in self.lot:
            self.slot_tree.insert("", "end", values=(slot.number, "Free" if slot.is_free else "Occupied",
                slot.vehicle_number or "—", slot.vehicle_type or "—", slot.entry_time or "—"))
        self.queue_tree.delete(*self.queue_tree.get_children())
        for index, vehicle in enumerate(self.lot.waiting, 1):
            self.queue_tree.insert("", "end", values=(index, vehicle["vehicle_number"], vehicle["vehicle_type"]))
        self.linked_list.configure(state="normal")
        self.linked_list.delete("1.0", "end")
        chain = "HEAD"
        for slot in self.lot:
            status = f"{slot.number}: {slot.vehicle_number or 'FREE'}"
            chain += f"  →  [ {status} ]"
        self.linked_list.insert("1.0", chain + "  →  None\n\n"
            "Each box is a node in the singly linked list. The next arrow follows the node reference.")
        self.linked_list.configure(state="disabled")
        self.history_tree.delete(*self.history_tree.get_children())
        for session in reversed(self.lot.sessions):
            self.history_tree.insert("", "end", values=(session.exit_time.replace("T", " "), session.vehicle_number,
                session.slot_number, session.billed_hours, f"₹{session.fee:.2f}"))


if __name__ == "__main__":
    LotManagerApp().mainloop()
