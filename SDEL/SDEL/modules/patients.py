# modules/patients.py
# ─────────────────────────────────────────────────────────────────────────────
#  PureHealth Diagnostic Center — Patient Management Module
#  MERGED: groupmate's full UI + database integration
#  Requires:  pip install tkcalendar customtkinter
# ─────────────────────────────────────────────────────────────────────────────

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from datetime import datetime, date
from tkcalendar import Calendar
from database import db

# ── Colour palette ────────────────────────────────────────────────────────────
TEAL_DARK   = "#073b4c"
TEAL_MID    = "#0c637f"
TEAL_ACCENT = "#0cb0a9"
WHITE       = "#ffffff"
BG_LIGHT    = "#f4f6f8"
BORDER      = "#e2e8f0"
TEXT_MAIN   = "#1a202c"
TEXT_MUTED  = "#718096"
TEXT_HINT   = "#a0aec0"

STATUS_ACTIVE   = ("#d1fae5", "#065f46")
STATUS_UNPAID   = ("#fee2e2", "#991b1b")
STATUS_INACTIVE = ("#f3f4f6", "#374151")


# ── Age helper ────────────────────────────────────────────────────────────────
def _calc_age(dob_str: str) -> str:
    try:
        dob   = datetime.strptime(str(dob_str), "%Y-%m-%d").date()
        today = date.today()
        age   = today.year - dob.year - (
            (today.month, today.day) < (dob.month, dob.day))
        return str(age)
    except Exception:
        return "—"


