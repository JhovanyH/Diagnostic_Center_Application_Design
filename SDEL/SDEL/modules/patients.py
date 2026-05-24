# modules/patients.py
# ─────────────────────────────────────────────────────────────────────────────
#  PureHealth Diagnostic Center — Patients Module
#  CONNECTED TO DATABASE — data saves and loads from purehealthDb.db
#  BUG FIXED: show() clears frame before rebuilding — no stacking
# ─────────────────────────────────────────────────────────────────────────────

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from datetime import datetime, date
from database import db

# ── Colour palette ────────────────────────────────────────────────────────────
TEAL_DARK  = "#073b4c"
TEAL_MID   = "#0c637f"
TEAL_ACCENT= "#0cb0a9"
WHITE      = "#ffffff"
BG_LIGHT   = "#f4f6f8"
BORDER     = "#e2e8f0"
TEXT_MAIN  = "#1a202c"
TEXT_MUTED = "#718096"
TEXT_HINT  = "#a0aec0"
GREEN_BG   = "#f0fff4"
GREEN_FG   = "#065f46"
RED_BG     = "#fff5f5"
RED_FG     = "#c53030"
YELLOW_BG  = "#fffff0"
YELLOW_FG  = "#975a16"
BLUE_BG    = "#dbeafe"
BLUE_FG    = "#1e40af"


