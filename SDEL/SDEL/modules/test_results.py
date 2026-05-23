# modules/test_results.py
# ─────────────────────────────────────────────────────────────────────────────
#  PureHealth Diagnostic Center — Test Results Module (Receptionist View)
#  Improved design using CustomTkinter
#  Receptionist can VIEW and PRINT results only — no editing
#  BUG FIXED: show() clears frame before rebuilding — no stacking
# ─────────────────────────────────────────────────────────────────────────────

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from datetime import datetime

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

# Status colours
STATUS_DONE   = ("#d1fae5", "#065f46", "● Completed")
STATUS_PROG   = ("#dbeafe", "#1e40af", "◑ In Progress")
STATUS_PEND   = ("#fef9c3", "#854d0e", "○ Pending")

# Category badge colours  (bg, fg)
CAT_COLORS = {
    "Hematology":  ("#dbeafe", "#1e40af"),
    "Urinalysis":  ("#fef9c3", "#854d0e"),
    "Chemistry":   ("#f3f4f6", "#374151"),
    "Radiology":   ("#fee2e2", "#991b1b"),
    "Cardiology":  ("#ede9fe", "#5b21b6"),
    "Microbiology":("#d1fae5", "#065f46"),
}

# ── Sample data (replace with real DB queries later) ──────────────────────────
SAMPLE_RESULTS = [
    {
        "patient":     "Juan dela Cruz",
        "patient_id":  "PHC-2025-00124",
        "test":        "Complete Blood Count (CBC)",
        "category":    "Hematology",
        "date":        "May 5, 2025",
        "reviewed_by": "R. Garcia, RMT",
        "doctor":      "Dr. Jose Reyes, M.D.",
        "status":      "Completed",
        "parameters": [
            ("Hemoglobin",    "14.5", "g/dL",     "13.5 – 17.5", "Normal"),
            ("Hematocrit",    "42",   "%",         "41 – 53",     "Normal"),
            ("WBC Count",     "11.2", "×10³/µL",  "4.5 – 11.0",  "High"),
            ("Platelet Count","220",  "×10³/µL",  "150 – 400",   "Normal"),
            ("RBC Count",     "4.8",  "×10⁶/µL",  "4.5 – 5.9",  "Normal"),
        ],
        "remarks": "WBC count is slightly elevated. Clinical correlation recommended.",
    },
    {
        "patient":     "Ana Santos",
        "patient_id":  "PHC-2025-00123",
        "test":        "Chest X-Ray PA",
        "category":    "Radiology",
        "date":        "May 5, 2025",
        "reviewed_by": "B. Torres, RT",
        "doctor":      "Dr. Jose Reyes, M.D.",
        "status":      "In Progress",
        "parameters": [],
        "remarks":     "Radiograph being reviewed.",
    },
    {
        "patient":     "Pedro Bautista",
        "patient_id":  "PHC-2025-00122",
        "test":        "Blood Chemistry Panel",
        "category":    "Chemistry",
        "date":        "May 5, 2025",
        "reviewed_by": "—",
        "doctor":      "—",
        "status":      "Pending",
        "parameters": [],
        "remarks":     "",
    },
    {
        "patient":     "Liza Reyes",
        "patient_id":  "PHC-2025-00121",
        "test":        "Urinalysis",
        "category":    "Urinalysis",
        "date":        "May 5, 2025",
        "reviewed_by": "R. Garcia, RMT",
        "doctor":      "Dr. Jose Reyes, M.D.",
        "status":      "Completed",
        "parameters": [
            ("Color",       "Yellow",  "",      "Yellow",         "Normal"),
            ("Appearance",  "Clear",   "",      "Clear",          "Normal"),
            ("pH",          "6.0",     "",      "4.5 – 8.0",      "Normal"),
            ("Protein",     "Negative","",      "Negative",       "Normal"),
            ("Glucose",     "Negative","",      "Negative",       "Normal"),
            ("WBC",         "0–2",     "/hpf",  "0 – 5",          "Normal"),
            ("RBC",         "0–1",     "/hpf",  "0 – 3",          "Normal"),
        ],
        "remarks": "Results within normal limits.",
    },
    {
        "patient":     "Carlo Mendoza",
        "patient_id":  "PHC-2025-00120",
        "test":        "Electrocardiogram (ECG)",
        "category":    "Cardiology",
        "date":        "May 4, 2025",
        "reviewed_by": "R. Garcia, RMT",
        "doctor":      "Dr. Jose Reyes, M.D.",
        "status":      "Completed",
        "parameters": [
            ("Heart Rate",     "78",   "bpm",  "60 – 100",  "Normal"),
            ("PR Interval",    "160",  "ms",   "120 – 200", "Normal"),
            ("QRS Duration",   "88",   "ms",   "< 120",     "Normal"),
            ("QT Interval",    "380",  "ms",   "350 – 440", "Normal"),
        ],
        "remarks": "Normal sinus rhythm. No acute changes noted.",
    },
    {
        "patient":     "Rosa Garcia",
        "patient_id":  "PHC-2025-00119",
        "test":        "Fasting Blood Sugar (FBS)",
        "category":    "Chemistry",
        "date":        "May 4, 2025",
        "reviewed_by": "R. Garcia, RMT",
        "doctor":      "Dr. Clara Lim, M.D.",
        "status":      "Completed",
        "parameters": [
            ("Fasting Blood Sugar", "98", "mg/dL", "70 – 100", "Normal"),
        ],
        "remarks": "Fasting glucose within normal range.",
    },
]

