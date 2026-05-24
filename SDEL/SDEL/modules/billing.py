# modules/billing.py
# ─────────────────────────────────────────────────────────────────────────────
#  PureHealth Diagnostic Center — Billing & Payments Module
#  CONNECTED TO DATABASE — bills and payments save to purehealthDb.db
#  FIXED: Reads the test menu directly from services.py
# ─────────────────────────────────────────────────────────────────────────────

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
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
GREEN_BG = "#f0fff4"
GREEN_FG = "#276749"
RED_BG = "#fff5f5"
RED_FG = "#c53030"
YELLOW_BG = "#fffff0"
YELLOW_FG = "#975a16"

DISCOUNT_OPTIONS = {
    "None": 0,
    "Senior Citizen (20%)": 20,
    "PWD (20%)": 20,
    "Employee (10%)": 10,
    "PhilHealth (5%)": 5,
}


# ─────────────────────────────────────────────────────────────────────────────
class BillingModule:
    # ─────────────────────────────────────────────────────────────────────────────

    def __init__(self, parent):
        self.parent = parent
        self._reset_state()

    # ── State ─────────────────────────────────────────────────────────────────

    def _reset_state(self):
        self.current_patient = None  # full DB row
        self.added_services = []  # list of DB service rows
        self.subtotal = 0.0
        self.discount_pct = 0

    # ── Entry point ───────────────────────────────────────────────────────────

    def show(self):
        for w in self.parent.winfo_children():
            w.destroy()
        self._reset_state()
        self.parent.configure(bg=BG_LIGHT)
        self._build_ui()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Header ────────────────────────────────────────────────────────────
        header = tk.Frame(self.parent, bg=WHITE)
        header.pack(fill="x")
        tk.Frame(header, bg=BORDER, height=1).pack(
            fill="x", side="bottom")

        title_block = tk.Frame(header, bg=WHITE)
        title_block.pack(side="left", padx=20, pady=12)
        tk.Label(title_block, text="Billing & Payments",
                 font=("Segoe UI", 16, "bold"),
                 bg=WHITE, fg=TEXT_MAIN).pack(anchor="w")
        tk.Label(title_block,
                 text="Create bills, collect payments, print receipts",
                 font=("Segoe UI", 10),
                 bg=WHITE, fg=TEXT_MUTED).pack(anchor="w")

        btn_frame = tk.Frame(header, bg=WHITE)
        btn_frame.pack(side="right", padx=20)
        self._outline_btn(btn_frame, "Unpaid Balances",
                          self._show_unpaid).pack(
            side="left", padx=(0, 8))
        self._solid_btn(btn_frame, "+ New Bill",
                        self.show).pack(side="left")

        # ── Body: left + right columns ────────────────────────────────────────
        body = tk.Frame(self.parent, bg=BG_LIGHT)
        body.pack(fill="both", expand=True, padx=18, pady=14)

        left = tk.Frame(body, bg=BG_LIGHT)
        left.pack(side="left", fill="both",
                  expand=True, padx=(0, 12))

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

        tk.Label(card, text="PATIENT",
                 font=("Segoe UI", 9, "bold"),
                 bg=WHITE, fg=TEXT_MUTED).pack(
            anchor="w", padx=16, pady=(14, 6))

        search_row = tk.Frame(card, bg=WHITE)
        search_row.pack(fill="x", padx=16, pady=(0, 10))

        self.search_entry = ctk.CTkEntry(
            search_row,
            placeholder_text="Search patient by name or ID...",
            font=("Segoe UI", 12), height=36,
            corner_radius=8, border_color=BORDER,
            fg_color=WHITE, text_color=TEXT_MAIN)
        self.search_entry.pack(side="left", fill="x",
                               expand=True, padx=(0, 8))
        self.search_entry.bind(
            "<Return>", lambda e: self._search_patient())

        self._solid_btn(search_row, "Search",
                        self._search_patient).pack(side="left")

        # Patient display area
        self.patient_display = tk.Frame(card, bg=WHITE)
        self.patient_display.pack(
            fill="x", padx=16, pady=(0, 14))
        self._show_patient_hint()

    def _show_patient_hint(self):
        for w in self.patient_display.winfo_children():
            w.destroy()
        hint = tk.Frame(self.patient_display, bg="#f8fafc",
                        highlightbackground=BORDER,
                        highlightthickness=1)
        hint.pack(fill="x")
        tk.Label(hint,
                 text="No patient selected. "
                      "Search above to find a patient.",
                 font=("Segoe UI", 10),
                 bg="#f8fafc", fg=TEXT_HINT,
                 pady=12).pack()

    def _show_patient_chip(self, patient):
        for w in self.patient_display.winfo_children():
            w.destroy()

        chip = tk.Frame(self.patient_display, bg="#f0f9ff",
                        highlightbackground="#bae6fd",
                        highlightthickness=1)
        chip.pack(fill="x")

        inner = tk.Frame(chip, bg="#f0f9ff")
        inner.pack(fill="x", padx=12, pady=10)

        # Initials avatar
        initials = (patient["first_name"][0]
                    + patient["last_name"][0]).upper()
        tk.Label(inner, text=initials,
                 font=("Segoe UI", 11, "bold"),
                 bg=TEAL_ACCENT, fg=WHITE,
                 width=3, height=1).pack(
            side="left", padx=(0, 10))

        info = tk.Frame(inner, bg="#f0f9ff")
        info.pack(side="left", fill="x", expand=True)
        full_name = (f"{patient['last_name']}, "
                     f"{patient['first_name']}")
        tk.Label(info, text=full_name,
                 font=("Segoe UI", 12, "bold"),
                 bg="#f0f9ff", fg=TEXT_MAIN).pack(anchor="w")
        tk.Label(info,
                 text=f"{patient['patient_code']}  ·  "
                      f"{patient['sex'] or ''}",
                 font=("Segoe UI", 9),
                 bg="#f0f9ff", fg=TEXT_MUTED).pack(anchor="w")

        tk.Button(inner, text="✕",
                  font=("Segoe UI", 10),
                  bg="#f0f9ff", fg=TEXT_MUTED,
                  bd=0, cursor="hand2",
                  command=self._clear_patient).pack(side="right")

        # Unpaid balance warning
        unpaid = db.get_patient_unpaid_total(patient["id"])
        if unpaid > 0:
            warn = tk.Frame(self.patient_display,
                            bg=YELLOW_BG,
                            highlightbackground="#f6e05e",
                            highlightthickness=1)
            warn.pack(fill="x", pady=(4, 0))
            tk.Label(warn,
                     text=f"⚠  Existing unpaid balance: "
                          f"₱{unpaid:,.2f}",
                     font=("Segoe UI", 9),
                     bg=YELLOW_BG, fg=YELLOW_FG,
                     pady=7, padx=12).pack(anchor="w")

    def _search_patient(self):
        query = self.search_entry.get().strip()
        if not query:
            messagebox.showwarning(
                "Search", "Please enter a name or patient ID.")
            return

        # Search from real database
        results = db.search_patients(query)

        if not results:
            messagebox.showinfo(
                "Not Found",
                f"No patient found matching \"{query}\".\n"
                "Make sure the patient is registered first.")
            return

        if len(results) == 1:
            # Only one match — select directly
            self.current_patient = results[0]
            self._show_patient_chip(results[0])
        else:
            # Multiple matches — show picker
            self._show_patient_picker(results)

    def _show_patient_picker(self, results):
        """Popup to pick from multiple search results."""
        win = tk.Toplevel(self.parent)
        win.title("Select Patient")
        win.geometry("500x360")
        win.grab_set()
        win.configure(bg=WHITE)

        tk.Frame(win, bg=TEAL_DARK,
                 height=44).pack(fill="x")
        tk.Label(win, text="Multiple patients found — select one:",
                 font=("Segoe UI", 11, "bold"),
                 bg=TEAL_DARK, fg=WHITE).place(x=14, y=12)

        style = ttk.Style()
        style.configure("Pick.Treeview",
                        rowheight=32,
                        font=("Segoe UI", 10))
        style.configure("Pick.Treeview.Heading",
                        font=("Segoe UI", 9, "bold"))

        cols = ("code", "name", "contact")
        tree = ttk.Treeview(win, columns=cols,
                            show="headings",
                            style="Pick.Treeview",
                            height=8)
        tree.heading("code", text="Patient ID")
        tree.heading("name", text="Full Name")
        tree.heading("contact", text="Contact")
        tree.column("code", width=130)
        tree.column("name", width=200)
        tree.column("contact", width=130)

        for r in results:
            tree.insert("", "end",
                        values=(
                            r["patient_code"],
                            f"{r['last_name']}, {r['first_name']}",
                            r["contact_number"] or "—"),
                        iid=str(r["id"]))

        tree.pack(fill="both", expand=True,
                  padx=16, pady=(52, 8))

        def select():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning(
                    "Select", "Please click a patient first.")
                return
            pid = int(sel[0])
            picked = db.get_patient_by_id(pid)
            self.current_patient = picked
            self._show_patient_chip(picked)
            win.destroy()

        tk.Button(win, text="Select Patient",
                  command=select,
                  font=("Segoe UI", 10, "bold"),
                  bg=TEAL_DARK, fg=WHITE,
                  relief="flat", cursor="hand2",
                  padx=14, pady=7).pack(pady=(0, 12))

        tree.bind("<Double-1>", lambda e: select())

    def _clear_patient(self):
        self.current_patient = None
        self.search_entry.delete(0, "end")
        self._show_patient_hint()

    # ── Services / Tests section ──────────────────────────────────────────────

    def _build_tests_section(self, parent):
        card = self._card(parent)
        card.pack(fill="both", expand=True)

        hdr = tk.Frame(card, bg=WHITE)
        hdr.pack(fill="x", padx=16, pady=(14, 8))
        tk.Label(hdr, text="REQUESTED TESTS",
                 font=("Segoe UI", 9, "bold"),
                 bg=WHITE, fg=TEXT_MUTED).pack(side="left")
        self._solid_btn(hdr, "+ Add Test",
                        self._open_add_test).pack(side="right")

        # Table
        table_frame = tk.Frame(card, bg=WHITE)
        table_frame.pack(fill="both", expand=True,
                         padx=16, pady=(0, 8))

        style = ttk.Style()
        style.configure("Billing.Treeview",
                        background=WHITE,
                        fieldbackground=WHITE,
                        foreground=TEXT_MAIN,
                        rowheight=36,
                        font=("Segoe UI", 10))
        style.configure("Billing.Treeview.Heading",
                        background="#f8fafc",
                        foreground=TEXT_MUTED,
                        font=("Segoe UI", 9, "bold"),
                        relief="flat", padding=6)
        style.map("Billing.Treeview",
                  background=[("selected", "#e0f2fe")],
                  foreground=[("selected", TEXT_MAIN)])

        cols = ("test", "category", "price")
        self.test_tree = ttk.Treeview(
            table_frame, columns=cols,
            show="headings", style="Billing.Treeview")
        self.test_tree.heading("test", text="Test / Service")
        self.test_tree.heading("category", text="Category")
        self.test_tree.heading("price", text="Price")
        self.test_tree.column("test", width=320, anchor="w")
        self.test_tree.column("category", width=150, anchor="w")
        self.test_tree.column("price", width=100, anchor="e")

        sb = ttk.Scrollbar(table_frame, orient="vertical",
                           command=self.test_tree.yview)
        self.test_tree.configure(yscrollcommand=sb.set)
        self.test_tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self.tests_hint = tk.Label(
            card,
            text="No tests added yet. Click \"+ Add Test\" to begin.",
            font=("Segoe UI", 10),
            bg=WHITE, fg=TEXT_HINT, pady=10)
        self.tests_hint.pack()

        remove_row = tk.Frame(card, bg=WHITE)
        remove_row.pack(fill="x", padx=16, pady=(0, 10))
        self._outline_btn(remove_row, "Remove Selected",
                          self._remove_selected,
                          danger=True).pack(side="right")

    def _open_add_test(self):
        """Popup showing real services from the services.py file."""
        # 1. We import ServicesModule safely to grab your list
        try:
            from modules.services import ServicesModule
        except ImportError:
            from services import ServicesModule

        temp_loader = ServicesModule(None)
        raw_list = temp_loader.all_services

        # 2. Convert the list into the format the UI uses
        services = []
        for i, item in enumerate(raw_list):
            try:
                price_val = float(item[3].replace('₱', '').replace(',', ''))
            except ValueError:
                price_val = 0.0

            services.append({
                "id": i,
                "name": item[0],
                "category": item[1],
                "turnaround": item[2],
                "price": price_val
            })

        if not services:
            messagebox.showinfo(
                "No Services",
                "No services found in services.py.")
            return

        win = tk.Toplevel(self.parent)
        win.title("Add Test / Service")
        win.geometry("520x480")
        win.resizable(False, False)
        win.grab_set()
        win.configure(bg=WHITE)

        # Header
        hdr = tk.Frame(win, bg=TEAL_DARK, pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Add Test / Service",
                 font=("Segoe UI", 13, "bold"),
                 bg=TEAL_DARK, fg=WHITE).pack(
            side="left", padx=16)
        tk.Button(hdr, text="✕ Close",
                  font=("Segoe UI", 9),
                  bg=TEAL_DARK, fg=WHITE,
                  bd=0, cursor="hand2",
                  command=win.destroy).pack(
            side="right", padx=16)

        # Search bar
        search_var = tk.StringVar()
        sf = tk.Frame(win, bg=WHITE, pady=10)
        sf.pack(fill="x", padx=16)
        ctk.CTkEntry(sf,
                     placeholder_text="Search test name...",
                     textvariable=search_var,
                     font=("Segoe UI", 11), height=34,
                     corner_radius=8, border_color=BORDER,
                     fg_color=WHITE,
                     text_color=TEXT_MAIN).pack(fill="x")

        # Scrollable list
        list_frame = tk.Frame(win, bg=WHITE)
        list_frame.pack(fill="both", expand=True,
                        padx=16, pady=(0, 14))
        canvas = tk.Canvas(list_frame, bg=WHITE,
                           highlightthickness=0)
        sb = ttk.Scrollbar(list_frame, orient="vertical",
                           command=canvas.yview)
        inner = tk.Frame(canvas, bg=WHITE)
        inner.bind("<Configure>",
                   lambda e: canvas.configure(
                       scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        def render(filter_text=""):
            for w in inner.winfo_children():
                w.destroy()
            for svc in services:
                if filter_text and \
                        filter_text.lower() not in svc["name"].lower() \
                        and filter_text.lower() not in \
                        svc["category"].lower():
                    continue
                self._service_row(
                    inner, svc, win)

        render()
        search_var.trace_add(
            "write", lambda *_: render(search_var.get()))

    def _service_row(self, parent, svc, win):
        row = tk.Frame(parent, bg=WHITE, cursor="hand2",
                       highlightbackground=BORDER,
                       highlightthickness=1)
        row.pack(fill="x", pady=3)

        inner = tk.Frame(row, bg=WHITE)
        inner.pack(fill="x", padx=12, pady=8)

        left = tk.Frame(inner, bg=WHITE)
        left.pack(side="left", fill="x", expand=True)
        tk.Label(left, text=svc["name"],
                 font=("Segoe UI", 11, "bold"),
                 bg=WHITE, fg=TEXT_MAIN).pack(anchor="w")
        tk.Label(left,
                 text=f"{svc['category']}  ·  "
                      f"{svc['turnaround'] or ''}",
                 font=("Segoe UI", 9),
                 bg=WHITE, fg=TEXT_MUTED).pack(anchor="w")

        tk.Label(inner,
                 text=f"₱{svc['price']:,.2f}",
                 font=("Segoe UI", 11, "bold"),
                 bg=WHITE, fg=TEAL_MID).pack(side="right")

        def on_enter(e):
            for w in [row, inner, left] + \
                     inner.winfo_children() + \
                     left.winfo_children():
                try:
                    w.configure(bg="#f0f9ff")
                except Exception:
                    pass

        def on_leave(e):
            for w in [row, inner, left] + \
                     inner.winfo_children() + \
                     left.winfo_children():
                try:
                    w.configure(bg=WHITE)
                except Exception:
                    pass

        def on_click(e, s=svc):
            self._add_service(s)
            win.destroy()

        for widget in [row, inner, left] + \
                      inner.winfo_children() + \
                      left.winfo_children():
            try:
                widget.bind("<Enter>", on_enter)
                widget.bind("<Leave>", on_leave)
                widget.bind("<Button-1>", on_click)
            except Exception:
                pass

    def _add_service(self, svc):
        # Prevent duplicates
        existing_ids = [s["id"] for s in self.added_services]
        if svc["id"] in existing_ids:
            messagebox.showinfo(
                "Already Added",
                f'"{svc["name"]}" is already in the bill.')
            return

        self.added_services.append(svc)
        tag = "even" if len(self.added_services) % 2 == 0 \
            else "odd"
        self.test_tree.insert(
            "", "end",
            values=(svc["name"], svc["category"],
                    f"₱{svc['price']:,.2f}"),
            tags=(tag,),
            iid=str(svc["id"]))
        self.test_tree.tag_configure(
            "even", background="#f8fafc")
        self.test_tree.tag_configure(
            "odd", background=WHITE)

        self.subtotal += svc["price"]
        self.tests_hint.pack_forget()
        self._update_summary()

    def _remove_selected(self):
        sel = self.test_tree.selection()
        if not sel:
            messagebox.showwarning(
                "Remove",
                "Please click a test row to select it first.")
            return
        for iid in sel:
            svc_id = int(iid)
            self.added_services = [
                s for s in self.added_services
                if s["id"] != svc_id]
            vals = self.test_tree.item(iid, "values")
            price_str = vals[2].replace("₱", "").replace(",", "")
            self.subtotal = max(
                0.0, self.subtotal - float(price_str))
            self.test_tree.delete(iid)

        if not self.added_services:
            self.tests_hint.pack()
        self._update_summary()

    # ── Payment panel ─────────────────────────────────────────────────────────

    def _build_payment_panel(self, parent):
        card = self._card(parent)
        card.pack(fill="both", expand=True)
        pad = {"padx": 16}

        tk.Label(card, text="PAYMENT SUMMARY",
                 font=("Segoe UI", 9, "bold"),
                 bg=WHITE, fg=TEXT_MUTED).pack(
            anchor="w", pady=(14, 10), **pad)

        self._summary_row(card, "Subtotal",
                          "subtotal_lbl", "₱0.00")
        tk.Frame(card, bg=BORDER,
                 height=1).pack(fill="x", padx=16, pady=8)

        # Discount
        tk.Label(card, text="Discount",
                 font=("Segoe UI", 10),
                 bg=WHITE, fg=TEXT_MUTED).pack(
            anchor="w", **pad)
        self.discount_var = tk.StringVar(value="None")
        ctk.CTkComboBox(
            card,
            values=list(DISCOUNT_OPTIONS.keys()),
            variable=self.discount_var,
            font=("Segoe UI", 10), height=32,
            corner_radius=6, border_color=BORDER,
            fg_color=WHITE, text_color=TEXT_MAIN,
            command=self._on_discount_change
        ).pack(fill="x", padx=16, pady=(4, 0))

        self.discount_row = tk.Frame(card, bg=WHITE)
        self.discount_row.pack(
            fill="x", padx=16, pady=(4, 0))
        tk.Label(self.discount_row,
                 text="Discount amount:",
                 font=("Segoe UI", 9),
                 bg=WHITE, fg=TEXT_MUTED).pack(side="left")
        self.discount_lbl = tk.Label(
            self.discount_row, text="— ₱0.00",
            font=("Segoe UI", 9, "bold"),
            bg=WHITE, fg=GREEN_FG)
        self.discount_lbl.pack(side="right")
        self.discount_row.pack_forget()

        tk.Frame(card, bg=BORDER,
                 height=1).pack(fill="x", padx=16, pady=8)

        # Total
        total_row = tk.Frame(card, bg=WHITE)
        total_row.pack(fill="x", **pad)
        tk.Label(total_row, text="Total",
                 font=("Segoe UI", 13, "bold"),
                 bg=WHITE, fg=TEXT_MAIN).pack(side="left")
        self.total_lbl = tk.Label(
            total_row, text="₱0.00",
            font=("Segoe UI", 16, "bold"),
            bg=WHITE, fg=TEAL_DARK)
        self.total_lbl.pack(side="right")

        tk.Frame(card, bg=BORDER,
                 height=1).pack(fill="x", padx=16, pady=10)

        # Payment method
        tk.Label(card, text="Payment Method",
                 font=("Segoe UI", 10, "bold"),
                 bg=WHITE, fg=TEXT_MAIN).pack(
            anchor="w", **pad)
        self.payment_var = tk.StringVar(value="Cash")
        method_row = tk.Frame(card, bg=WHITE)
        method_row.pack(fill="x", padx=16, pady=(6, 0))
        method_row.columnconfigure(0, weight=1)
        method_row.columnconfigure(1, weight=1)
        self.cash_btn = self._method_btn(
            method_row, "Cash", "Cash", 0)
        self.online_btn = self._method_btn(
            method_row, "Online", "Online", 1)
        self._highlight_method("Cash")

        tk.Frame(card, bg=BORDER,
                 height=1).pack(fill="x", padx=16, pady=10)

        # Amount received
        tk.Label(card, text="Amount Received",
                 font=("Segoe UI", 10),
                 bg=WHITE, fg=TEXT_MUTED).pack(
            anchor="w", **pad)
        self.amount_entry = ctk.CTkEntry(
            card, placeholder_text="0.00",
            font=("Segoe UI", 13), height=38,
            corner_radius=8, border_color=BORDER,
            fg_color=WHITE, text_color=TEXT_MAIN,
            justify="right")
        self.amount_entry.pack(
            fill="x", padx=16, pady=(4, 0))
        self.amount_entry.bind(
            "<KeyRelease>",
            lambda e: self.parent.after(10, self._calc_change))

        # Change
        self.change_frame = tk.Frame(
            card, bg=GREEN_BG,
            highlightbackground="#9ae6b4",
            highlightthickness=1)
        self.change_frame.pack(
            fill="x", padx=16, pady=(6, 0))
        ci = tk.Frame(self.change_frame, bg=GREEN_BG)
        ci.pack(fill="x", padx=10, pady=7)
        tk.Label(ci, text="Change",
                 font=("Segoe UI", 10),
                 bg=GREEN_BG, fg=GREEN_FG).pack(side="left")
        self.change_lbl = tk.Label(
            ci, text="₱0.00",
            font=("Segoe UI", 11, "bold"),
            bg=GREEN_BG, fg=GREEN_FG)
        self.change_lbl.pack(side="right")

        tk.Frame(card, bg=BORDER,
                 height=1).pack(fill="x", padx=16, pady=10)

        # Action buttons
        self._solid_btn(card,
                        "Process Payment & Print Receipt",
                        self._process_payment,
                        wide=True).pack(fill="x", padx=16)
        self._outline_btn(
            card, "Save as Unpaid Balance",
            self._save_unpaid).pack(
            fill="x", padx=16, pady=(6, 4))
        tk.Label(card,
                 text="Official receipt auto-prints "
                      "after processing",
                 font=("Segoe UI", 8),
                 bg=WHITE, fg=TEXT_HINT).pack(
            pady=(0, 14))

    def _method_btn(self, parent, label, value, col):
        f = tk.Frame(parent, cursor="hand2",
                     highlightbackground=BORDER,
                     highlightthickness=1)
        f.grid(row=0, column=col, sticky="ew",
               padx=(0, 4) if col == 0 else (4, 0))
        tk.Label(f, text=label,
                 font=("Segoe UI", 11, "bold"),
                 bg=WHITE, fg=TEXT_MAIN,
                 pady=7).pack()
        f.bind("<Button-1>",
               lambda e, v=value: self._select_method(v))
        f.winfo_children()[0].bind(
            "<Button-1>",
            lambda e, v=value: self._select_method(v))
        return f

    def _select_method(self, value):
        self.payment_var.set(value)
        self._highlight_method(value)

    def _highlight_method(self, active):
        for btn, val in [
            (self.cash_btn, "Cash"),
            (self.online_btn, "Online")
        ]:
            if val == active:
                btn.configure(
                    bg="#e0f2fe",
                    highlightbackground=TEAL_ACCENT,
                    highlightthickness=2)
                btn.winfo_children()[0].configure(
                    bg="#e0f2fe", fg=TEAL_DARK)
            else:
                btn.configure(
                    bg=WHITE,
                    highlightbackground=BORDER,
                    highlightthickness=1)
                btn.winfo_children()[0].configure(
                    bg=WHITE, fg=TEXT_MAIN)

    # ── Summary calculations ──────────────────────────────────────────────────

    def _summary_row(self, parent, label, attr, initial):
        row = tk.Frame(parent, bg=WHITE)
        row.pack(fill="x", padx=16, pady=2)
        tk.Label(row, text=label,
                 font=("Segoe UI", 10),
                 bg=WHITE, fg=TEXT_MUTED).pack(side="left")
        lbl = tk.Label(row, text=initial,
                       font=("Segoe UI", 10),
                       bg=WHITE, fg=TEXT_MAIN)
        lbl.pack(side="right")
        setattr(self, attr, lbl)

    def _update_summary(self):
        disc_amt = self.subtotal * (self.discount_pct / 100)
        total = max(0.0, self.subtotal - disc_amt)
        self.subtotal_lbl.configure(
            text=f"₱{self.subtotal:,.2f}")
        self.total_lbl.configure(
            text=f"₱{total:,.2f}")
        if self.discount_pct > 0:
            self.discount_row.pack(
                fill="x", padx=16, pady=(4, 0))
            self.discount_lbl.configure(
                text=f"— ₱{disc_amt:,.2f}")
        else:
            self.discount_row.pack_forget()
        self._calc_change()

    def _on_discount_change(self, choice):
        self.discount_pct = DISCOUNT_OPTIONS.get(choice, 0)
        self._update_summary()

    def _calc_change(self):
        try:
            total_text = self.total_lbl.cget("text")
            for ch in ["₱", ",", " "]:
                total_text = total_text.replace(ch, "")
            total = float(total_text)

            recv_text = self.amount_entry.get().strip()
            for ch in ["₱", ",", " "]:
                recv_text = recv_text.replace(ch, "")
            if not recv_text:
                self.change_lbl.configure(
                    text="₱0.00", fg=GREEN_FG)
                self.change_frame.configure(
                    bg=GREEN_BG,
                    highlightbackground="#9ae6b4")
                return
            recv = float(recv_text)

        except (ValueError, AttributeError):
            return

        change = recv - total

        if change >= 0:
            self.change_frame.configure(
                bg=GREEN_BG,
                highlightbackground="#9ae6b4")
            self.change_lbl.configure(
                text=f"₱{change:,.2f}",
                fg=GREEN_FG, bg=GREEN_BG)
        else:
            self.change_frame.configure(
                bg=RED_BG,
                highlightbackground="#feb2b2")
            self.change_lbl.configure(
                text=f"Short by ₱{abs(change):,.2f}",
                fg=RED_FG, bg=RED_BG)

        # Force tkinter to visually refresh
        self.change_frame.update_idletasks()

    # ── Actions — SAVES TO DATABASE ───────────────────────────────────────────

    def _process_payment(self):
        if not self._validate():
            return

        disc_type = self.discount_var.get()
        disc_pct = DISCOUNT_OPTIONS.get(disc_type, 0)
        disc_amt = self.subtotal * (disc_pct / 100)
        total = max(0.0, self.subtotal - disc_amt)
        method = self.payment_var.get()

        try:
            recv = float(
                self.amount_entry.get()
                .replace("₱", "").replace(",", ""))
        except ValueError:
            recv = total

        service_ids = [s["id"] for s in self.added_services]

        try:
            bill_id = db.create_bill(
                patient_id=self.current_patient["id"],
                service_ids=service_ids,
                discount_type=disc_type,
                discount_amount=disc_amt,
                payment_method=method,
                amount_received=recv,
                status="Paid",
            )
            db.log_action(
                "receptionist",
                "Bill Created & Paid",
                f"Bill #{bill_id} — "
                f"{self.current_patient['patient_code']} — "
                f"₱{total:,.2f}")

            messagebox.showinfo(
                "Payment Processed ✓",
                f"Payment saved successfully!\n\n"
                f"Bill No.  : #{bill_id}\n"
                f"Patient   : {self.current_patient['last_name']}"
                f", {self.current_patient['first_name']}\n"
                f"Total     : ₱{total:,.2f}\n"
                f"Method    : {method}\n\n"
                f"Official receipt sent to printer.")
            self.show()  # reset for next bill

        except Exception as ex:
            messagebox.showerror(
                "Save Error",
                f"Could not save the bill:\n{ex}")

    def _save_unpaid(self):
        if not self._validate():
            return

        disc_type = self.discount_var.get()
        disc_pct = DISCOUNT_OPTIONS.get(disc_type, 0)
        disc_amt = self.subtotal * (disc_pct / 100)
        service_ids = [s["id"] for s in self.added_services]

        try:
            bill_id = db.create_bill(
                patient_id=self.current_patient["id"],
                service_ids=service_ids,
                discount_type=disc_type,
                discount_amount=disc_amt,
                payment_method="—",
                amount_received=0.0,
                status="Unpaid",
            )
            db.log_action(
                "receptionist",
                "Bill Saved as Unpaid",
                f"Bill #{bill_id} — "
                f"{self.current_patient['patient_code']}")

            total = max(0.0, self.subtotal - disc_amt)
            messagebox.showinfo(
                "Saved as Unpaid",
                f"Bill saved as unpaid balance.\n\n"
                f"Bill No. : #{bill_id}\n"
                f"Patient  : {self.current_patient['last_name']}"
                f", {self.current_patient['first_name']}\n"
                f"Amount   : ₱{total:,.2f}\n\n"
                f"Collect later under \"Unpaid Balances\".")
            self.show()

        except Exception as ex:
            messagebox.showerror(
                "Save Error",
                f"Could not save the bill:\n{ex}")

    def _validate(self):
        if not self.current_patient:
            messagebox.showwarning(
                "No Patient",
                "Please search and select a patient first.")
            return False
        if not self.added_services:
            messagebox.showwarning(
                "No Tests",
                "Please add at least one test to the bill.")
            return False
        return True

    # ── Unpaid balances popup ─────────────────────────────────────────────────

    def _show_unpaid(self):
        unpaid_bills = db.get_unpaid_bills()
        win = tk.Toplevel(self.parent)
        win.title("Unpaid Balances")
        win.geometry("700x440")
        win.grab_set()
        win.configure(bg=WHITE)

        # Header
        hdr = tk.Frame(win, bg=RED_FG)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Unpaid Balances",
                 font=("Segoe UI", 13, "bold"),
                 bg=RED_FG, fg=WHITE).pack(
            side="left", padx=16, pady=12)
        tk.Label(hdr,
                 text=f"{len(unpaid_bills)} accounts",
                 font=("Segoe UI", 10),
                 bg=RED_FG, fg=WHITE).pack(
            side="right", padx=16)

        # Table
        style = ttk.Style()
        style.configure("Unpaid.Treeview",
                        rowheight=34,
                        font=("Segoe UI", 10))
        style.configure("Unpaid.Treeview.Heading",
                        font=("Segoe UI", 9, "bold"))

        cols = ("bill", "patient", "code", "amount", "date")
        tree = ttk.Treeview(win, columns=cols,
                            show="headings",
                            style="Unpaid.Treeview")
        tree.heading("bill", text="Bill #")
        tree.heading("patient", text="Patient Name")
        tree.heading("code", text="Patient ID")
        tree.heading("amount", text="Amount Due")
        tree.heading("date", text="Date Created")
        tree.column("bill", width=60, anchor="center")
        tree.column("patient", width=180, anchor="w")
        tree.column("code", width=130, anchor="w")
        tree.column("amount", width=110, anchor="e")
        tree.column("date", width=120, anchor="center")

        total_due = 0.0
        for r in unpaid_bills:
            tree.insert("", "end",
                        values=(
                            f"#{r['id']}",
                            r["patient_name"],
                            r["patient_code"],
                            f"₱{r['total']:,.2f}",
                            str(r["created_at"])[:10]),
                        iid=str(r["id"]))
            total_due += r["total"]

        tree.pack(fill="both", expand=True, padx=16, pady=12)

        # Bottom bar
        bottom = tk.Frame(win, bg=RED_BG)
        bottom.pack(fill="x", padx=16, pady=(0, 12))

        tk.Label(bottom,
                 text=f"Total Outstanding:  ₱{total_due:,.2f}",
                 font=("Segoe UI", 11, "bold"),
                 bg=RED_BG, fg=RED_FG,
                 pady=8, padx=14).pack(side="left")

        def collect_selected():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning(
                    "No Selection",
                    "Please click an unpaid bill first.")
                return
            bill_id = int(sel[0])
            # Find the bill record
            bill = next(
                (r for r in unpaid_bills
                 if r["id"] == bill_id), None)
            if not bill:
                return
            win.destroy()
            self._collect_unpaid(bill)

        tk.Button(bottom, text="Collect Payment",
                  command=collect_selected,
                  font=("Segoe UI", 10, "bold"),
                  bg=TEAL_DARK, fg=WHITE,
                  activebackground=TEAL_MID,
                  relief="flat", cursor="hand2",
                  padx=14, pady=7).pack(side="right")
        tk.Button(bottom, text="Close",
                  command=win.destroy,
                  font=("Segoe UI", 10),
                  bg=WHITE, fg=TEXT_MUTED,
                  relief="flat", cursor="hand2",
                  padx=14, pady=7).pack(
            side="right", padx=(0, 8))

        tree.bind("<Double-1>", lambda e: collect_selected())

    def _collect_unpaid(self, bill):
        """Open a payment popup for an existing unpaid bill."""
        patient = db.get_patient_by_id(bill["patient_id"])
        if not patient:
            messagebox.showerror("Error", "Patient not found.")
            return

        win = tk.Toplevel(self.parent)
        win.title(f"Collect Payment — Bill #{bill['id']}")
        win.geometry("400x480")
        win.resizable(False, False)
        win.grab_set()
        win.configure(bg=BG_LIGHT)

        # Header
        hdr = tk.Frame(win, bg=TEAL_DARK)
        hdr.pack(fill="x")
        tk.Label(hdr, text=f"Collect Payment — Bill #{bill['id']}",
                 font=("Segoe UI", 12, "bold"),
                 bg=TEAL_DARK, fg=WHITE).pack(
            side="left", padx=16, pady=12)

        body = tk.Frame(win, bg=WHITE,
                        highlightbackground=BORDER,
                        highlightthickness=1)
        body.pack(fill="both", expand=True,
                  padx=16, pady=12)

        # Patient info
        tk.Label(body,
                 text=f"{patient['last_name']}, "
                      f"{patient['first_name']}",
                 font=("Segoe UI", 13, "bold"),
                 bg=WHITE, fg=TEXT_MAIN).pack(
            anchor="w", padx=14, pady=(12, 2))
        tk.Label(body,
                 text=patient["patient_code"],
                 font=("Segoe UI", 9),
                 bg=WHITE, fg=TEXT_MUTED).pack(
            anchor="w", padx=14)

        tk.Frame(body, bg=BORDER,
                 height=1).pack(fill="x", padx=14, pady=10)

        # Amount due
        amt_row = tk.Frame(body, bg=WHITE)
        amt_row.pack(fill="x", padx=14, pady=4)
        tk.Label(amt_row, text="Amount Due",
                 font=("Segoe UI", 10),
                 bg=WHITE, fg=TEXT_MUTED).pack(side="left")
        tk.Label(amt_row,
                 text=f"₱{bill['total']:,.2f}",
                 font=("Segoe UI", 14, "bold"),
                 bg=WHITE, fg=TEAL_DARK).pack(side="right")

        tk.Frame(body, bg=BORDER,
                 height=1).pack(fill="x", padx=14, pady=10)

        # Payment method
        tk.Label(body, text="Payment Method",
                 font=("Segoe UI", 10),
                 bg=WHITE, fg=TEXT_MUTED).pack(
            anchor="w", padx=14)

        pay_var = tk.StringVar(value="Cash")
        method_row = tk.Frame(body, bg=WHITE)
        method_row.pack(fill="x", padx=14, pady=(6, 10))

        def make_method_btn(label, value, side):
            btn = tk.Frame(method_row, cursor="hand2",
                           highlightbackground=BORDER,
                           highlightthickness=1)
            btn.pack(side=side, fill="x",
                     expand=True,
                     padx=(0, 4) if side == "left"
                     else (4, 0))
            lbl = tk.Label(btn, text=label,
                           font=("Segoe UI", 10, "bold"),
                           bg=WHITE, fg=TEXT_MAIN, pady=7)
            lbl.pack()

            def select(v=value, b=btn, l=lbl):
                pay_var.set(v)
                for f, fl in btns:
                    is_active = fl.cget("text") == label
                    f.configure(
                        bg="#e0f2fe"
                        if is_active else WHITE,
                        highlightbackground=TEAL_ACCENT
                        if is_active else BORDER,
                        highlightthickness=2
                        if is_active else 1)
                    fl.configure(
                        bg="#e0f2fe"
                        if is_active else WHITE,
                        fg=TEAL_DARK
                        if is_active else TEXT_MAIN)

            btn.bind("<Button-1>", lambda e: select())
            lbl.bind("<Button-1>", lambda e: select())
            return btn, lbl

        btns = []
        b1, l1 = make_method_btn("Cash", "Cash", "left")
        b2, l2 = make_method_btn("Online", "Online", "right")
        btns = [(b1, l1), (b2, l2)]

        # Highlight Cash by default
        b1.configure(bg="#e0f2fe",
                     highlightbackground=TEAL_ACCENT,
                     highlightthickness=2)
        l1.configure(bg="#e0f2fe", fg=TEAL_DARK)

        # Amount received
        tk.Label(body, text="Amount Received",
                 font=("Segoe UI", 10),
                 bg=WHITE, fg=TEXT_MUTED).pack(
            anchor="w", padx=14)
        recv_entry = ctk.CTkEntry(
            body, placeholder_text="0.00",
            font=("Segoe UI", 13), height=36,
            corner_radius=6, border_color=BORDER,
            fg_color=WHITE, text_color=TEXT_MAIN,
            justify="right")
        recv_entry.pack(fill="x", padx=14, pady=(4, 12))

        def confirm():
            try:
                recv = float(
                    recv_entry.get()
                    .replace("₱", "").replace(",", ""))
            except ValueError:
                messagebox.showwarning(
                    "Invalid Amount",
                    "Please enter a valid amount received.")
                return

            total = bill["total"]
            if recv < total:
                if not messagebox.askyesno(
                        "Underpayment",
                        f"Amount received (₱{recv:,.2f}) is less "
                        f"than the total (₱{total:,.2f}).\n\n"
                        f"Save anyway as partial payment?"):
                    return

            change = max(0.0, recv - total)

            try:
                db.mark_bill_paid(
                    bill_id=bill["id"],
                    payment_method=pay_var.get(),
                    amount_received=recv,
                    change_amount=change)
                db.log_action(
                    "receptionist",
                    "Unpaid Bill Collected",
                    f"Bill #{bill['id']} — "
                    f"{patient['patient_code']} — "
                    f"₱{total:,.2f}")
                win.destroy()
                messagebox.showinfo(
                    "Payment Collected ✓",
                    f"Payment collected successfully!\n\n"
                    f"Bill No. : #{bill['id']}\n"
                    f"Patient  : {patient['last_name']}, "
                    f"{patient['first_name']}\n"
                    f"Paid     : ₱{recv:,.2f}\n"
                    f"Change   : ₱{change:,.2f}\n\n"
                    f"Receipt sent to printer.")
            except Exception as ex:
                messagebox.showerror(
                    "Error",
                    f"Could not update bill:\n{ex}")

        tk.Button(body, text="Confirm & Print Receipt",
                  command=confirm,
                  font=("Segoe UI", 11, "bold"),
                  bg=TEAL_DARK, fg=WHITE,
                  activebackground=TEAL_MID,
                  relief="flat", cursor="hand2",
                  padx=14, pady=9).pack(
            fill="x", padx=14, pady=(0, 14))

    # ── Widget helpers ────────────────────────────────────────────────────────

    def _card(self, parent):
        return tk.Frame(parent, bg=WHITE,
                        highlightbackground=BORDER,
                        highlightthickness=1)

    def _solid_btn(self, parent, text, command, wide=False):
        return tk.Button(parent, text=text,
                         command=command,
                         font=("Segoe UI", 10, "bold"),
                         bg=TEAL_DARK, fg=WHITE,
                         activebackground=TEAL_MID,
                         relief="flat", cursor="hand2",
                         padx=14, pady=7)

    def _outline_btn(self, parent, text,
                     command, danger=False):
        fg = RED_FG if danger else TEXT_MUTED
        return tk.Button(parent, text=text,
                         command=command,
                         font=("Segoe UI", 10),
                         bg=WHITE, fg=fg,
                         activebackground=BG_LIGHT,
                         relief="flat", bd=0,
                         cursor="hand2",
                         padx=14, pady=6)