# modules/billing.py
# ─────────────────────────────────────────────────────────────────────────────
#  PureHealth Diagnostic Center — Billing & Payments Module
#  Improved design using CustomTkinter
#  BUG FIXED: "New Bill" no longer stacks — clears the frame properly first
# ─────────────────────────────────────────────────────────────────────────────

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk

# ── Colour palette (matches PureHealth teal theme) ───────────────────────────
TEAL_DARK   = "#073b4c"
TEAL_MID    = "#0c637f"
TEAL_ACCENT = "#0cb0a9"
WHITE       = "#ffffff"
BG_LIGHT    = "#f4f6f8"
BG_CARD     = "#ffffff"
BORDER      = "#e2e8f0"
TEXT_MAIN   = "#1a202c"
TEXT_MUTED  = "#718096"
TEXT_HINT   = "#a0aec0"
GREEN_BG    = "#f0fff4"
GREEN_FG    = "#276749"
RED_BG      = "#fff5f5"
RED_FG      = "#c53030"
YELLOW_BG   = "#fffff0"
YELLOW_FG   = "#975a16"
BADGE_HEM   = ("#dbeafe", "#1e40af")   # bg, fg
BADGE_URI   = ("#fef9c3", "#854d0e")
BADGE_CHE   = ("#f3f4f6", "#374151")
BADGE_RAD   = ("#fee2e2", "#991b1b")
BADGE_CAR   = ("#ede9fe", "#5b21b6")


# ── Sample service catalogue (replace with real DB query later) ───────────────
SERVICES = [
    ("Complete Blood Count (CBC)", "Hematology",   "Same day",  350.00, BADGE_HEM),
    ("Urinalysis",                 "Urinalysis",   "2 hours",   150.00, BADGE_URI),
    ("Fasting Blood Sugar (FBS)", "Chemistry",     "Same day",  200.00, BADGE_CHE),
    ("Blood Chemistry Panel",     "Chemistry",     "Same day",  350.00, BADGE_CHE),
    ("Chest X-Ray PA",            "Radiology",     "1 hour",    450.00, BADGE_RAD),
    ("Ultrasound — OB",           "Radiology",     "Same day",  800.00, BADGE_RAD),
    ("Electrocardiogram (ECG)",   "Cardiology",    "30 mins",   400.00, BADGE_CAR),
    ("Blood Typing",              "Hematology",    "Same day",  180.00, BADGE_HEM),
    ("Lipid Profile",             "Chemistry",     "Same day",  450.00, BADGE_CHE),
    ("Thyroid Function (TSH)",    "Chemistry",     "1–2 days",  650.00, BADGE_CHE),
]

DISCOUNT_OPTIONS = {
    "None":                  0,
    "Senior Citizen (20%)": 20,
    "PWD (20%)":            20,
    "Employee (10%)":       10,
    "PhilHealth":            5,
}

# ── Mock patients (replace with real DB query later) ─────────────────────────
MOCK_PATIENTS = [
    {"id": "PHC-2025-00124", "name": "Juan dela Cruz",  "initials": "JC",
     "age": 35, "sex": "Male",   "unpaid": 0.00},
    {"id": "PHC-2025-00123", "name": "Ana Santos",      "initials": "AS",
     "age": 28, "sex": "Female", "unpaid": 0.00},
    {"id": "PHC-2025-00122", "name": "Pedro Bautista",  "initials": "PB",
     "age": 52, "sex": "Male",   "unpaid": 0.00},
    {"id": "PHC-2025-00118", "name": "Ben Torres",      "initials": "BT",
     "age": 44, "sex": "Male",   "unpaid": 850.00},
    {"id": "PHC-2025-00115", "name": "Clara Santos",    "initials": "CS",
     "age": 31, "sex": "Female", "unpaid": 450.00},
]


