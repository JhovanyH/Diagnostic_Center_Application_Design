# modules/reports.py
# ─────────────────────────────────────────────────────────────────────────────
#  PureHealth Diagnostic Center — Reports Module
#  Improved design using CustomTkinter
#  All original features kept:
#    - 6 report types selectable from sidebar
#    - Date range filter, Sort By, Generate, Export PDF, Export Excel
#    - Preview table with patient data
#    - Today at a Glance summary
#    - Monthly bar chart (drawn with Canvas)
#  BUG FIXED: show() clears frame before rebuilding — no stacking
# ─────────────────────────────────────────────────────────────────────────────

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk

# ── Colour palette ─────────────────────────────────────────────────────────────
TEAL_DARK    = "#073b4c"
TEAL_MID     = "#0c637f"
TEAL_ACCENT  = "#0cb0a9"
WHITE        = "#ffffff"
BG_LIGHT     = "#f4f6f8"
BORDER       = "#e2e8f0"
TEXT_MAIN    = "#1a202c"
TEXT_MUTED   = "#718096"
TEXT_HINT    = "#a0aec0"
GREEN_BG     = "#f0fff4"
GREEN_FG     = "#065f46"
RED_BG       = "#fff5f5"
RED_FG       = "#c53030"
BLUE_BG      = "#dbeafe"
BLUE_FG      = "#1e40af"
YELLOW_BG    = "#fef9c3"
YELLOW_FG    = "#854d0e"
PURPLE_BG    = "#ede9fe"
PURPLE_FG    = "#5b21b6"

# ── Report type definitions ────────────────────────────────────────────────────
REPORT_TYPES = [
    ("Daily Patient Report",    "Lists all patients seen on a selected date",
     BLUE_BG,   BLUE_FG),
    ("Monthly Summary",         "Patient volume and revenue overview by month",
     GREEN_BG,  GREEN_FG),
    ("Test Statistics",         "Most requested tests and category breakdown",
     PURPLE_BG, PURPLE_FG),
    ("Revenue Report",          "Collections, discounts, and unpaid balances",
     YELLOW_BG, YELLOW_FG),
    ("Unpaid Balances",         "Patients with outstanding payment balances",
     RED_BG,    RED_FG),
    ("Appointment History",     "All appointments within a date range",
     BLUE_BG,   TEAL_MID),
]

SORT_OPTIONS = ["Name (A–Z)", "Name (Z–A)", "Time of Visit",
                "Test Type", "Amount (High–Low)"]

# ── Sample data (replace with real DB queries later) ──────────────────────────
DAILY_DATA = [
    ("Juan dela Cruz",  "PHC-2025-00124", "CBC, Urinalysis",        "8:00 AM",  "₱500.00",  "Paid"),
    ("Ana Santos",      "PHC-2025-00123", "Chest X-Ray PA",         "9:30 AM",  "₱450.00",  "Paid"),
    ("Rosa Garcia",     "PHC-2025-00125", "Urinalysis",             "9:14 AM",  "₱150.00",  "Paid"),
    ("Pedro Bautista",  "PHC-2025-00122", "Blood Chemistry",        "10:00 AM", "₱350.00",  "Paid"),
    ("Liza Reyes",      "PHC-2025-00121", "Ultrasound OB",          "11:00 AM", "₱800.00",  "Paid"),
    ("Ben Torres",      "PHC-2025-00118", "CBC",                    "9:28 AM",  "₱350.00",  "Unpaid"),
    ("Carlo Mendoza",   "PHC-2025-00120", "ECG, CBC",               "1:30 PM",  "₱750.00",  "Paid"),
    ("Clara Santos",    "PHC-2025-00115", "FBS, Urinalysis",        "2:00 PM",  "₱350.00",  "Unpaid"),
    ("Mario Villanueva","PHC-2025-00126", "Lipid Profile",          "2:30 PM",  "₱450.00",  "Paid"),
    ("Elena Cruz",      "PHC-2025-00127", "TSH, FBS",               "3:00 PM",  "₱850.00",  "Paid"),
]

TEST_STATS = [
    ("Complete Blood Count (CBC)", "Hematology",  89, 89 / 3.07),
    ("Urinalysis",                 "Urinalysis",  74, 74 / 3.07),
    ("Blood Chemistry Panel",      "Chemistry",   61, 61 / 3.07),
    ("Chest X-Ray PA",             "Radiology",   48, 48 / 3.07),
    ("Ultrasound — OB",            "Radiology",   35, 35 / 3.07),
    ("Fasting Blood Sugar",        "Chemistry",   29, 29 / 3.07),
    ("ECG",                        "Cardiology",  22, 22 / 3.07),
    ("Lipid Profile",              "Chemistry",   18, 18 / 3.07),
    ("Blood Typing",               "Hematology",  14, 14 / 3.07),
    ("TSH",                        "Chemistry",   11, 11 / 3.07),
]

