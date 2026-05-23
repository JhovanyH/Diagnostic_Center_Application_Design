# modules/dashboard_module.py
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from time import strftime

class DashboardModule:
    def __init__(self, parent):
        self.parent = parent

    def show(self):
        # ====================== MAIN CONTAINER ======================
        main_container = tk.Frame(self.parent, bg="white")
        main_container.pack(fill="both", expand=True, padx=20, pady=15)

        # ====================== TOP GREETING ======================
        def get_greeting():
            hour = datetime.now().hour
            if 5 <= hour < 12:
                return "Good Morning!"
            elif 12 <= hour < 18:
                return "Good Afternoon!"
            else:
                return "Good Evening!"

        greeting_frame = tk.Frame(main_container, bg="#f8f9fa")
        greeting_frame.pack(fill="x", pady=(0, 15))

        tk.Label(greeting_frame, text=get_greeting(),
                font=("Arial", 24, "bold"), bg="#f8f9fa", fg="#2c3e50").pack(anchor="w")

        current_date = datetime.now().strftime("%A, %B %d, %Y")

        tk.Label(greeting_frame, text=current_date,
                 font=("Arial", 12), bg="#f8f9fa", fg="#7f8c8d").pack(anchor="w")


        # ====================== STATS CARDS ======================
        stats_frame = tk.Frame(main_container, bg="#f8f9fa")
        stats_frame.pack(fill="x", pady=10)

        stats = [
            ("Today's Patients", "24", "+3 walk-ins", "#3498db"),
            ("Appointments", "18", "6 remaining", "#2ecc71"),
            ("Pending Results", "7", "2 urgent", "#e67e22"),
            ("Today's Collections", "₱15,400", "12 transactions", "#9b59b6")
        ]

        for title, value, subtitle, color in stats:
            card = tk.Frame(stats_frame, bg="white", relief="solid", bd=1, padx=15, pady=12)
            card.pack(side="left", fill="both", expand=True, padx=8)

            tk.Label(card, text=title, font=("Arial", 10, "bold"), fg="#2c3e50").pack(anchor="w")
            tk.Label(card, text=value, font=("Arial", 26, "bold"), fg=color).pack(anchor="w", pady=4)
            tk.Label(card, text=subtitle, font=("Arial", 9), fg="#27ae60").pack(anchor="w")

        # ====================== QUICK ACTIONS ======================
        action_frame = tk.Frame(main_container, bg="#f8f9fa")
        action_frame.pack(fill="x", pady=15)

        ttk.Button(action_frame, text="+ New Appointment",
                  command=self.open_new_appointment, style="Accent.TButton").pack(side="left", padx=5)
        ttk.Button(action_frame, text="+ Register Patient",
                  command=self.open_register_patient, style="Accent.TButton").pack(side="left", padx=5)

        # ====================== TODAY'S SCHEDULE ======================
        tk.Label(main_container, text="Today's Schedule",
                font=("Arial", 15, "bold"), bg="#f8f9fa", fg="#2c3e50").pack(anchor="w", pady=(10, 5))

        columns = ("Time", "Patient", "Tests", "Status")
        schedule_tree = ttk.Treeview(main_container, columns=columns, show="headings", height=9)

        schedule_tree.heading("Time", text="Time")
        schedule_tree.heading("Patient", text="Patient")
        schedule_tree.heading("Tests", text="Tests")
        schedule_tree.heading("Status", text="Status")

        schedule_tree.column("Time", width=90)
        schedule_tree.column("Patient", width=180)
        schedule_tree.column("Tests", width=280)
        schedule_tree.column("Status", width=110)

        data = [
            ("8:00 AM", "Juan dela Cruz", "CBC - Urinalysis", "Done"),
            ("9:30 AM", "Ana Santos", "Chest X-Ray PA", "In Progress"),
            ("10:00 AM", "Pedro Bautista", "Blood Chemistry", "Waiting"),
            ("11:00 AM", "Liza Reyes", "Ultrasound OB", "Waiting"),
        ]

        for row in data:
            schedule_tree.insert("", "end", values=row)

        schedule_tree.pack(fill="x", pady=5)

        # ====================== BOTTOM SECTION ======================
        bottom = tk.Frame(main_container, bg="#f8f9fa")
        bottom.pack(fill="both", expand=True, pady=15)

        # Walk-in Queue
        queue_frame = tk.Frame(bottom, bg="white", relief="solid", bd=1)
        queue_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tk.Label(queue_frame, text="Walk-in Queue (2 waiting)",
                font=("Arial", 13, "bold"), bg="white").pack(anchor="w", padx=15, pady=10)

        # Unpaid Balances
        unpaid_frame = tk.Frame(bottom, bg="white", relief="solid", bd=1)
        unpaid_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))

        tk.Label(unpaid_frame, text="Unpaid Balances (3 accounts)",
                font=("Arial", 13, "bold"), fg="#e74c3c", bg="white").pack(anchor="w", padx=15, pady=10)

    # ====================== ACTION METHODS ======================
    def open_new_appointment(self):
        from modules.appointments import AppointmentsModule
        hidden = tk.Frame(self.parent)
        mod = AppointmentsModule(hidden)
        hidden.pack_forget()
        mod.new_appointment()

    def open_register_patient(self):
        from modules.patients import PatientsModule
        hidden = tk.Frame(self.parent)
        mod = PatientsModule(hidden)
        mod.show()
        hidden.pack_forget()
        mod.open_patient_registration()