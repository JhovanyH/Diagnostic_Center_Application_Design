# modules/appointments_module.py
import tkinter as tk
from tkinter import ttk, messagebox
import calendar
from datetime import datetime


class AppointmentsModule:
    def __init__(self, parent):
        self.parent = parent

    def show(self):
        """Appointments Module - Matches your screenshot"""
        header = tk.Frame(self.parent, bg="white")
        header.pack(fill="x", padx=25, pady=15)

        tk.Label(header, text="Appointments", font=("Arial", 18, "bold"), bg="white").pack(side="left")
        tk.Label(header, text="May 2025 - Schedule & Walk-ins", fg="gray", bg="white").pack(side="left", padx=20)

        ttk.Button(header, text="+ New Appointment",
                  command=self.new_appointment).pack(side="right")

        # Main Content
        main = tk.Frame(self.parent, bg="white")
        main.pack(fill="both", expand=True, padx=25, pady=5)

        # Left Side: Calendar
        left = tk.Frame(main, bg="white", width=340)
        left.pack(side="left", fill="y", padx=(0, 20))
        left.pack_propagate(False)

        tk.Label(left, text="May 2025", font=("Arial", 14, "bold"), bg="white").pack(pady=8)
        self.create_calendar(left)

        # Right Side: Appointment List + Walk-in Queue
        right = tk.Frame(main, bg="white")
        right.pack(side="right", fill="both", expand=True)

        # Today's Booked
        tk.Label(right, text="Monday, May 5 — 18 booked Today",
                font=("Arial", 13, "bold"), bg="white").pack(anchor="w", pady=(0,8))

        # Appointment Table
        columns = ("Time", "Patient", "Tests Requested", "Status")
        tree = ttk.Treeview(right, columns=columns, show="headings", height=18)

        tree.heading("Time", text="Time")
        tree.heading("Patient", text="Patient")
        tree.heading("Tests Requested", text="Tests Requested")
        tree.heading("Status", text="Status")

        tree.column("Time", width=90)
        tree.column("Patient", width=160)
        tree.column("Tests Requested", width=260)
        tree.column("Status", width=110)

        # Sample Data matching your screenshot
        appointments = [
            ("8:00 AM", "Juan dela Cruz", "CBC - Urinalysis", "Done"),
            ("9:30 AM", "Ana Santos", "Chest X-Ray PA", "In Progress"),
            ("10:00 AM", "Pedro Bautista", "Blood Chemistry", "Waiting"),
            ("11:00 AM", "Liza Reyes", "Ultrasound OB", "Waiting"),
            ("1:30 PM", "Carlo Mendoza", "ECG - Fasting Blood", "Scheduled"),
        ]

        status_colors = {"Done": "green", "In Progress": "blue", "Waiting": "orange", "Scheduled": "gray"}

        for app in appointments:
            item = tree.insert("", "end", values=app)
            tree.item(item, tags=(app[3],))

        for status, color in status_colors.items():
            tree.tag_configure(status, foreground=color)

        tree.pack(fill="both", expand=True, pady=5)

    def create_calendar(self, parent):
        """Simple Calendar for May 2025"""
        days = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]
        for i, day in enumerate(days):
            tk.Label(parent, text=day, width=5, bg="#f0f0f0", font=("Arial", 9, "bold")).grid(row=0, column=i, padx=1, pady=4)

        # Dates (May 2025 starts on Thursday)
        date = 1
        for row in range(1, 6):
            for col in range(7):
                if (row == 1 and col < 3) or date > 31:  # Adjust for May 2025
                    lbl = tk.Label(parent, text="", width=5, height=2)
                else:
                    bg = "#e3f2fd" if date == 5 else "white"
                    fg = "blue" if date == 5 else "black"
                    lbl = tk.Label(parent, text=str(date), width=5, height=2,
                                 bg=bg, fg=fg, relief="ridge", font=("Arial", 10))
                    date += 1
                lbl.grid(row=row, column=col, padx=1, pady=1)

    def new_appointment(self):
        """New Appointment Form"""
        win = tk.Toplevel(self.parent)
        win.title("New Appointment")
        win.geometry("680x720")
        win.grab_set()

        tk.Label(win, text="New Appointment", font=("Arial", 16, "bold")).pack(pady=15)

        form = tk.Frame(win)
        form.pack(pady=10, padx=40, fill="both", expand=True)

        # Patient Search
        tk.Label(form, text="Patient Name/ID").grid(row=0, column=0, sticky="w", pady=8)
        ttk.Entry(form, width=40).grid(row=0, column=1, pady=8, columnspan=2, sticky="ew")

        # Date & Time
        tk.Label(form, text="Date").grid(row=1, column=0, sticky="w", pady=8)
        ttk.Entry(form, width=20).grid(row=1, column=1, pady=8, sticky="w")
        tk.Label(form, text="Time").grid(row=1, column=2, sticky="w", pady=8, padx=20)
        ttk.Entry(form, width=15).grid(row=1, column=3, pady=8, sticky="w")

        # Tests Requested
        tk.Label(form, text="Tests Requested").grid(row=2, column=0, sticky="w", pady=8)
        tests_entry = tk.Text(form, height=4, width=50)
        tests_entry.grid(row=2, column=1, columnspan=3, pady=8, sticky="ew")
        tests_entry.insert("1.0", "CBC, Urinalysis, X-Ray...")

        # Remarks
        tk.Label(form, text="Remarks / Notes").grid(row=3, column=0, sticky="w", pady=8)
        remarks = tk.Text(form, height=4, width=50)
        remarks.grid(row=3, column=1, columnspan=3, pady=8, sticky="ew")
        remarks.insert("1.0", "Fasting required, referral, etc.")

        # Buttons
        btn_frame = tk.Frame(win)
        btn_frame.pack(pady=25)
        ttk.Button(btn_frame, text="Save Appointment & Send Reminder",
                  command=lambda: self.save_appointment(win)).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="Cancel", command=win.destroy).pack(side="left", padx=10)

    def save_appointment(self, window):
        messagebox.showinfo("Success", "Appointment saved successfully!\nReminder sent to patient.")
        window.destroy()