MONTHLY_BARS = [
    ("Nov", 180, "#cbd5e1"),
    ("Dec", 195, "#cbd5e1"),
    ("Jan", 210, "#cbd5e1"),
    ("Feb", 225, "#cbd5e1"),
    ("Mar", 238, "#cbd5e1"),
    ("Apr", 219, "#cbd5e1"),
    ("May", 247, TEAL_ACCENT),
]

UNPAID_DATA = [
    ("Ben Torres",   "PHC-2025-00118", "CBC",              "May 5, 2025",  "₱350.00"),
    ("Clara Santos", "PHC-2025-00115", "FBS, Urinalysis",  "May 5, 2025",  "₱350.00"),
    ("Leo Manalo",   "PHC-2025-00109", "X-Ray PA",         "Apr 28, 2025", "₱450.00"),
    ("Grace Tan",    "PHC-2025-00103", "Blood Chemistry",  "Apr 22, 2025", "₱350.00"),
    ("Mike Reyes",   "PHC-2025-00098", "Urinalysis",       "Apr 18, 2025", "₱150.00"),
]

APPT_DATA = [
    ("Juan dela Cruz",  "PHC-2025-00124", "CBC, Urinalysis",    "May 5, 2025", "8:00 AM",  "Appointment", "Done"),
    ("Ana Santos",      "PHC-2025-00123", "Chest X-Ray PA",     "May 5, 2025", "9:30 AM",  "Appointment", "Done"),
    ("Rosa Garcia",     "PHC-2025-00125", "Urinalysis",         "May 5, 2025", "9:14 AM",  "Walk-in",     "Done"),
    ("Pedro Bautista",  "PHC-2025-00122", "Blood Chemistry",    "May 5, 2025", "10:00 AM", "Appointment", "Done"),
    ("Liza Reyes",      "PHC-2025-00121", "Ultrasound OB",      "May 5, 2025", "11:00 AM", "Appointment", "Done"),
    ("Carlo Mendoza",   "PHC-2025-00120", "ECG, CBC",           "May 5, 2025", "1:30 PM",  "Appointment", "Done"),
]


