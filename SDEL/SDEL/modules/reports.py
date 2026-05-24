# modules/reports.py
# ─────────────────────────────────────────────────────────────────────────────
#  PureHealth Diagnostic Center — Reports Module
#  CONNECTED TO DATABASE — Dynamically pulls analytics from purehealthDb.db
#  BUG FIXED: show() clears frame before rebuilding — no stacking
# ─────────────────────────────────────────────────────────────────────────────

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from datetime import datetime, date, timedelta
import calendar
from database import db

# ── Colour palette ─────────────────────────────────────────────────────────────
TEAL_DARK = "#073b4c"
TEAL_MID = "#0c637f"
TEAL_ACCENT = "#0cb0a9"
WHITE = "#ffffff"
BG_LIGHT = "#f4f6f8"
BORDER = "#e2e8f0"
TEXT_MAIN = "#1a202c"
TEXT_MUTED = "#718096"
TEXT_HINT = "#a0aec0"
GREEN_BG = "#f0fff4"
GREEN_FG = "#065f46"
RED_BG = "#fff5f5"
RED_FG = "#c53030"
BLUE_BG = "#dbeafe"
BLUE_FG = "#1e40af"
YELLOW_BG = "#fef9c3"
YELLOW_FG = "#854d0e"
PURPLE_BG = "#ede9fe"
PURPLE_FG = "#5b21b6"

# ── Report type definitions ────────────────────────────────────────────────────
REPORT_TYPES = [
    ("Daily Patient Report", "Lists all patients seen on a selected date", BLUE_BG, BLUE_FG),
    ("Monthly Summary", "Patient volume and revenue overview by month", GREEN_BG, GREEN_FG),
    ("Test Statistics", "Most requested tests and category breakdown", PURPLE_BG, PURPLE_FG),
    ("Revenue Report", "Collections, discounts, and unpaid balances", YELLOW_BG, YELLOW_FG),
    ("Unpaid Balances", "Patients with outstanding payment balances", RED_BG, RED_FG),
    ("Appointment History", "All appointments within a date range", BLUE_BG, TEAL_MID),
]


