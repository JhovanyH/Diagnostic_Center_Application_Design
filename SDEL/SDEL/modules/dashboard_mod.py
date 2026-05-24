# modules/dashboard_mod.py
# ─────────────────────────────────────────────────────────────────────────────
#  PureHealth Diagnostic Center — Dashboard Module
#  CONNECTED TO DATABASE — Live stats, schedules, and queues
# ─────────────────────────────────────────────────────────────────────────────

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from datetime import datetime
from database import db

# ── Colour palette ────────────────────────────────────────────────────────────
TEAL_DARK = "#073b4c"
TEAL_MID = "#0c637f"
TEAL_ACCENT = "#0cb0a9"
WHITE = "#ffffff"
BG_LIGHT = "#f4f6f8"
BORDER = "#e2e8f0"
TEXT_MAIN = "#1a202c"
TEXT_MUTED = "#718096"
TEXT_HINT = "#a0aec0"

STATUS_DONE = ("#d1fae5", "#065f46")
STATUS_PROG = ("#dbeafe", "#1e40af")
STATUS_WAIT = ("#fef9c3", "#854d0e")
STATUS_SCHED = ("#f3f4f6", "#374151")
STATUS_UNPAID = ("#fee2e2", "#991b1b")


class DashboardModule:
    def __init__(self, parent):
        self.parent = parent

        # Live data lists
        self._schedule = []
        self._walkin = []
        self._unpaid = []

        # Stat card label references
        self._stat_labels = {}
        self._stat_sub_labels = {}

        # Frame references
        self._schedule_frame = None
        self._walkin_frame = None
        self._walkin_badge = None
        self._unpaid_frame = None
        self._unpaid_badge = None

        # Auto-refresh job id
        self._refresh_job = None

    # ── Entry point ───────────────────────────────────────────────────────────
    def show(self):
        if self._refresh_job is not None:
            try:
                self.parent.after_cancel(self._refresh_job)
            except Exception:
                pass
            self._refresh_job = None

        for w in self.parent.winfo_children():
            w.destroy()
        self.parent.configure(bg=BG_LIGHT)
        self._build_ui()
        self.refresh_stats()

    # ── DB refresh ────────────────────────────────────────────────────────────
    def refresh_stats(self):
        """Pull live counts from purehealthDb.db and update stat cards."""
        today_str = datetime.now().strftime("%Y-%m-%d")

        try:
            conn = db.connect()

            # 1. Today's New Patients
            row = conn.execute("SELECT COUNT(*) as count FROM patients WHERE DATE(created_at) = ?",
                               (today_str,)).fetchone()
            new_patients = row["count"] if row else 0
            self._set_stat("patients", str(new_patients), "new registrations today")

            # 2. Today's Appointments
            appts = db.get_appointments_by_date(today_str)
            appt_count = sum(1 for a in appts if a["appt_type"] == "By Appointment")
            walkin_count = sum(1 for a in appts if a["appt_type"] == "Walk-in")
            self._set_stat("appts", str(appt_count), f"+ {walkin_count} walk-ins")

            # 3. Pending Results
            row = conn.execute("SELECT COUNT(*) as count FROM test_results WHERE status = 'Pending'").fetchone()
            pending_count = row["count"] if row else 0
            self._set_stat("pending", str(pending_count), "awaiting med-tech")

            # 4. Today's Collections
            fin = db.get_financial_summary(today_str, today_str)
            collections = fin["collected"] if fin else 0.0
            bills_count = fin["total_bills"] if fin else 0
            self._set_stat("collections", f"₱{collections:,.2f}", f"from {bills_count} transactions")

            conn.close()

            # Update lists
            self._schedule = [a for a in appts if a["appt_type"] == "By Appointment"]
            self._walkin = [a for a in appts if a["appt_type"] == "Walk-in"]
            self._unpaid = db.get_unpaid_bills()[:5]  # Get top 5 unpaid for dashboard

            # Re-render frames safely if they exist
            if self._schedule_frame: self._render_schedule()
            if self._walkin_frame: self._render_walkin()
            if self._unpaid_frame: self._render_unpaid()

        except Exception as e:
            print(f"Dashboard DB error: {e}")

        # Auto-refresh every 10 seconds
        try:
            self._refresh_job = self.parent.after(10000, self.refresh_stats)
        except Exception:
            pass

    def _set_stat(self, key, value, subtitle):
        if key in self._stat_labels:
            try:
                self._stat_labels[key].configure(text=value)
            except Exception:
                pass
        if key in self._stat_sub_labels:
            try:
                self._stat_sub_labels[key].configure(text=subtitle)
            except Exception:
                pass

    # ── UI construction ───────────────────────────────────────────────────────
    def _build_ui(self):
        now = datetime.now()
        hour = now.hour
        greeting = ("Good Morning" if hour < 12
                    else "Good Afternoon" if hour < 17
        else "Good Evening")
        date_str = now.strftime("%A, %B %d, %Y")

        top_bar = tk.Frame(self.parent, bg=WHITE)
        top_bar.pack(fill="x")
        tk.Frame(top_bar, bg=BORDER, height=1).pack(fill="x", side="bottom")

        greet_block = tk.Frame(top_bar, bg=WHITE)
        greet_block.pack(side="left", padx=20, pady=14)
        tk.Label(greet_block,
                 text=f"{greeting}, Receptionist!",
                 font=("Segoe UI", 16, "bold"),
                 bg=WHITE, fg=TEXT_MAIN).pack(anchor="w")
        tk.Label(greet_block, text=date_str,
                 font=("Segoe UI", 10),
                 bg=WHITE, fg=TEXT_MUTED).pack(anchor="w")

        cards_row = tk.Frame(self.parent, bg=BG_LIGHT)
        cards_row.pack(fill="x", padx=18, pady=(14, 0))

        stat_defs = [
            ("patients", "NEW PATIENTS", "0", "loading...", TEXT_MAIN),
            ("appts", "TODAY'S SCHEDULE", "0", "loading...", TEXT_MAIN),
            ("pending", "PENDING RESULTS", "0", "loading...", "#c53030"),
            ("collections", "TODAY'S COLLECTIONS", "₱0.00", "loading...", TEAL_DARK),
        ]

        for key, title, value, sub, val_color in stat_defs:
            card = tk.Frame(cards_row, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
            card.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=4)
            card.pack_propagate(False)
            card.configure(height=100)

            inner = tk.Frame(card, bg=WHITE)
            inner.pack(fill="both", expand=True, padx=16, pady=12)

            tk.Label(inner, text=title, font=("Segoe UI", 8, "bold"), bg=WHITE, fg=TEXT_MUTED).pack(anchor="w")
            val_lbl = tk.Label(inner, text=value, font=("Segoe UI", 22, "bold"), bg=WHITE, fg=val_color)
            val_lbl.pack(anchor="w")
            self._stat_labels[key] = val_lbl

            sub_lbl = tk.Label(inner, text=sub, font=("Segoe UI", 9), bg=WHITE, fg=TEXT_MUTED)
            sub_lbl.pack(anchor="w")
            self._stat_sub_labels[key] = sub_lbl

        content = tk.Frame(self.parent, bg=BG_LIGHT)
        content.pack(fill="both", expand=True, padx=18, pady=12)
        content.columnconfigure(0, weight=3)
        content.columnconfigure(1, weight=2)
        content.rowconfigure(0, weight=1)

        left = tk.Frame(content, bg=BG_LIGHT)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        right = tk.Frame(content, bg=BG_LIGHT)
        right.grid(row=0, column=1, sticky="nsew")

        self._build_schedule(left)
        self._build_walkin(right)
        self._build_unpaid(right)

    # ── Today's Schedule ──────────────────────────────────────────────────────
    def _build_schedule(self, parent):
        card = tk.Frame(parent, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="both", expand=True)

        hdr = tk.Frame(card, bg=WHITE)
        hdr.pack(fill="x", padx=14, pady=(12, 0))
        tk.Label(hdr, text="Today's Appointments", font=("Segoe UI", 11, "bold"), bg=WHITE, fg=TEXT_MAIN).pack(
            side="left")

        tk.Frame(card, bg=BORDER, height=1).pack(fill="x", pady=(10, 0))

        self._schedule_frame = tk.Frame(card, bg=WHITE)
        self._schedule_frame.pack(fill="both", expand=True, pady=(0, 10))

    def _render_schedule(self):
        for w in self._schedule_frame.winfo_children():
            w.destroy()

        if not self._schedule:
            tk.Label(self._schedule_frame, text="No appointments scheduled for today.", font=("Segoe UI", 10), bg=WHITE,
                     fg=TEXT_HINT, pady=20).pack()
            return

        STATUS_CFG = {
            "Done": STATUS_DONE,
            "Completed": STATUS_DONE,
            "In Progress": STATUS_PROG,
            "Waiting": STATUS_WAIT,
            "Scheduled": STATUS_SCHED,
        }

        for i, item in enumerate(self._schedule):
            row_bg = WHITE if i % 2 == 0 else "#f8fafc"
            row = tk.Frame(self._schedule_frame, bg=row_bg)
            row.pack(fill="x")
            tk.Frame(self._schedule_frame, bg=BORDER, height=1).pack(fill="x")

            # Convert 24h DB time to 12h display
            display_time = item["appt_time"]
            try:
                display_time = datetime.strptime(item["appt_time"], "%H:%M").strftime("%I:%M %p")
            except:
                pass

            tk.Label(row, text=display_time, font=("Segoe UI", 9), bg=row_bg, fg=TEXT_MUTED, width=9, anchor="w",
                     pady=10, padx=14).pack(side="left")

            info = tk.Frame(row, bg=row_bg)
            info.pack(side="left", fill="x", expand=True, pady=6)
            tk.Label(info, text=item["patient_name"], font=("Segoe UI", 10, "bold"), bg=row_bg, fg=TEXT_MAIN,
                     anchor="w").pack(anchor="w")
            tk.Label(info, text=item["tests_requested"], font=("Segoe UI", 9), bg=row_bg, fg=TEXT_MUTED,
                     anchor="w").pack(anchor="w")

            st_cfg = STATUS_CFG.get(item["status"], STATUS_SCHED)
            badge = tk.Label(row, text=item["status"], font=("Segoe UI", 9, "bold"), bg=st_cfg[0], fg=st_cfg[1],
                             padx=10, pady=3, cursor="hand2")
            badge.pack(side="right", padx=14)

            # Cycle status directly from Dashboard
            def _make_cycler(appt_id, cur_status, badge_ref):
                def _cycle(e=None):
                    opts = ["Scheduled", "Waiting", "In Progress", "Done"]
                    nxt = opts[(opts.index(cur_status) + 1) % len(opts)] if cur_status in opts else "Waiting"

                    # Update DB
                    conn = db.connect()
                    conn.execute("UPDATE appointments SET status = ? WHERE id = ?", (nxt, appt_id))
                    conn.commit()
                    conn.close()

                    cfg = STATUS_CFG.get(nxt, STATUS_SCHED)
                    badge_ref.configure(text=nxt, bg=cfg[0], fg=cfg[1])

                    # Force full refresh to sync walkins if needed
                    self.refresh_stats()

                return _cycle

            badge.bind("<Button-1>", _make_cycler(item["id"], item["status"], badge))

    # ── Walk-in Queue ─────────────────────────────────────────────────────────
    def _build_walkin(self, parent):
        card = tk.Frame(parent, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="x", pady=(0, 10))

        hdr = tk.Frame(card, bg=WHITE)
        hdr.pack(fill="x", padx=14, pady=(12, 0))
        tk.Label(hdr, text="Walk-in Queue", font=("Segoe UI", 11, "bold"), bg=WHITE, fg=TEXT_MAIN).pack(side="left")

        self._walkin_badge = tk.Label(hdr, text="0 waiting", font=("Segoe UI", 9, "bold"), bg=STATUS_PROG[0],
                                      fg=STATUS_PROG[1], padx=8, pady=3)
        self._walkin_badge.pack(side="right")

        tk.Frame(card, bg=BORDER, height=1).pack(fill="x", pady=(10, 0))

        add_row = tk.Frame(card, bg=WHITE)
        add_row.pack(fill="x", padx=14, pady=(8, 4))
        tk.Button(add_row, text="+ Quick Add Walk-in", command=self._add_walkin, font=("Segoe UI", 9, "bold"),
                  bg=TEAL_DARK, fg=WHITE, activebackground=TEAL_MID, relief="flat", cursor="hand2", padx=10,
                  pady=4).pack(side="right")

        self._walkin_frame = tk.Frame(card, bg=WHITE)
        self._walkin_frame.pack(fill="x", pady=(0, 10))

    def _render_walkin(self):
        for w in self._walkin_frame.winfo_children():
            w.destroy()

        waiting = sum(1 for w in self._walkin if w["status"] in ("Waiting", "In Progress", "Scheduled"))
        if self._walkin_badge:
            self._walkin_badge.configure(text=f"{waiting} active")

        if not self._walkin:
            tk.Label(self._walkin_frame, text="No active walk-ins.", font=("Segoe UI", 10), bg=WHITE, fg=TEXT_HINT,
                     pady=14).pack()
            return

        for i, item in enumerate(self._walkin):
            row = tk.Frame(self._walkin_frame, bg="#f8fafc", highlightbackground=BORDER, highlightthickness=1)
            row.pack(fill="x", padx=14, pady=3)

            tk.Label(row, text=f"#{i + 1}", font=("Segoe UI", 11, "bold"), bg="#f8fafc", fg=TEAL_DARK, padx=12,
                     pady=8).pack(side="left")

            info = tk.Frame(row, bg="#f8fafc")
            info.pack(side="left", fill="x", expand=True, pady=6)
            tk.Label(info, text=item["patient_name"], font=("Segoe UI", 10, "bold"), bg="#f8fafc", fg=TEXT_MAIN,
                     anchor="w").pack(anchor="w")
            tk.Label(info, text=f"{item['tests_requested']}", font=("Segoe UI", 9), bg="#f8fafc", fg=TEXT_MUTED,
                     anchor="w").pack(anchor="w")

            st_cfg = {
                "Waiting": STATUS_WAIT,
                "In Progress": STATUS_PROG,
                "Done": STATUS_DONE,
                "Completed": STATUS_DONE,
            }.get(item["status"], STATUS_SCHED)
            tk.Label(row, text=item["status"], font=("Segoe UI", 9, "bold"), bg=st_cfg[0], fg=st_cfg[1], padx=8,
                     pady=3).pack(side="right", padx=12)

    def _add_walkin(self):
        """Opens a quick DB-linked search to add a walk-in to the queue"""
        win = tk.Toplevel(self.parent)
        win.title("Quick Walk-in")
        win.geometry("420x300")
        win.resizable(False, False)
        win.grab_set()
        win.configure(bg=BG_LIGHT)

        top = tk.Frame(win, bg=TEAL_DARK)
        top.pack(fill="x")
        tk.Label(top, text="Quick Add Walk-in", font=("Segoe UI", 12, "bold"), bg=TEAL_DARK, fg=WHITE, pady=11,
                 padx=16).pack(side="left")

        body = tk.Frame(win, bg=BG_LIGHT)
        body.pack(fill="both", expand=True, padx=18, pady=14)

        tk.Label(body, text="Search Patient by Name/ID *", font=("Segoe UI", 9), bg=BG_LIGHT, fg=TEXT_MUTED).pack(
            anchor="w")
        search_ent = ctk.CTkEntry(body, placeholder_text="e.g. Juan dela Cruz", font=("Segoe UI", 10), height=34,
                                  corner_radius=6, border_color=BORDER, fg_color=WHITE, text_color=TEXT_MAIN)
        search_ent.pack(fill="x", pady=(0, 8))

        tk.Label(body, text="Tests Required *", font=("Segoe UI", 9), bg=BG_LIGHT, fg=TEXT_MUTED).pack(anchor="w")
        proc_ent = ctk.CTkEntry(body, placeholder_text="e.g. CBC, Urinalysis", font=("Segoe UI", 10), height=34,
                                corner_radius=6, border_color=BORDER, fg_color=WHITE, text_color=TEXT_MAIN)
        proc_ent.pack(fill="x", pady=(0, 16))

        def _save():
            query = search_ent.get().strip()
            proc = proc_ent.get().strip()
            if not query or not proc:
                messagebox.showerror("Required", "Please fill in all fields.", parent=win)
                return

            # Require database link
            results = db.search_patients(query)
            if not results:
                messagebox.showerror("Not Found",
                                     f"No patient found for '{query}'. Please register them in Patients module first.",
                                     parent=win)
                return

            patient_id = results[0]["id"]
            today_str = datetime.now().strftime("%Y-%m-%d")
            time_str = datetime.now().strftime("%H:%M")

            db.add_appointment({
                "patient_id": patient_id,
                "appt_date": today_str,
                "appt_time": time_str,
                "appt_type": "Walk-in",
                "tests_requested": proc,
                "remarks": "Quick dashboard walk-in",
                "status": "Waiting"
            })

            self.refresh_stats()
            win.destroy()

        btn_row = tk.Frame(body, bg=BG_LIGHT)
        btn_row.pack(fill="x", pady=(4, 0))
        tk.Button(btn_row, text="Cancel", command=win.destroy, font=("Segoe UI", 10), bg=WHITE, fg=TEXT_MUTED,
                  relief="flat", cursor="hand2", padx=12, pady=6, highlightbackground=BORDER,
                  highlightthickness=1).pack(side="right", padx=(8, 0))
        tk.Button(btn_row, text="Add to Queue", command=_save, font=("Segoe UI", 10, "bold"), bg=TEAL_DARK, fg=WHITE,
                  activebackground=TEAL_MID, relief="flat", cursor="hand2", padx=12, pady=6).pack(side="right")

    # ── Unpaid Balances ───────────────────────────────────────────────────────
    def _build_unpaid(self, parent):
        card = tk.Frame(parent, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="x")

        hdr = tk.Frame(card, bg=WHITE)
        hdr.pack(fill="x", padx=14, pady=(12, 0))
        tk.Label(hdr, text="Recent Unpaid Bills", font=("Segoe UI", 11, "bold"), bg=WHITE, fg=TEXT_MAIN).pack(
            side="left")

        tk.Frame(card, bg=BORDER, height=1).pack(fill="x", pady=(10, 0))

        self._unpaid_frame = tk.Frame(card, bg=WHITE)
        self._unpaid_frame.pack(fill="x", pady=(0, 10))

    def _render_unpaid(self):
        for w in self._unpaid_frame.winfo_children():
            w.destroy()

        if not self._unpaid:
            tk.Label(self._unpaid_frame, text="No recent unpaid balances.", font=("Segoe UI", 10), bg=WHITE,
                     fg=TEXT_HINT, pady=14).pack()
            return

        for item in self._unpaid:
            row = tk.Frame(self._unpaid_frame, bg=WHITE)
            row.pack(fill="x", padx=14, pady=2)
            tk.Frame(self._unpaid_frame, bg=BORDER, height=1).pack(fill="x", padx=14)

            info = tk.Frame(row, bg=WHITE)
            info.pack(side="left", fill="x", expand=True, pady=7)
            tk.Label(info, text=item["patient_name"], font=("Segoe UI", 10, "bold"), bg=WHITE, fg=TEXT_MAIN,
                     anchor="w").pack(anchor="w")
            tk.Label(info, text=item["patient_code"], font=("Segoe UI", 9), bg=WHITE, fg=TEXT_MUTED, anchor="w").pack(
                anchor="w")

            tk.Label(row, text=f"₱{item['total']:,.2f}", font=("Segoe UI", 11, "bold"), bg=WHITE, fg="#991b1b").pack(
                side="right", pady=7)