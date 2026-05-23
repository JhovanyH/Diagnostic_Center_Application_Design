
import sqlite3
import hashlib
import os
from datetime import datetime


class Database:
    def __init__(self):
        self.db_name = "purehealth.db"
        self.create_tables()

    def connect(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row  # Makes rows dictionary-like
        return conn

    def get_cursor(self):
        return self.connect().cursor()

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def create_tables(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                email TEXT,
                status TEXT DEFAULT 'Active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS patients (
                patient_id INTEGER PRIMARY KEY,
                phc_id TEXT UNIQUE,
                first_name TEXT,
                middle_name TEXT,
                last_name TEXT,
                date_of_birth TEXT,
                sex TEXT,
                civil_status TEXT,
                contact_number TEXT,
                email TEXT,
                address TEXT,
                philhealth_number TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS services (
                service_id INTEGER PRIMARY KEY,
                service_name TEXT NOT NULL,
                category TEXT,
                turnaround TEXT,
                price REAL NOT NULL,
                status TEXT DEFAULT 'Active'
            );
        ''')

        # Insert default data
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'receptionist01'")
        if cursor.fetchone()[0] == 0:
            hashed = self.hash_password("123456")
            cursor.execute('''INSERT INTO users (full_name, username, password_hash, role) 
                            VALUES ('Maria Reyes', 'receptionist01', ?, 'Receptionist')''', (hashed,))

            cursor.execute('''INSERT INTO users (full_name, username, password_hash, role) 
                            VALUES ('Admin', 'admin', ?, 'Administrator')''', (hashed,))

            services = [
                ("Complete Blood Count (CBC)", "Hematology", "Same day", 350.00),
                ("Urinalysis", "Urinalysis", "2 hours", 150.00),
                ("Fasting Blood Sugar", "Chemistry", "Same day", 200.00),
                ("Chest X-Ray PA", "Radiology", "1 hour", 450.00),
                ("Ultrasound — OB", "Radiology", "Same day", 800.00)
            ]
            cursor.executemany("INSERT INTO services (service_name, category, turnaround, price) VALUES (?,?,?,?)",
                               services)

        conn.commit()
        conn.close()