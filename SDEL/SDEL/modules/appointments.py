# modules/appointments.py
# ─────────────────────────────────────────────────────────────────────────────
#  PureHealth Diagnostic Center — Appointments Module
#  CONNECTED TO DATABASE — saves/loads from purehealthDb.db
#  All original UI features kept (calendar, stats, table, dialogs)
#  BUG FIXED: show() clears frame before rebuilding
# ─────────────────────────────────────────────────────────────────────────────

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from datetime import datetime, date
import calendar
from database import db

# ── Colour palette ─────────────────────────────────────────────────────────────
TEAL_DARK  = "#073b4c"
TEAL_MID   = "#0c637f"
TEAL_ACCENT= "#0cb0a9"
WHITE      = "#ffffff"
BG_LIGHT   = "#f4f6f8"
BORDER     = "#e2e8f0"
TEXT_MAIN  = "#1a202c"
TEXT_MUTED = "#718096"
TEXT_HINT  = "#a0aec0"
BLUE_BG    = "#dbeafe"
BLUE_FG    = "#1e40af"
GREEN_BG   = "#f0fff4"
GREEN_FG   = "#065f46"
PURPLE_BG  = "#ede9fe"
PURPLE_FG  = "#5b21b6"
YELLOW_BG  = "#fef9c3"
YELLOW_FG  = "#854d0e"
RED_BG     = "#fff5f5"
RED_FG     = "#c53030"