# ─────────────────────────────────────────────────────────────────────────────
class BillingModule:
# ─────────────────────────────────────────────────────────────────────────────

    def __init__(self, parent):
        self.parent = parent
        self._reset_state()

    # ── Internal state helpers ────────────────────────────────────────────────

    def _reset_state(self):
        """Reset all billing data to blank."""
        self.current_patient = None
        self.added_tests     = []        # list of (name, category, price, badge)
        self.subtotal        = 0.0
        self.discount_pct    = 0
        self.payment_var     = None      # set when widgets are built
        self.amount_var      = None

    # ── Entry point (called by MainDashboard._switch) ─────────────────────────

    def show(self):
        # ── FIX: destroy every widget in parent before rebuilding ─────────────
        for widget in self.parent.winfo_children():
            widget.destroy()

        self._reset_state()
        self._build_ui()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        self.parent.configure(bg=BG_LIGHT)

        # ── Page header bar ───────────────────────────────────────────────────
        header = tk.Frame(self.parent, bg=WHITE, pady=12)
        header.pack(fill="x", padx=0)
        tk.Frame(header, bg=BORDER, height=1).pack(fill="x", side="bottom")

        tk.Label(header, text="Billing & Payments",
                 font=("Segoe UI", 16, "bold"), bg=WHITE,
                 fg=TEXT_MAIN).pack(side="left", padx=20)
        tk.Label(header, text="Create bills, collect payments, print receipts",
                 font=("Segoe UI", 10), bg=WHITE,
                 fg=TEXT_MUTED).pack(side="left")

        btn_frame = tk.Frame(header, bg=WHITE)
        btn_frame.pack(side="right", padx=20)
        self._outline_btn(btn_frame, "Unpaid Balances",
                          self._show_unpaid).pack(side="left", padx=(0, 8))
        self._solid_btn(btn_frame, "+ New Bill",
                        self.show).pack(side="left")

        # ── Body: two-column layout ───────────────────────────────────────────
        body = tk.Frame(self.parent, bg=BG_LIGHT)
        body.pack(fill="both", expand=True, padx=18, pady=14)

        # Left column (patient + tests)
        left = tk.Frame(body, bg=BG_LIGHT)
        left.pack(side="left", fill="both", expand=True, padx=(0, 12))

        # Right column (payment summary — fixed width)
        right = tk.Frame(body, bg=BG_LIGHT, width=290)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        self._build_patient_section(left)
        self._build_tests_section(left)
        self._build_payment_panel(right)

    # ── Patient section ───────────────────────────────────────────────────────

    def _build_patient_section(self, parent):
        card = self._card(parent)
        card.pack(fill="x", pady=(0, 10))

        # Section label
        tk.Label(card, text="PATIENT", font=("Segoe UI", 9, "bold"),
                 bg=WHITE, fg=TEXT_MUTED).pack(anchor="w", padx=16, pady=(14, 6))

        # Search row
        search_row = tk.Frame(card, bg=WHITE)
        search_row.pack(fill="x", padx=16, pady=(0, 10))

        self.search_entry = ctk.CTkEntry(
            search_row, placeholder_text="Search by name or patient ID...",
            font=("Segoe UI", 12), height=36, corner_radius=8,
            border_color=BORDER, fg_color=WHITE, text_color=TEXT_MAIN)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.search_entry.bind("<Return>", lambda e: self._search_patient())

        self._solid_btn(search_row, "Search",
                        self._search_patient).pack(side="left")

        # Patient display area (swaps between hint and chip)
        self.patient_display = tk.Frame(card, bg=WHITE)
        self.patient_display.pack(fill="x", padx=16, pady=(0, 14))
        self._show_patient_hint()

    def _show_patient_hint(self):
        for w in self.patient_display.winfo_children():
            w.destroy()
        hint = tk.Frame(self.patient_display, bg="#f8fafc",
                        highlightbackground=BORDER, highlightthickness=1)
        hint.pack(fill="x")
        tk.Label(hint, text="No patient selected. Search above to find a patient.",
                 font=("Segoe UI", 10), bg="#f8fafc", fg=TEXT_HINT,
                 pady=12).pack()

    def _show_patient_chip(self, patient):
        for w in self.patient_display.winfo_children():
            w.destroy()

        chip = tk.Frame(self.patient_display, bg="#f0f9ff",
                        highlightbackground="#bae6fd", highlightthickness=1)
        chip.pack(fill="x")

        inner = tk.Frame(chip, bg="#f0f9ff")
        inner.pack(fill="x", padx=12, pady=10)

        # Avatar circle (simulated with a label)
        av = tk.Label(inner, text=patient["initials"],
                      font=("Segoe UI", 11, "bold"),
                      bg=TEAL_ACCENT, fg=WHITE, width=3, height=1,
                      relief="flat")
        av.pack(side="left", padx=(0, 10))

        info = tk.Frame(inner, bg="#f0f9ff")
        info.pack(side="left", fill="x", expand=True)
        tk.Label(info, text=patient["name"],
                 font=("Segoe UI", 12, "bold"),
                 bg="#f0f9ff", fg=TEXT_MAIN).pack(anchor="w")
        tk.Label(info,
                 text=f"{patient['id']}  ·  {patient['age']} y/o  ·  {patient['sex']}",
                 font=("Segoe UI", 9), bg="#f0f9ff", fg=TEXT_MUTED).pack(anchor="w")

        # Clear button
        tk.Button(inner, text="✕", font=("Segoe UI", 10),
                  bg="#f0f9ff", fg=TEXT_MUTED, bd=0, cursor="hand2",
                  command=self._clear_patient).pack(side="right")

        # Unpaid warning
        if patient.get("unpaid", 0) > 0:
            warn = tk.Frame(self.patient_display, bg=YELLOW_BG,
                            highlightbackground="#f6e05e", highlightthickness=1)
            warn.pack(fill="x", pady=(4, 0))
            tk.Label(warn,
                     text=f"⚠  This patient has an existing unpaid balance of "
                          f"₱{patient['unpaid']:,.2f}",
                     font=("Segoe UI", 9), bg=YELLOW_BG, fg=YELLOW_FG,
                     pady=7, padx=12).pack(anchor="w")

    def _search_patient(self):
        query = self.search_entry.get().strip().lower()
        if not query:
            messagebox.showwarning("Search", "Please enter a name or patient ID.")
            return
        found = next((p for p in MOCK_PATIENTS
                      if query in p["name"].lower()
                      or query in p["id"].lower()), None)
        if found:
            self.current_patient = found
            self._show_patient_chip(found)
        else:
            messagebox.showinfo("Not Found",
                                f"No patient found matching \"{query}\".\n"
                                "Make sure the patient is registered first.")

    def _clear_patient(self):
        self.current_patient = None
        self.search_entry.delete(0, "end")
        self._show_patient_hint()

    # ── Tests section ─────────────────────────────────────────────────────────

    def _build_tests_section(self, parent):
        card = self._card(parent)
        card.pack(fill="both", expand=True)

        # Header row
        hdr = tk.Frame(card, bg=WHITE)
        hdr.pack(fill="x", padx=16, pady=(14, 8))
        tk.Label(hdr, text="REQUESTED TESTS",
                 font=("Segoe UI", 9, "bold"),
                 bg=WHITE, fg=TEXT_MUTED).pack(side="left")
        self._solid_btn(hdr, "+ Add Test",
                        self._open_add_test).pack(side="right")

        # Treeview (table)
        table_frame = tk.Frame(card, bg=WHITE)
        table_frame.pack(fill="both", expand=True, padx=16, pady=(0, 14))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Billing.Treeview",
                        background=WHITE, fieldbackground=WHITE,
                        foreground=TEXT_MAIN, rowheight=36,
                        font=("Segoe UI", 10))
        style.configure("Billing.Treeview.Heading",
                        background="#f8fafc", foreground=TEXT_MUTED,
                        font=("Segoe UI", 9, "bold"), relief="flat", padding=6)
        style.map("Billing.Treeview",
                  background=[("selected", "#e0f2fe")],
                  foreground=[("selected", TEXT_MAIN)])

        cols = ("test", "category", "price", "action")
        self.test_tree = ttk.Treeview(table_frame, columns=cols,
                                      show="headings", style="Billing.Treeview")
        self.test_tree.heading("test",     text="Test / Service")
        self.test_tree.heading("category", text="Category")
        self.test_tree.heading("price",    text="Price")
        self.test_tree.heading("action",   text="")
        self.test_tree.column("test",     width=320, anchor="w")
        self.test_tree.column("category", width=130, anchor="w")
        self.test_tree.column("price",    width=90,  anchor="e")
        self.test_tree.column("action",   width=80,  anchor="center")

        sb = ttk.Scrollbar(table_frame, orient="vertical",
                           command=self.test_tree.yview)
        self.test_tree.configure(yscrollcommand=sb.set)
        self.test_tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # Hint label (shown when no tests added)
        self.tests_hint = tk.Label(card,
                                   text="No tests added yet. Click \"+ Add Test\" to begin.",
                                   font=("Segoe UI", 10), bg=WHITE, fg=TEXT_HINT, pady=10)
        self.tests_hint.pack()

        # Remove button below table
        remove_row = tk.Frame(card, bg=WHITE)
        remove_row.pack(fill="x", padx=16, pady=(0, 10))
        self._outline_btn(remove_row, "Remove Selected",
                          self._remove_selected_test,
                          danger=True).pack(side="right")

    def _open_add_test(self):
        """Open a pop-up to choose a test from the catalogue."""
        win = tk.Toplevel(self.parent)
        win.title("Add Test / Service")
        win.geometry("520x460")
        win.resizable(False, False)
        win.grab_set()
        win.configure(bg=WHITE)

        # Header
        hdr = tk.Frame(win, bg=TEAL_DARK, pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Add Test / Service",
                 font=("Segoe UI", 13, "bold"),
                 bg=TEAL_DARK, fg=WHITE).pack(side="left", padx=16)
        tk.Button(hdr, text="✕ Close", font=("Segoe UI", 9),
                  bg=TEAL_DARK, fg=WHITE, bd=0, cursor="hand2",
                  command=win.destroy).pack(side="right", padx=16)

        # Search bar
        search_var = tk.StringVar()
        search_frame = tk.Frame(win, bg=WHITE, pady=10)
        search_frame.pack(fill="x", padx=16)
        ctk.CTkEntry(search_frame,
                     placeholder_text="Search test name...",
                     textvariable=search_var,
                     font=("Segoe UI", 11), height=34,
                     corner_radius=8, border_color=BORDER,
                     fg_color=WHITE, text_color=TEXT_MAIN
                     ).pack(fill="x")

        # Scrollable list
        list_frame = tk.Frame(win, bg=WHITE)
        list_frame.pack(fill="both", expand=True, padx=16, pady=(0, 14))

        canvas = tk.Canvas(list_frame, bg=WHITE, highlightthickness=0)
        sb = ttk.Scrollbar(list_frame, orient="vertical",
                           command=canvas.yview)
        self.service_inner = tk.Frame(canvas, bg=WHITE)
        self.service_inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.service_inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        def render_list(filter_text=""):
            for w in self.service_inner.winfo_children():
                w.destroy()
            for name, cat, turn, price, badge in SERVICES:
                if filter_text and filter_text.lower() not in name.lower() \
                        and filter_text.lower() not in cat.lower():
                    continue
                self._service_row(self.service_inner, name, cat,
                                  turn, price, badge, win)

        render_list()
        search_var.trace_add("write",
                             lambda *_: render_list(search_var.get()))

    def _service_row(self, parent, name, cat, turn, price, badge, win):
        """One clickable row in the Add Test popup."""
        bg_badge, fg_badge = badge
        row = tk.Frame(parent, bg=WHITE, cursor="hand2",
                       highlightbackground=BORDER, highlightthickness=1)
        row.pack(fill="x", pady=3)

        inner = tk.Frame(row, bg=WHITE)
        inner.pack(fill="x", padx=12, pady=8)

        left = tk.Frame(inner, bg=WHITE)
        left.pack(side="left", fill="x", expand=True)
        tk.Label(left, text=name, font=("Segoe UI", 11, "bold"),
                 bg=WHITE, fg=TEXT_MAIN).pack(anchor="w")
        meta = tk.Frame(left, bg=WHITE)
        meta.pack(anchor="w", pady=(2, 0))
        tk.Label(meta, text=cat, font=("Segoe UI", 9, "bold"),
                 bg=bg_badge, fg=fg_badge,
                 padx=6, pady=1).pack(side="left")
        tk.Label(meta, text=f"  ·  {turn}",
                 font=("Segoe UI", 9), bg=WHITE,
                 fg=TEXT_MUTED).pack(side="left")

        tk.Label(inner, text=f"₱{price:,.2f}",
                 font=("Segoe UI", 11, "bold"),
                 bg=WHITE, fg=TEAL_MID).pack(side="right")

        # Hover effect
        def on_enter(e):
            row.configure(bg="#f0f9ff")
            for w in row.winfo_descendants():
                try:
                    if w.cget("bg") == WHITE:
                        w.configure(bg="#f0f9ff")
                except Exception:
                    pass

        def on_leave(e):
            row.configure(bg=WHITE)
            for w in row.winfo_descendants():
                try:
                    if w.cget("bg") == "#f0f9ff":
                        w.configure(bg=WHITE)
                except Exception:
                    pass

        def on_click(e, n=name, c=cat, p=price, b=badge):
            self._add_test(n, c, p, b)
            win.destroy()

        for widget in [row, inner, left, meta] + inner.winfo_children() + left.winfo_children():
            try:
                widget.bind("<Enter>", on_enter)
                widget.bind("<Leave>", on_leave)
                widget.bind("<Button-1>", on_click)
            except Exception:
                pass

    def _add_test(self, name, category, price, badge):
        # Prevent duplicate
        existing = [t[0] for t in self.added_tests]
        if name in existing:
            messagebox.showinfo("Already Added",
                                f'"{name}" is already in the bill.')
            return
        self.added_tests.append((name, category, price, badge))
        iid = self.test_tree.insert(
            "", "end",
            values=(name, category, f"₱{price:,.2f}", ""))
        # Colour alternate rows
        tag = "even" if len(self.added_tests) % 2 == 0 else "odd"
        self.test_tree.item(iid, tags=(tag,))
        self.test_tree.tag_configure("even", background="#f8fafc")
        self.test_tree.tag_configure("odd",  background=WHITE)

        self.subtotal += price
        self.tests_hint.pack_forget()
        self._update_summary()

    def _remove_selected_test(self):
        sel = self.test_tree.selection()
        if not sel:
            messagebox.showwarning("Remove Test",
                                   "Please select a test row to remove first.")
            return
        for iid in sel:
            vals = self.test_tree.item(iid, "values")
            test_name = vals[0]
            self.added_tests = [t for t in self.added_tests
                                if t[0] != test_name]
            price_str = vals[2].replace("₱", "").replace(",", "")
            self.subtotal = max(0.0, self.subtotal - float(price_str))
            self.test_tree.delete(iid)

        if not self.added_tests:
            self.tests_hint.pack()
        self._update_summary()

    # ── Payment panel ─────────────────────────────────────────────────────────

    def _build_payment_panel(self, parent):
        card = self._card(parent)
        card.pack(fill="both", expand=True)

        pad = {"padx": 16}

        tk.Label(card, text="PAYMENT SUMMARY",
                 font=("Segoe UI", 9, "bold"),
                 bg=WHITE, fg=TEXT_MUTED).pack(anchor="w", pady=(14, 10), **pad)

        # ── Subtotal ──────────────────────────────────────────────────────────
        self._summary_row(card, "Subtotal", "subtotal_lbl", "₱0.00")
        tk.Frame(card, bg=BORDER, height=1).pack(fill="x", padx=16, pady=8)

        # ── Discount ──────────────────────────────────────────────────────────
        tk.Label(card, text="Discount",
                 font=("Segoe UI", 10), bg=WHITE,
                 fg=TEXT_MUTED).pack(anchor="w", **pad)

        self.discount_var = tk.StringVar(value="None")
        disc_combo = ctk.CTkComboBox(
            card,
            values=list(DISCOUNT_OPTIONS.keys()),
            variable=self.discount_var,
            font=("Segoe UI", 10), height=32,
            corner_radius=6, border_color=BORDER,
            fg_color=WHITE, text_color=TEXT_MAIN,
            command=self._on_discount_change)
        disc_combo.pack(fill="x", padx=16, pady=(4, 0))

        self.discount_row = tk.Frame(card, bg=WHITE)
        self.discount_row.pack(fill="x", padx=16, pady=(4, 0))
        tk.Label(self.discount_row, text="Discount amount:",
                 font=("Segoe UI", 9), bg=WHITE, fg=TEXT_MUTED).pack(side="left")
        self.discount_lbl = tk.Label(self.discount_row, text="— ₱0.00",
                                     font=("Segoe UI", 9, "bold"),
                                     bg=WHITE, fg=GREEN_FG)
        self.discount_lbl.pack(side="right")
        self.discount_row.pack_forget()   # hidden until a discount is chosen

        tk.Frame(card, bg=BORDER, height=1).pack(fill="x", padx=16, pady=8)

        # ── Total ─────────────────────────────────────────────────────────────
        total_row = tk.Frame(card, bg=WHITE)
        total_row.pack(fill="x", **pad)
        tk.Label(total_row, text="Total",
                 font=("Segoe UI", 13, "bold"),
                 bg=WHITE, fg=TEXT_MAIN).pack(side="left")
        self.total_lbl = tk.Label(total_row, text="₱0.00",
                                  font=("Segoe UI", 16, "bold"),
                                  bg=WHITE, fg=TEAL_DARK)
        self.total_lbl.pack(side="right")

        tk.Frame(card, bg=BORDER, height=1).pack(fill="x", padx=16, pady=10)

        # ── Payment method ────────────────────────────────────────────────────
        tk.Label(card, text="Payment Method",
                 font=("Segoe UI", 10, "bold"),
                 bg=WHITE, fg=TEXT_MAIN).pack(anchor="w", **pad)

        self.payment_var = tk.StringVar(value="Cash")
        method_row = tk.Frame(card, bg=WHITE)
        method_row.pack(fill="x", padx=16, pady=(6, 0))
        method_row.columnconfigure(0, weight=1)
        method_row.columnconfigure(1, weight=1)

        self.cash_btn  = self._method_btn(method_row, "Cash",  "Cash",  0)
        self.gcash_btn = self._method_btn(method_row, "Online", "Online", 1)
        self._highlight_method("Cash")

        tk.Frame(card, bg=BORDER, height=1).pack(fill="x", padx=16, pady=10)

        # ── Amount received ───────────────────────────────────────────────────
        tk.Label(card, text="Amount Received",
                 font=("Segoe UI", 10), bg=WHITE,
                 fg=TEXT_MUTED).pack(anchor="w", **pad)

        self.amount_entry = ctk.CTkEntry(
            card, placeholder_text="₱0.00",
            font=("Segoe UI", 13), height=38, corner_radius=8,
            border_color=BORDER, fg_color=WHITE, text_color=TEXT_MAIN,
            justify="right")
        self.amount_entry.pack(fill="x", padx=16, pady=(4, 0))
        self.amount_entry.bind("<KeyRelease>", lambda e: self._calc_change())

        # Change display
        self.change_frame = tk.Frame(card, bg=GREEN_BG,
                                     highlightbackground="#9ae6b4",
                                     highlightthickness=1)
        self.change_frame.pack(fill="x", padx=16, pady=(6, 0))
        change_inner = tk.Frame(self.change_frame, bg=GREEN_BG)
        change_inner.pack(fill="x", padx=10, pady=7)
        tk.Label(change_inner, text="Change",
                 font=("Segoe UI", 10), bg=GREEN_BG,
                 fg=GREEN_FG).pack(side="left")
        self.change_lbl = tk.Label(change_inner, text="₱0.00",
                                   font=("Segoe UI", 11, "bold"),
                                   bg=GREEN_BG, fg=GREEN_FG)
        self.change_lbl.pack(side="right")
        self.change_frame.pack_forget()

        tk.Frame(card, bg=BORDER, height=1).pack(fill="x", padx=16, pady=10)

        # ── Action buttons ────────────────────────────────────────────────────
        self._solid_btn(card, "Process Payment & Print Receipt",
                        self._process_payment,
                        wide=True).pack(fill="x", padx=16)
        self._outline_btn(card, "Save as Unpaid Balance",
                          self._save_unpaid).pack(fill="x", padx=16, pady=(6, 4))

        tk.Label(card,
                 text="Official receipt auto-prints after processing",
                 font=("Segoe UI", 8), bg=WHITE,
                 fg=TEXT_HINT).pack(pady=(0, 14))

    def _method_btn(self, parent, label, value, col):
        f = tk.Frame(parent, cursor="hand2",
                     highlightbackground=BORDER, highlightthickness=1)
        f.grid(row=0, column=col, sticky="ew",
               padx=(0, 4) if col == 0 else (4, 0))
        tk.Label(f, text=label, font=("Segoe UI", 11, "bold"),
                 bg=WHITE, fg=TEXT_MAIN, pady=7).pack()
        f.bind("<Button-1>",
               lambda e, v=value: self._select_method(v))
        f.winfo_children()[0].bind(
            "<Button-1>", lambda e, v=value: self._select_method(v))
        return f

    def _select_method(self, value):
        self.payment_var.set(value)
        self._highlight_method(value)

    def _highlight_method(self, active):
        for btn, val in [(self.cash_btn, "Cash"),
                         (self.gcash_btn, "Online")]:
            if val == active:
                btn.configure(bg="#e0f2fe",
                              highlightbackground=TEAL_ACCENT,
                              highlightthickness=2)
                btn.winfo_children()[0].configure(bg="#e0f2fe",
                                                  fg=TEAL_DARK)
            else:
                btn.configure(bg=WHITE,
                              highlightbackground=BORDER,
                              highlightthickness=1)
                btn.winfo_children()[0].configure(bg=WHITE,
                                                  fg=TEXT_MAIN)

    # ── Summary helpers ───────────────────────────────────────────────────────

    def _summary_row(self, parent, label_text, attr, initial):
        row = tk.Frame(parent, bg=WHITE)
        row.pack(fill="x", padx=16, pady=2)
        tk.Label(row, text=label_text, font=("Segoe UI", 10),
                 bg=WHITE, fg=TEXT_MUTED).pack(side="left")
        lbl = tk.Label(row, text=initial, font=("Segoe UI", 10),
                       bg=WHITE, fg=TEXT_MAIN)
        lbl.pack(side="right")
        setattr(self, attr, lbl)

    def _update_summary(self):
        discount_amt = self.subtotal * (self.discount_pct / 100)
        total        = max(0.0, self.subtotal - discount_amt)

        self.subtotal_lbl.configure(text=f"₱{self.subtotal:,.2f}")
        self.total_lbl.configure(text=f"₱{total:,.2f}")

        if self.discount_pct > 0:
            self.discount_row.pack(fill="x", padx=16, pady=(4, 0))
            self.discount_lbl.configure(
                text=f"— ₱{discount_amt:,.2f}")
        else:
            self.discount_row.pack_forget()

        self._calc_change()

    def _on_discount_change(self, choice):
        self.discount_pct = DISCOUNT_OPTIONS.get(choice, 0)
        self._update_summary()

    def _calc_change(self):
        try:
            total_str = self.total_lbl.cget("text").replace("₱", "").replace(",", "")
            total     = float(total_str)
            amt_str   = self.amount_entry.get().replace("₱", "").replace(",", "")
            received  = float(amt_str)
        except (ValueError, AttributeError):
            self.change_frame.pack_forget()
            return

        change = received - total
        self.change_frame.pack(fill="x", padx=16, pady=(6, 0))

        if change >= 0:
            # Enough — green
            self.change_frame.configure(bg=GREEN_BG,
                                        highlightbackground="#9ae6b4")
            for w in self.change_frame.winfo_descendants():
                try:
                    w.configure(bg=GREEN_BG)
                except Exception:
                    pass
            self.change_lbl.configure(text=f"₱{change:,.2f}", fg=GREEN_FG)
            for w in self.change_frame.winfo_children():
                try:
                    w.winfo_children()[0].configure(fg=GREEN_FG)
                except Exception:
                    pass
        else:
            # Short — red
            self.change_frame.configure(bg=RED_BG,
                                        highlightbackground="#feb2b2")
            for w in self.change_frame.winfo_descendants():
                try:
                    w.configure(bg=RED_BG)
                except Exception:
                    pass
            self.change_lbl.configure(
                text=f"Short by ₱{abs(change):,.2f}", fg=RED_FG)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _process_payment(self):
        if not self.current_patient:
            messagebox.showwarning("No Patient",
                                   "Please search and select a patient first.")
            return
        if not self.added_tests:
            messagebox.showwarning("No Tests",
                                   "Please add at least one test to the bill.")
            return
        total_str = self.total_lbl.cget("text")
        method    = self.payment_var.get()
        name      = self.current_patient["name"]
        pid       = self.current_patient["id"]
        messagebox.showinfo(
            "Payment Processed ✓",
            f"Payment processed successfully!\n\n"
            f"Patient : {name}\n"
            f"ID      : {pid}\n"
            f"Total   : {total_str}\n"
            f"Method  : {method}\n\n"
            f"Official receipt has been sent to the printer.")
        self.show()    # reset for next bill — safe because show() clears first

    def _save_unpaid(self):
        if not self.current_patient:
            messagebox.showwarning("No Patient",
                                   "Please search and select a patient first.")
            return
        if not self.added_tests:
            messagebox.showwarning("No Tests",
                                   "Please add at least one test to the bill.")
            return
        total_str = self.total_lbl.cget("text")
        name      = self.current_patient["name"]
        messagebox.showinfo(
            "Saved as Unpaid",
            f"Bill saved as an unpaid balance.\n\n"
            f"Patient : {name}\n"
            f"Amount  : {total_str}\n\n"
            f"You can collect this later under \"Unpaid Balances\".")

    def _show_unpaid(self):
        win = tk.Toplevel(self.parent)
        win.title("Unpaid Balances")
        win.geometry("580x360")
        win.grab_set()
        win.configure(bg=WHITE)

        tk.Frame(win, bg=TEAL_DARK, height=50).pack(fill="x")
        tk.Label(win, text="Unpaid Balances",
                 font=("Segoe UI", 13, "bold"),
                 bg=TEAL_DARK, fg=WHITE).place(x=16, y=14)

        cols = ("Patient", "ID", "Amount")
        tree = ttk.Treeview(win, columns=cols, show="headings", height=10)
        for col in cols:
            tree.heading(col, text=col)
        tree.column("Patient", width=200)
        tree.column("ID",      width=150)
        tree.column("Amount",  width=120, anchor="e")

        for p in MOCK_PATIENTS:
            if p["unpaid"] > 0:
                tree.insert("", "end",
                            values=(p["name"], p["id"],
                                    f"₱{p['unpaid']:,.2f}"))
        tree.pack(fill="both", expand=True, padx=16, pady=(60, 16))
        ttk.Button(win, text="Close",
                   command=win.destroy).pack(pady=(0, 14))

    # ── Widget factory helpers ─────────────────────────────────────────────────

    def _card(self, parent):
        f = tk.Frame(parent, bg=WHITE,
                     highlightbackground=BORDER, highlightthickness=1)
        return f

    def _solid_btn(self, parent, text, command, wide=False):
        w = 0 if not wide else None
        return tk.Button(parent, text=text, command=command,
                         font=("Segoe UI", 10, "bold"),
                         bg=TEAL_DARK, fg=WHITE, activebackground=TEAL_MID,
                         activeforeground=WHITE, relief="flat",
                         cursor="hand2", padx=14, pady=7, width=w)

    def _outline_btn(self, parent, text, command, danger=False):
        fg = RED_FG if danger else TEXT_MUTED
        return tk.Button(parent, text=text, command=command,
                         font=("Segoe UI", 10),
                         bg=WHITE, fg=fg,
                         activebackground=BG_LIGHT,
                         relief="flat", bd=0, cursor="hand2",
                         padx=14, pady=6)