# ─────────────────────────────────────────────────────────────────────────────
class PatientsModule:
# ─────────────────────────────────────────────────────────────────────────────

    def __init__(self, parent):
        self.parent = parent
        # In-memory list of DB row dicts — refreshed from DB on show()
        self._all_patients  = []
        # Live stat labels — updated whenever data changes
        self._lbl_active    = None
        self._lbl_unpaid    = None
        self._lbl_inactive  = None

    # ── Entry point ───────────────────────────────────────────────────────────

    def show(self):
        for w in self.parent.winfo_children():
            w.destroy()
        self.parent.configure(bg=BG_LIGHT)
        self._all_patients = self._fetch_all()   # load fresh from DB
        self._build_ui()

    # ── DB helpers ────────────────────────────────────────────────────────────

    def _fetch_all(self):
        """Pull all patients from DB and normalise into the dict shape the UI
        expects (mirrors groupmate's field names so the rest of the code works
        without changes)."""
        rows = db.get_all_patients()
        result = []
        for r in rows:
            unpaid = db.get_patient_unpaid_total(r["id"])
            # Derive status from unpaid balance
            if unpaid > 0:
                status = "Unpaid"
            else:
                status = "Active"

            result.append({
                # DB fields
                "_db_id":       r["id"],
                # UI-facing fields (matches groupmate's key names)
                "patient_id":   r["patient_code"],
                "last_name":    r["last_name"]          or "",
                "first_name":   r["first_name"]         or "",
                "middle_name":  r["middle_name"]        or "",
                "dob":          str(r["birthdate"])     if r["birthdate"] else "",
                "sex":          r["sex"]                or "",
                "civil_status": r["civil_status"]       or "",
                "contact":      r["contact_number"]     or "",
                "email":        r["email"]              or "",
                "philhealth":   r["philhealth_no"]      or "",
                "address":      r["address"]            or "",
                "ec_name":      r["emergency_name"]     or "",
                "ec_rel":       r["emergency_relation"] or "",
                "ec_contact":   r["emergency_contact"]  or "",
                "last_visit":   str(r["created_at"])[:10] if r["created_at"] else "—",
                "status":       status,
                "unpaid_bal":   unpaid,
            })
        return result

    def _patient_by_pid(self, patient_id_str):
        """Return the in-memory dict for a given patient_id string."""
        return next(
            (p for p in self._all_patients
             if p["patient_id"] == patient_id_str), None)

    # ── Live stat chips ───────────────────────────────────────────────────────

    def _refresh_stats(self):
        active   = sum(1 for p in self._all_patients if p["status"] == "Active")
        unpaid   = sum(1 for p in self._all_patients if p["status"] == "Unpaid")
        inactive = sum(1 for p in self._all_patients if p["status"] == "Inactive")
        if self._lbl_active:
            self._lbl_active.configure(text=f" {active} Active ")
        if self._lbl_unpaid:
            self._lbl_unpaid.configure(text=f" {unpaid} Unpaid ")
        if self._lbl_inactive:
            self._lbl_inactive.configure(text=f" {inactive} Inactive ")

    # ── UI construction ───────────────────────────────────────────────────────

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
        tk.Label(title_block, text="Register and manage patient records",
                 font=("Segoe UI", 10), bg=WHITE,
                 fg=TEXT_MUTED).pack(anchor="w")

        # Register button
        tk.Button(header, text="+ Register New Patient",
                  command=self._open_register_form,
                  font=("Segoe UI", 10, "bold"),
                  bg=TEAL_DARK, fg=WHITE, activebackground=TEAL_MID,
                  relief="flat", cursor="hand2",
                  padx=14, pady=7).pack(
                      side="right", padx=(0, 14), pady=10)

        # Live stats chips
        stats_bar = tk.Frame(header, bg=WHITE)
        stats_bar.pack(side="right", padx=8)

        active   = sum(1 for p in self._all_patients if p["status"] == "Active")
        unpaid   = sum(1 for p in self._all_patients if p["status"] == "Unpaid")
        inactive = sum(1 for p in self._all_patients if p["status"] == "Inactive")

        _, self._lbl_active   = self._stat_chip(
            stats_bar, active,   "Active",   *STATUS_ACTIVE)
        _, self._lbl_unpaid   = self._stat_chip(
            stats_bar, unpaid,   "Unpaid",   *STATUS_UNPAID)
        _, self._lbl_inactive = self._stat_chip(
            stats_bar, inactive, "Inactive", *STATUS_INACTIVE)

        # ── Search & filter bar ───────────────────────────────────────────────
        filter_card = tk.Frame(self.parent, bg=WHITE,
                               highlightbackground=BORDER,
                               highlightthickness=1)
        filter_card.pack(fill="x", padx=18, pady=10)

        row = tk.Frame(filter_card, bg=WHITE)
        row.pack(fill="x", padx=14, pady=10)

        self.search_entry = ctk.CTkEntry(
            row, placeholder_text="Search by name, ID, or contact...",
            font=("Segoe UI", 11), height=34, corner_radius=8,
            border_color=BORDER, fg_color=WHITE, text_color=TEXT_MAIN)
        self.search_entry.pack(
            side="left", fill="x", expand=True, padx=(0, 8))
        self.search_entry.bind("<Return>", lambda e: self._apply_filters())

        self.status_var = tk.StringVar(value="All Status")
        ctk.CTkComboBox(row,
                        values=["All Status", "Active", "Unpaid", "Inactive"],
                        variable=self.status_var,
                        font=("Segoe UI", 10), height=34, width=130,
                        corner_radius=8, border_color=BORDER,
                        fg_color=WHITE, text_color=TEXT_MAIN,
                        command=lambda _: self._apply_filters()
                        ).pack(side="left", padx=(0, 8))

        self.sex_var = tk.StringVar(value="All Sex")
        ctk.CTkComboBox(row, values=["All Sex", "Male", "Female"],
                        variable=self.sex_var,
                        font=("Segoe UI", 10), height=34, width=110,
                        corner_radius=8, border_color=BORDER,
                        fg_color=WHITE, text_color=TEXT_MAIN,
                        command=lambda _: self._apply_filters()
                        ).pack(side="left", padx=(0, 8))

        tk.Button(row, text="Search", command=self._apply_filters,
                  font=("Segoe UI", 10, "bold"),
                  bg=TEAL_DARK, fg=WHITE, activebackground=TEAL_MID,
                  relief="flat", cursor="hand2",
                  padx=14, pady=6).pack(side="left", padx=(0, 6))

        tk.Button(row, text="Clear", command=self._clear_filters,
                  font=("Segoe UI", 10), bg=WHITE, fg=TEXT_MUTED,
                  relief="flat", cursor="hand2",
                  padx=10, pady=6).pack(side="left")

        # ── Patient table ─────────────────────────────────────────────────────
        table_wrapper = tk.Frame(self.parent, bg=WHITE,
                                 highlightbackground=BORDER,
                                 highlightthickness=1)
        table_wrapper.pack(fill="both", expand=True, padx=18, pady=(0, 16))

        tbl_hdr = tk.Frame(table_wrapper, bg="#f8fafc")
        tbl_hdr.pack(fill="x")
        tk.Frame(table_wrapper, bg=BORDER, height=1).pack(fill="x")

        self.count_lbl = tk.Label(tbl_hdr,
                                  text=f"{len(self._all_patients)} patients",
                                  font=("Segoe UI", 9),
                                  bg="#f8fafc", fg=TEXT_MUTED)
        self.count_lbl.pack(side="right", padx=14, pady=7)
        tk.Label(tbl_hdr, text="All Patients",
                 font=("Segoe UI", 10, "bold"),
                 bg="#f8fafc", fg=TEXT_MAIN).pack(side="left", padx=14, pady=7)

        # Treeview style
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Pat.Treeview",
                        background=WHITE, fieldbackground=WHITE,
                        foreground=TEXT_MAIN, rowheight=38,
                        font=("Segoe UI", 10))
        style.configure("Pat.Treeview.Heading",
                        background="#f8fafc", foreground=TEXT_MUTED,
                        font=("Segoe UI", 9, "bold"),
                        relief="flat", padding=8)
        style.map("Pat.Treeview",
                  background=[("selected", "#e0f2fe")],
                  foreground=[("selected", TEXT_MAIN)])

        cols = ("patient_id", "name", "age_sex", "contact",
                "last_visit", "status", "actions")
        self.tree = ttk.Treeview(table_wrapper, columns=cols,
                                 show="headings", style="Pat.Treeview")

        self.tree.heading("patient_id", text="Patient ID")
        self.tree.heading("name",       text="Name")
        self.tree.heading("age_sex",    text="Age / Sex")
        self.tree.heading("contact",    text="Contact")
        self.tree.heading("last_visit", text="Registered")
        self.tree.heading("status",     text="Status")
        self.tree.heading("actions",    text="Actions")

        self.tree.column("patient_id", width=130, anchor="w",     stretch=False)
        self.tree.column("name",       width=200, anchor="w")
        self.tree.column("age_sex",    width=75,  anchor="center", stretch=False)
        self.tree.column("contact",    width=135, anchor="w",     stretch=False)
        self.tree.column("last_visit", width=100, anchor="center", stretch=False)
        self.tree.column("status",     width=100, anchor="center", stretch=False)
        self.tree.column("actions",    width=160, anchor="center", stretch=False)

        self.tree.pack(fill="both", expand=True)

        self.tree.bind("<Double-1>", self._on_tree_double_click)
        self.tree.bind("<ButtonRelease-1>", self._on_tree_click)

        # ── Bottom hint ───────────────────────────────────────────────────────
        action_bar = tk.Frame(self.parent, bg=BG_LIGHT)
        action_bar.pack(fill="x", padx=18, pady=(0, 14))
        tk.Label(action_bar,
                 text="Double-click a row to view details  ·  "
                      "Click Edit / Delete in the Actions column",
                 font=("Segoe UI", 9),
                 bg=BG_LIGHT, fg=TEXT_HINT).pack(side="left")

        self._load_table(self._all_patients)

    # ── Table population ──────────────────────────────────────────────────────

    def _load_table(self, patients):
        for row in self.tree.get_children():
            self.tree.delete(row)

        for i, p in enumerate(patients):
            age       = _calc_age(p["dob"])
            sex_short = "M" if p["sex"] == "Male" else \
                        "F" if p["sex"] == "Female" else "—"
            full_name = " ".join(
                filter(None, [p["first_name"],
                              p["middle_name"],
                              p["last_name"]]))
            status_label = {
                "Active":   "● Active",
                "Unpaid":   "● Unpaid",
                "Inactive": "○ Inactive",
            }.get(p["status"], p["status"])

            self.tree.insert("", "end",
                values=(p["patient_id"], full_name,
                        f"{age}/{sex_short}", p["contact"],
                        p["last_visit"], status_label,
                        "✏ Edit    🗑 Delete"),
                tags=(p["status"], "even" if i % 2 == 0 else "odd"),
                iid=p["patient_id"])   # use patient_id string as iid

        self.tree.tag_configure("even",     background=WHITE)
        self.tree.tag_configure("odd",      background="#f8fafc")
        self.tree.tag_configure("Active",   foreground="#065f46")
        self.tree.tag_configure("Unpaid",   foreground="#991b1b")
        self.tree.tag_configure("Inactive", foreground="#374151")

        n = len(patients)
        self.count_lbl.configure(
            text=f"{n} patient{'s' if n != 1 else ''}")

    # ── Filter & search ───────────────────────────────────────────────────────

    def _apply_filters(self):
        q      = self.search_entry.get().strip().lower()
        st_sel = self.status_var.get()
        sx_sel = self.sex_var.get()
        filtered = [
            p for p in self._all_patients
            if (not q
                or q in p["last_name"].lower()
                or q in p["first_name"].lower()
                or q in p["patient_id"].lower()
                or q in p["contact"].lower())
            and (st_sel == "All Status" or p["status"] == st_sel)
            and (sx_sel == "All Sex"    or p["sex"]    == sx_sel)
        ]
        self._load_table(filtered)

    def _clear_filters(self):
        self.search_entry.delete(0, "end")
        self.status_var.set("All Status")
        self.sex_var.set("All Sex")
        self._load_table(self._all_patients)

    # ── Click handlers ────────────────────────────────────────────────────────

    def _get_selected_patient(self):
        sel = self.tree.selection()
        if not sel:
            return None
        pid = self.tree.item(sel[0], "values")[0]
        return self._patient_by_pid(pid)

    def _on_tree_double_click(self, event):
        col = self.tree.identify_column(event.x)
        if col == "#7":   # actions column — ignore
            return
        self._view_selected()

    def _on_tree_click(self, event):
        col = self.tree.identify_column(event.x)
        row = self.tree.identify_row(event.y)
        if not row or col != "#7":
            return
        bbox = self.tree.bbox(row, "#7")
        if not bbox:
            return
        x_in_cell = event.x - bbox[0]
        cell_w    = bbox[2]
        self.tree.selection_set(row)
        if x_in_cell < cell_w // 2:
            self._edit_selected()
        else:
            self._delete_selected()

    def _view_selected(self):
        p = self._get_selected_patient()
        if not p:
            messagebox.showinfo("No Selection",
                                "Please click on a patient row first.")
            return
        self._open_detail_window(p)

    def _edit_selected(self):
        p = self._get_selected_patient()
        if not p:
            messagebox.showinfo("No Selection",
                                "Please click on a patient row first.")
            return
        self._open_edit_form(p)

    def _delete_selected(self):
        p = self._get_selected_patient()
        if not p:
            messagebox.showinfo("No Selection",
                                "Please click on a patient row first.")
            return
        confirm = messagebox.askyesno(
            "Delete Patient",
            f"Are you sure you want to delete the record for:\n\n"
            f"  {p['first_name']} {p['middle_name']} {p['last_name']}\n"
            f"  ID: {p['patient_id']}\n\n"
            "This action cannot be undone.",
            icon="warning")
        if confirm:
            try:
                db.delete_patient(p["_db_id"])
            except Exception as ex:
                messagebox.showerror("Error",
                    f"Could not delete patient:\n{ex}")
                return
            # Remove from in-memory list and refresh
            self._all_patients = [
                x for x in self._all_patients
                if x["patient_id"] != p["patient_id"]
            ]
            self._apply_filters()
            self._refresh_stats()

    # ── Calendar date-picker helper ───────────────────────────────────────────

    def _pick_date(self, dob_var: tk.StringVar, parent_win):
        popup = tk.Toplevel(parent_win)
        popup.title("Select Date of Birth")
        popup.grab_set()
        popup.resizable(False, False)
        popup.configure(bg=WHITE)

        current = dob_var.get()
        try:
            y, m, d = map(int, current.split("-"))
        except Exception:
            today   = date.today()
            y, m, d = today.year - 25, today.month, today.day

        top = tk.Frame(popup, bg=TEAL_DARK)
        top.pack(fill="x")
        tk.Label(top, text="Date of Birth",
                 font=("Segoe UI", 12, "bold"),
                 bg=TEAL_DARK, fg=WHITE,
                 pady=10, padx=16).pack(side="left")

        cal = Calendar(popup,
                       selectmode="day",
                       year=y, month=m, day=d,
                       date_pattern="yyyy-mm-dd",
                       background=TEAL_DARK,
                       foreground=WHITE,
                       selectbackground=TEAL_ACCENT,
                       selectforeground=WHITE,
                       headersbackground=TEAL_MID,
                       headersforeground=WHITE,
                       weekendbackground=WHITE,
                       weekendforeground="#991b1b",
                       othermonthforeground=TEXT_HINT,
                       othermonthweforeground=TEXT_HINT,
                       bordercolor=BORDER,
                       font=("Segoe UI", 10),
                       showweeknumbers=False)
        cal.pack(padx=16, pady=12)

        btn_row = tk.Frame(popup, bg=WHITE)
        btn_row.pack(fill="x", padx=16, pady=(0, 14))

        def _confirm():
            dob_var.set(cal.get_date())
            popup.destroy()

        tk.Button(btn_row, text="Cancel", command=popup.destroy,
                  font=("Segoe UI", 10), bg=WHITE, fg=TEXT_MUTED,
                  relief="flat", cursor="hand2", padx=12, pady=6,
                  highlightbackground=BORDER,
                  highlightthickness=1).pack(side="right", padx=(6, 0))
        tk.Button(btn_row, text="Confirm Date", command=_confirm,
                  font=("Segoe UI", 10, "bold"),
                  bg=TEAL_DARK, fg=WHITE, activebackground=TEAL_MID,
                  relief="flat", cursor="hand2",
                  padx=12, pady=6).pack(side="right")

    # ── Shared form builder (Register & Edit) ─────────────────────────────────

    def _build_patient_form(self, win, existing: dict = None):
        """Build the form inside `win`. Returns (body_frame, fields, dob_var)."""
        is_edit = existing is not None
        fields  = {}
        dob_var = tk.StringVar(
            value=existing["dob"] if is_edit else "")

        body = tk.Frame(win, bg=BG_LIGHT)
        body.pack(fill="both", expand=True, padx=18, pady=14)

        # ── local helpers ─────────────────────────────────────────────────────
        def _card(title):
            outer = tk.Frame(body, bg=WHITE,
                             highlightbackground=BORDER,
                             highlightthickness=1)
            tk.Label(outer, text=title,
                     font=("Segoe UI", 10, "bold"),
                     bg=WHITE, fg=TEXT_MAIN,
                     pady=9, padx=14).pack(anchor="w")
            tk.Frame(outer, bg=BORDER, height=1).pack(fill="x")
            inner = tk.Frame(outer, bg=WHITE)
            inner.pack(fill="x", padx=14, pady=10)
            return outer, inner

        def _lbl(parent, text):
            tk.Label(parent, text=text,
                     font=("Segoe UI", 9), bg=WHITE,
                     fg=TEXT_MUTED).pack(anchor="w")

        def _entry(parent, key, placeholder="", prefill=""):
            e = ctk.CTkEntry(parent,
                             placeholder_text=placeholder,
                             font=("Segoe UI", 10), height=34,
                             corner_radius=6, border_color=BORDER,
                             fg_color=WHITE, text_color=TEXT_MAIN)
            e.pack(fill="x", pady=(0, 2))
            if prefill:
                e.insert(0, prefill)
            fields[key] = e
            return e

        def _combo(parent, key, options, prefill=""):
            var = tk.StringVar(value=prefill if prefill else options[0])
            cb  = ctk.CTkComboBox(
                parent, values=options, variable=var,
                font=("Segoe UI", 10), height=34,
                corner_radius=6, border_color=BORDER,
                fg_color=WHITE, text_color=TEXT_MAIN)
            cb.pack(fill="x", pady=(0, 2))
            fields[key] = var
            return cb

        def _cols(parent, n):
            f = tk.Frame(parent, bg=WHITE)
            f.pack(fill="x", pady=3)
            cells = []
            for i in range(n):
                c = tk.Frame(f, bg=WHITE)
                c.pack(side="left", fill="x", expand=True,
                       padx=(0 if i == 0 else 10, 0))
                cells.append(c)
            return cells

        # ── Personal Information ──────────────────────────────────────────────
        pi_card, pi = _card("Personal Information")
        pi_card.pack(fill="x", pady=(0, 10))

        c1, c2, c3 = _cols(pi, 3)
        _lbl(c1, "Last Name *")
        _entry(c1, "last_name", "Dela Cruz",
               existing["last_name"] if is_edit else "")
        _lbl(c2, "First Name *")
        _entry(c2, "first_name", "Juan",
               existing["first_name"] if is_edit else "")
        _lbl(c3, "Middle Name")
        _entry(c3, "middle_name", "Santos",
               existing["middle_name"] if is_edit else "")

        c1, c2, c3 = _cols(pi, 3)

        # DOB clickable calendar
        _lbl(c1, "Date of Birth *")
        dob_frame = tk.Frame(c1, bg=WHITE,
                             highlightbackground=BORDER,
                             highlightthickness=1, cursor="hand2")
        dob_frame.pack(fill="x", pady=(0, 2))
        tk.Label(dob_frame, text="📅",
                 font=("Segoe UI", 11),
                 bg=WHITE, fg=TEAL_MID,
                 padx=6, pady=6).pack(side="left")
        dob_val_lbl = tk.Label(dob_frame, textvariable=dob_var,
                               font=("Segoe UI", 10), bg=WHITE,
                               fg=TEXT_MAIN, anchor="w")
        dob_ph_lbl  = tk.Label(dob_frame,
                               text="Click to select date",
                               font=("Segoe UI", 10, "italic"),
                               bg=WHITE, fg=TEXT_HINT, anchor="w")

        def _refresh_dob(*_):
            if dob_var.get():
                dob_ph_lbl.pack_forget()
                dob_val_lbl.pack(side="left", fill="x", expand=True)
            else:
                dob_val_lbl.pack_forget()
                dob_ph_lbl.pack(side="left", fill="x", expand=True)

        dob_var.trace_add("write", _refresh_dob)
        _refresh_dob()

        _open_cal = lambda e=None: self._pick_date(dob_var, win)
        dob_frame.bind("<Button-1>", _open_cal)
        for w in dob_frame.winfo_children():
            w.bind("<Button-1>", _open_cal)

        _lbl(c2, "Sex *")
        _combo(c2, "sex", ["Select", "Male", "Female"],
               existing["sex"] if is_edit else "")
        _lbl(c3, "Civil Status")
        _combo(c3, "civil_status",
               ["Select", "Single", "Married", "Widowed", "Separated"],
               existing["civil_status"] if is_edit else "")

        c1, c2, c3 = _cols(pi, 3)
        _lbl(c1, "Contact Number *")
        _entry(c1, "contact", "09XX XXX XXXX",
               existing["contact"] if is_edit else "")
        _lbl(c2, "Email")
        _entry(c2, "email", "juan@email.com",
               existing["email"] if is_edit else "")
        _lbl(c3, "PhilHealth No.")
        _entry(c3, "philhealth", "XX-XXXXXXXXX-X",
               existing["philhealth"] if is_edit else "")

        addr_row = tk.Frame(pi, bg=WHITE)
        addr_row.pack(fill="x", pady=3)
        _lbl(addr_row, "Complete Address *")
        _entry(addr_row, "address",
               "House No., Street, Barangay, City, Province",
               existing["address"] if is_edit else "")

        # ── Emergency Contact ─────────────────────────────────────────────────
        ec_card, ec = _card("Emergency Contact")
        ec_card.pack(fill="x", pady=(0, 10))

        c1, c2, c3 = _cols(ec, 3)
        _lbl(c1, "Name")
        _entry(c1, "ec_name", "Maria Dela Cruz",
               existing["ec_name"] if is_edit else "")
        _lbl(c2, "Relationship")
        _entry(c2, "ec_rel", "Spouse",
               existing["ec_rel"] if is_edit else "")
        _lbl(c3, "Contact")
        _entry(c3, "ec_contact", "09XX XXX XXXX",
               existing["ec_contact"] if is_edit else "")

        return body, fields, dob_var

    # ── Register new patient ──────────────────────────────────────────────────

    def _open_register_form(self):
        win = tk.Toplevel(self.parent)
        win.title("Register New Patient")
        win.geometry("820x680")
        win.minsize(820, 680)
        win.resizable(True, True)
        win.grab_set()
        win.configure(bg=BG_LIGHT)

        next_code = db.generate_patient_code()

        top = tk.Frame(win, bg=TEAL_DARK)
        top.pack(fill="x")
        tk.Label(top, text="Register New Patient",
                 font=("Segoe UI", 13, "bold"),
                 bg=TEAL_DARK, fg=WHITE).pack(
                     side="left", padx=16, pady=13)
        tk.Label(top, text=f"Auto-ID: {next_code}",
                 font=("Segoe UI", 9),
                 bg=TEAL_MID, fg=WHITE,
                 padx=10, pady=4).pack(side="right", padx=16)

        body, fields, dob_var = self._build_patient_form(win)

        # Footer
        btn_frame = tk.Frame(body, bg=BG_LIGHT)
        btn_frame.pack(fill="x", pady=(4, 0))

        def _save():
            ln  = fields["last_name"].get().strip()
            fn  = fields["first_name"].get().strip()
            sex = fields["sex"].get()
            ct  = fields["contact"].get().strip()

            if not ln or not fn:
                messagebox.showerror("Required",
                    "Last Name and First Name are required.",
                    parent=win)
                return
            if sex in ("Select", ""):
                messagebox.showerror("Required",
                    "Please select the patient's sex.", parent=win)
                return
            if not ct:
                messagebox.showerror("Required",
                    "Contact number is required.", parent=win)
                return

            civil = fields["civil_status"].get()
            data  = {
                "last_name":           ln,
                "first_name":          fn,
                "middle_name":         fields["middle_name"].get().strip(),
                "birthdate":           dob_var.get() or None,
                "sex":                 sex,
                "civil_status":        civil if civil != "Select" else "",
                "contact_number":      ct,
                "email":               fields["email"].get().strip(),
                "philhealth_no":       fields["philhealth"].get().strip(),
                "address":             fields["address"].get().strip(),
                "emergency_name":      fields["ec_name"].get().strip(),
                "emergency_relation":  fields["ec_rel"].get().strip(),
                "emergency_contact":   fields["ec_contact"].get().strip(),
            }

            try:
                code = db.add_patient(data)
                win.destroy()
                # Re-fetch from DB so everything stays in sync
                self._all_patients = self._fetch_all()
                self._apply_filters()
                self._refresh_stats()
                messagebox.showinfo(
                    "Patient Registered ✓",
                    f"Patient registered successfully!\n\n"
                    f"Patient ID : {code}\n"
                    f"Name       : {fn} {ln}\n\n"
                    f"You can now create a bill for this patient.")
            except Exception as ex:
                messagebox.showerror("Error",
                    f"Could not save patient:\n{ex}")

        tk.Button(btn_frame, text="Cancel", command=win.destroy,
                  font=("Segoe UI", 10), bg=WHITE, fg=TEXT_MUTED,
                  relief="flat", cursor="hand2", padx=16, pady=8,
                  highlightbackground=BORDER,
                  highlightthickness=1).pack(side="right", padx=(8, 0))
        tk.Button(btn_frame, text="Save Patient & Proceed to Billing",
                  command=_save,
                  font=("Segoe UI", 10, "bold"),
                  bg=TEAL_DARK, fg=WHITE, activebackground=TEAL_MID,
                  relief="flat", cursor="hand2",
                  padx=16, pady=8).pack(side="right")

    # ── Edit patient ──────────────────────────────────────────────────────────

    def _open_edit_form(self, p: dict):
        win = tk.Toplevel(self.parent)
        win.title(f"Edit Patient — {p['first_name']} {p['last_name']}")
        win.geometry("820x680")
        win.minsize(820, 680)
        win.resizable(True, True)
        win.grab_set()
        win.configure(bg=BG_LIGHT)

        top = tk.Frame(win, bg=TEAL_MID)
        top.pack(fill="x")
        tk.Label(top, text="Edit Patient Information",
                 font=("Segoe UI", 13, "bold"),
                 bg=TEAL_MID, fg=WHITE).pack(
                     side="left", padx=16, pady=13)
        tk.Label(top, text=p["patient_id"],
                 font=("Segoe UI", 9),
                 bg=TEAL_DARK, fg=WHITE,
                 padx=10, pady=4).pack(side="right", padx=16)

        body, fields, dob_var = self._build_patient_form(win, existing=p)

        # Footer
        btn_frame = tk.Frame(body, bg=BG_LIGHT)
        btn_frame.pack(fill="x", pady=(4, 0))

        def _save_edit():
            ln  = fields["last_name"].get().strip()
            fn  = fields["first_name"].get().strip()
            sex = fields["sex"].get()
            ct  = fields["contact"].get().strip()

            if not ln or not fn:
                messagebox.showerror("Required",
                    "Last Name and First Name are required.",
                    parent=win)
                return
            if sex in ("Select", ""):
                messagebox.showerror("Required",
                    "Please select the patient's sex.", parent=win)
                return
            if not ct:
                messagebox.showerror("Required",
                    "Contact number is required.", parent=win)
                return

            civil = fields["civil_status"].get()
            data  = {
                "last_name":           ln,
                "first_name":          fn,
                "middle_name":         fields["middle_name"].get().strip(),
                "birthdate":           dob_var.get() or None,
                "sex":                 sex,
                "civil_status":        civil if civil != "Select" else "",
                "contact_number":      ct,
                "email":               fields["email"].get().strip(),
                "philhealth_no":       fields["philhealth"].get().strip(),
                "address":             fields["address"].get().strip(),
                "emergency_name":      fields["ec_name"].get().strip(),
                "emergency_relation":  fields["ec_rel"].get().strip(),
                "emergency_contact":   fields["ec_contact"].get().strip(),
            }

            try:
                db.update_patient(p["_db_id"], data)
                win.destroy()
                # Re-fetch so the in-memory list is fully up to date
                self._all_patients = self._fetch_all()
                self._apply_filters()
                self._refresh_stats()
                messagebox.showinfo("Saved",
                    f"Patient record for {fn} {ln} has been updated.")
            except Exception as ex:
                messagebox.showerror("Error",
                    f"Could not update patient:\n{ex}")

        tk.Button(btn_frame, text="Cancel", command=win.destroy,
                  font=("Segoe UI", 10), bg=WHITE, fg=TEXT_MUTED,
                  relief="flat", cursor="hand2", padx=16, pady=8,
                  highlightbackground=BORDER,
                  highlightthickness=1).pack(side="right", padx=(8, 0))
        tk.Button(btn_frame, text="Save Changes",
                  command=_save_edit,
                  font=("Segoe UI", 10, "bold"),
                  bg=TEAL_MID, fg=WHITE, activebackground=TEAL_DARK,
                  relief="flat", cursor="hand2",
                  padx=16, pady=8).pack(side="right")

    # ── Detail popup ──────────────────────────────────────────────────────────

    def _open_detail_window(self, p):
        win = tk.Toplevel(self.parent)
        win.title(f"Patient — {p['first_name']} {p['last_name']}")
        win.geometry("780x600")
        win.minsize(780, 600)
        win.resizable(True, True)
        win.grab_set()
        win.configure(bg=BG_LIGHT)

        # ── Header ────────────────────────────────────────────────────────────
        top = tk.Frame(win, bg=TEAL_DARK)
        top.pack(fill="x")
        tk.Label(top, text="Patient Details",
                 font=("Segoe UI", 13, "bold"),
                 bg=TEAL_DARK, fg=WHITE).pack(
                     side="left", padx=16, pady=13)

        s_bg, s_fg = {
            "Active":   STATUS_ACTIVE,
            "Unpaid":   STATUS_UNPAID,
            "Inactive": STATUS_INACTIVE,
        }.get(p["status"], STATUS_INACTIVE)
        tk.Label(top, text=f"● {p['status']}",
                 font=("Segoe UI", 9, "bold"),
                 bg=s_bg, fg=s_fg,
                 padx=10, pady=4).pack(side="left", padx=4)

        tk.Button(top, text="✏  Edit Patient",
                  command=lambda: [win.destroy(),
                                   self._open_edit_form(p)],
                  font=("Segoe UI", 9, "bold"),
                  bg=TEAL_ACCENT, fg=TEAL_DARK,
                  activebackground=TEAL_MID,
                  relief="flat", cursor="hand2",
                  padx=12, pady=5).pack(
                      side="right", padx=16, pady=10)

        # Unpaid balance banner
        if p.get("unpaid_bal", 0) > 0:
            banner = tk.Frame(win, bg="#fff5f5",
                              highlightbackground="#feb2b2",
                              highlightthickness=1)
            banner.pack(fill="x")
            tk.Label(banner,
                     text=f"⚠  Unpaid balance: "
                          f"₱{p['unpaid_bal']:,.2f}",
                     font=("Segoe UI", 10, "bold"),
                     bg="#fff5f5", fg="#c53030",
                     pady=8, padx=16).pack(anchor="w")

        # ── Body ──────────────────────────────────────────────────────────────
        body = tk.Frame(win, bg=BG_LIGHT)
        body.pack(fill="both", expand=True, padx=18, pady=14)

        pad = {"pady": 8}

        def _detail_card(title):
            outer = tk.Frame(body, bg=WHITE,
                             highlightbackground=BORDER,
                             highlightthickness=1)
            tk.Label(outer, text=title,
                     font=("Segoe UI", 10, "bold"),
                     bg=WHITE, fg=TEXT_MAIN,
                     pady=10, padx=14).pack(anchor="w")
            tk.Frame(outer, bg=BORDER, height=1).pack(fill="x")
            return outer

        def _grid_rows(card, row_data):
            g = tk.Frame(card, bg=WHITE)
            g.pack(fill="x", padx=16, pady=(0, 14))
            g.columnconfigure(1, weight=1)
            g.columnconfigure(3, weight=1)
            for ri, (l1, v1, l2, v2) in enumerate(row_data):
                tk.Label(g, text=l1 + ":",
                         font=("Segoe UI", 10), bg=WHITE,
                         fg=TEXT_MUTED, anchor="w").grid(
                             row=ri, column=0, sticky="w",
                             padx=(0, 10), pady=5)
                span = 3 if not l2 else 1
                tk.Label(g, text=v1,
                         font=("Segoe UI", 11, "bold"),
                         bg=WHITE, fg=TEXT_MAIN, anchor="w",
                         wraplength=260).grid(
                             row=ri, column=1, sticky="w",
                             pady=5, columnspan=span)
                if l2:
                    tk.Label(g, text=l2 + ":",
                             font=("Segoe UI", 10), bg=WHITE,
                             fg=TEXT_MUTED, anchor="w").grid(
                                 row=ri, column=2, sticky="w",
                                 padx=(24, 10), pady=5)
                    tk.Label(g, text=v2,
                             font=("Segoe UI", 11, "bold"),
                             bg=WHITE, fg=TEXT_MAIN, anchor="w").grid(
                                 row=ri, column=3, sticky="w",
                                 pady=5)

        age  = _calc_age(p["dob"])
        full = " ".join(filter(None, [p["first_name"],
                                      p["middle_name"],
                                      p["last_name"]]))

        # Personal info
        pc = _detail_card("Personal Information")
        pc.pack(fill="x", **pad)
        _grid_rows(pc, [
            ("Patient ID",    p["patient_id"],          "Full Name",     full),
            ("Date of Birth", p["dob"] or "—",           "Age / Sex",
             f"{age} / {p['sex']}"),
            ("Civil Status",  p["civil_status"] or "—", "PhilHealth No.",
             p["philhealth"] or "—"),
            ("Address",       p["address"] or "—",       "",              ""),
        ])

        # Contact info
        cc = _detail_card("Contact Information")
        cc.pack(fill="x", **pad)
        _grid_rows(cc, [
            ("Contact Number", p["contact"],       "Email",      p["email"] or "—"),
            ("Registered",     p["last_visit"],    "Status",     p["status"]),
        ])

        # Emergency contact
        ec = _detail_card("Emergency Contact")
        ec.pack(fill="x", **pad)
        _grid_rows(ec, [
            ("Name",    p["ec_name"] or "—",    "Relationship",
             p["ec_rel"] or "—"),
            ("Contact", p["ec_contact"] or "—", "",              ""),
        ])

        tk.Button(body, text="Close", command=win.destroy,
                  font=("Segoe UI", 10), bg=WHITE, fg=TEXT_MUTED,
                  relief="flat", cursor="hand2", padx=20, pady=8,
                  highlightbackground=BORDER,
                  highlightthickness=1).pack(
                      side="right", pady=(6, 0))

    # ── Widget helpers ────────────────────────────────────────────────────────

    def _stat_chip(self, parent, value, label, bg, fg):
        chip = tk.Frame(parent, bg=bg,
                        highlightbackground=BORDER,
                        highlightthickness=1)
        chip.pack(side="left", padx=4)
        lbl = tk.Label(chip, text=f" {value} {label} ",
                       font=("Segoe UI", 9, "bold"),
                       bg=bg, fg=fg, pady=5, padx=6)
        lbl.pack()
        return chip, lbl