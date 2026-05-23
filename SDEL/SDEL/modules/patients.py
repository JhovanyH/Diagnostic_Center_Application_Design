# modules/patients_module.py
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
import re

class PatientsModule:
    def __init__(self, parent):
        self.parent = parent
        self.db_path = "purehealthDb.db"
        self.init_db()
        self.insert_sample_data_if_empty()

    def init_db(self):
        """Create tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT UNIQUE NOT NULL,
                last_name TEXT NOT NULL,
                first_name TEXT NOT NULL,
                middle_name TEXT,
                dob DATE,
                sex TEXT CHECK(sex IN ('Male', 'Female')),
                civil_status TEXT CHECK(civil_status IN ('Single', 'Married', 'Widowed')),
                contact TEXT NOT NULL,
                email TEXT,
                philhealth TEXT,
                address TEXT NOT NULL,
                last_visit DATE,
                status TEXT DEFAULT 'Active'
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS emergency_contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT NOT NULL,
                name TEXT NOT NULL,
                relationship TEXT NOT NULL,
                contact TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE
            )
        ''')
        conn.commit()
        conn.close()

    def insert_sample_data_if_empty(self):
        """Insert sample patients if table is empty"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM patients")
        count = cursor.fetchone()[0]
        if count == 0:
            sample_patients = [
                ("PHC-2025-00118", "Torres", "Ben", "", "1981-01-15", "Male", "Single", "0956-789-0123", "", "", "Blk 1 Lot 2, GMA, Cavite", "2025-05-03", "Unpaid"),
                ("PHC-2025-00121", "Reyes", "Liza", "", "1994-03-22", "Female", "Married", "0945-678-9012", "liza@email.com", "", "123 Street, GMA, Cavite", "2025-05-04", "Active"),
                ("PHC-2025-00122", "Bautista", "Pedro", "", "1973-08-10", "Male", "Married", "0934-567-8901", "", "", "456 Avenue, GMA, Cavite", "2025-05-05", "Active"),
                ("PHC-2025-00123", "Santos", "Ana", "", "1997-05-18", "Female", "Single", "0923-456-7890", "ana@email.com", "", "789 Road, GMA, Cavite", "2025-05-05", "Active"),
                ("PHC-2025-00124", "Dela Cruz", "Juan", "", "1990-07-12", "Male", "Married", "0912-345-6789", "juan@email.com", "12-3456789-0", "House 10, GMA, Cavite", "2025-05-05", "Active"),
            ]
            for p in sample_patients:
                cursor.execute('''
                    INSERT INTO patients (patient_id, last_name, first_name, middle_name, dob, sex, civil_status,
                                          contact, email, philhealth, address, last_visit, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', p)
            # Add emergency contact for Juan
            cursor.execute('''
                INSERT INTO emergency_contacts (patient_id, name, relationship, contact)
                VALUES (?, ?, ?, ?)
            ''', ("PHC-2025-00124", "Maria Dela Cruz", "Spouse", "0917-123-4567"))
            conn.commit()
        conn.close()

    def show(self):
        """Main Patient Management Screen"""
        # Clear parent frame
        for widget in self.parent.winfo_children():
            widget.destroy()

        # Header
        header = tk.Frame(self.parent, bg="white")
        header.pack(fill="x", padx=25, pady=15)

        tk.Label(header, text="Patient Management",
                 font=("Arial", 18, "bold"), bg="white").pack(side="left")

        ttk.Button(header, text="+ Register New Patient",
                   command=self.open_patient_registration).pack(side="right")

        # Search Bar
        search_frame = tk.Frame(self.parent, bg="white")
        search_frame.pack(fill="x", padx=25, pady=8)

        tk.Label(search_frame, text="Search Patient:", bg="white").pack(side="left")
        self.search_entry = ttk.Entry(search_frame, width=40)
        self.search_entry.pack(side="left", padx=10, fill="x", expand=True)
        ttk.Button(search_frame, text="Search", command=self.search_patients).pack(side="left", padx=5)
        ttk.Button(search_frame, text="All Patients", command=self.load_all_patients).pack(side="left", padx=5)

        # Patient Table
        columns = ("Patient ID", "Full Name", "Age/Sex", "Contact Number", "Last Visit", "Status")
        self.tree = ttk.Treeview(self.parent, columns=columns, show="headings", height=22)

        column_widths = [130, 200, 100, 140, 110, 100]
        for i, col in enumerate(columns):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=column_widths[i], anchor="center")

        self.tree.pack(fill="both", expand=True, padx=25, pady=10)

        # Double click to view details
        self.tree.bind("<Double-1>", self.view_patient_details)

        # Load data
        self.load_all_patients()

    def calculate_age_sex(self, dob_str, sex):
        """Return string like '35/M' or '?/?'"""
        if not dob_str:
            return f"?/{sex[0] if sex else '?'}"
        try:
            dob = datetime.strptime(dob_str, "%Y-%m-%d")
            today = datetime.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            return f"{age}/{sex[0] if sex else '?'}"
        except:
            return f"?/{sex[0] if sex else '?'}"

    def load_all_patients(self):
        """Load all patients from database into treeview"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT patient_id, last_name, first_name, middle_name, dob, sex, contact, last_visit, status
            FROM patients ORDER BY patient_id DESC
        ''')
        rows = cursor.fetchall()
        conn.close()

        # Clear existing rows
        for row in self.tree.get_children():
            self.tree.delete(row)

        for row in rows:
            patient_id = row[0]
            full_name = f"{row[2]} {row[1]}"
            if row[3]:
                full_name += f" {row[3]}"
            age_sex = self.calculate_age_sex(row[4], row[5])
            contact = row[6] if row[6] else "N/A"
            last_visit = row[7] if row[7] else "Never"
            status = row[8] if row[8] else "Active"
            self.tree.insert("", "end", values=(patient_id, full_name, age_sex, contact, last_visit, status))

    def search_patients(self):
        keyword = self.search_entry.get().strip()
        if not keyword:
            self.load_all_patients()
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT patient_id, last_name, first_name, middle_name, dob, sex, contact, last_visit, status
            FROM patients
            WHERE patient_id LIKE ? OR first_name LIKE ? OR last_name LIKE ?
            ORDER BY patient_id DESC
        ''', (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'))
        rows = cursor.fetchall()
        conn.close()

        # Clear and display filtered
        for row in self.tree.get_children():
            self.tree.delete(row)
        for row in rows:
            patient_id = row[0]
            full_name = f"{row[2]} {row[1]}"
            if row[3]:
                full_name += f" {row[3]}"
            age_sex = self.calculate_age_sex(row[4], row[5])
            contact = row[6] if row[6] else "N/A"
            last_visit = row[7] if row[7] else "Never"
            status = row[8] if row[8] else "Active"
            self.tree.insert("", "end", values=(patient_id, full_name, age_sex, contact, last_visit, status))

    def generate_next_patient_id(self):
        """Generate next ID in format PHC-YYYY-XXXXX"""
        current_year = datetime.now().year
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT patient_id FROM patients WHERE patient_id LIKE ? ORDER BY patient_id DESC LIMIT 1",
                       (f'PHC-{current_year}-%',))
        last = cursor.fetchone()
        conn.close()
        if last:
            match = re.search(r'(\d+)$', last[0])
            if match:
                last_num = int(match.group(1))
                next_num = last_num + 1
            else:
                next_num = 1
        else:
            next_num = 1
        return f"PHC-{current_year}-{next_num:05d}"

    def save_patient_to_db(self, data):
        """Insert patient and emergency contacts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO patients
                (patient_id, last_name, first_name, middle_name, dob, sex, civil_status,
                 contact, email, philhealth, address, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['patient_id'], data['last_name'], data['first_name'], data['middle_name'],
                data['dob'], data['sex'], data['civil_status'], data['contact'],
                data['email'], data['philhealth'], data['address'], 'Active'
            ))
            for ec in data['emergency_contacts']:
                cursor.execute('''
                    INSERT INTO emergency_contacts (patient_id, name, relationship, contact)
                    VALUES (?, ?, ?, ?)
                ''', (data['patient_id'], ec['name'], ec['relationship'], ec['contact']))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def open_patient_registration(self):
        """Full registration form matching your screenshot"""
        reg_win = tk.Toplevel(self.parent)
        reg_win.title("Register New Patient")
        reg_win.geometry("860x820")
        reg_win.grab_set()
        reg_win.configure(bg="#f0f0f0")

        next_id = self.generate_next_patient_id()
        tk.Label(reg_win, text="Register New Patient", font=("Arial", 16, "bold"), bg="#f0f0f0").pack(pady=10)
        tk.Label(reg_win, text=f"Patient ID: {next_id}", fg="blue", font=("Arial", 10, "bold"), bg="#f0f0f0").pack()

        form_frame = tk.Frame(reg_win, bg="#f0f0f0")
        form_frame.pack(pady=15, padx=40, fill="both", expand=True)

        # Personal Information
        pers_frame = tk.LabelFrame(form_frame, text="Personal Information", font=("Arial", 12, "bold"), bg="#f0f0f0")
        pers_frame.pack(fill="x", pady=5)

        fields = [
            ("Last Name *", 0, 0),
            ("First Name *", 0, 2),
            ("Middle Name", 0, 4),
            ("Date of Birth * (YYYY-MM-DD)", 1, 0),
            ("Sex *", 1, 2),
            ("Civil Status", 1, 4),
        ]

        entries = {}
        for label_text, row, col in fields:
            tk.Label(pers_frame, text=label_text, bg="#f0f0f0").grid(row=row, column=col, sticky="w", pady=6, padx=5)
            if label_text == "Sex *":
                combo = ttk.Combobox(pers_frame, values=["Male", "Female"], width=20, state="readonly")
                combo.grid(row=row, column=col+1, pady=6, padx=5)
                combo.current(0)
                entries["sex"] = combo
            elif label_text == "Civil Status":
                combo = ttk.Combobox(pers_frame, values=["Single", "Married", "Widowed"], width=20, state="readonly")
                combo.grid(row=row, column=col+1, pady=6, padx=5)
                combo.current(0)
                entries["civil_status"] = combo
            else:
                entry = ttk.Entry(pers_frame, width=25)
                entry.grid(row=row, column=col+1, pady=6, padx=5)
                key = label_text.lower().replace(" *", "").replace(" ", "_")
                entries[key] = entry

        # Contact Information
        contact_frame = tk.LabelFrame(form_frame, text="Contact Information", font=("Arial", 12, "bold"), bg="#f0f0f0")
        contact_frame.pack(fill="x", pady=10)

        contact_fields = [
            ("Contact Number *", 0, 0),
            ("Email", 0, 2),
            ("PhilHealth No.", 0, 4),
        ]
        for label_text, row, col in contact_fields:
            tk.Label(contact_frame, text=label_text, bg="#f0f0f0").grid(row=row, column=col, sticky="w", pady=6, padx=5)
            entry = ttk.Entry(contact_frame, width=25)
            entry.grid(row=row, column=col+1, pady=6, padx=5)
            key = label_text.lower().replace(" *", "").replace(" ", "_")
            entries[key] = entry

        # Address
        tk.Label(form_frame, text="Complete Address *", bg="#f0f0f0", font=("Arial", 10, "bold")).pack(anchor="w", pady=(10,0))
        address_text = tk.Text(form_frame, height=3, width=80)
        address_text.pack(pady=5, fill="x")
        address_text.insert("1.0", "House No., Street, Barangay, GMA, Cavite")
        entries["address"] = address_text

        # Emergency Contact
        emerg_frame = tk.LabelFrame(form_frame, text="Emergency Contact", font=("Arial", 12, "bold"), bg="#f0f0f0")
        emerg_frame.pack(fill="x", pady=10)

        tk.Label(emerg_frame, text="Name", bg="#f0f0f0").grid(row=0, column=0, padx=5, pady=5)
        tk.Label(emerg_frame, text="Relationship", bg="#f0f0f0").grid(row=0, column=1, padx=5, pady=5)
        tk.Label(emerg_frame, text="Contact Number", bg="#f0f0f0").grid(row=0, column=2, padx=5, pady=5)

        emerg_name = ttk.Entry(emerg_frame, width=25)
        emerg_name.grid(row=1, column=0, padx=5, pady=5)
        emerg_rel = ttk.Entry(emerg_frame, width=20)
        emerg_rel.grid(row=1, column=1, padx=5, pady=5)
        emerg_contact = ttk.Entry(emerg_frame, width=25)
        emerg_contact.grid(row=1, column=2, padx=5, pady=5)

        # Buttons
        btn_frame = tk.Frame(reg_win, bg="#f0f0f0")
        btn_frame.pack(pady=20)

        def save():
            # Validate required fields
            last_name = entries["last_name"].get().strip()
            first_name = entries["first_name"].get().strip()
            dob = entries["date_of_birth"].get().strip()
            sex = entries["sex"].get()
            contact = entries["contact_number"].get().strip()
            address = address_text.get("1.0", tk.END).strip()

            if not last_name or not first_name or not dob or not sex or not contact or not address:
                messagebox.showerror("Error", "All fields with * are required.")
                return

            # Validate date format
            try:
                datetime.strptime(dob, "%Y-%m-%d")
            except:
                messagebox.showerror("Error", "Date of Birth must be in YYYY-MM-DD format.")
                return

            # Prepare data
            patient_data = {
                'patient_id': next_id,
                'last_name': last_name,
                'first_name': first_name,
                'middle_name': entries.get("middle_name", tk.StringVar()).get().strip() or None,
                'dob': dob,
                'sex': sex,
                'civil_status': entries["civil_status"].get(),
                'contact': contact,
                'email': entries.get("email", tk.StringVar()).get().strip() or None,
                'philhealth': entries.get("philhealth_no", tk.StringVar()).get().strip() or None,
                'address': address,
                'emergency_contacts': []
            }
            if emerg_name.get().strip() and emerg_rel.get().strip():
                patient_data['emergency_contacts'].append({
                    'name': emerg_name.get().strip(),
                    'relationship': emerg_rel.get().strip(),
                    'contact': emerg_contact.get().strip() or None
                })

            # Save to database
            success = self.save_patient_to_db(patient_data)
            if success:
                messagebox.showinfo("Success", f"Patient registered successfully!\nPatient ID: {next_id}")
                reg_win.destroy()
                self.load_all_patients()   # refresh table
            else:
                messagebox.showerror("Error", "Patient ID already exists. Please try again.")

        ttk.Button(btn_frame, text="Cancel", command=reg_win.destroy).pack(side="left", padx=15)
        ttk.Button(btn_frame, text="Save Patient", command=save).pack(side="left", padx=15)

    def view_patient_details(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        patient_id = self.tree.item(selected[0])['values'][0]

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))
        patient = cursor.fetchone()
        cursor.execute("SELECT name, relationship, contact FROM emergency_contacts WHERE patient_id = ?", (patient_id,))
        emergencies = cursor.fetchall()
        conn.close()

        if not patient:
            messagebox.showerror("Error", "Patient not found")
            return

        # Patient columns: index: 0:id,1:patient_id,2:last_name,3:first_name,4:middle_name,5:dob,6:sex,7:civil_status,8:contact,9:email,10:philhealth,11:address,12:last_visit,13:status
        detail_win = tk.Toplevel(self.parent)
        detail_win.title(f"Patient Details - {patient_id}")
        detail_win.geometry("700x550")
        detail_win.grab_set()

        full_name = f"{patient[3]} {patient[2]}"
        if patient[4]:
            full_name += f" {patient[4]}"

        tk.Label(detail_win, text=f"Patient ID: {patient[1]}", font=("Arial", 14, "bold")).pack(pady=5)
        tk.Label(detail_win, text=f"Name: {full_name}", font=("Arial", 12)).pack()
        tk.Label(detail_win, text=f"Date of Birth: {patient[5] or 'N/A'} | Sex: {patient[6]} | Civil Status: {patient[7] or 'N/A'}").pack()
        tk.Label(detail_win, text=f"Contact: {patient[8]} | Email: {patient[9] or 'N/A'} | PhilHealth: {patient[10] or 'N/A'}").pack()
        tk.Label(detail_win, text=f"Address: {patient[11]}", wraplength=600).pack(pady=5)
        tk.Label(detail_win, text=f"Last Visit: {patient[12] or 'Never'} | Status: {patient[13]}").pack(pady=5)

        if emergencies:
            tk.Label(detail_win, text="Emergency Contacts:", font=("Arial", 12, "bold")).pack(pady=(10,0))
            for name, rel, cont in emergencies:
                tk.Label(detail_win, text=f"• {name} ({rel}) - {cont or 'No contact'}").pack(anchor="w", padx=20)
        else:
            tk.Label(detail_win, text="No emergency contacts registered.").pack(pady=5)

        ttk.Button(detail_win, text="Close", command=detail_win.destroy).pack(pady=20)