class AppointmentsModule:
    def __init__(self, parent):
        self.parent = parent
        calendar.setfirstweekday(calendar.SUNDAY)
        self.selected_date  = date.today()
        self.current_year   = self.selected_date.year
        self.current_month  = self.selected_date.month
        self.max_hourly_capacity = 3

        self.operating_hours = [
            "08:00 AM", "09:00 AM", "10:00 AM", "11:00 AM",
            "01:00 PM", "02:00 PM", "03:00 PM", "04:00 PM",
            "05:00 PM"
        ]

        self.checklist_options = [
            "Hematology",
            "Clinical Chemistry",
            "Serology and Immunology",
            "Urinalysis",
            "Clinical Microscopy",
            "Medical Imaging"
        ]

        # Widget references
        self.calendar_grid_frame  = None
        self.calendar_month_lbl   = None
        self.table_date_lbl       = None
        self.tree                 = None

        self.lbl_stat_done        = None
        self.lbl_stat_progress    = None
        self.lbl_stat_waiting     = None
        self.lbl_stat_scheduled   = None

    # ── Entry point ────────────────────────────────────────────────────────────
    def show(self):
        for w in self.parent.winfo_children():
            w.destroy()
        self.parent.configure(bg=BG_LIGHT)
        self._build_header_strip()

        workplane = tk.Frame(self.parent, bg=BG_LIGHT)
        workplane.pack(fill="both", expand=True, padx=18, pady=14)

        left_panel = tk.Frame(workplane, bg=WHITE, width=360,
                              highlightbackground=BORDER,
                              highlightthickness=1)
        left_panel.pack(side="left", fill="y", padx=(0, 14))
        left_panel.pack_propagate(False)

        self._build_calendar_widget(left_panel)

        right_panel = tk.Frame(workplane, bg=BG_LIGHT)
        right_panel.pack(side="left", fill="both", expand=True)

        self._build_table_workspace(right_panel)
        self._refresh_data_views()

    # ── Header ─────────────────────────────────────────────────────────────────
    def _build_header_strip(self):
        header = tk.Frame(self.parent, bg=WHITE)
        header.pack(fill="x")
        tk.Frame(header, bg=BORDER, height=1).pack(
            fill="x", side="bottom")

        title_block = tk.Frame(header, bg=WHITE)
        title_block.pack(side="left", padx=20, pady=12)
        tk.Label(title_block,
                 text="Patient Appointments Management",
                 font=("Segoe UI", 16, "bold"),
                 bg=WHITE, fg=TEXT_MAIN).pack(anchor="w")
        tk.Label(title_block,
                 text="Schedule appointments, manage walk-ins, "
                      "and track patient status",
                 font=("Segoe UI", 10),
                 bg=WHITE, fg=TEXT_MUTED).pack(anchor="w")

        action_box = tk.Frame(header, bg=WHITE)
        action_box.pack(side="right", padx=20)
        self._solid_btn(
            action_box, "+ Create New Appointment",
            self._open_appointment_dialog).pack()

    # ── Calendar widget ────────────────────────────────────────────────────────
    def _build_calendar_widget(self, parent):
        nav_frame = tk.Frame(parent, bg=WHITE)
        nav_frame.pack(fill="x", padx=14, pady=(18, 10))

        tk.Button(nav_frame, text="◀",
                  command=self._prev_month,
                  font=("Segoe UI", 11, "bold"),
                  bg=WHITE, fg=TEAL_MID,
                  relief="flat", cursor="hand2",
                  activebackground=BG_LIGHT).pack(side="left")

        self.calendar_month_lbl = tk.Label(
            nav_frame, text="",
            font=("Segoe UI", 13, "bold"),
            bg=WHITE, fg=TEXT_MAIN)
        self.calendar_month_lbl.pack(
            side="left", expand=True)

        tk.Button(nav_frame, text="▶",
                  command=self._next_month,
                  font=("Segoe UI", 11, "bold"),
                  bg=WHITE, fg=TEAL_MID,
                  relief="flat", cursor="hand2",
                  activebackground=BG_LIGHT).pack(side="right")

        days_headers = tk.Frame(parent, bg=WHITE)
        days_headers.pack(fill="x", padx=14, pady=(10, 4))

        for idx, day_text in enumerate(
                ["Sun", "Mon", "Tue", "Wed",
                 "Thu", "Fri", "Sat"]):
            fg = RED_FG if idx == 0 else TEXT_MUTED
            tk.Label(days_headers, text=day_text,
                     font=("Segoe UI", 9, "bold"),
                     bg=WHITE, fg=fg,
                     width=4).grid(
                         row=0, column=idx,
                         pady=6, sticky="ew")

        days_headers.grid_columnconfigure(
            list(range(7)), weight=1)

        tk.Frame(parent, bg=BORDER,
                 height=1).pack(fill="x", padx=14,
                                pady=(2, 6))

        self.calendar_grid_frame = tk.Frame(parent, bg=WHITE)
        self.calendar_grid_frame.pack(
            fill="both", expand=True, padx=14, pady=(4, 14))

        self.calendar_grid_frame.grid_columnconfigure(
            list(range(7)), weight=1)

    # ── Table workspace ────────────────────────────────────────────────────────
    def _build_table_workspace(self, parent):
        stats_frame = tk.Frame(parent, bg=BG_LIGHT)
        stats_frame.pack(fill="x", pady=(0, 12))

        self.lbl_stat_done = self._create_metric_node(
            stats_frame, "0", "Completed",
            GREEN_BG, GREEN_FG)
        self.lbl_stat_progress = self._create_metric_node(
            stats_frame, "0", "In Progress",
            BLUE_BG, BLUE_FG)
        self.lbl_stat_waiting = self._create_metric_node(
            stats_frame, "0", "Waiting",
            YELLOW_BG, YELLOW_FG)
        self.lbl_stat_scheduled = self._create_metric_node(
            stats_frame, "0", "Scheduled",
            PURPLE_BG, PURPLE_FG)

        table_card = tk.Frame(parent, bg=WHITE,
                              highlightbackground=BORDER,
                              highlightthickness=1)
        table_card.pack(fill="both", expand=True)

        th = tk.Frame(table_card, bg="#f8fafc")
        th.pack(fill="x")
        tk.Frame(table_card, bg=BORDER,
                 height=1).pack(fill="x")

        self.table_date_lbl = tk.Label(
            th, text="",
            font=("Segoe UI", 11, "bold"),
            bg="#f8fafc", fg=TEXT_MAIN)
        self.table_date_lbl.pack(
            side="left", padx=14, pady=10)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("App.Treeview",
                        background=WHITE,
                        fieldbackground=WHITE,
                        foreground=TEXT_MAIN,
                        rowheight=38,
                        font=("Segoe UI", 10))
        style.configure("App.Treeview.Heading",
                        background="#f8fafc",
                        foreground=TEXT_MUTED,
                        font=("Segoe UI", 9, "bold"),
                        relief="flat", padding=6)
        style.map("App.Treeview",
                  background=[("selected", "#e0f2fe")],
                  foreground=[("selected", TEXT_MAIN)])

        cols = ("Time", "Patient Name",
                "Type", "Tests Requested", "Status")
        widths = [110, 180, 120, 280, 110]

        self.tree = ttk.Treeview(
            table_card, columns=cols,
            show="headings", style="App.Treeview")

        for col, width in zip(cols, widths):
            self.tree.heading(col, text=col.upper())
            anchor = "center" if col in (
                "Time", "Type", "Status") else "w"
            self.tree.column(col, width=width,
                             anchor=anchor)

        vsb = ttk.Scrollbar(table_card,
                            orient="vertical",
                            command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both",
                       expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.tag_configure(
            "Done",       foreground=GREEN_FG)
        self.tree.tag_configure(
            "In Progress",foreground=BLUE_FG)
        self.tree.tag_configure(
            "Waiting",    foreground=YELLOW_FG)
        self.tree.tag_configure(
            "Scheduled",  foreground=PURPLE_FG)
        self.tree.tag_configure(
            "Cancelled",  foreground=RED_FG)
        self.tree.tag_configure(
            "oddrow",  background="#f8fafc")
        self.tree.tag_configure(
            "evenrow", background=WHITE)

        self.tree.bind("<Double-1>",
                       self._on_tree_row_double_click)

    # ── Calendar rendering ─────────────────────────────────────────────────────
    def _render_calendar_grid(self):
        for w in self.calendar_grid_frame.winfo_children():
            w.destroy()

        self.calendar_month_lbl.configure(
            text=f"{calendar.month_name[self.current_month]}"
                 f" {self.current_year}")

        # Get real appointment counts from DB
        counts = db.get_appointment_counts_for_month(
            self.current_year, self.current_month)

        cal_matrix = calendar.monthcalendar(
            self.current_year, self.current_month)

        for row_idx, week in enumerate(cal_matrix):
            for col_idx, day_val in enumerate(week):
                if day_val == 0:
                    lbl = tk.Label(
                        self.calendar_grid_frame,
                        text="", bg=WHITE)
                    lbl.grid(row=row_idx,
                             column=col_idx,
                             sticky="ewns",
                             padx=3, pady=3)
                    continue

                loop_date = date(
                    self.current_year,
                    self.current_month, day_val)
                date_str   = loop_date.strftime(
                    "%Y-%m-%d")
                appt_count = counts.get(date_str, 0)

                dot_color = None
                if appt_count > 0:
                    if appt_count <= 3:
                        dot_color = "#10b981"
                    elif appt_count <= 8:
                        dot_color = "#f59e0b"
                    else:
                        dot_color = "#ef4444"

                if col_idx == 0:
                    bg_color    = "#f8fafc"
                    fg_color    = TEXT_HINT
                    cursor_style = "arrow"
                elif loop_date == self.selected_date:
                    bg_color    = TEAL_ACCENT
                    fg_color    = WHITE
                    cursor_style = "hand2"
                else:
                    bg_color    = WHITE
                    fg_color    = TEXT_MAIN
                    cursor_style = "hand2"

                cell = tk.Frame(
                    self.calendar_grid_frame,
                    bg=bg_color,
                    highlightbackground=BORDER,
                    highlightthickness=1,
                    cursor=cursor_style)
                cell.grid(row=row_idx,
                          column=col_idx,
                          sticky="ewns",
                          padx=3, pady=3)

                num_lbl = tk.Label(
                    cell, text=str(day_val),
                    font=("Segoe UI", 10, "bold"),
                    bg=bg_color, fg=fg_color)
                num_lbl.pack(anchor="center",
                             pady=(4, 2))

                dot_container = tk.Frame(
                    cell, bg=bg_color, height=8)
                dot_container.pack(
                    fill="x", side="bottom",
                    pady=(0, 4))

                if dot_color and col_idx != 0:
                    dot = tk.Frame(
                        dot_container,
                        bg=dot_color,
                        width=6, height=6)
                    dot.pack(anchor="center")
                    dot.pack_propagate(False)

                if col_idx != 0:
                    for el in (cell, num_lbl,
                               dot_container):
                        el.bind(
                            "<Button-1>",
                            lambda e, d=loop_date:
                            self._handle_date_click(d))

        for r in range(len(cal_matrix)):
            self.calendar_grid_frame.grid_rowconfigure(
                r, weight=1)

    # ── Data refresh — loads from DB ───────────────────────────────────────────
    def _refresh_data_views(self):
        self._render_calendar_grid()

        date_str = self.selected_date.strftime("%Y-%m-%d")
        rows     = db.get_appointments_by_date(date_str)

        weekday  = self.selected_date.strftime("%A")
        friendly = self.selected_date.strftime("%B %d, %Y")

        done_vol      = sum(1 for r in rows
                            if r["status"] == "Done")
        progress_vol  = sum(1 for r in rows
                            if r["status"] == "In Progress")
        waiting_vol   = sum(1 for r in rows
                            if r["status"] == "Waiting")
        scheduled_vol = sum(1 for r in rows
                            if r["status"] == "Scheduled")

        self.lbl_stat_done.configure(
            text=str(done_vol))
        self.lbl_stat_progress.configure(
            text=str(progress_vol))
        self.lbl_stat_waiting.configure(
            text=str(waiting_vol))
        self.lbl_stat_scheduled.configure(
            text=str(scheduled_vol))

        self.table_date_lbl.configure(
            text=f"{weekday}, {friendly} "
                 f"— {len(rows)} appointments")

        for item in self.tree.get_children():
            self.tree.delete(item)

        for idx, r in enumerate(rows):
            shade = "evenrow" if idx % 2 == 0 \
                    else "oddrow"

            # Format time for display
            t = r["appt_time"] or "—"
            try:
                t = datetime.strptime(
                    r["appt_time"], "%H:%M"
                ).strftime("%I:%M %p")
            except Exception:
                pass

            self.tree.insert(
                "", "end",
                values=(
                    t,
                    r["patient_name"],
                    r["appt_type"],
                    r["tests_requested"] or "—",
                    r["status"],
                ),
                tags=(r["status"], shade),
                iid=str(r["id"]))

    # ── Calendar navigation ────────────────────────────────────────────────────
    def _handle_date_click(self, targeted_date):
        self.selected_date = targeted_date
        self._refresh_data_views()

    def _prev_month(self):
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self._render_calendar_grid()

    def _next_month(self):
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self._render_calendar_grid()

    def _get_earliest_walkin_slot(self, date_str):
        rows = db.get_appointments_by_date(date_str)
        for slot in self.operating_hours:
            slot_24 = self._to_24h(slot)
            count   = sum(1 for r in rows
                          if r["appt_time"] == slot_24)
            if count < self.max_hourly_capacity:
                return slot
        return None

    def _to_24h(self, time_12h):
        """Convert '08:00 AM' → '08:00'."""
        try:
            return datetime.strptime(
                time_12h, "%I:%M %p"
            ).strftime("%H:%M")
        except Exception:
            return time_12h

    # ── Double-click row → detail popup ───────────────────────────────────────
    def _on_tree_row_double_click(self, event):
        sel = self.tree.selection()
        if not sel:
            return

        appt_id = int(sel[0])

        # Find full row from DB
        date_str = self.selected_date.strftime("%Y-%m-%d")
        rows     = db.get_appointments_by_date(date_str)
        record   = next(
            (r for r in rows if r["id"] == appt_id),
            None)

        if record:
            self._open_patient_detail_popup(record)

    # ── Appointment detail / edit popup ───────────────────────────────────────
    def _open_patient_detail_popup(self, record):
        win = tk.Toplevel(self.parent)
        win.title("Appointment Details")
        win.geometry("500x500")
        win.resizable(False, False)
        win.grab_set()
        win.configure(bg=WHITE)

        # Header
        top = tk.Frame(win, bg=TEAL_DARK)
        top.pack(fill="x")
        tk.Label(top, text="Appointment Details",
                 font=("Segoe UI", 12, "bold"),
                 bg=TEAL_DARK, fg=WHITE).pack(
                     side="left", padx=16, pady=14)

        del_btn = tk.Button(
            top, text="✕ Cancel Appointment",
            font=("Segoe UI", 9, "bold"),
            bg=RED_BG, fg=RED_FG,
            activebackground=RED_FG,
            activeforeground=WHITE,
            relief="flat", cursor="hand2",
            padx=10, pady=4)
        del_btn.pack(side="right", padx=16)

        body = tk.Frame(win, bg=WHITE,
                        padx=20, pady=16)
        body.pack(fill="both", expand=True)

        # Patient info (read-only)
        tk.Label(body, text="Patient",
                 font=("Segoe UI", 9, "bold"),
                 bg=WHITE, fg=TEXT_MUTED).pack(
                     anchor="w", pady=(0, 2))

        info_chip = tk.Frame(body, bg="#f0f9ff",
                             highlightbackground="#bae6fd",
                             highlightthickness=1)
        info_chip.pack(fill="x", pady=(0, 12))

        tk.Label(info_chip,
                 text=record["patient_name"],
                 font=("Segoe UI", 12, "bold"),
                 bg="#f0f9ff", fg=TEXT_MAIN).pack(
                     anchor="w", padx=12, pady=(8, 2))
        tk.Label(info_chip,
                 text=f"{record['patient_code']}  ·  "
                      f"{record['appt_date']}  ·  "
                      f"{record['appt_time'] or ''}",
                 font=("Segoe UI", 9),
                 bg="#f0f9ff", fg=TEXT_MUTED).pack(
                     anchor="w", padx=12, pady=(0, 8))

        # Status
        tk.Label(body, text="Status",
                 font=("Segoe UI", 9, "bold"),
                 bg=WHITE, fg=TEXT_MUTED).pack(
                     anchor="w", pady=(0, 2))

        status_combo = ctk.CTkComboBox(
            body,
            values=["Scheduled", "Waiting",
                    "In Progress", "Done",
                    "Cancelled"],
            height=32, corner_radius=6,
            border_color=BORDER,
            fg_color=WHITE, text_color=TEXT_MAIN)
        status_combo.pack(fill="x", pady=(0, 12))
        status_combo.set(record["status"])

        # Tests requested
        tk.Label(body, text="Tests Requested",
                 font=("Segoe UI", 9, "bold"),
                 bg=WHITE, fg=TEXT_MUTED).pack(
                     anchor="w", pady=(0, 2))
        tests_box = tk.Text(
            body, height=3,
            font=("Segoe UI", 10),
            highlightbackground=BORDER,
            highlightthickness=1,
            relief="flat", wrap="word",
            fg=TEXT_MAIN)
        tests_box.pack(fill="x", pady=(0, 12))
        tests_box.insert(
            "1.0", record["tests_requested"] or "")

        # Remarks
        tk.Label(body, text="Remarks / Notes",
                 font=("Segoe UI", 9, "bold"),
                 bg=WHITE, fg=TEXT_MUTED).pack(
                     anchor="w", pady=(0, 2))
        notes_box = tk.Text(
            body, height=3,
            font=("Segoe UI", 10),
            highlightbackground=BORDER,
            highlightthickness=1,
            relief="flat", wrap="word",
            fg=TEXT_MAIN)
        notes_box.pack(fill="x", pady=(0, 14))
        notes_box.insert(
            "1.0", record["remarks"] or "")

        def save_changes():
            new_status = status_combo.get()
            new_tests  = tests_box.get(
                "1.0", "end-1c").strip()
            new_notes  = notes_box.get(
                "1.0", "end-1c").strip()

            try:
                conn = db.connect()
                conn.execute("""
                    UPDATE appointments
                    SET status=?, tests_requested=?,
                        remarks=?
                    WHERE id=?
                """, (new_status, new_tests,
                      new_notes, record["id"]))
                conn.commit()
                conn.close()

                db.log_action(
                    "receptionist",
                    "Appointment Updated",
                    f"Appt #{record['id']} → "
                    f"{new_status}")

                self._refresh_data_views()
                win.destroy()
            except Exception as ex:
                messagebox.showerror(
                    "Error",
                    f"Could not save changes:\n{ex}")

        def delete_appt():
            if messagebox.askyesno(
                "Cancel Appointment",
                f"Cancel appointment for "
                f"{record['patient_name']}?\n\n"
                f"This cannot be undone.",
                parent=win):
                try:
                    db.delete_appointment(
                        record["id"])
                    db.log_action(
                        "receptionist",
                        "Appointment Cancelled",
                        f"Appt #{record['id']} — "
                        f"{record['patient_name']}")

                    self._refresh_data_views()
                    win.destroy()
                except Exception as ex:
                    messagebox.showerror(
                        "Error",
                        f"Could not cancel:\n{ex}")

        del_btn.configure(command=delete_appt)

        btn_box = tk.Frame(body, bg=WHITE)
        btn_box.pack(fill="x", side="bottom")

        self._solid_btn(
            btn_box, "Save Changes",
            save_changes).pack(side="right")
        tk.Button(
            btn_box, text="Close",
            command=win.destroy,
            font=("Segoe UI", 10),
            bg=WHITE, fg=TEXT_MUTED,
            highlightbackground=BORDER,
            highlightthickness=1,
            relief="flat", cursor="hand2",
            padx=12, pady=6).pack(
                side="right", padx=8)

    # ── Create appointment dialog — SAVES TO DB ───────────────────────────────
    def _open_appointment_dialog(self):
        win = tk.Toplevel(self.parent)
        win.title("Create New Appointment")
        win.geometry("540x700")
        win.resizable(False, False)
        win.grab_set()
        win.configure(bg=BG_LIGHT)

        top = tk.Frame(win, bg=TEAL_DARK)
        top.pack(fill="x")
        tk.Label(top, text="New Appointment",
                 font=("Segoe UI", 12, "bold"),
                 bg=TEAL_DARK, fg=WHITE).pack(
                     side="left", padx=16, pady=14)

        body_scroll = tk.Canvas(win, bg=WHITE,
                                highlightthickness=0)
        scrollbar   = ttk.Scrollbar(
            win, orient="vertical",
            command=body_scroll.yview)
        body = tk.Frame(body_scroll, bg=WHITE)

        body.bind(
            "<Configure>",
            lambda e: body_scroll.configure(
                scrollregion=body_scroll.bbox("all")))
        body_scroll.create_window(
            (0, 0), window=body,
            anchor="nw", width=520)
        body_scroll.configure(
            yscrollcommand=scrollbar.set)

        body_scroll.pack(side="left", fill="both",
                         expand=True,
                         padx=(10, 0), pady=10)
        scrollbar.pack(side="right", fill="y")

        # ── Patient search ────────────────────────────────
        tk.Label(body, text="Patient *",
                 font=("Segoe UI", 9, "bold"),
                 bg=WHITE, fg=TEXT_MUTED).pack(
                     anchor="w", padx=16,
                     pady=(14, 2))

        search_row = tk.Frame(body, bg=WHITE)
        search_row.pack(fill="x", padx=16,
                        pady=(0, 4))

        search_ent = ctk.CTkEntry(
            search_row,
            placeholder_text="Search registered patient...",
            height=32, corner_radius=6,
            border_color=BORDER,
            fg_color=WHITE, text_color=TEXT_MAIN)
        search_ent.pack(side="left", fill="x",
                        expand=True, padx=(0, 6))

        selected_patient = {"data": None}
        patient_chip_frame = tk.Frame(body, bg=WHITE)
        patient_chip_frame.pack(fill="x", padx=16,
                                pady=(0, 10))

        def show_patient_chip(p):
            for w in patient_chip_frame.winfo_children():
                w.destroy()

            chip = tk.Frame(
                patient_chip_frame, bg="#f0f9ff",
                highlightbackground="#bae6fd",
                highlightthickness=1)
            chip.pack(fill="x")

            initials = (p["first_name"][0]
                        + p["last_name"][0]).upper()
            tk.Label(chip, text=initials,
                     font=("Segoe UI", 10, "bold"),
                     bg=TEAL_ACCENT, fg=WHITE,
                     width=3).pack(
                         side="left",
                         padx=(8, 6), pady=6)

            info = tk.Frame(chip, bg="#f0f9ff")
            info.pack(side="left")
            tk.Label(info,
                     text=f"{p['last_name']}, "
                          f"{p['first_name']}",
                     font=("Segoe UI", 10, "bold"),
                     bg="#f0f9ff",
                     fg=TEXT_MAIN).pack(anchor="w")
            tk.Label(info,
                     text=p["patient_code"],
                     font=("Segoe UI", 9),
                     bg="#f0f9ff",
                     fg=TEXT_MUTED).pack(anchor="w")

        def search_patient():
            query   = search_ent.get().strip()
            if not query:
                messagebox.showwarning(
                    "Search",
                    "Please enter a name or ID.",
                    parent=win)
                return

            results = db.search_patients(query)
            if not results:
                messagebox.showinfo(
                    "Not Found",
                    f"No patient matching \"{query}\".",
                    parent=win)
                return

            if len(results) == 1:
                selected_patient["data"] = results[0]
                show_patient_chip(results[0])
            else:
                _pick_patient(results)

        def _pick_patient(results):
            pw = tk.Toplevel(win)
            pw.title("Select Patient")
            pw.geometry("480x300")
            pw.grab_set()
            pw.configure(bg=WHITE)

            tk.Frame(pw, bg=TEAL_DARK,
                     height=40).pack(fill="x")
            tk.Label(pw,
                     text="Select a patient:",
                     font=("Segoe UI", 10, "bold"),
                     bg=TEAL_DARK,
                     fg=WHITE).place(x=14, y=10)

            ptree = ttk.Treeview(
                pw, columns=("code", "name"),
                show="headings", height=7)
            ptree.heading("code", text="Patient ID")
            ptree.heading("name", text="Name")
            ptree.column("code", width=130)
            ptree.column("name", width=250)

            for r in results:
                ptree.insert(
                    "", "end",
                    values=(
                        r["patient_code"],
                        f"{r['last_name']}, "
                        f"{r['first_name']}"),
                    iid=str(r["id"]))
            ptree.pack(fill="both", expand=True,
                       padx=16, pady=(48, 8))

            def pick():
                sel = ptree.selection()
                if not sel:
                    return
                pid = int(sel[0])
                p   = db.get_patient_by_id(pid)
                selected_patient["data"] = p
                show_patient_chip(p)
                pw.destroy()

            tk.Button(pw, text="Select",
                      command=pick,
                      font=("Segoe UI", 10, "bold"),
                      bg=TEAL_DARK, fg=WHITE,
                      relief="flat",
                      cursor="hand2",
                      padx=14, pady=6).pack(
                          pady=(0, 10))

            ptree.bind("<Double-1>",
                       lambda e: pick())

        tk.Button(search_row, text="Search",
                  command=search_patient,
                  font=("Segoe UI", 9, "bold"),
                  bg=TEAL_DARK, fg=WHITE,
                  relief="flat", cursor="hand2",
                  padx=10, pady=5).pack(side="left")

        # ── Appointment type ──────────────────────────────
        tk.Label(body,
                 text="Appointment Type",
                 font=("Segoe UI", 9, "bold"),
                 bg=WHITE, fg=TEXT_MUTED).pack(
                     anchor="w", padx=16,
                     pady=(4, 2))

        type_combo = ctk.CTkComboBox(
            body,
            values=["By Appointment", "Walk-in"],
            height=32, corner_radius=6,
            border_color=BORDER,
            fg_color=WHITE, text_color=TEXT_MAIN)
        type_combo.set("By Appointment")
        type_combo.pack(fill="x", padx=16)

        # ── Date and time ─────────────────────────────────
        sched_wrapper = tk.Frame(body, bg=WHITE)
        sched_wrapper.pack(fill="x", padx=16,
                           pady=(10, 0))

        date_sf = tk.Frame(sched_wrapper, bg=WHITE)
        date_sf.pack(side="left", fill="x",
                     expand=True)
        tk.Label(date_sf, text="Date",
                 font=("Segoe UI", 9, "bold"),
                 bg=WHITE, fg=TEXT_MUTED).pack(
                     anchor="w", pady=(0, 2))

        date_ent = ctk.CTkEntry(
            date_sf, height=32, corner_radius=6,
            border_color=BORDER,
            fg_color="#f1f5f9",
            text_color=TEXT_MUTED)
        date_ent.pack(fill="x", padx=(0, 8))
        date_ent.insert(
            0, self.selected_date.strftime(
                "%Y-%m-%d"))
        date_ent.configure(state="disabled")

        time_sf = tk.Frame(sched_wrapper, bg=WHITE)
        time_sf.pack(side="left", fill="x",
                     expand=True)
        self.time_lbl = tk.Label(
            time_sf, text="Time",
            font=("Segoe UI", 9, "bold"),
            bg=WHITE, fg=TEXT_MUTED)
        self.time_lbl.pack(anchor="w", pady=(0, 2))

        time_combo = ctk.CTkComboBox(
            time_sf, values=self.operating_hours,
            height=32, corner_radius=6,
            border_color=BORDER,
            fg_color=WHITE, text_color=TEXT_MAIN)
        time_combo.pack(fill="x", padx=(8, 0))
        time_combo.set("08:00 AM")

        # ── Lab services checklist ────────────────────────
        tk.Label(body,
                 text="Laboratory Services *",
                 font=("Segoe UI", 9, "bold"),
                 bg=WHITE, fg=TEXT_MUTED).pack(
                     anchor="w", padx=16,
                     pady=(14, 4))

        checklist_frame = tk.Frame(body, bg=WHITE)
        checklist_frame.pack(fill="x", padx=16,
                             pady=4)

        checkbox_refs = {}
        for idx, option in enumerate(
                self.checklist_options):
            row_num = idx // 2
            col_num = idx % 2

            cb_var  = tk.BooleanVar()
            cb = ctk.CTkCheckBox(
                checklist_frame, text=option,
                variable=cb_var,
                font=("Segoe UI", 11),
                text_color=TEXT_MAIN,
                hover_color=BG_LIGHT,
                fg_color=TEAL_ACCENT,
                border_color=BORDER,
                corner_radius=4)
            cb.grid(row=row_num, column=col_num,
                    sticky="w", padx=10, pady=8)
            checkbox_refs[option] = cb_var

        checklist_frame.grid_columnconfigure(
            0, weight=1)
        checklist_frame.grid_columnconfigure(
            1, weight=1)

        # Other custom request
        misc_card = tk.Frame(body, bg=WHITE,
                             highlightbackground=BORDER,
                             highlightthickness=1)
        misc_card.pack(fill="x", padx=16,
                       pady=(8, 0))

        other_var = tk.BooleanVar()
        other_cb  = tk.Checkbutton(
            misc_card, text="Other:",
            variable=other_var,
            font=("Segoe UI", 9, "bold"),
            bg=WHITE, activebackground=WHITE,
            fg=TEXT_MUTED)
        other_cb.pack(side="left", padx=10, pady=6)

        other_ent = ctk.CTkEntry(
            misc_card, height=26, corner_radius=4,
            border_color=BORDER,
            fg_color=WHITE, text_color=TEXT_MAIN,
            state="disabled")
        other_ent.pack(side="left", fill="x",
                       expand=True, padx=(4, 10))

        def toggle_other():
            if other_var.get():
                other_ent.configure(
                    state="normal", fg_color=WHITE)
                other_ent.focus()
            else:
                other_ent.delete(0, tk.END)
                other_ent.configure(
                    state="disabled",
                    fg_color="#f1f5f9")

        other_cb.configure(command=toggle_other)

        # ── Remarks ───────────────────────────────────────
        tk.Label(body, text="Remarks / Notes",
                 font=("Segoe UI", 9, "bold"),
                 bg=WHITE, fg=TEXT_MUTED).pack(
                     anchor="w", padx=16,
                     pady=(12, 2))

        placeholder = ("e.g., Fasting since 10 PM, "
                       "bring previous records...")
        notes_text  = tk.Text(
            body, height=3,
            font=("Segoe UI", 10),
            highlightbackground=BORDER,
            highlightthickness=1,
            relief="flat", wrap="word",
            fg=TEXT_HINT)
        notes_text.pack(fill="x", padx=16)

        notes_text.insert("1.0", placeholder)

        def on_focus_in(e):
            if notes_text.get(
                    "1.0", "end-1c") == placeholder:
                notes_text.delete("1.0", tk.END)
                notes_text.configure(fg=TEXT_MAIN)

        def on_focus_out(e):
            if not notes_text.get(
                    "1.0", "end-1c").strip():
                notes_text.insert("1.0", placeholder)
                notes_text.configure(fg=TEXT_HINT)

        notes_text.bind("<FocusIn>",  on_focus_in)
        notes_text.bind("<FocusOut>", on_focus_out)

        # Walk-in auto-slot logic
        def toggle_type(choice):
            date_str = self.selected_date.strftime(
                "%Y-%m-%d")
            if choice == "Walk-in":
                slot = self._get_earliest_walkin_slot(
                    date_str)
                if slot:
                    time_combo.set(slot)
                    self.time_lbl.configure(
                        text="Auto-Assigned Slot")
                else:
                    time_combo.set("FULLY BOOKED")
                    self.time_lbl.configure(
                        text="Day Fully Booked")
                time_combo.configure(state="disabled")
            else:
                time_combo.configure(state="normal")
                self.time_lbl.configure(text="Time")
                time_combo.set("08:00 AM")

        type_combo.configure(command=toggle_type)

        # ── Save to DB ────────────────────────────────────
        def save_appointment():
            if not selected_patient["data"]:
                messagebox.showwarning(
                    "No Patient",
                    "Please search and select "
                    "a registered patient.",
                    parent=win)
                return

            selected_panels = [
                opt for opt, var in
                checkbox_refs.items()
                if var.get()]

            if other_var.get() and \
                    other_ent.get().strip():
                selected_panels.append(
                    other_ent.get().strip())

            if not selected_panels:
                messagebox.showwarning(
                    "No Tests",
                    "Please select at least "
                    "one lab service.",
                    parent=win)
                return

            adm_type   = type_combo.get()
            date_str   = self.selected_date.strftime(
                "%Y-%m-%d")
            raw_notes  = notes_text.get(
                "1.0", "end-1c").strip()
            staff_notes = "" if raw_notes == \
                              placeholder else raw_notes

            # Sunday check
            try:
                parsed = datetime.strptime(
                    date_str, "%Y-%m-%d").date()
                if parsed.weekday() == 6:
                    messagebox.showerror(
                        "Closed on Sundays",
                        "The clinic is closed on "
                        "Sundays. Please choose "
                        "another date.",
                        parent=win)
                    return
            except ValueError:
                return

            if adm_type == "Walk-in":
                slot = self._get_earliest_walkin_slot(
                    date_str)
                if not slot:
                    messagebox.showerror(
                        "Fully Booked",
                        "All time slots for this "
                        "day are full.",
                        parent=win)
                    return
                time_24 = self._to_24h(slot)
                status  = "Waiting"
            else:
                slot    = time_combo.get()
                time_24 = self._to_24h(slot)

                rows    = db.get_appointments_by_date(
                    date_str)
                count   = sum(
                    1 for r in rows
                    if r["appt_time"] == time_24)

                if count >= self.max_hourly_capacity:
                    messagebox.showerror(
                        "Time Slot Full",
                        f"'{slot}' is already full "
                        f"({self.max_hourly_capacity}"
                        f" max). Choose another time.",
                        parent=win)
                    return
                status = "Scheduled"

            try:
                appt_id = db.add_appointment({
                    "patient_id":
                        selected_patient["data"]["id"],
                    "appt_date":   date_str,
                    "appt_time":   time_24,
                    "appt_type":   adm_type,
                    "tests_requested":
                        ", ".join(selected_panels),
                    "remarks":     staff_notes,
                    "status":      status,
                })

                db.log_action(
                    "receptionist",
                    "Appointment Created",
                    f"Appt #{appt_id} — "
                    f"{selected_patient['data']['patient_code']}"
                    f" — {date_str} {time_24}")

                self.selected_date   = parsed
                self.current_month   = parsed.month
                self.current_year    = parsed.year

                self._refresh_data_views()

                messagebox.showinfo(
                    "Appointment Saved ✓",
                    f"Appointment saved!\n\n"
                    f"Patient : "
                    f"{selected_patient['data']['last_name']}"
                    f", "
                    f"{selected_patient['data']['first_name']}\n"
                    f"Date    : {date_str}\n"
                    f"Time    : {slot}\n"
                    f"Status  : {status}",
                    parent=win)
                win.destroy()

            except Exception as ex:
                messagebox.showerror(
                    "Error",
                    f"Could not save appointment:\n{ex}",
                    parent=win)

        btn_box = tk.Frame(body, bg=WHITE)
        btn_box.pack(fill="x", pady=(18, 14),
                     padx=16)

        self._solid_btn(
            btn_box, "Save Appointment",
            save_appointment).pack(side="right")
        tk.Button(
            btn_box, text="Cancel",
            command=win.destroy,
            font=("Segoe UI", 10),
            bg=WHITE, fg=TEXT_MUTED,
            highlightbackground=BORDER,
            highlightthickness=1,
            relief="flat", cursor="hand2",
            padx=12, pady=6).pack(
                side="right", padx=8)

    # ── Widget helpers ─────────────────────────────────────────────────────────
    def _create_metric_node(self, parent, bold_val,
                            title_lbl, bg_hex, fg_hex):
        box = tk.Frame(parent, bg=bg_hex,
                       highlightbackground=BORDER,
                       highlightthickness=1)
        box.pack(side="left", fill="x",
                 expand=True, padx=4)

        lbl_frame = tk.Frame(box, bg=bg_hex)
        lbl_frame.pack(padx=14, pady=8)

        counter_lbl = tk.Label(
            lbl_frame, text=bold_val,
            font=("Segoe UI", 12, "bold"),
            bg=bg_hex, fg=fg_hex)
        counter_lbl.pack(side="left")

        tk.Label(lbl_frame,
                 text=f"  {title_lbl}",
                 font=("Segoe UI", 9),
                 bg=bg_hex, fg=fg_hex).pack(
                     side="left")
        return counter_lbl

    def _solid_btn(self, parent, text, cmd):
        return tk.Button(
            parent, text=text, command=cmd,
            font=("Segoe UI", 10, "bold"),
            bg=TEAL_DARK, fg=WHITE,
            activebackground=TEAL_MID,
            relief="flat", cursor="hand2",
            padx=14, pady=6)