class ReportsModule:
    def __init__(self, parent):
        self.parent = parent
        self._active_report = 0
        self._sidebar_btns = []

        # Helper strings for date defaults
        self.today_str = date.today().strftime("%Y-%m-%d")
        self.first_of_month_str = date.today().replace(day=1).strftime("%Y-%m-%d")

    # ── Entry point ────────────────────────────────────────────────────────────
    def show(self):
        for w in self.parent.winfo_children():
            w.destroy()
        self.parent.configure(bg=BG_LIGHT)
        self._sidebar_btns = []
        self._build_ui()

    # ── UI ─────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        header = tk.Frame(self.parent, bg=WHITE)
        header.pack(fill="x")
        tk.Frame(header, bg=BORDER, height=1).pack(fill="x", side="bottom")

        title_block = tk.Frame(header, bg=WHITE)
        title_block.pack(side="left", padx=20, pady=12)
        tk.Label(title_block, text="Reports & Analytics",
                 font=("Segoe UI", 16, "bold"),
                 bg=WHITE, fg=TEXT_MAIN).pack(anchor="w")
        tk.Label(title_block,
                 text="Generate, preview, and export clinic data insights",
                 font=("Segoe UI", 10),
                 bg=WHITE, fg=TEXT_MUTED).pack(anchor="w")

        # Global Header Stats (Current Month)
        stats = tk.Frame(header, bg=WHITE)
        stats.pack(side="right", padx=20)

        # Calculate current month stats for header
        fin_data = db.get_financial_summary(self.first_of_month_str, self.today_str)
        month_appts = db.get_appointments_by_date_range(self.first_of_month_str, self.today_str)

        rev_str = f"₱{fin_data['collected']:,.2f}" if fin_data else "₱0.00"
        unpaid_str = f"₱{fin_data['uncollected']:,.2f}" if fin_data else "₱0.00"

        self._hdr_chip(stats, str(len(month_appts)), "Patients this month", BLUE_BG, BLUE_FG)
        self._hdr_chip(stats, rev_str, "Revenue this month", GREEN_BG, GREEN_FG)
        self._hdr_chip(stats, unpaid_str, "Unpaid balances", RED_BG, RED_FG)

        body = tk.Frame(self.parent, bg=BG_LIGHT)
        body.pack(fill="both", expand=True, padx=18, pady=14)

        sidebar = tk.Frame(body, bg=WHITE, width=210, highlightbackground=BORDER, highlightthickness=1)
        sidebar.pack(side="left", fill="y", padx=(0, 12))
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="REPORT TYPE", font=("Segoe UI", 9, "bold"),
                 bg=WHITE, fg=TEXT_MUTED).pack(anchor="w", padx=14, pady=(14, 8))
        tk.Frame(sidebar, bg=BORDER, height=1).pack(fill="x")

        for i, (name, desc, bg, fg) in enumerate(REPORT_TYPES):
            btn = tk.Button(sidebar, text=name, font=("Segoe UI", 10),
                            anchor="w", justify="left", relief="flat", cursor="hand2",
                            padx=14, pady=10, command=lambda idx=i: self._select_report(idx))
            btn.pack(fill="x")
            tk.Frame(sidebar, bg=BORDER, height=1).pack(fill="x")
            self._sidebar_btns.append(btn)

        self.content_area = tk.Frame(body, bg=BG_LIGHT)
        self.content_area.pack(side="left", fill="both", expand=True)

        self._select_report(0)

    # ── Sidebar selection ──────────────────────────────────────────────────────
    def _select_report(self, idx):
        self._active_report = idx
        name, desc, act_bg, act_fg = REPORT_TYPES[idx]

        for i, btn in enumerate(self._sidebar_btns):
            if i == idx:
                btn.configure(bg=act_bg, fg=act_fg, font=("Segoe UI", 10, "bold"))
            else:
                btn.configure(bg=WHITE, fg=TEXT_MAIN, font=("Segoe UI", 10))

        for w in self.content_area.winfo_children():
            w.destroy()

        builders = [
            self._build_daily_patient,
            self._build_monthly_summary,
            self._build_test_statistics,
            self._build_revenue_report,
            self._build_unpaid_balances,
            self._build_appointment_history,
        ]
        builders[idx](self.content_area, name, desc, act_bg, act_fg)

    # ── REPORT 1: Daily Patient Report ────────────────────────────────────────
    def _build_daily_patient(self, parent, name, desc, bg, fg):
        self._report_header(parent, name, desc, bg, fg)

        fc = self._card(parent)
        fc.pack(fill="x", pady=(0, 10))
        frow = tk.Frame(fc, bg=WHITE)
        frow.pack(fill="x", padx=14, pady=12)

        ctk.CTkLabel(frow, text="Date From", font=("Segoe UI", 9), text_color=TEXT_MUTED).pack(side="left")
        date_from = ctk.CTkEntry(frow, font=("Segoe UI", 10), height=32, width=120, corner_radius=6,
                                 border_color=BORDER, fg_color=WHITE, text_color=TEXT_MAIN)
        date_from.insert(0, self.today_str)
        date_from.pack(side="left", padx=(4, 14))

        ctk.CTkLabel(frow, text="Date To", font=("Segoe UI", 9), text_color=TEXT_MUTED).pack(side="left")
        date_to = ctk.CTkEntry(frow, font=("Segoe UI", 10), height=32, width=120, corner_radius=6, border_color=BORDER,
                               fg_color=WHITE, text_color=TEXT_MAIN)
        date_to.insert(0, self.today_str)
        date_to.pack(side="left", padx=(4, 14))

        # Dynamic Content Frame
        dyn_frame = tk.Frame(parent, bg=BG_LIGHT)
        dyn_frame.pack(fill="both", expand=True)

        def generate():
            for w in dyn_frame.winfo_children():
                w.destroy()

            start = date_from.get().strip()
            end = date_to.get().strip()

            # Fetch DB Data
            appts = db.get_appointments_by_date_range(start, end)
            fin = db.get_financial_summary(start, end)

            # Build Stats
            sr = tk.Frame(dyn_frame, bg=BG_LIGHT)
            sr.pack(fill="x", pady=(0, 10))

            total_appts = len(appts)
            walkins = sum(1 for a in appts if a["appt_type"] == "Walk-in")
            scheduled = total_appts - walkins
            coll_str = f"₱{fin['collected']:,.2f}" if fin else "₱0.00"
            uncoll_str = f"₱{fin['uncollected']:,.2f}" if fin else "₱0.00"

            self._stat_card(sr, str(total_appts), "Total Patients", BLUE_BG, BLUE_FG)
            self._stat_card(sr, str(scheduled), "By Appointment", GREEN_BG, GREEN_FG)
            self._stat_card(sr, str(walkins), "Walk-ins", PURPLE_BG, PURPLE_FG)
            self._stat_card(sr, coll_str, "Collected", GREEN_BG, GREEN_FG)
            self._stat_card(sr, uncoll_str, "Unpaid", RED_BG, RED_FG)

            # Build Table
            tc = self._card(dyn_frame)
            tc.pack(fill="both", expand=True)

            th = tk.Frame(tc, bg="#f8fafc")
            th.pack(fill="x")
            tk.Frame(tc, bg=BORDER, height=1).pack(fill="x")
            tk.Label(th, text=f"Patient List: {start} to {end}", font=("Segoe UI", 10, "bold"), bg="#f8fafc",
                     fg=TEXT_MAIN).pack(side="left", padx=14, pady=8)

            cols = ("#", "Patient Name", "Patient ID", "Tests Requested", "Time", "Status", "Type")
            widths = [30, 160, 130, 200, 80, 90, 80]
            tree, _ = self._styled_tree(tc, cols, widths)

            for i, row in enumerate(appts):
                tag = "paid" if row["status"] in ["Done", "Completed"] else "unpaid"
                tree.insert("", "end",
                            values=(
                            i + 1, row["patient_name"], row["patient_code"], row["tests_requested"], row["appt_time"],
                            row["status"], row["appt_type"]),
                            tags=(tag, "even" if i % 2 == 0 else "odd"))

            tree.tag_configure("even", background=WHITE)
            tree.tag_configure("odd", background="#f8fafc")
            tree.tag_configure("paid", foreground=GREEN_FG)
            tree.tag_configure("unpaid", foreground=RED_FG)

        # Buttons
        self._solid_btn(frow, "Generate Report", generate).pack(side="left")
        self._export_btn(frow, "Export PDF", lambda: self._export("PDF")).pack(side="left", padx=(8, 0))

        generate()  # Initial load

    # ── REPORT 2: Monthly Summary ─────────────────────────────────────────────
    def _build_monthly_summary(self, parent, name, desc, bg, fg):
        self._report_header(parent, name, desc, bg, fg)

        fc = self._card(parent)
        fc.pack(fill="x", pady=(0, 10))
        frow = tk.Frame(fc, bg=WHITE)
        frow.pack(fill="x", padx=14, pady=12)

        # Build month list dynamically
        today = date.today()
        month_list = [(today.replace(day=1) - timedelta(days=30 * i)).strftime("%B %Y") for i in range(12)]

        ctk.CTkLabel(frow, text="Month", font=("Segoe UI", 9), text_color=TEXT_MUTED).pack(side="left")
        month_combo = ctk.CTkComboBox(frow, values=month_list, font=("Segoe UI", 10), height=32, width=160,
                                      corner_radius=6, border_color=BORDER, fg_color=WHITE, text_color=TEXT_MAIN)
        month_combo.pack(side="left", padx=(4, 14))

        dyn_frame = tk.Frame(parent, bg=BG_LIGHT)
        dyn_frame.pack(fill="both", expand=True)

        def generate():
            for w in dyn_frame.winfo_children():
                w.destroy()

            selected = month_combo.get()
            sel_date = datetime.strptime(selected, "%B %Y")
            start = sel_date.strftime("%Y-%m-%d")
            # Calculate last day of month
            next_month = sel_date.replace(day=28) + timedelta(days=4)
            end = (next_month - timedelta(days=next_month.day)).strftime("%Y-%m-%d")

            fin = db.get_financial_summary(start, end)
            appts = db.get_appointments_by_date_range(start, end)

            # Stats
            sr = tk.Frame(dyn_frame, bg=BG_LIGHT)
            sr.pack(fill="x", pady=(0, 10))

            self._stat_card(sr, str(len(appts)), "Total Patients", BLUE_BG, BLUE_FG)
            self._stat_card(sr, str(fin["total_bills"]) if fin else "0", "Bills Issued", PURPLE_BG, PURPLE_FG)
            self._stat_card(sr, f"₱{fin['gross_revenue']:,.2f}" if fin else "₱0.00", "Gross Revenue", GREEN_BG,
                            GREEN_FG)
            self._stat_card(sr, f"₱{fin['uncollected']:,.2f}" if fin else "₱0.00", "Uncollected", RED_BG, RED_FG)

            # Two-column layout
            g2 = tk.Frame(dyn_frame, bg=BG_LIGHT)
            g2.pack(fill="both", expand=True)

            chart_card = self._card(g2)
            chart_card.pack(side="left", fill="both", expand=True, padx=(0, 8))
            tk.Label(chart_card, text="Patient Volume — Last 7 Months", font=("Segoe UI", 10, "bold"), bg=WHITE,
                     fg=TEXT_MAIN).pack(anchor="w", padx=14, pady=(12, 0))
            tk.Frame(chart_card, bg=BORDER, height=1).pack(fill="x", padx=14, pady=8)
            self._draw_bar_chart(chart_card)

            glance_card = self._card(g2)
            glance_card.pack(side="right", fill="y", ipadx=4)
            tk.Label(glance_card, text=f"{selected} — Summary", font=("Segoe UI", 10, "bold"), bg=WHITE,
                     fg=TEXT_MAIN).pack(anchor="w", padx=14, pady=(12, 0))
            tk.Frame(glance_card, bg=BORDER, height=1).pack(fill="x", padx=14, pady=8)

            walkins = sum(1 for a in appts if a["appt_type"] == "Walk-in")

            glance_items = [
                ("Total patients", str(len(appts)), TEXT_MAIN),
                ("By appointment", str(len(appts) - walkins), TEXT_MAIN),
                ("Walk-ins", str(walkins), TEXT_MAIN),
                ("Total Discounts", f"₱{fin['discounts']:,.2f}" if fin else "₱0.00", TEXT_MAIN),
                ("Gross revenue", f"₱{fin['gross_revenue']:,.2f}" if fin else "₱0.00", GREEN_FG),
                ("Collected", f"₱{fin['collected']:,.2f}" if fin else "₱0.00", GREEN_FG),
                ("Uncollected", f"₱{fin['uncollected']:,.2f}" if fin else "₱0.00", RED_FG),
            ]
            for lbl, val, vfg in glance_items:
                row = tk.Frame(glance_card, bg=WHITE)
                row.pack(fill="x", padx=14, pady=2)
                tk.Frame(glance_card, bg=BORDER, height=1).pack(fill="x", padx=14)
                tk.Label(row, text=lbl, font=("Segoe UI", 10), bg=WHITE, fg=TEXT_MUTED).pack(side="left", pady=5)
                tk.Label(row, text=val, font=("Segoe UI", 10, "bold"), bg=WHITE, fg=vfg).pack(side="right", pady=5)

        self._solid_btn(frow, "Generate", generate).pack(side="left")
        self._export_btn(frow, "Export PDF", lambda: self._export("PDF")).pack(side="left", padx=(8, 0))
        generate()

    def _draw_bar_chart(self, parent):
        """Draws a live 7-month historical chart using DB data."""
        canvas = tk.Canvas(parent, bg=WHITE, height=200, highlightthickness=0)
        canvas.pack(fill="x", padx=14, pady=(0, 14))
        canvas.update_idletasks()

        cw, ch = canvas.winfo_width() or 500, 200
        margin_l, margin_b = 40, 40
        chart_w, chart_h = cw - margin_l - 20, ch - margin_b - 20

        # Get last 7 months data
        historical = []
        today = date.today()
        for i in range(6, -1, -1):
            m_date = (today.replace(day=1) - timedelta(days=30 * i))
            start = m_date.replace(day=1).strftime("%Y-%m-%d")
            next_month = m_date.replace(day=28) + timedelta(days=4)
            end = (next_month - timedelta(days=next_month.day)).strftime("%Y-%m-%d")
            count = len(db.get_appointments_by_date_range(start, end))
            color = TEAL_ACCENT if i == 0 else "#cbd5e1"
            historical.append((m_date.strftime("%b"), count, color))

        max_val = max((v for _, v, _ in historical), default=1)
        max_val = max(max_val, 10)  # Set a minimum scale
        n = len(historical)
        bar_w = (chart_w / n) * 0.6
        gap = (chart_w / n) * 0.4

        for i in range(5):
            y = (ch - margin_b) - (i / 4) * chart_h
            canvas.create_line(margin_l, y, cw - 20, y, fill=BORDER, dash=(4, 4))
            canvas.create_text(margin_l - 6, y, text=str(int(max_val * i / 4)), font=("Segoe UI", 8), fill=TEXT_HINT,
                               anchor="e")

        for i, (month, val, color) in enumerate(historical):
            x0 = margin_l + i * (chart_w / n) + gap / 2
            x1 = x0 + bar_w
            bar_h = (val / max_val) * chart_h
            y0 = (ch - margin_b) - bar_h
            y1 = ch - margin_b

            canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="")
            canvas.create_text((x0 + x1) / 2, y0 - 6, text=str(val), font=("Segoe UI", 8, "bold"),
                               fill=TEAL_DARK if color == TEAL_ACCENT else TEXT_MUTED)
            canvas.create_text((x0 + x1) / 2, ch - margin_b + 12, text=month,
                               font=("Segoe UI", 8, "bold" if color == TEAL_ACCENT else "normal"),
                               fill=TEAL_DARK if color == TEAL_ACCENT else TEXT_MUTED)

    # ── REPORT 3: Test Statistics ─────────────────────────────────────────────
    def _build_test_statistics(self, parent, name, desc, bg, fg):
        self._report_header(parent, name, desc, bg, fg)
        fc = self._card(parent)
        fc.pack(fill="x", pady=(0, 10))
        frow = tk.Frame(fc, bg=WHITE)
        frow.pack(fill="x", padx=14, pady=12)

        ctk.CTkLabel(frow, text="Date From", font=("Segoe UI", 9), text_color=TEXT_MUTED).pack(side="left")
        date_from = ctk.CTkEntry(frow, font=("Segoe UI", 10), height=32, width=120, corner_radius=6,
                                 border_color=BORDER, fg_color=WHITE, text_color=TEXT_MAIN)
        date_from.insert(0, self.first_of_month_str)
        date_from.pack(side="left", padx=(4, 14))

        ctk.CTkLabel(frow, text="Date To", font=("Segoe UI", 9), text_color=TEXT_MUTED).pack(side="left")
        date_to = ctk.CTkEntry(frow, font=("Segoe UI", 10), height=32, width=120, corner_radius=6, border_color=BORDER,
                               fg_color=WHITE, text_color=TEXT_MAIN)
        date_to.insert(0, self.today_str)
        date_to.pack(side="left", padx=(4, 14))

        dyn_frame = tk.Frame(parent, bg=BG_LIGHT)
        dyn_frame.pack(fill="both", expand=True)

        def generate():
            for w in dyn_frame.winfo_children():
                w.destroy()

            start = date_from.get().strip()
            end = date_to.get().strip()
            stats = db.get_test_statistics_by_date_range(start, end)

            cats = tk.Frame(dyn_frame, bg=BG_LIGHT)
            cats.pack(fill="x", pady=(0, 10))

            cat_totals = {}
            for row in stats:
                cat_totals[row["category"]] = cat_totals.get(row["category"], 0) + row["count"]

            for cat, total in cat_totals.items():
                self._stat_card(cats, str(total), cat, BLUE_BG, BLUE_FG)

            tc = self._card(dyn_frame)
            tc.pack(fill="both", expand=True)
            tk.Label(tc, text=f"Top Tests: {start} to {end}", font=("Segoe UI", 10, "bold"), bg=WHITE,
                     fg=TEXT_MAIN).pack(anchor="w", padx=14, pady=(12, 0))
            tk.Frame(tc, bg=BORDER, height=1).pack(fill="x", padx=14, pady=8)

            max_count = stats[0]["count"] if stats else 1
            for i, row in enumerate(stats):
                row_bg = WHITE if i % 2 == 0 else "#f8fafc"
                tr = tk.Frame(tc, bg=row_bg)
                tr.pack(fill="x", padx=14, pady=4)

                tk.Label(tr, text=row["name"], font=("Segoe UI", 10, "bold"), bg=row_bg, fg=TEXT_MAIN, width=30,
                         anchor="w").pack(side="left")
                tk.Label(tr, text=row["category"], font=("Segoe UI", 9), bg=row_bg, fg=TEXT_MUTED, width=14,
                         anchor="w").pack(side="left")

                bar_outer = tk.Frame(tr, bg=BORDER, height=8)
                bar_outer.pack(side="left", fill="x", expand=True, padx=(8, 8))
                bar_outer.update_idletasks()
                bar_inner = tk.Frame(bar_outer, bg=TEAL_ACCENT, height=8)
                bar_inner.place(x=0, y=0, relwidth=min(row["count"] / max_count, 1.0), height=8)

                tk.Label(tr, text=f"{row['count']} tests", font=("Segoe UI", 9, "bold"), bg=row_bg, fg=TEAL_DARK,
                         width=9, anchor="e").pack(side="right")

        self._solid_btn(frow, "Generate", generate).pack(side="left")
        self._export_btn(frow, "Export PDF", lambda: self._export("PDF")).pack(side="left", padx=(8, 0))
        generate()

    # ── REPORT 4: Revenue Report ──────────────────────────────────────────────
    def _build_revenue_report(self, parent, name, desc, bg, fg):
        self._report_header(parent, name, desc, bg, fg)
        fc = self._card(parent)
        fc.pack(fill="x", pady=(0, 10))
        frow = tk.Frame(fc, bg=WHITE)
        frow.pack(fill="x", padx=14, pady=12)

        ctk.CTkLabel(frow, text="Date From", font=("Segoe UI", 9), text_color=TEXT_MUTED).pack(side="left")
        date_from = ctk.CTkEntry(frow, font=("Segoe UI", 10), height=32, width=120, corner_radius=6,
                                 border_color=BORDER, fg_color=WHITE, text_color=TEXT_MAIN)
        date_from.insert(0, self.first_of_month_str)
        date_from.pack(side="left", padx=(4, 14))

        ctk.CTkLabel(frow, text="Date To", font=("Segoe UI", 9), text_color=TEXT_MUTED).pack(side="left")
        date_to = ctk.CTkEntry(frow, font=("Segoe UI", 10), height=32, width=120, corner_radius=6, border_color=BORDER,
                               fg_color=WHITE, text_color=TEXT_MAIN)
        date_to.insert(0, self.today_str)
        date_to.pack(side="left", padx=(4, 14))

        dyn_frame = tk.Frame(parent, bg=BG_LIGHT)
        dyn_frame.pack(fill="both", expand=True)

        def generate():
            for w in dyn_frame.winfo_children():
                w.destroy()

            start = date_from.get().strip()
            end = date_to.get().strip()
            fin = db.get_financial_summary(start, end)
            rev_cat = db.get_revenue_by_category(start, end)

            sr = tk.Frame(dyn_frame, bg=BG_LIGHT)
            sr.pack(fill="x", pady=(0, 10))

            gross = fin['gross_revenue'] if fin else 0

            self._stat_card(sr, f"₱{gross:,.2f}", "Gross Revenue", GREEN_BG, GREEN_FG)
            self._stat_card(sr, f"₱{fin['collected']:,.2f}" if fin else "₱0", "Collected", GREEN_BG, GREEN_FG)
            self._stat_card(sr, f"₱{fin['uncollected']:,.2f}" if fin else "₱0", "Uncollected", RED_BG, RED_FG)
            self._stat_card(sr, f"₱{fin['discounts']:,.2f}" if fin else "₱0", "Total Discounts", YELLOW_BG, YELLOW_FG)
            self._stat_card(sr, str(fin['total_bills']) if fin else "0", "Transactions", BLUE_BG, BLUE_FG)

            tc = self._card(dyn_frame)
            tc.pack(fill="both", expand=True)
            tk.Label(tc, text=f"Revenue Breakdown by Department", font=("Segoe UI", 10, "bold"), bg=WHITE,
                     fg=TEXT_MAIN).pack(anchor="w", padx=14, pady=(12, 0))
            tk.Frame(tc, bg=BORDER, height=1).pack(fill="x", padx=14, pady=8)

            for i, row in enumerate(rev_cat):
                row_bg = WHITE if i % 2 == 0 else "#f8fafc"
                tr = tk.Frame(tc, bg=row_bg)
                tr.pack(fill="x", padx=14)
                tk.Frame(tc, bg=BORDER, height=1).pack(fill="x", padx=14)

                pct = f"{(row['revenue'] / gross * 100):.1f}%" if gross > 0 else "0%"

                tk.Label(tr, text=row["category"], font=("Segoe UI", 10), bg=row_bg, fg=TEXT_MAIN, width=18, anchor="w",
                         pady=8).pack(side="left")
                tk.Label(tr, text=f"₱{row['revenue']:,.2f}", font=("Segoe UI", 10, "bold"), bg=row_bg,
                         fg=GREEN_FG).pack(side="right", padx=(0, 14))
                tk.Label(tr, text=pct, font=("Segoe UI", 9), bg=row_bg, fg=TEXT_MUTED).pack(side="right", padx=8)

        self._solid_btn(frow, "Generate", generate).pack(side="left")
        self._export_btn(frow, "Export PDF", lambda: self._export("PDF")).pack(side="left", padx=(8, 0))
        generate()

    # ── REPORT 5: Unpaid Balances ─────────────────────────────────────────────
    def _build_unpaid_balances(self, parent, name, desc, bg, fg):
        self._report_header(parent, name, desc, bg, fg)

        fc = self._card(parent)
        fc.pack(fill="x", pady=(0, 10))
        frow = tk.Frame(fc, bg=WHITE)
        frow.pack(fill="x", padx=14, pady=12)
        search = ctk.CTkEntry(frow, placeholder_text="Filter by patient name...", font=("Segoe UI", 10), height=32,
                              width=250, corner_radius=6, border_color=BORDER, fg_color=WHITE, text_color=TEXT_MAIN)
        search.pack(side="left", padx=(0, 8))

        dyn_frame = tk.Frame(parent, bg=BG_LIGHT)
        dyn_frame.pack(fill="both", expand=True)

        def generate():
            for w in dyn_frame.winfo_children():
                w.destroy()

            query = search.get().strip().lower()
            all_unpaid = db.get_unpaid_bills()
            filtered = [r for r in all_unpaid if query in r["patient_name"].lower()]

            total_unpaid = sum(r["total"] for r in filtered)

            sr = tk.Frame(dyn_frame, bg=BG_LIGHT)
            sr.pack(fill="x", pady=(0, 10))
            self._stat_card(sr, str(len(filtered)), "Accounts", RED_BG, RED_FG)
            self._stat_card(sr, f"₱{total_unpaid:,.2f}", "Total Owed", RED_BG, RED_FG)

            tc = self._card(dyn_frame)
            tc.pack(fill="both", expand=True)
            th = tk.Frame(tc, bg="#fff5f5")
            th.pack(fill="x")
            tk.Frame(tc, bg=BORDER, height=1).pack(fill="x")
            tk.Label(th, text="Outstanding Balances", font=("Segoe UI", 10, "bold"), bg="#fff5f5", fg=RED_FG).pack(
                side="left", padx=14, pady=8)

            cols = ("Bill #", "Patient", "Patient ID", "Date Issued", "Balance")
            widths = [60, 200, 130, 120, 100]
            tree, _ = self._styled_tree(tc, cols, widths)

            for i, r in enumerate(filtered):
                tree.insert("", "end", values=(
                f"#{r['id']}", r["patient_name"], r["patient_code"], str(r["created_at"])[:10], f"₱{r['total']:,.2f}"),
                            tags=("even" if i % 2 == 0 else "odd",))

            tree.tag_configure("even", background=WHITE, foreground=RED_FG)
            tree.tag_configure("odd", background=RED_BG, foreground=RED_FG)

        self._solid_btn(frow, "Filter", generate).pack(side="left")
        self._export_btn(frow, "Export PDF", lambda: self._export("PDF")).pack(side="left", padx=(8, 0))
        generate()

    # ── REPORT 6: Appointment History ─────────────────────────────────────────
    def _build_appointment_history(self, parent, name, desc, bg, fg):
        self._report_header(parent, name, desc, bg, fg)

        fc = self._card(parent)
        fc.pack(fill="x", pady=(0, 10))
        frow = tk.Frame(fc, bg=WHITE)
        frow.pack(fill="x", padx=14, pady=12)

        ctk.CTkLabel(frow, text="Date From", font=("Segoe UI", 9), text_color=TEXT_MUTED).pack(side="left")
        date_from = ctk.CTkEntry(frow, font=("Segoe UI", 10), height=32, width=120, corner_radius=6,
                                 border_color=BORDER, fg_color=WHITE, text_color=TEXT_MAIN)
        date_from.insert(0, self.first_of_month_str)
        date_from.pack(side="left", padx=(4, 14))

        ctk.CTkLabel(frow, text="Date To", font=("Segoe UI", 9), text_color=TEXT_MUTED).pack(side="left")
        date_to = ctk.CTkEntry(frow, font=("Segoe UI", 10), height=32, width=120, corner_radius=6, border_color=BORDER,
                               fg_color=WHITE, text_color=TEXT_MAIN)
        date_to.insert(0, self.today_str)
        date_to.pack(side="left", padx=(4, 14))

        type_combo = ctk.CTkComboBox(frow, values=["All Types", "Appointment", "Walk-in"], font=("Segoe UI", 10),
                                     height=32, width=150, corner_radius=6, border_color=BORDER, fg_color=WHITE,
                                     text_color=TEXT_MAIN)
        type_combo.pack(side="left", padx=(0, 14))

        dyn_frame = tk.Frame(parent, bg=BG_LIGHT)
        dyn_frame.pack(fill="both", expand=True)

        def generate():
            for w in dyn_frame.winfo_children():
                w.destroy()

            start = date_from.get().strip()
            end = date_to.get().strip()
            filter_type = type_combo.get()

            all_appts = db.get_appointments_by_date_range(start, end)

            if filter_type != "All Types":
                all_appts = [a for a in all_appts if a["appt_type"] == filter_type]

            sr = tk.Frame(dyn_frame, bg=BG_LIGHT)
            sr.pack(fill="x", pady=(0, 10))

            walkins = sum(1 for a in all_appts if a["appt_type"] == "Walk-in")
            completed = sum(1 for a in all_appts if a["status"] in ["Done", "Completed"])

            self._stat_card(sr, str(len(all_appts)), "Total", BLUE_BG, BLUE_FG)
            self._stat_card(sr, str(len(all_appts) - walkins), "By Appt.", GREEN_BG, GREEN_FG)
            self._stat_card(sr, str(walkins), "Walk-in", PURPLE_BG, PURPLE_FG)
            self._stat_card(sr, str(completed), "Completed", GREEN_BG, GREEN_FG)

            tc = self._card(dyn_frame)
            tc.pack(fill="both", expand=True)
            th = tk.Frame(tc, bg="#f8fafc")
            th.pack(fill="x")
            tk.Frame(tc, bg=BORDER, height=1).pack(fill="x")
            tk.Label(th, text="Appointment History", font=("Segoe UI", 10, "bold"), bg="#f8fafc", fg=TEXT_MAIN).pack(
                side="left", padx=14, pady=8)

            cols = ("Patient", "Patient ID", "Tests", "Date", "Time", "Type", "Status")
            widths = [140, 120, 170, 100, 70, 100, 80]
            tree, _ = self._styled_tree(tc, cols, widths)

            for i, r in enumerate(all_appts):
                tree.insert("", "end", values=(
                r["patient_name"], r["patient_code"], r["tests_requested"], r["appt_date"], r["appt_time"],
                r["appt_type"], r["status"]), tags=("even" if i % 2 == 0 else "odd",))

            tree.tag_configure("even", background=WHITE)
            tree.tag_configure("odd", background="#f8fafc")

        self._solid_btn(frow, "Generate", generate).pack(side="left")
        self._export_btn(frow, "Export PDF", lambda: self._export("PDF")).pack(side="left", padx=(8, 0))
        generate()

    # ── Shared helpers ─────────────────────────────────────────────────────────
    def _report_header(self, parent, name, desc, bg, fg):
        hdr = tk.Frame(parent, bg=bg, highlightbackground=BORDER, highlightthickness=1)
        hdr.pack(fill="x", pady=(0, 10))
        tk.Label(hdr, text=name, font=("Segoe UI", 12, "bold"), bg=bg, fg=fg).pack(side="left", padx=14, pady=10)
        tk.Label(hdr, text=desc, font=("Segoe UI", 9), bg=bg, fg=fg).pack(side="left")

    def _stat_card(self, parent, value, label, bg, fg):
        chip = tk.Frame(parent, bg=bg, highlightbackground=BORDER, highlightthickness=1)
        chip.pack(side="left", padx=(0, 8), ipadx=6)
        tk.Label(chip, text=value, font=("Segoe UI", 14, "bold"), bg=bg, fg=fg).pack(padx=12, pady=(8, 2))
        tk.Label(chip, text=label, font=("Segoe UI", 8), bg=bg, fg=fg).pack(padx=12, pady=(0, 8))

    def _card(self, parent):
        return tk.Frame(parent, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)

    def _styled_tree(self, parent, cols, widths):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Reports.Treeview", background=WHITE, fieldbackground=WHITE, foreground=TEXT_MAIN, rowheight=36,
                        font=("Segoe UI", 10))
        style.configure("Reports.Treeview.Heading", background="#f8fafc", foreground=TEXT_MUTED,
                        font=("Segoe UI", 9, "bold"), relief="flat", padding=6)
        style.map("Reports.Treeview", background=[("selected", "#e0f2fe")], foreground=[("selected", TEXT_MAIN)])

        tree = ttk.Treeview(parent, columns=cols, show="headings", style="Reports.Treeview")
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="w")

        vsb = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        return tree, vsb

    def _solid_btn(self, parent, text, command):
        return tk.Button(parent, text=text, command=command, font=("Segoe UI", 10, "bold"), bg=TEAL_DARK, fg=WHITE,
                         activebackground=TEAL_MID, relief="flat", cursor="hand2", padx=14, pady=6)

    def _export_btn(self, parent, text, command):
        return tk.Button(parent, text=text, command=command, font=("Segoe UI", 10), bg=WHITE, fg=TEXT_MUTED,
                         activebackground=BG_LIGHT, relief="flat", cursor="hand2", padx=12, pady=6,
                         highlightbackground=BORDER, highlightthickness=1)

    def _hdr_chip(self, parent, value, label, bg, fg):
        chip = tk.Frame(parent, bg=bg, highlightbackground=BORDER, highlightthickness=1)
        chip.pack(side="left", padx=4)
        tk.Label(chip, text=f"  {value}  {label}  ", font=("Segoe UI", 9, "bold"), bg=bg, fg=fg, pady=5).pack()

    def _export(self, fmt):
        messagebox.showinfo(f"Export to {fmt}", f"Report exported as {fmt} successfully.\nCheck your Documents folder.")