# ─────────────────────────────────────────────────────────────────────────────
class ReportsModule:
# ─────────────────────────────────────────────────────────────────────────────

    def __init__(self, parent):
        self.parent          = parent
        self._active_report  = 0          # index into REPORT_TYPES
        self._sidebar_btns   = []

    # ── Entry point ────────────────────────────────────────────────────────────

    def show(self):
        # FIX: destroy all old widgets before rebuilding — prevents stacking
        for w in self.parent.winfo_children():
            w.destroy()
        self.parent.configure(bg=BG_LIGHT)
        self._sidebar_btns = []
        self._build_ui()

    # ── UI ─────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Page header ────────────────────────────────────────────────────────
        header = tk.Frame(self.parent, bg=WHITE)
        header.pack(fill="x")
        tk.Frame(header, bg=BORDER, height=1).pack(fill="x", side="bottom")

        title_block = tk.Frame(header, bg=WHITE)
        title_block.pack(side="left", padx=20, pady=12)
        tk.Label(title_block, text="Reports",
                 font=("Segoe UI", 16, "bold"),
                 bg=WHITE, fg=TEXT_MAIN).pack(anchor="w")
        tk.Label(title_block,
                 text="Generate, preview, and export clinic reports",
                 font=("Segoe UI", 10),
                 bg=WHITE, fg=TEXT_MUTED).pack(anchor="w")

        # Quick stat chips in header
        stats = tk.Frame(header, bg=WHITE)
        stats.pack(side="right", padx=20)
        self._hdr_chip(stats, "247",      "Patients this month", BLUE_BG,   BLUE_FG)
        self._hdr_chip(stats, "₱184,200", "Revenue this month",  GREEN_BG,  GREEN_FG)
        self._hdr_chip(stats, "₱7,850",   "Unpaid balances",     RED_BG,    RED_FG)

        # ── Body: sidebar + main content ───────────────────────────────────────
        body = tk.Frame(self.parent, bg=BG_LIGHT)
        body.pack(fill="both", expand=True, padx=18, pady=14)

        # Left sidebar
        sidebar = tk.Frame(body, bg=WHITE, width=210,
                           highlightbackground=BORDER,
                           highlightthickness=1)
        sidebar.pack(side="left", fill="y", padx=(0, 12))
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="REPORT TYPE",
                 font=("Segoe UI", 9, "bold"),
                 bg=WHITE, fg=TEXT_MUTED).pack(
                     anchor="w", padx=14, pady=(14, 8))
        tk.Frame(sidebar, bg=BORDER, height=1).pack(fill="x")

        for i, (name, desc, bg, fg) in enumerate(REPORT_TYPES):
            btn = tk.Button(sidebar, text=name,
                            font=("Segoe UI", 10),
                            anchor="w", justify="left",
                            relief="flat", cursor="hand2",
                            padx=14, pady=10,
                            command=lambda idx=i: self._select_report(idx))
            btn.pack(fill="x")
            tk.Frame(sidebar, bg=BORDER, height=1).pack(fill="x")
            self._sidebar_btns.append(btn)

        # Right: main content area
        self.content_area = tk.Frame(body, bg=BG_LIGHT)
        self.content_area.pack(side="left", fill="both", expand=True)

        # Highlight first report type and load it
        self._select_report(0)

    # ── Sidebar selection ──────────────────────────────────────────────────────

    def _select_report(self, idx):
        self._active_report = idx
        name, desc, act_bg, act_fg = REPORT_TYPES[idx]

        # Update sidebar button styles
        for i, btn in enumerate(self._sidebar_btns):
            if i == idx:
                btn.configure(bg=act_bg, fg=act_fg,
                              font=("Segoe UI", 10, "bold"))
            else:
                btn.configure(bg=WHITE, fg=TEXT_MAIN,
                              font=("Segoe UI", 10))

        # Clear and rebuild the content area
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

        # Filter card
        fc = self._card(parent)
        fc.pack(fill="x", pady=(0, 10))
        frow = tk.Frame(fc, bg=WHITE)
        frow.pack(fill="x", padx=14, pady=12)

        ctk.CTkLabel(frow, text="Date From",
                     font=("Segoe UI", 9),
                     text_color=TEXT_MUTED).pack(side="left")
        ctk.CTkEntry(frow, placeholder_text="2025-05-05",
                     font=("Segoe UI", 10), height=32, width=120,
                     corner_radius=6, border_color=BORDER,
                     fg_color=WHITE, text_color=TEXT_MAIN
                     ).pack(side="left", padx=(4, 14))

        ctk.CTkLabel(frow, text="Date To",
                     font=("Segoe UI", 9),
                     text_color=TEXT_MUTED).pack(side="left")
        ctk.CTkEntry(frow, placeholder_text="2025-05-05",
                     font=("Segoe UI", 10), height=32, width=120,
                     corner_radius=6, border_color=BORDER,
                     fg_color=WHITE, text_color=TEXT_MAIN
                     ).pack(side="left", padx=(4, 14))

        ctk.CTkLabel(frow, text="Sort By",
                     font=("Segoe UI", 9),
                     text_color=TEXT_MUTED).pack(side="left")
        ctk.CTkComboBox(frow, values=SORT_OPTIONS,
                        font=("Segoe UI", 10), height=32, width=160,
                        corner_radius=6, border_color=BORDER,
                        fg_color=WHITE, text_color=TEXT_MAIN
                        ).pack(side="left", padx=(4, 14))

        # Action buttons
        btn_row = tk.Frame(fc, bg=WHITE)
        btn_row.pack(fill="x", padx=14, pady=(0, 12))
        self._solid_btn(btn_row, "Generate Report",
                        lambda: self._generate_preview()).pack(side="left")
        self._export_btn(btn_row, "Export PDF",
                         lambda: self._export("PDF")).pack(side="left", padx=(8, 0))
        self._export_btn(btn_row, "Export Excel",
                         lambda: self._export("Excel")).pack(side="left", padx=(8, 0))

        # Stats row
        sr = tk.Frame(parent, bg=BG_LIGHT)
        sr.pack(fill="x", pady=(0, 10))
        stats = [
            ("24",       "Total Patients",   BLUE_BG,   BLUE_FG),
            ("18",       "By Appointment",   GREEN_BG,  GREEN_FG),
            ("6",        "Walk-ins",         PURPLE_BG, PURPLE_FG),
            ("₱14,750",  "Collected",        GREEN_BG,  GREEN_FG),
            ("₱700",     "Unpaid",           RED_BG,    RED_FG),
        ]
        for val, lbl, sbg, sfg in stats:
            self._stat_card(sr, val, lbl, sbg, sfg)

        # Preview table
        self._build_daily_table(parent)

    def _build_daily_table(self, parent):
        tc = self._card(parent)
        tc.pack(fill="both", expand=True)

        # Table header
        th = tk.Frame(tc, bg="#f8fafc")
        th.pack(fill="x")
        tk.Frame(tc, bg=BORDER, height=1).pack(fill="x")
        tk.Label(th, text="Preview — Daily Patient Report · May 5, 2025",
                 font=("Segoe UI", 10, "bold"),
                 bg="#f8fafc", fg=TEXT_MAIN).pack(side="left", padx=14, pady=8)
        tk.Label(th, text=f"{len(DAILY_DATA)} patients",
                 font=("Segoe UI", 9),
                 bg="#f8fafc", fg=TEXT_MUTED).pack(side="right", padx=14)

        cols = ("#", "Patient Name", "Patient ID",
                "Tests", "Time In", "Amount", "Status")
        widths = [30, 160, 130, 200, 80, 90, 80]
        tree, _ = self._styled_tree(tc, cols, widths)

        for i, (name, pid, tests, time, amt, status) in enumerate(DAILY_DATA):
            tag = "paid" if status == "Paid" else "unpaid"
            tree.insert("", "end",
                        values=(i + 1, name, pid, tests, time, amt, status),
                        tags=(tag, "even" if i % 2 == 0 else "odd"))

        tree.tag_configure("even",   background=WHITE)
        tree.tag_configure("odd",    background="#f8fafc")
        tree.tag_configure("paid",   foreground=GREEN_FG)
        tree.tag_configure("unpaid", foreground=RED_FG)

    # ── REPORT 2: Monthly Summary ─────────────────────────────────────────────

    def _build_monthly_summary(self, parent, name, desc, bg, fg):
        self._report_header(parent, name, desc, bg, fg)

        # Filter row
        fc = self._card(parent)
        fc.pack(fill="x", pady=(0, 10))
        frow = tk.Frame(fc, bg=WHITE)
        frow.pack(fill="x", padx=14, pady=12)
        ctk.CTkLabel(frow, text="Month", font=("Segoe UI", 9),
                     text_color=TEXT_MUTED).pack(side="left")
        ctk.CTkComboBox(
            frow,
            values=["May 2025", "April 2025", "March 2025",
                    "February 2025", "January 2025"],
            font=("Segoe UI", 10), height=32, width=160,
            corner_radius=6, border_color=BORDER,
            fg_color=WHITE, text_color=TEXT_MAIN
        ).pack(side="left", padx=(4, 14))
        self._solid_btn(frow, "Generate",
                        lambda: messagebox.showinfo(
                            "Report", "Monthly summary generated.")
                        ).pack(side="left")
        self._export_btn(frow, "Export PDF",
                         lambda: self._export("PDF")).pack(side="left", padx=(8, 0))
        self._export_btn(frow, "Export Excel",
                         lambda: self._export("Excel")).pack(side="left", padx=(8, 0))

        # Stats
        sr = tk.Frame(parent, bg=BG_LIGHT)
        sr.pack(fill="x", pady=(0, 10))
        for val, lbl, sbg, sfg in [
            ("247",      "Total Patients",   BLUE_BG,   BLUE_FG),
            ("614",      "Tests Done",       PURPLE_BG, PURPLE_FG),
            ("₱184,200", "Gross Revenue",    GREEN_BG,  GREEN_FG),
            ("₱7,850",   "Uncollected",      RED_BG,    RED_FG),
        ]:
            self._stat_card(sr, val, lbl, sbg, sfg)

        # Two-column layout: bar chart + glance
        g2 = tk.Frame(parent, bg=BG_LIGHT)
        g2.pack(fill="both", expand=True)

        # Bar chart card
        chart_card = self._card(g2)
        chart_card.pack(side="left", fill="both",
                        expand=True, padx=(0, 8))
        tk.Label(chart_card, text="Patient Volume — Last 7 Months",
                 font=("Segoe UI", 10, "bold"),
                 bg=WHITE, fg=TEXT_MAIN).pack(anchor="w", padx=14, pady=(12, 0))
        tk.Frame(chart_card, bg=BORDER, height=1).pack(
            fill="x", padx=14, pady=8)
        self._draw_bar_chart(chart_card)

        # Glance card
        glance_card = self._card(g2)
        glance_card.pack(side="right", fill="y", ipadx=4)
        tk.Label(glance_card, text="May 2025 — Summary",
                 font=("Segoe UI", 10, "bold"),
                 bg=WHITE, fg=TEXT_MAIN).pack(anchor="w", padx=14, pady=(12, 0))
        tk.Frame(glance_card, bg=BORDER, height=1).pack(
            fill="x", padx=14, pady=8)
        glance_items = [
            ("Total patients",   "247",       TEXT_MAIN),
            ("By appointment",   "189",       TEXT_MAIN),
            ("Walk-ins",         "58",        TEXT_MAIN),
            ("Tests completed",  "614",       TEXT_MAIN),
            ("Senior discounts", "23",        TEXT_MAIN),
            ("PWD discounts",    "11",        TEXT_MAIN),
            ("Gross revenue",    "₱184,200",  GREEN_FG),
            ("Collected",        "₱176,350",  GREEN_FG),
            ("Uncollected",      "₱7,850",    RED_FG),
        ]
        for lbl, val, vfg in glance_items:
            row = tk.Frame(glance_card, bg=WHITE)
            row.pack(fill="x", padx=14, pady=2)
            tk.Frame(glance_card, bg=BORDER, height=1).pack(
                fill="x", padx=14)
            tk.Label(row, text=lbl, font=("Segoe UI", 10),
                     bg=WHITE, fg=TEXT_MUTED).pack(side="left", pady=5)
            tk.Label(row, text=val,
                     font=("Segoe UI", 10, "bold"),
                     bg=WHITE, fg=vfg).pack(side="right", pady=5)

    def _draw_bar_chart(self, parent):
        """Draw a simple bar chart using tk.Canvas."""
        canvas = tk.Canvas(parent, bg=WHITE, height=200,
                           highlightthickness=0)
        canvas.pack(fill="x", padx=14, pady=(0, 14))

        canvas.update_idletasks()
        cw = canvas.winfo_width() or 500
        ch = 200
        margin_l, margin_b = 40, 40
        chart_w = cw - margin_l - 20
        chart_h = ch - margin_b - 20
        max_val = max(v for _, v, _ in MONTHLY_BARS)
        n = len(MONTHLY_BARS)
        bar_w = (chart_w / n) * 0.6
        gap   = (chart_w / n) * 0.4

        # Y gridlines
        for i in range(5):
            y = (ch - margin_b) - (i / 4) * chart_h
            canvas.create_line(margin_l, y, cw - 20, y,
                               fill=BORDER, dash=(4, 4))
            label = int(max_val * i / 4)
            canvas.create_text(margin_l - 6, y,
                               text=str(label),
                               font=("Segoe UI", 8),
                               fill=TEXT_HINT, anchor="e")

        # Bars
        for i, (month, val, color) in enumerate(MONTHLY_BARS):
            x0 = margin_l + i * (chart_w / n) + gap / 2
            x1 = x0 + bar_w
            bar_h = (val / max_val) * chart_h
            y0 = (ch - margin_b) - bar_h
            y1 = ch - margin_b

            # Bar with rounded top (approximated)
            canvas.create_rectangle(x0, y0, x1, y1,
                                    fill=color, outline="",
                                    tags=f"bar{i}")

            # Value on top
            canvas.create_text((x0 + x1) / 2, y0 - 6,
                                text=str(val),
                                font=("Segoe UI", 8, "bold"),
                                fill=TEAL_DARK if color == TEAL_ACCENT
                                else TEXT_MUTED)

            # Month label
            canvas.create_text((x0 + x1) / 2, ch - margin_b + 12,
                                text=month,
                                font=("Segoe UI", 8,
                                      "bold" if color == TEAL_ACCENT else "normal"),
                                fill=TEAL_DARK if color == TEAL_ACCENT
                                else TEXT_MUTED)

    # ── REPORT 3: Test Statistics ─────────────────────────────────────────────

    def _build_test_statistics(self, parent, name, desc, bg, fg):
        self._report_header(parent, name, desc, bg, fg)

        fc = self._card(parent)
        fc.pack(fill="x", pady=(0, 10))
        frow = tk.Frame(fc, bg=WHITE)
        frow.pack(fill="x", padx=14, pady=12)
        ctk.CTkLabel(frow, text="Period", font=("Segoe UI", 9),
                     text_color=TEXT_MUTED).pack(side="left")
        ctk.CTkComboBox(
            frow,
            values=["This Month", "Last 3 Months", "Last 6 Months", "This Year"],
            font=("Segoe UI", 10), height=32, width=160,
            corner_radius=6, border_color=BORDER,
            fg_color=WHITE, text_color=TEXT_MAIN
        ).pack(side="left", padx=(4, 14))
        self._solid_btn(frow, "Generate",
                        lambda: messagebox.showinfo(
                            "Report", "Test statistics generated.")
                        ).pack(side="left")
        self._export_btn(frow, "Export PDF",
                         lambda: self._export("PDF")).pack(side="left", padx=(8, 0))
        self._export_btn(frow, "Export Excel",
                         lambda: self._export("Excel")).pack(side="left", padx=(8, 0))

        # Category chips
        cats = tk.Frame(parent, bg=BG_LIGHT)
        cats.pack(fill="x", pady=(0, 10))
        cat_totals = {}
        for _, cat, count, _ in TEST_STATS:
            cat_totals[cat] = cat_totals.get(cat, 0) + count
        for cat, total in cat_totals.items():
            self._stat_card(cats, str(total), cat,
                            BLUE_BG, BLUE_FG)

        # Progress bar table
        tc = self._card(parent)
        tc.pack(fill="both", expand=True)
        tk.Label(tc, text="Top Tests This Period",
                 font=("Segoe UI", 10, "bold"),
                 bg=WHITE, fg=TEXT_MAIN).pack(anchor="w", padx=14, pady=(12, 0))
        tk.Frame(tc, bg=BORDER, height=1).pack(fill="x", padx=14, pady=8)

        max_count = TEST_STATS[0][2] if TEST_STATS else 1
        for i, (test, cat, count, pct) in enumerate(TEST_STATS):
            row_bg = WHITE if i % 2 == 0 else "#f8fafc"
            row = tk.Frame(tc, bg=row_bg)
            row.pack(fill="x", padx=14, pady=4)

            tk.Label(row, text=test,
                     font=("Segoe UI", 10, "bold"),
                     bg=row_bg, fg=TEXT_MAIN, width=30,
                     anchor="w").pack(side="left")
            tk.Label(row, text=cat,
                     font=("Segoe UI", 9),
                     bg=row_bg, fg=TEXT_MUTED, width=14,
                     anchor="w").pack(side="left")

            # Progress bar
            bar_outer = tk.Frame(row, bg=BORDER, height=8)
            bar_outer.pack(side="left", fill="x", expand=True,
                           padx=(8, 8))
            bar_outer.update_idletasks()
            bar_inner = tk.Frame(bar_outer, bg=TEAL_ACCENT, height=8)
            bar_inner.place(x=0, y=0,
                            relwidth=min(count / max_count, 1.0),
                            height=8)

            tk.Label(row, text=f"{count} tests",
                     font=("Segoe UI", 9, "bold"),
                     bg=row_bg, fg=TEAL_DARK, width=9,
                     anchor="e").pack(side="right")

    # ── REPORT 4: Revenue Report ──────────────────────────────────────────────

    def _build_revenue_report(self, parent, name, desc, bg, fg):
        self._report_header(parent, name, desc, bg, fg)

        fc = self._card(parent)
        fc.pack(fill="x", pady=(0, 10))
        frow = tk.Frame(fc, bg=WHITE)
        frow.pack(fill="x", padx=14, pady=12)
        ctk.CTkLabel(frow, text="Date From", font=("Segoe UI", 9),
                     text_color=TEXT_MUTED).pack(side="left")
        ctk.CTkEntry(frow, placeholder_text="2025-05-01",
                     font=("Segoe UI", 10), height=32, width=120,
                     corner_radius=6, border_color=BORDER,
                     fg_color=WHITE, text_color=TEXT_MAIN
                     ).pack(side="left", padx=(4, 14))
        ctk.CTkLabel(frow, text="Date To", font=("Segoe UI", 9),
                     text_color=TEXT_MUTED).pack(side="left")
        ctk.CTkEntry(frow, placeholder_text="2025-05-31",
                     font=("Segoe UI", 10), height=32, width=120,
                     corner_radius=6, border_color=BORDER,
                     fg_color=WHITE, text_color=TEXT_MAIN
                     ).pack(side="left", padx=(4, 14))
        self._solid_btn(frow, "Generate",
                        lambda: messagebox.showinfo(
                            "Report", "Revenue report generated.")
                        ).pack(side="left")
        self._export_btn(frow, "Export PDF",
                         lambda: self._export("PDF")).pack(side="left", padx=(8, 0))
        self._export_btn(frow, "Export Excel",
                         lambda: self._export("Excel")).pack(side="left", padx=(8, 0))

        # Stats
        sr = tk.Frame(parent, bg=BG_LIGHT)
        sr.pack(fill="x", pady=(0, 10))
        for val, lbl, sbg, sfg in [
            ("₱184,200", "Gross Revenue",     GREEN_BG, GREEN_FG),
            ("₱176,350", "Collected",         GREEN_BG, GREEN_FG),
            ("₱7,850",   "Uncollected",       RED_BG,   RED_FG),
            ("₱4,200",   "Total Discounts",   YELLOW_BG, YELLOW_FG),
            ("34",       "Transactions",      BLUE_BG,  BLUE_FG),
        ]:
            self._stat_card(sr, val, lbl, sbg, sfg)

        # Breakdown table
        tc = self._card(parent)
        tc.pack(fill="both", expand=True)
        tk.Label(tc, text="Revenue Breakdown — May 2025",
                 font=("Segoe UI", 10, "bold"),
                 bg=WHITE, fg=TEXT_MAIN).pack(anchor="w", padx=14, pady=(12, 0))
        tk.Frame(tc, bg=BORDER, height=1).pack(fill="x", padx=14, pady=8)

        breakdown = [
            ("Hematology",   "₱31,150",  "17%"),
            ("Chemistry",    "₱52,000",  "28%"),
            ("Radiology",    "₱62,000",  "34%"),
            ("Urinalysis",   "₱11,100",  "6%"),
            ("Cardiology",   "₱8,800",   "5%"),
            ("Others",       "₱19,150",  "10%"),
        ]
        for i, (cat, rev, pct) in enumerate(breakdown):
            row_bg = WHITE if i % 2 == 0 else "#f8fafc"
            row = tk.Frame(tc, bg=row_bg)
            row.pack(fill="x", padx=14)
            tk.Frame(tc, bg=BORDER, height=1).pack(fill="x", padx=14)
            tk.Label(row, text=cat,
                     font=("Segoe UI", 10), bg=row_bg,
                     fg=TEXT_MAIN, width=18, anchor="w",
                     pady=8).pack(side="left")
            tk.Label(row, text=rev,
                     font=("Segoe UI", 10, "bold"),
                     bg=row_bg, fg=GREEN_FG).pack(side="right", padx=(0, 14))
            tk.Label(row, text=pct,
                     font=("Segoe UI", 9),
                     bg=row_bg, fg=TEXT_MUTED).pack(side="right", padx=8)

    # ── REPORT 5: Unpaid Balances ─────────────────────────────────────────────

    def _build_unpaid_balances(self, parent, name, desc, bg, fg):
        self._report_header(parent, name, desc, bg, fg)

        fc = self._card(parent)
        fc.pack(fill="x", pady=(0, 10))
        frow = tk.Frame(fc, bg=WHITE)
        frow.pack(fill="x", padx=14, pady=12)
        ctk.CTkEntry(frow,
                     placeholder_text="Search patient name or ID...",
                     font=("Segoe UI", 10), height=32, width=250,
                     corner_radius=6, border_color=BORDER,
                     fg_color=WHITE, text_color=TEXT_MAIN
                     ).pack(side="left", padx=(0, 8))
        self._solid_btn(frow, "Search", lambda: None).pack(side="left")
        self._export_btn(frow, "Export PDF",
                         lambda: self._export("PDF")).pack(side="left", padx=(8, 0))
        self._export_btn(frow, "Export Excel",
                         lambda: self._export("Excel")).pack(side="left", padx=(8, 0))

        # Total unpaid chip
        total_unpaid = sum(
            float(r[4].replace("₱", "").replace(",", ""))
            for r in UNPAID_DATA)
        sr = tk.Frame(parent, bg=BG_LIGHT)
        sr.pack(fill="x", pady=(0, 10))
        self._stat_card(sr, str(len(UNPAID_DATA)), "Accounts",
                        RED_BG, RED_FG)
        self._stat_card(sr, f"₱{total_unpaid:,.2f}", "Total Owed",
                        RED_BG, RED_FG)

        # Table
        tc = self._card(parent)
        tc.pack(fill="both", expand=True)

        th = tk.Frame(tc, bg="#fff5f5")
        th.pack(fill="x")
        tk.Frame(tc, bg=BORDER, height=1).pack(fill="x")
        tk.Label(th, text="Outstanding Balances",
                 font=("Segoe UI", 10, "bold"),
                 bg="#fff5f5", fg=RED_FG).pack(
                     side="left", padx=14, pady=8)
        tk.Label(th, text=f"{len(UNPAID_DATA)} accounts",
                 font=("Segoe UI", 9),
                 bg="#fff5f5", fg=RED_FG).pack(side="right", padx=14)

        cols = ("Patient", "Patient ID", "Tests",
                "Visit Date", "Balance")
        widths = [160, 130, 200, 120, 100]
        tree, _ = self._styled_tree(tc, cols, widths)
        for i, row in enumerate(UNPAID_DATA):
            tree.insert("", "end", values=row,
                        tags=("even" if i % 2 == 0 else "odd",))
        tree.tag_configure("even", background=WHITE,  foreground=RED_FG)
        tree.tag_configure("odd",  background=RED_BG, foreground=RED_FG)

    # ── REPORT 6: Appointment History ─────────────────────────────────────────

    def _build_appointment_history(self, parent, name, desc, bg, fg):
        self._report_header(parent, name, desc, bg, fg)

        fc = self._card(parent)
        fc.pack(fill="x", pady=(0, 10))
        frow = tk.Frame(fc, bg=WHITE)
        frow.pack(fill="x", padx=14, pady=12)
        ctk.CTkLabel(frow, text="Date From", font=("Segoe UI", 9),
                     text_color=TEXT_MUTED).pack(side="left")
        ctk.CTkEntry(frow, placeholder_text="2025-05-01",
                     font=("Segoe UI", 10), height=32, width=120,
                     corner_radius=6, border_color=BORDER,
                     fg_color=WHITE, text_color=TEXT_MAIN
                     ).pack(side="left", padx=(4, 14))
        ctk.CTkLabel(frow, text="Date To", font=("Segoe UI", 9),
                     text_color=TEXT_MUTED).pack(side="left")
        ctk.CTkEntry(frow, placeholder_text="2025-05-31",
                     font=("Segoe UI", 10), height=32, width=120,
                     corner_radius=6, border_color=BORDER,
                     fg_color=WHITE, text_color=TEXT_MAIN
                     ).pack(side="left", padx=(4, 14))
        ctk.CTkComboBox(
            frow,
            values=["All Types", "By Appointment", "Walk-in"],
            font=("Segoe UI", 10), height=32, width=150,
            corner_radius=6, border_color=BORDER,
            fg_color=WHITE, text_color=TEXT_MAIN
        ).pack(side="left", padx=(0, 14))
        self._solid_btn(frow, "Generate",
                        lambda: messagebox.showinfo(
                            "Report", "Appointment history generated.")
                        ).pack(side="left")
        self._export_btn(frow, "Export PDF",
                         lambda: self._export("PDF")).pack(side="left", padx=(8, 0))
        self._export_btn(frow, "Export Excel",
                         lambda: self._export("Excel")).pack(side="left", padx=(8, 0))

        # Stats
        sr = tk.Frame(parent, bg=BG_LIGHT)
        sr.pack(fill="x", pady=(0, 10))
        for val, lbl, sbg, sfg in [
            ("6",  "Total",         BLUE_BG,   BLUE_FG),
            ("5",  "By Appt.",      GREEN_BG,  GREEN_FG),
            ("1",  "Walk-in",       PURPLE_BG, PURPLE_FG),
            ("6",  "Completed",     GREEN_BG,  GREEN_FG),
        ]:
            self._stat_card(sr, val, lbl, sbg, sfg)

        tc = self._card(parent)
        tc.pack(fill="both", expand=True)
        th = tk.Frame(tc, bg="#f8fafc")
        th.pack(fill="x")
        tk.Frame(tc, bg=BORDER, height=1).pack(fill="x")
        tk.Label(th, text="Appointment History",
                 font=("Segoe UI", 10, "bold"),
                 bg="#f8fafc", fg=TEXT_MAIN).pack(side="left", padx=14, pady=8)

        cols = ("Patient", "Patient ID", "Tests",
                "Date", "Time", "Type", "Status")
        widths = [140, 120, 170, 100, 70, 100, 80]
        tree, _ = self._styled_tree(tc, cols, widths)
        for i, row in enumerate(APPT_DATA):
            tree.insert("", "end", values=row,
                        tags=("even" if i % 2 == 0 else "odd",))
        tree.tag_configure("even", background=WHITE)
        tree.tag_configure("odd",  background="#f8fafc")

    # ── Shared helpers ─────────────────────────────────────────────────────────

    def _report_header(self, parent, name, desc, bg, fg):
        """Coloured section title banner."""
        hdr = tk.Frame(parent, bg=bg,
                       highlightbackground=BORDER,
                       highlightthickness=1)
        hdr.pack(fill="x", pady=(0, 10))
        tk.Label(hdr, text=name,
                 font=("Segoe UI", 12, "bold"),
                 bg=bg, fg=fg).pack(side="left", padx=14, pady=10)
        tk.Label(hdr, text=desc,
                 font=("Segoe UI", 9),
                 bg=bg, fg=fg).pack(side="left")

    def _stat_card(self, parent, value, label, bg, fg):
        chip = tk.Frame(parent, bg=bg,
                        highlightbackground=BORDER,
                        highlightthickness=1)
        chip.pack(side="left", padx=(0, 8), ipadx=6)
        tk.Label(chip, text=value,
                 font=("Segoe UI", 14, "bold"),
                 bg=bg, fg=fg).pack(padx=12, pady=(8, 2))
        tk.Label(chip, text=label,
                 font=("Segoe UI", 8),
                 bg=bg, fg=fg).pack(padx=12, pady=(0, 8))

    def _card(self, parent):
        return tk.Frame(parent, bg=WHITE,
                        highlightbackground=BORDER,
                        highlightthickness=1)

    def _styled_tree(self, parent, cols, widths):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Reports.Treeview",
                        background=WHITE, fieldbackground=WHITE,
                        foreground=TEXT_MAIN, rowheight=36,
                        font=("Segoe UI", 10))
        style.configure("Reports.Treeview.Heading",
                        background="#f8fafc", foreground=TEXT_MUTED,
                        font=("Segoe UI", 9, "bold"),
                        relief="flat", padding=6)
        style.map("Reports.Treeview",
                  background=[("selected", "#e0f2fe")],
                  foreground=[("selected", TEXT_MAIN)])

        tree = ttk.Treeview(parent, columns=cols,
                            show="headings",
                            style="Reports.Treeview")
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="w")

        vsb = ttk.Scrollbar(parent, orient="vertical",
                            command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        return tree, vsb

    def _solid_btn(self, parent, text, command):
        return tk.Button(parent, text=text, command=command,
                         font=("Segoe UI", 10, "bold"),
                         bg=TEAL_DARK, fg=WHITE,
                         activebackground=TEAL_MID,
                         relief="flat", cursor="hand2",
                         padx=14, pady=6)

    def _export_btn(self, parent, text, command):
        return tk.Button(parent, text=text, command=command,
                         font=("Segoe UI", 10),
                         bg=WHITE, fg=TEXT_MUTED,
                         activebackground=BG_LIGHT,
                         relief="flat", cursor="hand2",
                         padx=12, pady=6,
                         highlightbackground=BORDER,
                         highlightthickness=1)

    def _hdr_chip(self, parent, value, label, bg, fg):
        chip = tk.Frame(parent, bg=bg,
                        highlightbackground=BORDER,
                        highlightthickness=1)
        chip.pack(side="left", padx=4)
        tk.Label(chip, text=f"  {value}  {label}  ",
                 font=("Segoe UI", 9, "bold"),
                 bg=bg, fg=fg, pady=5).pack()

    def _generate_preview(self):
        messagebox.showinfo(
            "Report Generated",
            "Daily Patient Report has been generated.\n"
            "Preview updated below.")

    def _export(self, fmt):
        messagebox.showinfo(
            f"Export to {fmt}",
            f"Report exported as {fmt} successfully.\n"
            f"Check your Documents folder.")