# ─────────────────────────────────────────────────────────────────────────────
class PatientsModule:
# ─────────────────────────────────────────────────────────────────────────────

    def __init__(self, parent):
        self.parent = parent

    # ── Entry point ───────────────────────────────────────────────────────────

    def show(self):
        # FIX: clear old widgets before rebuilding — no stacking
        for w in self.parent.winfo_children():
            w.destroy()
        self.parent.configure(bg=BG_LIGHT)
        self._build_ui()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Page header ───────────────────────────────────────────────────────
        header = tk.Frame(self.parent, bg=WHITE)
        header.pack(fill="x")
        tk.Frame(header, bg=BORDER, height=1).pack(fill="x", side="bottom")

        title_block = tk.Frame(header, bg=WHITE)
        title_block.pack(side="left", padx=20, pady=12)
        tk.Label(title_block, text="Patient Management",
                 font=("Segoe UI", 16, "bold"),
                 bg=WHITE, fg=TEXT_MAIN).pack(anchor="w")
        tk.Label(title_block,
                 text="Register new patients and manage existing records",
                 font=("Segoe UI", 10),
                 bg=WHITE, fg=TEXT_MUTED).pack(anchor="w")

        btn_frame = tk.Frame(header, bg=WHITE)
        btn_frame.pack(side="right", padx=20)
        self._solid_btn(btn_frame, "+ Register New Patient",
                        self._open_register_form).pack()

        # ── Search bar ────────────────────────────────────────────────────────
        search_card = self._card(self.parent)
        search_card.pack(fill="x", padx=18, pady=(12, 0))

        search_row = tk.Frame(search_card, bg=WHITE)
        search_row.pack(fill="x", padx=14, pady=12)

        self.search_entry = ctk.CTkEntry(
            search_row,
            placeholder_text="Search by name or patient ID...",
            font=("Segoe UI", 11), height=34, corner_radius=8,
            border_color=BORDER, fg_color=WHITE, text_color=TEXT_MAIN)
        self.search_entry.pack(side="left", fill="x",
                               expand=True, padx=(0, 8))
        self.search_entry.bind("<Return>",
                               lambda e: self._search_patients())

        tk.Button(search_row, text="Search",
                  command=self._search_patients,
                  font=("Segoe UI", 10, "bold"),
                  bg=TEAL_DARK, fg=WHITE,
                  activebackground=TEAL_MID,
                  relief="flat", cursor="hand2",
                  padx=14, pady=6).pack(side="left", padx=(0, 6))

        tk.Button(search_row, text="Show All",
                  command=self._load_patients,
                  font=("Segoe UI", 10),
                  bg=WHITE, fg=TEXT_MUTED,
                  relief="flat", cursor="hand2",
                  padx=10, pady=6).pack(side="left")

        # ── Patients table ────────────────────────────────────────────────────
        table_card = self._card(self.parent)
        table_card.pack(fill="both", expand=True,
                        padx=18, pady=10)

        # Table header
        tbl_hdr = tk.Frame(table_card, bg="#f8fafc")
        tbl_hdr.pack(fill="x")
        tk.Frame(table_card, bg=BORDER, height=1).pack(fill="x")
        tk.Label(tbl_hdr, text="All Patients",
                 font=("Segoe UI", 10, "bold"),
                 bg="#f8fafc", fg=TEXT_MAIN).pack(
                     side="left", padx=14, pady=8)
        self.count_lbl = tk.Label(tbl_hdr, text="",
                                  font=("Segoe UI", 9),
                                  bg="#f8fafc", fg=TEXT_MUTED)
        self.count_lbl.pack(side="right", padx=14)

        # Treeview style
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Patients.Treeview",
                        background=WHITE,
                        fieldbackground=WHITE,
                        foreground=TEXT_MAIN,
                        rowheight=36,
                        font=("Segoe UI", 10))
        style.configure("Patients.Treeview.Heading",
                        background="#f8fafc",
                        foreground=TEXT_MUTED,
                        font=("Segoe UI", 9, "bold"),
                        relief="flat", padding=8)
        style.map("Patients.Treeview",
                  background=[("selected", "#e0f2fe")],
                  foreground=[("selected", TEXT_MAIN)])

        cols = ("code", "name", "age", "sex",
                "contact", "last_visit", "balance", "status")
        self.tree = ttk.Treeview(
            table_card, columns=cols,
            show="headings", style="Patients.Treeview")

        headers = {
            "code":       ("Patient ID",   130),
            "name":       ("Full Name",    200),
            "age":        ("Age",           50),
            "sex":        ("Sex",           60),
            "contact":    ("Contact",      140),
            "last_visit": ("Registered",   130),
            "balance":    ("Unpaid Bal.",  100),
            "status":     ("Status",        80),
        }
        for col, (label, width) in headers.items():
            self.tree.heading(col, text=label)
            anchor = "e" if col == "balance" else \
                     "center" if col in ("age","sex","status") else "w"
            self.tree.column(col, width=width, anchor=anchor)

        vsb = ttk.Scrollbar(table_card, orient="vertical",
                            command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # Double-click → view patient detail
        self.tree.bind("<Double-1>", self._on_row_double_click)

        # ── Bottom action bar ─────────────────────────────────────────────────
        action_bar = tk.Frame(self.parent, bg=BG_LIGHT)
        action_bar.pack(fill="x", padx=18, pady=(0, 14))
        tk.Label(action_bar,
                 text="Double-click a patient to view full profile",
                 font=("Segoe UI", 9),
                 bg=BG_LIGHT, fg=TEXT_HINT).pack(side="left")
        tk.Button(action_bar, text="View Profile",
                  command=self._view_selected,
                  font=("Segoe UI", 10, "bold"),
                  bg=TEAL_DARK, fg=WHITE,
                  activebackground=TEAL_MID,
                  relief="flat", cursor="hand2",
                  padx=14, pady=6).pack(side="right")

        # Load all patients on open
        self._load_patients()

    # ── Database operations ───────────────────────────────────────────────────

    def _load_patients(self):
        """Load all patients from the database into the table."""
        rows = db.get_all_patients()
        self._populate_table(rows)

    def _search_patients(self):
        query = self.search_entry.get().strip()
        if not query:
            self._load_patients()
            return
        rows = db.search_patients(query)
        self._populate_table(rows)
        if not rows:
            messagebox.showinfo(
                "No Results",
                f"No patients found matching \"{query}\".")

    def _populate_table(self, rows):
        """Clear the treeview and fill it with the given rows."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        for i, row in enumerate(rows):
            # Calculate age from birthdate
            age = self._calc_age(row["birthdate"])

            # Get unpaid balance
            unpaid = db.get_patient_unpaid_total(row["id"])
            balance_str = f"₱{unpaid:,.2f}" if unpaid > 0 else "—"

            # Format registered date (show only the date part)
            reg_date = str(row["created_at"])[:10] \
                       if row["created_at"] else "—"

            status = "⚠ Unpaid" if unpaid > 0 else "Active"

            tag = "unpaid" if unpaid > 0 else \
                  ("even" if i % 2 == 0 else "odd")

            self.tree.insert("", "end",
                values=(
                    row["patient_code"],
                    f"{row['last_name']}, {row['first_name']}",
                    age,
                    row["sex"] or "—",
                    row["contact_number"] or "—",
                    reg_date,
                    balance_str,
                    status,
                ),
                tags=(tag,),
                iid=str(row["id"]))   # use patient DB id as item id

        self.tree.tag_configure("even",   background=WHITE)
        self.tree.tag_configure("odd",    background="#f8fafc")
        self.tree.tag_configure("unpaid", background=RED_BG,
                                          foreground=RED_FG)

        count = len(rows)
        self.count_lbl.configure(
            text=f"{count} patient{'s' if count != 1 else ''}")

    def _calc_age(self, birthdate_str):
        """Calculate age from a YYYY-MM-DD string."""
        if not birthdate_str:
            return "—"
        try:
            bdate = datetime.strptime(
                str(birthdate_str), "%Y-%m-%d").date()
            today = date.today()
            age   = today.year - bdate.year - (
                (today.month, today.day) < (bdate.month, bdate.day))
            return str(age)
        except Exception:
            return "—"

    # ── Register form ─────────────────────────────────────────────────────────

    def _open_register_form(self, patient_data=None):
        """Open the register / edit patient popup."""
        is_edit = patient_data is not None
        win = tk.Toplevel(self.parent)
        win.title("Edit Patient" if is_edit else "Register New Patient")
        win.geometry("680x620")
        win.resizable(False, True)
        win.grab_set()
        win.configure(bg=BG_LIGHT)

        # Header
        hdr = tk.Frame(win, bg=TEAL_DARK)
        hdr.pack(fill="x")
        tk.Label(hdr,
                 text="Edit Patient Profile" if is_edit
                      else "Register New Patient",
                 font=("Segoe UI", 13, "bold"),
                 bg=TEAL_DARK, fg=WHITE).pack(
                     side="left", padx=16, pady=12)
        if not is_edit:
            # Show auto-generated patient code
            next_code = db.generate_patient_code()
            tk.Label(hdr, text=f"ID: {next_code}",
                     font=("Segoe UI", 10),
                     bg=TEAL_ACCENT, fg=TEAL_DARK,
                     padx=10, pady=5).pack(side="right", padx=16)

        # Scrollable body
        canvas = tk.Canvas(win, bg=BG_LIGHT, highlightthickness=0)
        vsb    = ttk.Scrollbar(win, orient="vertical",
                               command=canvas.yview)
        body   = tk.Frame(canvas, bg=BG_LIGHT)
        body.bind("<Configure>",
                  lambda e: canvas.configure(
                      scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=body, anchor="nw")
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        def on_wheel(e):
            canvas.yview_scroll(int(-1*(e.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", on_wheel)

        pad = {"padx": 18, "pady": 6}

        # ── Personal information ───────────────────────────────────────────────
        pi = self._form_card(body, "Personal Information")
        pi.pack(fill="x", **pad)

        fields = {}

        def field_row(parent, label, key, placeholder="",
                      width=None, options=None):
            row = tk.Frame(parent, bg=WHITE)
            row.pack(fill="x", padx=14, pady=4)
            tk.Label(row, text=label,
                     font=("Segoe UI", 9),
                     bg=WHITE, fg=TEXT_MUTED,
                     width=18, anchor="w").pack(side="left")
            if options:
                var = tk.StringVar(
                    value=patient_data.get(key, options[0])
                    if is_edit else options[0])
                combo = ctk.CTkComboBox(
                    row, values=options, variable=var,
                    font=("Segoe UI", 10), height=30,
                    width=width or 200, corner_radius=6,
                    border_color=BORDER, fg_color=WHITE,
                    text_color=TEXT_MAIN)
                combo.pack(side="left")
                fields[key] = var
            else:
                var = tk.StringVar(
                    value=patient_data.get(key, "")
                    if is_edit else "")
                e = ctk.CTkEntry(
                    row, textvariable=var,
                    placeholder_text=placeholder,
                    font=("Segoe UI", 10), height=30,
                    width=width or 340, corner_radius=6,
                    border_color=BORDER, fg_color=WHITE,
                    text_color=TEXT_MAIN)
                e.pack(side="left")
                fields[key] = var

        field_row(pi, "Last Name *",    "last_name",
                  "Dela Cruz")
        field_row(pi, "First Name *",   "first_name",
                  "Juan")
        field_row(pi, "Middle Name",    "middle_name",
                  "Santos")
        field_row(pi, "Date of Birth",  "birthdate",
                  "YYYY-MM-DD")
        field_row(pi, "Sex *",          "sex",
                  options=["Male", "Female"])
        field_row(pi, "Civil Status",   "civil_status",
                  options=["Single", "Married",
                           "Widowed", "Separated"])
        field_row(pi, "Contact No. *",  "contact_number",
                  "09XX XXX XXXX")
        field_row(pi, "Email",          "email",
                  "juan@email.com")
        field_row(pi, "PhilHealth No.", "philhealth_no",
                  "XX-XXXXXXXXX-X")
        field_row(pi, "Address *",      "address",
                  "House No., Street, Barangay, GMA, Cavite",
                  width=340)

        # ── Emergency contact ─────────────────────────────────────────────────
        ec = self._form_card(body, "Emergency Contact")
        ec.pack(fill="x", **pad)
        field_row(ec, "Full Name",      "emergency_name",
                  "Maria Dela Cruz")
        field_row(ec, "Relationship",   "emergency_relation",
                  "Spouse")
        field_row(ec, "Contact No.",    "emergency_contact",
                  "09XX XXX XXXX")

        # ── Save button ───────────────────────────────────────────────────────
        btn_row = tk.Frame(body, bg=BG_LIGHT)
        btn_row.pack(fill="x", padx=18, pady=12)

        def save():
            # Basic validation
            if not fields["last_name"].get().strip():
                messagebox.showwarning(
                    "Required Field",
                    "Last name is required.")
                return
            if not fields["first_name"].get().strip():
                messagebox.showwarning(
                    "Required Field",
                    "First name is required.")
                return
            if not fields["contact_number"].get().strip():
                messagebox.showwarning(
                    "Required Field",
                    "Contact number is required.")
                return

            data = {k: v.get().strip() for k, v in fields.items()}

            try:
                code = db.add_patient(data)
                canvas.unbind_all("<MouseWheel>")
                win.destroy()
                messagebox.showinfo(
                    "Patient Registered ✓",
                    f"Patient registered successfully!\n\n"
                    f"Patient ID: {code}\n"
                    f"Name: {data['last_name']}, "
                    f"{data['first_name']}\n\n"
                    f"You can now create a bill for this patient.")
                self._load_patients()   # refresh table
            except Exception as ex:
                messagebox.showerror(
                    "Error", f"Could not save patient:\n{ex}")

        tk.Button(btn_row, text="Save Patient Record",
                  command=save,
                  font=("Segoe UI", 11, "bold"),
                  bg=TEAL_DARK, fg=WHITE,
                  activebackground=TEAL_MID,
                  relief="flat", cursor="hand2",
                  padx=20, pady=9).pack(side="right")
        tk.Button(btn_row, text="Cancel",
                  command=lambda: [
                      canvas.unbind_all("<MouseWheel>"),
                      win.destroy()],
                  font=("Segoe UI", 10),
                  bg=WHITE, fg=TEXT_MUTED,
                  relief="flat", cursor="hand2",
                  padx=14, pady=8).pack(
                      side="right", padx=(0, 8))

    # ── Patient profile popup ─────────────────────────────────────────────────

    def _on_row_double_click(self, event):
        self._view_selected()

    def _view_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo(
                "No Selection",
                "Please click on a patient row first.")
            return
        patient_id = int(sel[0])
        patient    = db.get_patient_by_id(patient_id)
        if not patient:
            messagebox.showerror("Error", "Patient not found.")
            return
        self._open_profile(patient)

    def _open_profile(self, patient):
        win = tk.Toplevel(self.parent)
        win.title(
            f"Profile — {patient['first_name']} "
            f"{patient['last_name']}")
        win.geometry("600x520")
        win.grab_set()
        win.configure(bg=BG_LIGHT)

        # Header
        hdr = tk.Frame(win, bg=TEAL_DARK)
        hdr.pack(fill="x")

        initials = (patient["first_name"][0]
                    + patient["last_name"][0]).upper()
        tk.Label(hdr, text=initials,
                 font=("Segoe UI", 14, "bold"),
                 bg=TEAL_ACCENT, fg=WHITE,
                 width=3, pady=4).pack(
                     side="left", padx=16, pady=10)

        name_block = tk.Frame(hdr, bg=TEAL_DARK)
        name_block.pack(side="left")
        tk.Label(name_block,
                 text=f"{patient['last_name']}, "
                      f"{patient['first_name']} "
                      f"{patient['middle_name'] or ''}",
                 font=("Segoe UI", 13, "bold"),
                 bg=TEAL_DARK, fg=WHITE).pack(anchor="w")
        tk.Label(name_block,
                 text=patient["patient_code"],
                 font=("Segoe UI", 10),
                 bg=TEAL_DARK,
                 fg=TEAL_ACCENT).pack(anchor="w")

        # Unpaid balance banner
        unpaid = db.get_patient_unpaid_total(patient["id"])
        if unpaid > 0:
            banner = tk.Frame(win, bg=RED_BG,
                              highlightbackground="#feb2b2",
                              highlightthickness=1)
            banner.pack(fill="x")
            tk.Label(banner,
                     text=f"⚠  Unpaid balance: ₱{unpaid:,.2f}",
                     font=("Segoe UI", 10, "bold"),
                     bg=RED_BG, fg=RED_FG,
                     pady=8, padx=16).pack(anchor="w")

        # Info grid
        scroll_frame = tk.Frame(win, bg=BG_LIGHT)
        scroll_frame.pack(fill="both", expand=True,
                          padx=16, pady=12)

        info_card = self._form_card(scroll_frame,
                                    "Personal Information")
        info_card.pack(fill="x", pady=(0, 10))

        profile_fields = [
            ("Date of Birth",   patient["birthdate"] or "—"),
            ("Age",             self._calc_age(patient["birthdate"])),
            ("Sex",             patient["sex"] or "—"),
            ("Civil Status",    patient["civil_status"] or "—"),
            ("Contact Number",  patient["contact_number"] or "—"),
            ("Email",           patient["email"] or "—"),
            ("PhilHealth No.",  patient["philhealth_no"] or "—"),
            ("Address",         patient["address"] or "—"),
            ("Registered On",   str(patient["created_at"])[:10]),
        ]
        for label, value in profile_fields:
            row = tk.Frame(info_card, bg=WHITE)
            row.pack(fill="x", padx=14, pady=3)
            tk.Frame(info_card, bg=BORDER,
                     height=1).pack(fill="x", padx=14)
            tk.Label(row, text=label,
                     font=("Segoe UI", 9),
                     bg=WHITE, fg=TEXT_MUTED,
                     width=16, anchor="w",
                     pady=6).pack(side="left")
            tk.Label(row, text=value,
                     font=("Segoe UI", 10, "bold"),
                     bg=WHITE, fg=TEXT_MAIN,
                     anchor="w").pack(side="left")

        ec_card = self._form_card(scroll_frame,
                                  "Emergency Contact")
        ec_card.pack(fill="x")
        for label, value in [
            ("Name",         patient["emergency_name"] or "—"),
            ("Relationship", patient["emergency_relation"] or "—"),
            ("Contact",      patient["emergency_contact"] or "—"),
        ]:
            row = tk.Frame(ec_card, bg=WHITE)
            row.pack(fill="x", padx=14, pady=3)
            tk.Frame(ec_card, bg=BORDER,
                     height=1).pack(fill="x", padx=14)
            tk.Label(row, text=label,
                     font=("Segoe UI", 9),
                     bg=WHITE, fg=TEXT_MUTED,
                     width=16, anchor="w",
                     pady=6).pack(side="left")
            tk.Label(row, text=value,
                     font=("Segoe UI", 10, "bold"),
                     bg=WHITE, fg=TEXT_MAIN).pack(side="left")

        # Close button
        tk.Button(win, text="Close",
                  command=win.destroy,
                  font=("Segoe UI", 10),
                  bg=WHITE, fg=TEXT_MUTED,
                  relief="flat", cursor="hand2",
                  padx=20, pady=8).pack(pady=10)

    # ── Widget helpers ────────────────────────────────────────────────────────

    def _card(self, parent):
        return tk.Frame(parent, bg=WHITE,
                        highlightbackground=BORDER,
                        highlightthickness=1)

    def _form_card(self, parent, title):
        outer = tk.Frame(parent, bg=WHITE,
                         highlightbackground=BORDER,
                         highlightthickness=1)
        tk.Label(outer, text=title,
                 font=("Segoe UI", 10, "bold"),
                 bg=WHITE, fg=TEXT_MAIN,
                 pady=10, padx=14).pack(anchor="w")
        tk.Frame(outer, bg=BORDER,
                 height=1).pack(fill="x")
        return outer

    def _solid_btn(self, parent, text, command):
        return tk.Button(parent, text=text,
                         command=command,
                         font=("Segoe UI", 10, "bold"),
                         bg=TEAL_DARK, fg=WHITE,
                         activebackground=TEAL_MID,
                         relief="flat", cursor="hand2",
                         padx=14, pady=7)