CATEGORIES = ["All Categories", "Hematology", "Urinalysis",
               "Chemistry", "Radiology", "Cardiology", "Microbiology"]


# ─────────────────────────────────────────────────────────────────────────────
class TestResultsModule:
# ─────────────────────────────────────────────────────────────────────────────

    def __init__(self, parent):
        self.parent = parent
        self._all_results = SAMPLE_RESULTS   # swap for DB list later

    # ── Entry point ───────────────────────────────────────────────────────────

    def show(self):
        # FIX: clear old widgets before rebuilding — prevents stacking
        for w in self.parent.winfo_children():
            w.destroy()
        self.parent.configure(bg=BG_LIGHT)
        self._build_ui()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Page header ───────────────────────────────────────────────────────
        header = tk.Frame(self.parent, bg=WHITE)
        header.pack(fill="x")
        tk.Frame(header, bg=BORDER, height=1).pack(fill="x", side="bottom")

        title_block = tk.Frame(header, bg=WHITE)
        title_block.pack(side="left", padx=20, pady=12)
        tk.Label(title_block, text="Test Results",
                 font=("Segoe UI", 16, "bold"),
                 bg=WHITE, fg=TEXT_MAIN).pack(anchor="w")
        tk.Label(title_block,
                 text="View and print diagnostic results",
                 font=("Segoe UI", 10),
                 bg=WHITE, fg=TEXT_MUTED).pack(anchor="w")

        # Stats chips in header
        stats_bar = tk.Frame(header, bg=WHITE)
        stats_bar.pack(side="right", padx=20)
        done  = sum(1 for r in self._all_results if r["status"] == "Completed")
        prog  = sum(1 for r in self._all_results if r["status"] == "In Progress")
        pend  = sum(1 for r in self._all_results if r["status"] == "Pending")
        self._stat_chip(stats_bar, str(done), "Completed", *STATUS_DONE[:2])
        self._stat_chip(stats_bar, str(prog), "In Progress", *STATUS_PROG[:2])
        self._stat_chip(stats_bar, str(pend), "Pending",     *STATUS_PEND[:2])

        # ── Receptionist notice banner ────────────────────────────────────────
        banner = tk.Frame(self.parent, bg="#fffff0",
                          highlightbackground="#f6e05e",
                          highlightthickness=1)
        banner.pack(fill="x", padx=18, pady=(12, 0))
        tk.Label(banner,
                 text="ℹ  Receptionist access:  View and Print only.  "
                      "Result entry is done by the Med Technologist / Rad Tech.",
                 font=("Segoe UI", 9),
                 bg="#fffff0", fg="#975a16", pady=8, padx=14).pack(anchor="w")

        # ── Search & filter bar ───────────────────────────────────────────────
        filter_card = tk.Frame(self.parent, bg=WHITE,
                               highlightbackground=BORDER,
                               highlightthickness=1)
        filter_card.pack(fill="x", padx=18, pady=10)

        row = tk.Frame(filter_card, bg=WHITE)
        row.pack(fill="x", padx=14, pady=10)

        # Search entry
        self.search_entry = ctk.CTkEntry(
            row, placeholder_text="Search by patient name or ID...",
            font=("Segoe UI", 11), height=34, corner_radius=8,
            border_color=BORDER, fg_color=WHITE, text_color=TEXT_MAIN)
        self.search_entry.pack(side="left", fill="x", expand=True,
                               padx=(0, 8))
        self.search_entry.bind("<Return>", lambda e: self._apply_filters())

        # Category dropdown
        self.cat_var = tk.StringVar(value="All Categories")
        cat_combo = ctk.CTkComboBox(
            row, values=CATEGORIES,
            variable=self.cat_var,
            font=("Segoe UI", 10), height=34, width=160,
            corner_radius=8, border_color=BORDER,
            fg_color=WHITE, text_color=TEXT_MAIN,
            command=lambda _: self._apply_filters())
        cat_combo.pack(side="left", padx=(0, 8))

        # Status dropdown
        self.status_var = tk.StringVar(value="All Status")
        status_combo = ctk.CTkComboBox(
            row,
            values=["All Status", "Completed", "In Progress", "Pending"],
            variable=self.status_var,
            font=("Segoe UI", 10), height=34, width=140,
            corner_radius=8, border_color=BORDER,
            fg_color=WHITE, text_color=TEXT_MAIN,
            command=lambda _: self._apply_filters())
        status_combo.pack(side="left", padx=(0, 8))

        # Search & Clear buttons
        tk.Button(row, text="Search", command=self._apply_filters,
                  font=("Segoe UI", 10, "bold"),
                  bg=TEAL_DARK, fg=WHITE, activebackground=TEAL_MID,
                  relief="flat", cursor="hand2",
                  padx=14, pady=6).pack(side="left", padx=(0, 6))

        tk.Button(row, text="Clear", command=self._clear_filters,
                  font=("Segoe UI", 10),
                  bg=WHITE, fg=TEXT_MUTED,
                  relief="flat", cursor="hand2",
                  padx=10, pady=6).pack(side="left")

        # ── Results table ─────────────────────────────────────────────────────
        table_wrapper = tk.Frame(self.parent, bg=WHITE,
                                 highlightbackground=BORDER,
                                 highlightthickness=1)
        table_wrapper.pack(fill="both", expand=True, padx=18, pady=(0, 16))

        # Table header row
        tbl_hdr = tk.Frame(table_wrapper, bg="#f8fafc")
        tbl_hdr.pack(fill="x")
        tk.Frame(table_wrapper, bg=BORDER, height=1).pack(fill="x")
        self.result_count_lbl = tk.Label(
            tbl_hdr,
            text=f"{len(self._all_results)} results",
            font=("Segoe UI", 9), bg="#f8fafc",
            fg=TEXT_MUTED)
        self.result_count_lbl.pack(side="right", padx=14, pady=7)
        tk.Label(tbl_hdr, text="All Results",
                 font=("Segoe UI", 10, "bold"),
                 bg="#f8fafc", fg=TEXT_MAIN).pack(side="left", padx=14, pady=7)

        # Treeview style
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Results.Treeview",
                        background=WHITE,
                        fieldbackground=WHITE,
                        foreground=TEXT_MAIN,
                        rowheight=38,
                        font=("Segoe UI", 10))
        style.configure("Results.Treeview.Heading",
                        background="#f8fafc",
                        foreground=TEXT_MUTED,
                        font=("Segoe UI", 9, "bold"),
                        relief="flat", padding=8)
        style.map("Results.Treeview",
                  background=[("selected", "#e0f2fe")],
                  foreground=[("selected", TEXT_MAIN)])

        cols = ("patient", "patient_id", "test", "category",
                "date", "reviewed_by", "status")
        self.tree = ttk.Treeview(
            table_wrapper, columns=cols,
            show="headings", style="Results.Treeview")

        self.tree.heading("patient",     text="Patient")
        self.tree.heading("patient_id",  text="Patient ID")
        self.tree.heading("test",        text="Test / Procedure")
        self.tree.heading("category",    text="Category")
        self.tree.heading("date",        text="Date")
        self.tree.heading("reviewed_by", text="Reviewed By")
        self.tree.heading("status",      text="Status")

        self.tree.column("patient",     width=150, anchor="w")
        self.tree.column("patient_id",  width=130, anchor="w")
        self.tree.column("test",        width=210, anchor="w")
        self.tree.column("category",    width=110, anchor="w")
        self.tree.column("date",        width=100, anchor="center")
        self.tree.column("reviewed_by", width=150, anchor="w")
        self.tree.column("status",      width=110, anchor="center")

        vsb = ttk.Scrollbar(table_wrapper, orient="vertical",
                            command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # Double-click → view details
        self.tree.bind("<Double-1>", self._on_row_double_click)

        # Right-click context menu
        self.context_menu = tk.Menu(self.tree, tearoff=0,
                                    font=("Segoe UI", 10))
        self.context_menu.add_command(
            label="View Details", command=self._view_selected)
        self.context_menu.add_command(
            label="Print Result", command=self._print_selected)
        self.tree.bind("<Button-3>", self._show_context_menu)

        # ── Bottom action bar ─────────────────────────────────────────────────
        action_bar = tk.Frame(self.parent, bg=BG_LIGHT)
        action_bar.pack(fill="x", padx=18, pady=(0, 14))
        tk.Label(action_bar,
                 text="Double-click a row to view full result details",
                 font=("Segoe UI", 9), bg=BG_LIGHT,
                 fg=TEXT_HINT).pack(side="left")
        tk.Button(action_bar, text="Print Selected",
                  command=self._print_selected,
                  font=("Segoe UI", 10, "bold"),
                  bg=TEAL_DARK, fg=WHITE, activebackground=TEAL_MID,
                  relief="flat", cursor="hand2",
                  padx=14, pady=6).pack(side="right")
        tk.Button(action_bar, text="View Details",
                  command=self._view_selected,
                  font=("Segoe UI", 10),
                  bg=WHITE, fg=TEXT_MUTED,
                  relief="flat", cursor="hand2",
                  padx=14, pady=6,
                  highlightbackground=BORDER,
                  highlightthickness=1).pack(side="right", padx=(0, 8))

        # Load all results into table
        self._load_results(self._all_results)

    # ── Data helpers ──────────────────────────────────────────────────────────

    def _load_results(self, results):
        """Clear and repopulate the treeview."""
        for row in self.tree.get_children():
            self.tree.delete(row)

        for i, r in enumerate(results):
            status_label = {
                "Completed":   "● Completed",
                "In Progress": "◑ In Progress",
                "Pending":     "○ Pending",
            }.get(r["status"], r["status"])

            iid = self.tree.insert(
                "", "end",
                values=(r["patient"], r["patient_id"], r["test"],
                        r["category"], r["date"],
                        r["reviewed_by"], status_label),
                tags=(r["status"], "even" if i % 2 == 0 else "odd"))

        # Row colour tags
        self.tree.tag_configure("even", background=WHITE)
        self.tree.tag_configure("odd",  background="#f8fafc")

        # Status-specific foreground (applied via tag priority)
        self.tree.tag_configure("Completed",   foreground="#065f46")
        self.tree.tag_configure("In Progress", foreground="#1e40af")
        self.tree.tag_configure("Pending",     foreground="#854d0e")

        count = len(results)
        self.result_count_lbl.configure(
            text=f"{count} result{'s' if count != 1 else ''}")

    def _apply_filters(self):
        query     = self.search_entry.get().strip().lower()
        cat_sel   = self.cat_var.get()
        stat_sel  = self.status_var.get()

        filtered = [
            r for r in self._all_results
            if (not query
                or query in r["patient"].lower()
                or query in r["patient_id"].lower()
                or query in r["test"].lower())
            and (cat_sel  == "All Categories" or r["category"] == cat_sel)
            and (stat_sel == "All Status"     or r["status"]   == stat_sel)
        ]
        self._load_results(filtered)

    def _clear_filters(self):
        self.search_entry.delete(0, "end")
        self.cat_var.set("All Categories")
        self.status_var.set("All Status")
        self._load_results(self._all_results)

    # ── Interaction handlers ──────────────────────────────────────────────────

    def _get_selected_record(self):
        sel = self.tree.selection()
        if not sel:
            return None
        vals    = self.tree.item(sel[0], "values")
        pid     = vals[1]
        test    = vals[2]
        record  = next((r for r in self._all_results
                        if r["patient_id"] == pid
                        and r["test"] == test), None)
        return record

    def _on_row_double_click(self, event):
        self._view_selected()

    def _show_context_menu(self, event):
        try:
            self.tree.selection_set(
                self.tree.identify_row(event.y))
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def _view_selected(self):
        record = self._get_selected_record()
        if not record:
            messagebox.showinfo("No Selection",
                                "Please click on a result row first.")
            return
        self._open_detail_window(record)

    def _print_selected(self):
        record = self._get_selected_record()
        if not record:
            messagebox.showinfo("No Selection",
                                "Please click on a result row first.")
            return
        if record["status"] != "Completed":
            messagebox.showwarning(
                "Not Ready",
                f"This result is still \"{record['status']}\".\n"
                "Only completed results can be printed.")
            return
        messagebox.showinfo(
            "Printing ✓",
            f"Result sent to printer.\n\n"
            f"Patient : {record['patient']}\n"
            f"Test    : {record['test']}\n"
            f"Date    : {record['date']}")

    # ── Detail popup window ───────────────────────────────────────────────────

    def _open_detail_window(self, r):
        win = tk.Toplevel(self.parent)
        win.title(f"Result — {r['patient']} — {r['test']}")
        win.geometry("700x580")
        win.resizable(True, True)
        win.grab_set()
        win.configure(bg=BG_LIGHT)

        # ── Top header strip ──────────────────────────────────────────────────
        top = tk.Frame(win, bg=TEAL_DARK)
        top.pack(fill="x")
        tk.Label(top, text="Test Result",
                 font=("Segoe UI", 13, "bold"),
                 bg=TEAL_DARK, fg=WHITE).pack(side="left", padx=16, pady=12)

        # Status badge in header
        s_bg, s_fg, s_txt = {
            "Completed":   STATUS_DONE,
            "In Progress": STATUS_PROG,
            "Pending":     STATUS_PEND,
        }.get(r["status"], STATUS_PEND)
        tk.Label(top, text=s_txt,
                 font=("Segoe UI", 9, "bold"),
                 bg=s_bg, fg=s_fg, padx=10, pady=4).pack(
                     side="left", padx=4)

        # Print button in header (only if completed)
        if r["status"] == "Completed":
            tk.Button(top, text="🖨  Print Result",
                      command=lambda: self._print_selected(),
                      font=("Segoe UI", 10, "bold"),
                      bg=TEAL_ACCENT, fg=WHITE,
                      activebackground=TEAL_MID,
                      relief="flat", cursor="hand2",
                      padx=14, pady=6).pack(side="right", padx=16, pady=8)

        # ── Scrollable body ───────────────────────────────────────────────────
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

        # Mouse wheel scroll
        def _on_wheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_wheel)

        pad = {"padx": 18, "pady": 6}

        # ── Patient info card ─────────────────────────────────────────────────
        info_card = self._detail_card(body, "Patient Information")
        info_card.pack(fill="x", **pad)

        grid = tk.Frame(info_card, bg=WHITE)
        grid.pack(fill="x", padx=14, pady=(0, 14))
        grid.columnconfigure(1, weight=1)
        grid.columnconfigure(3, weight=1)

        fields = [
            ("Patient Name",  r["patient"],    "Patient ID",   r["patient_id"]),
            ("Test",          r["test"],        "Category",     r["category"]),
            ("Date",          r["date"],        "Reviewed By",  r["reviewed_by"]),
            ("Pathologist",   r["doctor"],      "Status",       r["status"]),
        ]
        for row_idx, (l1, v1, l2, v2) in enumerate(fields):
            tk.Label(grid, text=l1 + ":",
                     font=("Segoe UI", 9), bg=WHITE,
                     fg=TEXT_MUTED, anchor="w").grid(
                         row=row_idx, column=0, sticky="w",
                         padx=(0, 8), pady=3)
            tk.Label(grid, text=v1,
                     font=("Segoe UI", 10, "bold"), bg=WHITE,
                     fg=TEXT_MAIN, anchor="w").grid(
                         row=row_idx, column=1, sticky="w", pady=3)
            tk.Label(grid, text=l2 + ":",
                     font=("Segoe UI", 9), bg=WHITE,
                     fg=TEXT_MUTED, anchor="w").grid(
                         row=row_idx, column=2, sticky="w",
                         padx=(20, 8), pady=3)
            tk.Label(grid, text=v2,
                     font=("Segoe UI", 10, "bold"), bg=WHITE,
                     fg=TEXT_MAIN, anchor="w").grid(
                         row=row_idx, column=3, sticky="w", pady=3)

        # ── Parameters table (only if there are results) ──────────────────────
        if r["parameters"]:
            param_card = self._detail_card(body, "Test Parameters")
            param_card.pack(fill="x", **pad)

            # Build parameter table inside the card
            tbl_frame = tk.Frame(param_card, bg=WHITE)
            tbl_frame.pack(fill="x", padx=14, pady=(0, 14))

            headers = ["Parameter", "Result", "Unit", "Reference Range", "Flag"]
            col_widths = [190, 80, 80, 150, 90]

            # Header row
            hdr_row = tk.Frame(tbl_frame, bg="#f8fafc")
            hdr_row.pack(fill="x")
            tk.Frame(tbl_frame, bg=BORDER, height=1).pack(fill="x")
            for i, (h, w) in enumerate(zip(headers, col_widths)):
                tk.Label(hdr_row, text=h,
                         font=("Segoe UI", 9, "bold"),
                         bg="#f8fafc", fg=TEXT_MUTED,
                         width=w // 7, anchor="w",
                         pady=7, padx=8).pack(side="left")

            # Data rows
            for idx, (param, val, unit, ref, flag) in enumerate(r["parameters"]):
                row_bg = WHITE if idx % 2 == 0 else "#f8fafc"
                data_row = tk.Frame(tbl_frame, bg=row_bg)
                data_row.pack(fill="x")
                tk.Frame(tbl_frame, bg=BORDER, height=1).pack(fill="x")

                cells = [param, val, unit, ref]
                for i, (text, w) in enumerate(zip(cells, col_widths)):
                    font = ("Segoe UI", 10, "bold") if i == 1 else ("Segoe UI", 10)
                    fg   = TEXT_MAIN
                    if i == 1 and flag == "High":
                        fg = "#c53030"
                    elif i == 1 and flag == "Low":
                        fg = "#1e40af"
                    tk.Label(data_row, text=text, font=font,
                             bg=row_bg, fg=fg,
                             width=w // 7, anchor="w",
                             pady=7, padx=8).pack(side="left")

                # Flag badge
                f_bg = {"Normal": "#d1fae5", "High": "#fee2e2",
                        "Low": "#dbeafe"}.get(flag, "#f3f4f6")
                f_fg = {"Normal": "#065f46", "High": "#991b1b",
                        "Low": "#1e40af"}.get(flag, "#374151")
                tk.Label(data_row, text=flag,
                         font=("Segoe UI", 9, "bold"),
                         bg=f_bg, fg=f_fg,
                         padx=8, pady=3).pack(side="left", padx=4)

        else:
            # No parameters yet (Pending / In Progress)
            pending_card = self._detail_card(body, "Test Parameters")
            pending_card.pack(fill="x", **pad)
            tk.Label(pending_card,
                     text="Results have not been entered yet.\n"
                          "Please check back once the Med Technologist has "
                          "completed processing.",
                     font=("Segoe UI", 10), bg=WHITE,
                     fg=TEXT_HINT, pady=20).pack()

        # ── Remarks ───────────────────────────────────────────────────────────
        if r.get("remarks"):
            rem_card = self._detail_card(body, "Remarks / Interpretation")
            rem_card.pack(fill="x", **pad)
            tk.Label(rem_card, text=r["remarks"],
                     font=("Segoe UI", 10), bg=WHITE,
                     fg=TEXT_MAIN, wraplength=600,
                     justify="left", padx=14,
                     pady=(0, 14)).pack(anchor="w")

        # ── Signatures ────────────────────────────────────────────────────────
        if r["status"] == "Completed":
            sig_card = self._detail_card(body, "Verified & Signed By")
            sig_card.pack(fill="x", **pad)

            sig_row = tk.Frame(sig_card, bg=WHITE)
            sig_row.pack(fill="x", padx=14, pady=(0, 14))

            for role, name in [
                ("Medical Technologist", r["reviewed_by"]),
                ("Pathologist / Doctor", r["doctor"]),
            ]:
                box = tk.Frame(sig_row, bg="#f0fdf4",
                               highlightbackground="#86efac",
                               highlightthickness=1)
                box.pack(side="left", fill="x", expand=True, padx=(0, 8))
                tk.Label(box, text=role,
                         font=("Segoe UI", 8), bg="#f0fdf4",
                         fg=TEXT_MUTED, pady=4, padx=10).pack(anchor="w")
                tk.Label(box, text=f"✓  {name}",
                         font=("Segoe UI", 10, "bold"),
                         bg="#f0fdf4", fg="#15803d",
                         pady=6, padx=10).pack(anchor="w")

        # Close button
        tk.Button(body, text="Close",
                  command=lambda: [
                      canvas.unbind_all("<MouseWheel>"),
                      win.destroy()],
                  font=("Segoe UI", 10),
                  bg=WHITE, fg=TEXT_MUTED,
                  relief="flat", cursor="hand2",
                  padx=20, pady=8,
                  highlightbackground=BORDER,
                  highlightthickness=1).pack(pady=(6, 18))

    # ── Widget helpers ────────────────────────────────────────────────────────
    def _detail_card(self, parent, title):
        """A white card with a bold section title."""
        outer = tk.Frame(parent, bg=WHITE,
                         highlightbackground=BORDER,
                         highlightthickness=1)
        tk.Label(outer, text=title,
                 font=("Segoe UI", 10, "bold"),
                 bg=WHITE, fg=TEXT_MAIN,
                 pady=10, padx=14).pack(anchor="w")
        tk.Frame(outer, bg=BORDER, height=1).pack(fill="x")
        return outer

    def _stat_chip(self, parent, value, label, bg, fg):
        """Small stat badge shown in the page header."""
        chip = tk.Frame(parent, bg=bg,
                        highlightbackground=BORDER,
                        highlightthickness=1)
        chip.pack(side="left", padx=4)
        tk.Label(chip, text=f" {value} {label} ",
                 font=("Segoe UI", 9, "bold"),
                 bg=bg, fg=fg, pady=5, padx=6).pack()