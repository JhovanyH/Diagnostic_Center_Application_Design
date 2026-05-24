# database.py
# ─────────────────────────────────────────────────────────────────────────────
#  PureHealth Diagnostic Center — Central Database Handler
#  Uses SQLite — works fully OFFLINE, no internet needed
#  One file (purehealthDb.db) stores everything
# ─────────────────────────────────────────────────────────────────────────────

import sqlite3
import hashlib
import os
from datetime import datetime

# ── Single source of truth for the DB filename ────────────────────────────────
DB_NAME = "purehealthDb.db"


class Database:

    def __init__(self):
        self.db_name = DB_NAME
        self.create_tables()    # always run on startup — safe, uses IF NOT EXISTS

    # ─────────────────────────────────────────────────────────────────────────
    # CONNECTION
    # ─────────────────────────────────────────────────────────────────────────

    def connect(self):
        """Open and return a connection. Always call .close() when done."""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row   # rows behave like dicts: row["name"]
        conn.execute("PRAGMA foreign_keys = ON")   # enforce FK relationships
        return conn

    # ─────────────────────────────────────────────────────────────────────────
    # TABLE CREATION  (IF NOT EXISTS = safe to run every launch)
    # ─────────────────────────────────────────────────────────────────────────

    def create_tables(self):
        conn = self.connect()
        c    = conn.cursor()

        # ── 1. Users (staff accounts) ─────────────────────────────────────────
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name     TEXT    NOT NULL,
                username      TEXT    NOT NULL UNIQUE,
                password_hash TEXT    NOT NULL,
                role          TEXT    NOT NULL,   -- Receptionist | Med Tech | Rad Tech | Doctor | Admin
                license_no    TEXT,
                email         TEXT,
                is_active     INTEGER DEFAULT 1,  -- 1=active 0=disabled
                created_at    TEXT    DEFAULT (datetime('now','localtime'))
            )
        """)

        # ── 2. Patients ───────────────────────────────────────────────────────
        c.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_code       TEXT    NOT NULL UNIQUE,  -- PHC-2025-00001
                last_name          TEXT    NOT NULL,
                first_name         TEXT    NOT NULL,
                middle_name        TEXT,
                birthdate          TEXT,
                sex                TEXT,
                civil_status       TEXT,
                contact_number     TEXT,
                email              TEXT,
                address            TEXT,
                philhealth_no      TEXT,
                emergency_name     TEXT,
                emergency_relation TEXT,
                emergency_contact  TEXT,
                created_at         TEXT DEFAULT (datetime('now','localtime'))
            )
        """)

        # ── 3. Services (test catalogue) ──────────────────────────────────────
        c.execute("""
            CREATE TABLE IF NOT EXISTS services (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                name           TEXT    NOT NULL UNIQUE,
                category       TEXT    NOT NULL,
                turnaround     TEXT,
                price          REAL    NOT NULL,
                is_active      INTEGER DEFAULT 1,
                created_at     TEXT DEFAULT (datetime('now','localtime'))
            )
        """)

        # ── 4. Appointments ───────────────────────────────────────────────────
        c.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id     INTEGER NOT NULL REFERENCES patients(id),
                appt_date      TEXT    NOT NULL,   -- YYYY-MM-DD
                appt_time      TEXT,               -- HH:MM
                appt_type      TEXT    DEFAULT 'Appointment',  -- Appointment | Walk-in
                tests_requested TEXT,              -- comma-separated service names
                remarks        TEXT,
                status         TEXT    DEFAULT 'Scheduled', -- Scheduled|Waiting|In Progress|Done|Cancelled
                created_at     TEXT DEFAULT (datetime('now','localtime'))
            )
        """)

        # ── 5. Bills ──────────────────────────────────────────────────────────
        c.execute("""
            CREATE TABLE IF NOT EXISTS bills (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id      INTEGER NOT NULL REFERENCES patients(id),
                appointment_id  INTEGER REFERENCES appointments(id),
                subtotal        REAL    NOT NULL DEFAULT 0,
                discount_type   TEXT    DEFAULT 'None',
                discount_amount REAL    DEFAULT 0,
                total           REAL    NOT NULL DEFAULT 0,
                payment_method  TEXT    DEFAULT 'Cash',  -- Cash | Online
                amount_received REAL    DEFAULT 0,
                change_amount   REAL    DEFAULT 0,
                status          TEXT    DEFAULT 'Unpaid', -- Unpaid | Paid
                created_at      TEXT DEFAULT (datetime('now','localtime')),
                paid_at         TEXT
            )
        """)

        # ── 6. Bill Items (one row per test in a bill) ────────────────────────
        c.execute("""
            CREATE TABLE IF NOT EXISTS bill_items (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                bill_id     INTEGER NOT NULL REFERENCES bills(id),
                service_id  INTEGER NOT NULL REFERENCES services(id),
                price       REAL    NOT NULL
            )
        """)

        # ── 7. Test Results ───────────────────────────────────────────────────
        c.execute("""
            CREATE TABLE IF NOT EXISTS test_results (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id     INTEGER NOT NULL REFERENCES patients(id),
                bill_id        INTEGER REFERENCES bills(id),
                service_id     INTEGER NOT NULL REFERENCES services(id),
                status         TEXT DEFAULT 'Pending', -- Pending|In Progress|Completed
                remarks        TEXT,
                reviewed_by    TEXT,   -- Med Tech name
                doctor         TEXT,   -- Doctor/Pathologist name
                signed_at      TEXT,
                result_date    TEXT DEFAULT (datetime('now','localtime')),
                updated_at     TEXT DEFAULT (datetime('now','localtime'))
            )
        """)

        # ── 8. Result Parameters (one row per test line e.g. Hemoglobin) ──────
        c.execute("""
            CREATE TABLE IF NOT EXISTS result_parameters (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                test_result_id   INTEGER NOT NULL REFERENCES test_results(id),
                parameter_name   TEXT    NOT NULL,
                value            TEXT,
                unit             TEXT,
                reference_range  TEXT,
                flag             TEXT DEFAULT 'Normal'  -- Normal|High|Low
            )
        """)

        # ── 9. Activity Log (security audit trail) ────────────────────────────
        c.execute("""
            CREATE TABLE IF NOT EXISTS activity_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER REFERENCES users(id),
                username    TEXT,
                action      TEXT    NOT NULL,
                details     TEXT,
                logged_at   TEXT DEFAULT (datetime('now','localtime'))
            )
        """)

        conn.commit()
        conn.close()

        # Seed default data if tables are empty
        self._seed_defaults()

    # ─────────────────────────────────────────────────────────────────────────
    # SEED DEFAULT DATA  (only runs once when DB is brand new)
    # ─────────────────────────────────────────────────────────────────────────

    def _seed_defaults(self):
        """Insert default admin account and sample services if not yet present."""
        conn = self.connect()
        c    = conn.cursor()

        # Default admin account
        c.execute("SELECT COUNT(*) FROM users")
        if c.fetchone()[0] == 0:
            c.execute("""
                INSERT INTO users (full_name, username, password_hash, role)
                VALUES (?, ?, ?, ?)
            """, ("Administrator", "admin",
                  self.hash_password("admin123"), "Admin"))

        # Default services
        c.execute("SELECT COUNT(*) FROM services")
        if c.fetchone()[0] == 0:
            default_services = [
                ("Complete Blood Count (CBC)", "Hematology",  "Same day", 350.00),
                ("Urinalysis",                 "Urinalysis",  "2 hours",  150.00),
                ("Fasting Blood Sugar (FBS)",  "Chemistry",   "Same day", 200.00),
                ("Blood Chemistry Panel",      "Chemistry",   "Same day", 350.00),
                ("Chest X-Ray PA",             "Radiology",   "1 hour",   450.00),
                ("Ultrasound — OB",            "Radiology",   "Same day", 800.00),
                ("Electrocardiogram (ECG)",    "Cardiology",  "30 mins",  400.00),
                ("Blood Typing",               "Hematology",  "Same day", 180.00),
                ("Lipid Profile",              "Chemistry",   "Same day", 450.00),
                ("Thyroid Function (TSH)",     "Chemistry",   "1-2 days", 650.00),
            ]
            c.executemany("""
                INSERT INTO services (name, category, turnaround, price)
                VALUES (?, ?, ?, ?)
            """, default_services)

        conn.commit()
        conn.close()

    # ─────────────────────────────────────────────────────────────────────────
    # UTILITY
    # ─────────────────────────────────────────────────────────────────────────

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def log_action(self, username, action, details=""):
        """Call this whenever something important happens (save, delete, login)."""
        conn = self.connect()
        conn.execute("""
            INSERT INTO activity_log (username, action, details)
            VALUES (?, ?, ?)
        """, (username, action, details))
        conn.commit()
        conn.close()

    def generate_patient_code(self):
        """Auto-generate next patient ID: PHC-2025-00001"""
        conn = self.connect()
        c    = conn.cursor()
        c.execute("SELECT COUNT(*) FROM patients")
        count = c.fetchone()[0]
        conn.close()
        year = datetime.now().year
        return f"PHC-{year}-{str(count + 1).zfill(5)}"

    # ─────────────────────────────────────────────────────────────────────────
    # PATIENTS
    # ─────────────────────────────────────────────────────────────────────────

    def add_patient(self, data: dict):
        """
        data keys: last_name, first_name, middle_name, birthdate, sex,
                   civil_status, contact_number, email, address,
                   philhealth_no, emergency_name, emergency_relation,
                   emergency_contact
        Returns the new patient_code string.
        """
        code = self.generate_patient_code()
        conn = self.connect()
        conn.execute("""
            INSERT INTO patients (
                patient_code, last_name, first_name, middle_name,
                birthdate, sex, civil_status, contact_number, email,
                address, philhealth_no, emergency_name,
                emergency_relation, emergency_contact
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            code,
            data.get("last_name", ""),
            data.get("first_name", ""),
            data.get("middle_name", ""),
            data.get("birthdate", ""),
            data.get("sex", ""),
            data.get("civil_status", ""),
            data.get("contact_number", ""),
            data.get("email", ""),
            data.get("address", ""),
            data.get("philhealth_no", ""),
            data.get("emergency_name", ""),
            data.get("emergency_relation", ""),
            data.get("emergency_contact", ""),
        ))
        conn.commit()
        conn.close()
        return code

    def get_all_patients(self):
        """Return all patients ordered by newest first."""
        conn  = self.connect()
        rows  = conn.execute(
            "SELECT * FROM patients ORDER BY created_at DESC"
        ).fetchall()
        conn.close()
        return rows

    def search_patients(self, query: str):
        """Search by name or patient code."""
        q    = f"%{query}%"
        conn = self.connect()
        rows = conn.execute("""
            SELECT * FROM patients
            WHERE last_name   LIKE ? OR first_name   LIKE ?
               OR patient_code LIKE ?
            ORDER BY last_name
        """, (q, q, q)).fetchall()
        conn.close()
        return rows

    def get_patient_by_id(self, patient_id: int):
        conn = self.connect()
        row  = conn.execute(
            "SELECT * FROM patients WHERE id = ?", (patient_id,)
        ).fetchone()
        conn.close()
        return row

    def get_patient_unpaid_total(self, patient_id: int):
        """Return total unpaid balance for a patient."""
        conn  = self.connect()
        row   = conn.execute("""
            SELECT COALESCE(SUM(total), 0) as total
            FROM bills
            WHERE patient_id = ? AND status = 'Unpaid'
        """, (patient_id,)).fetchone()
        conn.close()
        return row["total"] if row else 0.0

    # ─────────────────────────────────────────────────────────────────────────
    # SERVICES
    # ─────────────────────────────────────────────────────────────────────────

    def get_all_services(self, active_only=True):
        conn  = self.connect()
        query = "SELECT * FROM services"
        if active_only:
            query += " WHERE is_active = 1"
        query += " ORDER BY category, name"
        rows  = conn.execute(query).fetchall()
        conn.close()
        return rows

    def add_service(self, name, category, turnaround, price):
        conn = self.connect()
        conn.execute("""
            INSERT INTO services (name, category, turnaround, price)
            VALUES (?, ?, ?, ?)
        """, (name, category, turnaround, price))
        conn.commit()
        conn.close()

    def update_service_price(self, service_id, new_price):
        conn = self.connect()
        conn.execute(
            "UPDATE services SET price = ? WHERE id = ?",
            (new_price, service_id))
        conn.commit()
        conn.close()

    # ─────────────────────────────────────────────────────────────────────────
    # APPOINTMENTS
    # ─────────────────────────────────────────────────────────────────────────

    def add_appointment(self, data: dict):
        conn = self.connect()
        c    = conn.cursor()
        c.execute("""
            INSERT INTO appointments
                (patient_id, appt_date, appt_time, appt_type,
                 tests_requested, remarks, status)
            VALUES (?,?,?,?,?,?,?)
        """, (
            data["patient_id"],
            data.get("appt_date", ""),
            data.get("appt_time", ""),
            data.get("appt_type", "Appointment"),
            data.get("tests_requested", ""),
            data.get("remarks", ""),
            data.get("status", "Scheduled"),
        ))
        conn.commit()
        appt_id = c.lastrowid
        conn.close()
        return appt_id

    def get_appointments_by_date(self, date_str: str):
        """Get all appointments for a specific date (YYYY-MM-DD)."""
        conn = self.connect()
        rows = conn.execute("""
            SELECT a.*, p.first_name || ' ' || p.last_name AS patient_name,
                   p.patient_code
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            WHERE a.appt_date = ?
            ORDER BY a.appt_time
        """, (date_str,)).fetchall()
        conn.close()
        return rows

    def update_appointment_status(self, appt_id, status):
        conn = self.connect()
        conn.execute(
            "UPDATE appointments SET status = ? WHERE id = ?",
            (status, appt_id))
        conn.commit()
        conn.close()

    # ─────────────────────────────────────────────────────────────────────────
    # BILLING
    # ─────────────────────────────────────────────────────────────────────────

    def create_bill(self, patient_id, service_ids: list,
                    discount_type="None", discount_amount=0.0,
                    payment_method="Cash", amount_received=0.0,
                    status="Paid", appointment_id=None):
        """
        Create a bill + its line items in one transaction.
        Returns the new bill ID.
        """
        conn = self.connect()
        c    = conn.cursor()

        # Calculate subtotal from service prices
        placeholders = ",".join("?" * len(service_ids))
        rows = conn.execute(
            f"SELECT id, price FROM services WHERE id IN ({placeholders})",
            service_ids
        ).fetchall()
        subtotal = sum(r["price"] for r in rows)
        total    = max(0.0, subtotal - discount_amount)
        change   = max(0.0, amount_received - total)
        paid_at  = datetime.now().strftime("%Y-%m-%d %H:%M:%S") \
                   if status == "Paid" else None

        c.execute("""
            INSERT INTO bills
                (patient_id, appointment_id, subtotal, discount_type,
                 discount_amount, total, payment_method,
                 amount_received, change_amount, status, paid_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (patient_id, appointment_id, subtotal, discount_type,
              discount_amount, total, payment_method,
              amount_received, change, status, paid_at))

        bill_id = c.lastrowid

        # Insert one row per service
        for row in rows:
            c.execute("""
                INSERT INTO bill_items (bill_id, service_id, price)
                VALUES (?,?,?)
            """, (bill_id, row["id"], row["price"]))

        conn.commit()
        conn.close()
        return bill_id

    def get_unpaid_bills(self):
        conn = self.connect()
        rows = conn.execute("""
            SELECT b.*,
                   p.first_name || ' ' || p.last_name AS patient_name,
                   p.patient_code
            FROM bills b
            JOIN patients p ON b.patient_id = p.id
            WHERE b.status = 'Unpaid'
            ORDER BY b.created_at DESC
        """).fetchall()
        conn.close()
        return rows

    def mark_bill_paid(self, bill_id, payment_method,
                       amount_received, change_amount):
        conn = self.connect()
        conn.execute("""
            UPDATE bills SET status='Paid', payment_method=?,
                             amount_received=?, change_amount=?,
                             paid_at=datetime('now','localtime')
            WHERE id=?
        """, (payment_method, amount_received, change_amount, bill_id))
        conn.commit()
        conn.close()

    def get_bills_by_date(self, date_str: str):
        """For daily report — all bills on a given date."""
        conn = self.connect()
        rows = conn.execute("""
            SELECT b.*,
                   p.first_name || ' ' || p.last_name AS patient_name,
                   p.patient_code
            FROM bills b
            JOIN patients p ON b.patient_id = p.id
            WHERE DATE(b.created_at) = ?
            ORDER BY b.created_at
        """, (date_str,)).fetchall()
        conn.close()
        return rows

    # ─────────────────────────────────────────────────────────────────────────
    # TEST RESULTS
    # ─────────────────────────────────────────────────────────────────────────

    def create_test_result(self, patient_id, service_id,
                           bill_id=None, status="Pending"):
        conn = self.connect()
        c    = conn.cursor()
        c.execute("""
            INSERT INTO test_results
                (patient_id, service_id, bill_id, status)
            VALUES (?,?,?,?)
        """, (patient_id, service_id, bill_id, status))
        conn.commit()
        result_id = c.lastrowid
        conn.close()
        return result_id

    def save_result_parameters(self, test_result_id, parameters: list):
        """
        parameters = list of dicts with keys:
            parameter_name, value, unit, reference_range, flag
        """
        conn = self.connect()
        # Remove old parameters first (allows editing)
        conn.execute(
            "DELETE FROM result_parameters WHERE test_result_id = ?",
            (test_result_id,))
        for p in parameters:
            conn.execute("""
                INSERT INTO result_parameters
                    (test_result_id, parameter_name, value,
                     unit, reference_range, flag)
                VALUES (?,?,?,?,?,?)
            """, (test_result_id,
                  p.get("parameter_name", ""),
                  p.get("value", ""),
                  p.get("unit", ""),
                  p.get("reference_range", ""),
                  p.get("flag", "Normal")))
        conn.commit()
        conn.close()

    def finalize_result(self, test_result_id, reviewed_by,
                        doctor, remarks=""):
        """Mark a result as Completed and record signatures."""
        conn = self.connect()
        conn.execute("""
            UPDATE test_results
            SET status='Completed', reviewed_by=?, doctor=?,
                remarks=?, signed_at=datetime('now','localtime'),
                updated_at=datetime('now','localtime')
            WHERE id=?
        """, (reviewed_by, doctor, remarks, test_result_id))
        conn.commit()
        conn.close()

    def get_results_by_patient(self, patient_id):
        conn = self.connect()
        rows = conn.execute("""
            SELECT tr.*, s.name AS test_name, s.category
            FROM test_results tr
            JOIN services s ON tr.service_id = s.id
            WHERE tr.patient_id = ?
            ORDER BY tr.result_date DESC
        """, (patient_id,)).fetchall()
        conn.close()
        return rows

    def get_result_parameters(self, test_result_id):
        conn  = self.connect()
        rows  = conn.execute("""
            SELECT * FROM result_parameters
            WHERE test_result_id = ?
        """, (test_result_id,)).fetchall()
        conn.close()
        return rows

    def get_all_results(self):
        conn = self.connect()
        rows = conn.execute("""
            SELECT tr.*,
                   p.first_name || ' ' || p.last_name AS patient_name,
                   p.patient_code,
                   s.name AS test_name, s.category
            FROM test_results tr
            JOIN patients  p ON tr.patient_id  = p.id
            JOIN services  s ON tr.service_id  = s.id
            ORDER BY tr.result_date DESC
        """).fetchall()
        conn.close()
        return rows

    # ─────────────────────────────────────────────────────────────────────────
    # REPORTS
    # ─────────────────────────────────────────────────────────────────────────

    def get_daily_patient_report(self, date_str: str):
        """All patients who had a bill on a given date."""
        conn = self.connect()
        rows = conn.execute("""
            SELECT b.id AS bill_id,
                   p.first_name || ' ' || p.last_name AS patient_name,
                   p.patient_code,
                   b.total, b.status, b.payment_method,
                   b.created_at,
                   GROUP_CONCAT(s.name, ', ') AS tests
            FROM bills b
            JOIN patients  p ON b.patient_id  = p.id
            JOIN bill_items bi ON bi.bill_id   = b.id
            JOIN services   s ON bi.service_id = s.id
            WHERE DATE(b.created_at) = ?
            GROUP BY b.id
            ORDER BY b.created_at
        """, (date_str,)).fetchall()
        conn.close()
        return rows

    def get_monthly_summary(self, year: int, month: int):
        conn = self.connect()
        row  = conn.execute("""
            SELECT
                COUNT(DISTINCT patient_id)    AS total_patients,
                COUNT(*)                      AS total_bills,
                COALESCE(SUM(total),0)        AS gross_revenue,
                COALESCE(SUM(CASE WHEN status='Paid'   THEN total ELSE 0 END),0) AS collected,
                COALESCE(SUM(CASE WHEN status='Unpaid' THEN total ELSE 0 END),0) AS uncollected,
                COALESCE(SUM(discount_amount),0) AS total_discounts
            FROM bills
            WHERE strftime('%Y', created_at) = ?
              AND strftime('%m', created_at) = ?
        """, (str(year), str(month).zfill(2))).fetchone()
        conn.close()
        return row

    def get_test_statistics(self, year: int, month: int):
        conn = self.connect()
        rows = conn.execute("""
            SELECT s.name, s.category, COUNT(*) AS count
            FROM bill_items bi
            JOIN services  s  ON bi.service_id = s.id
            JOIN bills     b  ON bi.bill_id     = b.id
            WHERE strftime('%Y', b.created_at) = ?
              AND strftime('%m', b.created_at) = ?
            GROUP BY s.id
            ORDER BY count DESC
        """, (str(year), str(month).zfill(2))).fetchall()
        conn.close()
        return rows

    # ─────────────────────────────────────────────────────────────────────────
    # USER ACCOUNTS
    # ─────────────────────────────────────────────────────────────────────────

    def login(self, username, password):
        """Return user row if credentials match, else None."""
        conn = self.connect()
        row  = conn.execute("""
            SELECT * FROM users
            WHERE username = ? AND password_hash = ? AND is_active = 1
        """, (username, self.hash_password(password))).fetchone()
        conn.close()
        return row

    def add_user(self, full_name, username, password, role,
                 license_no="", email=""):
        conn = self.connect()
        try:
            conn.execute("""
                INSERT INTO users
                    (full_name, username, password_hash, role,
                     license_no, email)
                VALUES (?,?,?,?,?,?)
            """, (full_name, username,
                  self.hash_password(password),
                  role, license_no, email))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False   # username already taken
        finally:
            conn.close()

    def get_all_users(self):
        conn = self.connect()
        rows = conn.execute(
            "SELECT id, full_name, username, role, license_no, "
            "email, is_active, created_at FROM users ORDER BY full_name"
        ).fetchall()
        conn.close()
        return rows

    def change_password(self, user_id, new_password):
        conn = self.connect()
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (self.hash_password(new_password), user_id))
        conn.commit()
        conn.close()

    def get_appointment_counts_for_month(self, year, month):
        """Returns {date_str: count} for calendar dots."""
        conn = self.connect()
        rows = conn.execute("""
            SELECT appt_date, COUNT(*) as count
            FROM appointments
            WHERE strftime('%Y', appt_date) = ?
              AND strftime('%m', appt_date) = ?
            GROUP BY appt_date
        """, (str(year), str(month).zfill(2))).fetchall()
        conn.close()
        return {row["appt_date"]: row["count"] for row in rows}

    def delete_appointment(self, appt_id):
        """Permanently delete an appointment by ID."""
        conn = self.connect()
        conn.execute(
            "DELETE FROM appointments WHERE id = ?",
            (appt_id,))
        conn.commit()
        conn.close()

    # ── REPORTS & ANALYTICS ──────────────────────────────────────────────────

    def get_appointments_by_date_range(self, start_date, end_date):
        """Fetch appointments within a specific date range."""
        conn = self.connect()
        rows = conn.execute("""
            SELECT a.*, p.first_name || ' ' || p.last_name AS patient_name,
                   p.patient_code
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            WHERE a.appt_date >= ? AND a.appt_date <= ?
            ORDER BY a.appt_date DESC, a.appt_time ASC
        """, (start_date, end_date)).fetchall()
        conn.close()
        return rows

    def get_financial_summary(self, start_date, end_date):
        """Aggregate revenue, collections, and discounts for a time period."""
        conn = self.connect()
        row = conn.execute("""
            SELECT 
                COUNT(*) as total_bills,
                COALESCE(SUM(total), 0) as gross_revenue,
                COALESCE(SUM(CASE WHEN status='Paid' THEN total ELSE 0 END), 0) as collected,
                COALESCE(SUM(CASE WHEN status='Unpaid' THEN total ELSE 0 END), 0) as uncollected,
                COALESCE(SUM(discount_amount), 0) as discounts
            FROM bills
            WHERE DATE(created_at) >= ? AND DATE(created_at) <= ?
        """, (start_date, end_date)).fetchone()
        conn.close()
        return dict(row) if row else None

    def get_revenue_by_category(self, start_date, end_date):
        """Group revenue by diagnostic department."""
        conn = self.connect()
        rows = conn.execute("""
            SELECT s.category, SUM(bi.price) as revenue
            FROM bill_items bi
            JOIN services s ON bi.service_id = s.id
            JOIN bills b ON bi.bill_id = b.id
            WHERE DATE(b.created_at) >= ? AND DATE(b.created_at) <= ?
            GROUP BY s.category
            ORDER BY revenue DESC
        """, (start_date, end_date)).fetchall()
        conn.close()
        return rows

    def get_test_statistics_by_date_range(self, start_date, end_date):
        """Count the most popular tests performed."""
        conn = self.connect()
        rows = conn.execute("""
            SELECT s.name, s.category, COUNT(*) AS count
            FROM bill_items bi
            JOIN services  s  ON bi.service_id = s.id
            JOIN bills     b  ON bi.bill_id     = b.id
            WHERE DATE(b.created_at) >= ? AND DATE(b.created_at) <= ?
            GROUP BY s.id
            ORDER BY count DESC
        """, (start_date, end_date)).fetchall()
        conn.close()
        return rows


# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL INSTANCE  — import this everywhere instead of creating new Database()
# ─────────────────────────────────────────────────────────────────────────────
db = Database()