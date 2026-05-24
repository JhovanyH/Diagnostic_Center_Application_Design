# modules/services.py

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk

# ── PureHealth Palette Matching Reference Module Exactly ──────────────────────
TEAL_DARK = "#073b4c"
TEAL_MID = "#0c637f"
TEAL_ACCENT = "#0cb0a9"
WHITE = "#ffffff"
BG_LIGHT = "#f4f6f8"
BORDER = "#e2e8f0"
TEXT_MAIN = "#1a202c"
TEXT_MUTED = "#718096"
TEXT_HINT = "#a0aec0"

# Context-driven visual status chips matching reports pattern
BLUE_BG = "#dbeafe"
BLUE_FG = "#1e40af"
GREEN_BG = "#f0fff4"
GREEN_FG = "#065f46"
PURPLE_BG = "#ede9fe"
PURPLE_FG = "#5b21b6"
YELLOW_BG = "#fef9c3"
YELLOW_FG = "#854d0e"
RED_BG = "#fff5f5"
RED_FG = "#c53030"

# ── Service Definitions & Structural Categorization ───────────────────────────
CATEGORY_CONFIG = [
    ("All Specialties", "Complete laboratory diagnostic and imaging catalog index", BLUE_BG, TEAL_MID),
    ("Hematology", "Whole blood analytics, coagulation testing, and morphology profiles", PURPLE_BG, PURPLE_FG),
    ("Clinical Chemistry", "Metabolic panels, routine lipid assessments, and organ function screens", GREEN_BG,
     GREEN_FG),
    ("Serology & Immunology", "Antibody detection, viral markers, and immune response titrations", BLUE_BG, BLUE_FG),
    ("Urinalysis", "Microscopic urine sediment assays and macroscopic biochemical indices", YELLOW_BG, YELLOW_FG),
    ("Clinical Microscopy", "Stool analytes, fecal occult testing, and body fluid examinations", RED_BG, TEAL_DARK),
    ("Medical Imaging", "Diagnostic sonography, soft-tissue views, and ultrasound scans", RED_BG, RED_FG),
]


class ServicesModule:
    def __init__(self, parent):
        self.parent = parent
        self._active_cat_idx = 0
        self._sidebar_btns = []

        # Master directory dataset with strict 1-item-per-row tracking (min 10 items per dept)
        self.all_services = [
            # --- Hematology (10 Items) ---
            ["Activated Partial Thromboplastin Time (aPTT)", "Hematology", "3 hours", "₱450.00"],
            ["Bleeding Time (BT)", "Hematology", "1 hour", "₱150.00"],
            ["Blood Typing", "Hematology", "2 hours", "₱160.00"],
            ["CBC with Platelet Count", "Hematology", "3 hours", "₱300.00"],
            ["Clotting Time (CT)", "Hematology", "1 hour", "₱150.00"],
            ["Erythrocyte Sedimentation Rate (ESR)", "Hematology", "4 hours", "₱200.00"],
            ["Hemoglobin & Hematocrit (H&H)", "Hematology", "2 hours", "₱180.00"],
            ["Peripheral Blood Smear Morphology", "Hematology", "24 hours", "₱550.00"],
            ["Prothrombin Time (PT) with INR", "Hematology", "3 hours", "₱450.00"],
            ["Reticulocyte Count", "Hematology", "4 hours", "₱250.00"],
            ["Rh Typing", "Hematology", "2 hours", "₱160.00"],

            # --- Clinical Chemistry (10 Items) ---
            ["Blood Urea Nitrogen (BUN)", "Clinical Chemistry", "4 hours", "₱155.00"],
            ["Calcium (Serum Electrolyte Test)", "Clinical Chemistry", "6 hours", "₱155.00"],
            ["Creatinine (Kidney Function Test)", "Clinical Chemistry", "4 hours", "₱155.00"],
            ["Fasting Blood Sugar (FBS)", "Clinical Chemistry", "3 hours", "₱200.00"],
            ["Glycated Hemoglobin (HbA1c)", "Clinical Chemistry", "4 hours", "₱650.00"],
            ["HDL Cholesterol", "Clinical Chemistry", "4 hours", "₱300.00"],
            ["LDL Cholesterol", "Clinical Chemistry", "4 hours", "₱300.00"],
            ["Phosphorus (Serum Electrolyte Test)", "Clinical Chemistry", "6 hours", "₱410.00"],
            ["Potassium (Serum Electrolyte Test)", "Clinical Chemistry", "4 hours", "₱300.00"],
            ["Random Blood Sugar (RBS)", "Clinical Chemistry", "2 hours", "₱200.00"],
            ["Sodium (Serum Electrolyte Test)", "Clinical Chemistry", "4 hours", "₱300.00"],
            ["Total Cholesterol Assay", "Clinical Chemistry", "4 hours", "₱250.00"],
            ["Triglycerides Assay", "Clinical Chemistry", "4 hours", "₱300.00"],
            ["Uric Acid Serum Test", "Clinical Chemistry", "4 hours", "₱220.00"],

            # --- Serology & Immunology (10 Items) ---
            ["AIDS Confirmatory Test", "Serology & Immunology", "48 hours", "₱760.00"],
            ["Anti-HCV (Hepatitis C Antibody Screening)", "Serology & Immunology", "6 hours", "₱600.00"],
            ["Antistreptolysin O Titer (ASO)", "Serology & Immunology", "6 hours", "₱450.00"],
            ["C-Reactive Protein (CRP) Quantitative", "Serology & Immunology", "4 hours", "₱550.00"],
            ["Dengue NS1 Antigen Rapid Test", "Serology & Immunology", "2 hours", "₱850.00"],
            ["Hepatitis B Surface Antigen (HBsAg)", "Serology & Immunology", "4 hours", "₱250.00"],
            ["HIV 1 Screening", "Serology & Immunology", "12 hours", "₱380.00"],
            ["HIV 2 Screening", "Serology & Immunology", "12 hours", "₱380.00"],
            ["Rheumatoid Factor (RF) Titer", "Serology & Immunology", "6 hours", "₱450.00"],
            ["Syphilis Screening (VDRL/RPR)", "Serology & Immunology", "4 hours", "₱300.00"],
            ["Typhidot Test (Salmonella IgM/IgG)", "Serology & Immunology", "3 hours", "₱650.00"],

            # --- Urinalysis (10 Items) ---
            ["24-Hour Urine Protein Quantitation", "Urinalysis", "24 hours", "₱650.00"],
            ["Microalbuminuria (Early Kidney Screen)", "Urinalysis", "6 hours", "₱450.00"],
            ["Urine Bence Jones Protein Test", "Urinalysis", "12 hours", "₱550.00"],
            ["Urine Creatinine Clearance Assay", "Urinalysis", "24 hours", "₱500.00"],
            ["Urine Ketones Qualitative Assay", "Urinalysis", "1 hour", "₱150.00"],
            ["Urine Microscopic Casts/Crystals Audit", "Urinalysis", "2 hours", "₱150.00"],
            ["Urine pH and Specific Gravity Metrics", "Urinalysis", "1 hour", "₱100.00"],
            ["Urine Pregnancy Test (hCG Qualitative)", "Urinalysis", "1 hour", "₱150.00"],
            ["Urine Protein Dipstick Assessment", "Urinalysis", "1 hour", "₱100.00"],
            ["Urine Sediment Microscopic Examination", "Urinalysis", "2 hours", "₱120.00"],
            ["Urinalysis (Routine Physical/Chemical)", "Urinalysis", "2 hours", "₱105.00"],

            # --- Clinical Microscopy (10 Items) ---
            ["Activated Fecal Smear (WBC Check)", "Clinical Microscopy", "4 hours", "₱150.00"],
            ["Fecal Occult Blood Test (FOBT)", "Clinical Microscopy", "3 hours", "₱250.00"],
            ["Fecalysis (Routine Parasite Screen)", "Clinical Microscopy", "2 hours", "₱105.00"],
            ["Fecal Smear (Gram Stain)", "Clinical Microscopy", "4 hours", "₱180.00"],
            ["Gastric Juice Free Acid Analysis", "Clinical Microscopy", "6 hours", "₱500.00"],
            ["Modified Acid-Fast Staining (Cryptosporidium)", "Clinical Microscopy", "5 hours", "₱350.00"],
            ["Pinworm Swab (Cellophane Tape Test)", "Clinical Microscopy", "3 hours", "₱150.00"],
            ["Pregnancy Test (Serum Quantitative)", "Clinical Microscopy", "3 hours", "₱350.00"],
            ["Semen Analysis (Fertility Profile)", "Clinical Microscopy", "6 hours", "₱600.00"],
            ["Semen Liquefaction & Viscosity Panel", "Clinical Microscopy", "6 hours", "₱400.00"],
            ["Stool pH Testing", "Clinical Microscopy", "2 hours", "₱150.00"],

            # --- Medical Imaging (10 Items) ---
            ["Appendix Ultrasound View", "Medical Imaging", "4 hours", "₱450.00"],
            ["Breast Mapping Sonography", "Medical Imaging", "5 hours", "₱1,050.00"],
            ["Gallbladder Ultrasound Scan", "Medical Imaging", "4 hours", "₱350.00"],
            ["Hepatobiliary Ultrasound View", "Medical Imaging", "4 hours", "₱500.00"],
            ["Kidneys Ultrasound Scan", "Medical Imaging", "4 hours", "₱400.00"],
            ["Liver Ultrasound Scan", "Medical Imaging", "4 hours", "₱400.00"],
            ["Pelvic Ultrasound Scan", "Medical Imaging", "4 hours", "₱470.00"],
            ["Prostate Gland Ultrasound View", "Medical Imaging", "4 hours", "₱550.00"],
            ["Spleen Ultrasound Mapping", "Medical Imaging", "4 hours", "₱400.00"],
            ["Thyroid Gland Soft Tissue Sonography", "Medical Imaging", "4 hours", "₱750.00"],
            ["Urinary Bladder Ultrasound Scan", "Medical Imaging", "4 hours", "₱350.00"],
            ["Whole Abdomen Ultrasound Profile", "Medical Imaging", "6 hours", "₱2,250.00"],
        ]

        self.lbl_stat_total = None
        self.lbl_stat_lab = None
        self.lbl_stat_img = None

    def show(self):
        """Clears rendering stacking bounds explicitly before grid processing"""
        for w in self.parent.winfo_children():
            w.destroy()
        self.parent.configure(bg=BG_LIGHT)
        self._sidebar_btns = []
        self._build_ui()

    def _build_ui(self):
        # ── Page Header Strip ─────────────────────────────────────────────────
        header = tk.Frame(self.parent, bg=WHITE)
        header.pack(fill="x")
        tk.Frame(header, bg=BORDER, height=1).pack(fill="x", side="bottom")

        title_block = tk.Frame(header, bg=WHITE)
        title_block.pack(side="left", padx=20, pady=12)
        tk.Label(title_block, text="Clinical Services & Fee Directory",
                 font=("Segoe UI", 16, "bold"), bg=WHITE, fg=TEXT_MAIN).pack(anchor="w")
        tk.Label(title_block,
                 text="Maintain department procedure items, turn-around parameters, and retail base pricing matrices",
                 font=("Segoe UI", 10), bg=WHITE, fg=TEXT_MUTED).pack(anchor="w")

        # Context-Driven Global Totals Header Chips (Dynamic Counter Variables)
        self.stats_frame = tk.Frame(header, bg=WHITE)
        self.stats_frame.pack(side="right", padx=20)

        self.lbl_stat_total = None
        self.lbl_stat_lab = None
        self.lbl_stat_img = None

        self._init_stat_chips(self.stats_frame)

        # ── Layout Main Splitting Area ────────────────────────────────────────
        body = tk.Frame(self.parent, bg=BG_LIGHT)
        body.pack(fill="both", expand=True, padx=18, pady=14)

        # Left Categorization Sidebar Canvas
        sidebar = tk.Frame(body, bg=WHITE, width=220, highlightbackground=BORDER, highlightthickness=1)
        sidebar.pack(side="left", fill="y", padx=(0, 12))
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="DIAGNOSTIC DEPARTMENTS", font=("Segoe UI", 9, "bold"),
                 bg=WHITE, fg=TEXT_MUTED).pack(anchor="w", padx=14, pady=(14, 8))
        tk.Frame(sidebar, bg=BORDER, height=1).pack(fill="x")

        for i, (name, desc, bg, fg) in enumerate(CATEGORY_CONFIG):
            btn = tk.Button(sidebar, text=name, font=("Segoe UI", 10),
                            anchor="w", justify="left", relief="flat", cursor="hand2",
                            padx=14, pady=10, command=lambda idx=i: self._select_category(idx))
            btn.pack(fill="x")
            tk.Frame(sidebar, bg=BORDER, height=1).pack(fill="x")
            self._sidebar_btns.append(btn)

        # Right Interactive Working Content Plane
        self.content_area = tk.Frame(body, bg=BG_LIGHT)
        self.content_area.pack(side="left", fill="both", expand=True)

        self._select_category(0)

    def _init_stat_chips(self, parent):
        for w in parent.winfo_children():
            w.destroy()

        self.lbl_stat_total = self._create_metric_node(parent, "0", "Directory Records", BLUE_BG, BLUE_FG)
        self.lbl_stat_lab = self._create_metric_node(parent, "0", "Laboratory Panels", PURPLE_BG, PURPLE_FG)
        self.lbl_stat_img = self._create_metric_node(parent, "0", "Imaging Diagnostic", RED_BG, RED_FG)
        self._recalculate_global_metrics()

    def _recalculate_global_metrics(self):
        if not self.lbl_stat_total:
            return

        total_items = len(self.all_services)
        lab_items = sum(1 for r in self.all_services if r[1] != "Medical Imaging")
        img_items = sum(1 for r in self.all_services if r[1] == "Medical Imaging")

        self.lbl_stat_total.configure(text=str(total_items))
        self.lbl_stat_lab.configure(text=str(lab_items))
        self.lbl_stat_img.configure(text=str(img_items))

    def _select_category(self, idx):
        self._active_cat_idx = idx
        name, desc, act_bg, act_fg = CATEGORY_CONFIG[idx]

        for i, btn in enumerate(self._sidebar_btns):
            if i == idx:
                btn.configure(bg=act_bg, fg=act_fg, font=("Segoe UI", 10, "bold"))
            else:
                btn.configure(bg=WHITE, fg=TEXT_MAIN, font=("Segoe UI", 10))

        for w in self.content_area.winfo_children():
            w.destroy()

        self._build_catalog_workspace(self.content_area, name, desc, act_bg, act_fg)

    def _build_catalog_workspace(self, parent, cat_name, cat_desc, theme_bg, theme_fg):
        self._workspace_header(parent, cat_name, cat_desc, theme_bg, theme_fg)

        filter_card = self._card(parent)
        filter_card.pack(fill="x", pady=(0, 10))

        frow = tk.Frame(filter_card, bg=WHITE)
        frow.pack(fill="x", padx=14, pady=12)

        ctk.CTkLabel(frow, text="Search Directory", font=("Segoe UI", 9), text_color=TEXT_MUTED).pack(side="left")
        self.search_ent = ctk.CTkEntry(
            frow, placeholder_text="Type catalog procedure keywords...", font=("Segoe UI", 10),
            height=32, width=280, corner_radius=6, border_color=BORDER, fg_color=WHITE, text_color=TEXT_MAIN)
        self.search_ent.pack(side="left", padx=(6, 12))
        self.search_ent.bind("<Return>", lambda e: self._refresh_table_view(cat_name))

        self._solid_btn(frow, "Apply Search Filter", lambda: self._refresh_table_view(cat_name)).pack(side="left")

        tk.Button(frow, text="Clear", command=self._clear_search, font=("Segoe UI", 10),
                  bg=WHITE, fg=TEXT_MUTED, relief="flat", cursor="hand2", padx=12, pady=6).pack(side="left", padx=4)

        self._solid_btn(frow, "＋ Add Diagnostic Service", self._add_service_dialog).pack(side="right")

        table_card = self._card(parent)
        table_card.pack(fill="both", expand=True)

        th = tk.Frame(table_card, bg="#f8fafc")
        th.pack(fill="x")
        tk.Frame(table_card, bg=BORDER, height=1).pack(fill="x")

        tk.Label(th, text=f"Master List Index — {cat_name} Panel View", font=("Segoe UI", 10, "bold"), bg="#f8fafc",
                 fg=TEXT_MAIN).pack(side="left", padx=14, pady=8)
        self.record_counter_lbl = tk.Label(th, text="0 procedures found", font=("Segoe UI", 9), bg="#f8fafc",
                                           fg=TEXT_MUTED)
        self.record_counter_lbl.pack(side="right", padx=14)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Catalog.Treeview", background=WHITE, fieldbackground=WHITE, foreground=TEXT_MAIN, rowheight=36,
                        font=("Segoe UI", 10))
        style.configure("Catalog.Treeview.Heading", background="#f8fafc", foreground=TEXT_MUTED,
                        font=("Segoe UI", 9, "bold"), relief="flat", padding=6)
        style.map("Catalog.Treeview", background=[("selected", "#e0f2fe")], foreground=[("selected", TEXT_MAIN)])

        cols = ("#", "Clinical Procedure Name", "Department Specialization", "Turnaround Scale", "Standard Fee Rate")
        widths = [40, 360, 160, 130, 110]

        self.tree = ttk.Treeview(table_card, columns=cols, show="headings", style="Catalog.Treeview")
        for col, width in zip(cols, widths):
            self.tree.heading(col, text=col.upper())
            self.tree.column(col, width=width, anchor="center" if col in ["#",
                                                                          "Turnaround Scale"] else "e" if col == "Standard Fee Rate" else "w")

        vsb = ttk.Scrollbar(table_card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", lambda e: self._edit_service_dialog())

        self._refresh_table_view(cat_name)

    def _refresh_table_view(self, category_filter):
        """Filters catalog objects onto grid views dynamically and sorts alphabetically"""
        for entry in self.tree.get_children():
            self.tree.delete(entry)

        query = self.search_ent.get().strip().lower()
        rendered_count = 0
        adjusted_filter = "All Specialties" if category_filter == "All Categories" else category_filter

        # Sort master dataset alphabetically by procedure name (index 0) before parsing
        sorted_services = sorted(self.all_services, key=lambda x: x[0].lower())

        for row in sorted_services:
            name, cat, tat, price = row
            cat_match = (adjusted_filter == "All Specialties" or cat == adjusted_filter)
            key_match = (query in name.lower() or query in cat.lower())

            if cat_match and key_match:
                rendered_count += 1
                self.tree.insert("", "end", values=(rendered_count, name, cat, tat, price),
                                 tags=("even" if rendered_count % 2 == 0 else "odd",))

        self.tree.tag_configure("even", background=WHITE)
        self.tree.tag_configure("odd", background="#f8fafc")
        self.record_counter_lbl.configure(text=f"{rendered_count} items registered")

    def _clear_search(self):
        self.search_ent.delete(0, "end")
        name = CATEGORY_CONFIG[self._active_cat_idx][0]
        self._refresh_table_view(name)

    def _add_service_dialog(self):
        win = tk.Toplevel(self.parent)
        win.title("Add New Specialty Entry")
        win.geometry("450x420")
        win.resizable(False, False)
        win.grab_set()
        win.configure(bg=BG_LIGHT)

        top = tk.Frame(win, bg=TEAL_DARK)
        top.pack(fill="x")
        tk.Label(top, text="Create Procedure Record", font=("Segoe UI", 12, "bold"), bg=TEAL_DARK, fg=WHITE).pack(
            side="left", padx=16, pady=12)

        body = tk.Frame(win, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        body.pack(fill="both", expand=True, padx=16, pady=16)

        tk.Label(body, text="Diagnostic Procedure Name", font=("Segoe UI", 9, "bold"), bg=WHITE, fg=TEXT_MUTED).pack(
            anchor="w", padx=16, pady=(14, 2))
        name_ent = ctk.CTkEntry(body, placeholder_text="e.g., Target Diagnostic Run", height=32, corner_radius=6,
                                border_color=BORDER, fg_color=WHITE, text_color=TEXT_MAIN)
        name_ent.pack(fill="x", padx=16)

        tk.Label(body, text="Department Assignment", font=("Segoe UI", 9, "bold"), bg=WHITE, fg=TEXT_MUTED).pack(
            anchor="w", padx=16, pady=(10, 2))
        cat_options = [c[0] for c in CATEGORY_CONFIG[1:]]
        cat_combo = ctk.CTkComboBox(body, values=cat_options, height=32, corner_radius=6, border_color=BORDER,
                                    fg_color=WHITE, text_color=TEXT_MAIN)
        cat_combo.set("Clinical Chemistry")
        cat_combo.pack(fill="x", padx=16)

        tk.Label(body, text="Operational Turnaround Scale Window", font=("Segoe UI", 9, "bold"), bg=WHITE,
                 fg=TEXT_MUTED).pack(anchor="w", padx=16, pady=(10, 2))
        tat_ent = ctk.CTkEntry(body, placeholder_text="e.g., 2 hours, 6 hours", height=32, corner_radius=6,
                               border_color=BORDER, fg_color=WHITE, text_color=TEXT_MAIN)
        tat_ent.insert(0, "3 hours")
        tat_ent.pack(fill="x", padx=16)

        tk.Label(body, text="Standard Base Price (₱)", font=("Segoe UI", 9, "bold"), bg=WHITE, fg=TEXT_MUTED).pack(
            anchor="w", padx=16, pady=(10, 2))
        prc_ent = ctk.CTkEntry(body, placeholder_text="0.00", height=32, corner_radius=6, border_color=BORDER,
                               fg_color=WHITE, text_color=TEXT_MAIN)
        prc_ent.pack(fill="x", padx=16)

        btn_box = tk.Frame(body, bg=WHITE)
        btn_box.pack(fill="x", pady=20, padx=16)

        def save():
            n, c, t, p = name_ent.get().strip(), cat_combo.get(), tat_ent.get().strip(), prc_ent.get().strip()
            if not n or not p:
                messagebox.showerror("Form Validation Error",
                                     "Procedure specifications cannot contain blank parameters.", parent=win)
                return

            try:
                formatted_price = f"₱{float(p.replace('₱', '').replace(',', '')):,.2f}"
            except ValueError:
                formatted_price = f"₱{p}"

            self.all_services.append([n, c, t, formatted_price])
            self._recalculate_global_metrics()

            messagebox.showinfo("Success", f"'{n}' added safely to master registry configuration.", parent=win)
            win.destroy()
            self._refresh_table_view(CATEGORY_CONFIG[self._active_cat_idx][0])

        tk.Button(btn_box, text="Save Record", command=save, font=("Segoe UI", 10, "bold"), bg=TEAL_ACCENT, fg=WHITE,
                  activebackground=TEAL_MID, relief="flat", cursor="hand2", padx=16, pady=6).pack(side="right")
        tk.Button(btn_box, text="Cancel", command=win.destroy, font=("Segoe UI", 10), bg=WHITE, fg=TEXT_MUTED,
                  highlightbackground=BORDER, highlightthickness=1, activebackground="#f8fafc", relief="flat",
                  cursor="hand2", padx=12, pady=6).pack(side="right", padx=8)

    def _edit_service_dialog(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Selection Empty",
                                   "Highlight an index data line row from the registry table matrix first.")
            return

        _, old_name, old_cat, old_tat, old_prc = self.tree.item(sel[0], "values")

        win = tk.Toplevel(self.parent)
        win.title("Modify System Registry Row")
        win.geometry("450x460")
        win.resizable(False, False)
        win.grab_set()
        win.configure(bg=BG_LIGHT)

        top = tk.Frame(win, bg=TEAL_DARK)
        top.pack(fill="x")
        tk.Label(top, text="Update Procedure Metrics", font=("Segoe UI", 12, "bold"), bg=TEAL_DARK, fg=WHITE).pack(
            side="left", padx=16, pady=12)

        body = tk.Frame(win, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        body.pack(fill="both", expand=True, padx=16, pady=16)

        tk.Label(body, text="Service Entry Description Title", font=("Segoe UI", 9, "bold"), bg=WHITE,
                 fg=TEXT_MUTED).pack(anchor="w", padx=16, pady=(14, 2))
        name_ent = ctk.CTkEntry(body, height=32, corner_radius=6, border_color=BORDER, fg_color=WHITE,
                                text_color=TEXT_MAIN)
        name_ent.insert(0, old_name)
        name_ent.pack(fill="x", padx=16)

        tk.Label(body, text="Diagnostic Department Assignment", font=("Segoe UI", 9, "bold"), bg=WHITE,
                 fg=TEXT_MUTED).pack(anchor="w", padx=16, pady=(10, 2))
        cat_options = [c[0] for c in CATEGORY_CONFIG[1:]]
        cat_combo = ctk.CTkComboBox(body, values=cat_options, height=32, corner_radius=6, border_color=BORDER,
                                    fg_color=WHITE, text_color=TEXT_MAIN)
        cat_combo.set(old_cat)
        cat_combo.pack(fill="x", padx=16)

        tk.Label(body, text="Turnaround Target Standard Scale", font=("Segoe UI", 9, "bold"), bg=WHITE,
                 fg=TEXT_MUTED).pack(anchor="w", padx=16, pady=(10, 2))
        tat_ent = ctk.CTkEntry(body, height=32, corner_radius=6, border_color=BORDER, fg_color=WHITE,
                               text_color=TEXT_MAIN)
        tat_ent.insert(0, old_tat)
        tat_ent.pack(fill="x", padx=16)

        tk.Label(body, text="Retail Value Level Base Rate (₱)", font=("Segoe UI", 9, "bold"), bg=WHITE,
                 fg=TEXT_MUTED).pack(anchor="w", padx=16, pady=(10, 2))
        prc_ent = ctk.CTkEntry(body, height=32, corner_radius=6, border_color=BORDER, fg_color=WHITE,
                               text_color=TEXT_MAIN)
        prc_ent.insert(0, old_prc.replace("₱", "").replace(",", ""))
        prc_ent.pack(fill="x", padx=16)

        btn_box = tk.Frame(body, bg=WHITE)
        btn_box.pack(fill="x", pady=20, padx=16)

        def delete():
            if messagebox.askyesno("Confirm Deletion", f"Permanently wipe '{old_name}' from backend systems catalog?",
                                   parent=win):
                for idx, item in enumerate(self.all_services):
                    if item[0] == old_name:
                        self.all_services.pop(idx)
                        break
                self._recalculate_global_metrics()
                win.destroy()
                self._refresh_table_view(CATEGORY_CONFIG[self._active_cat_idx][0])

        def update():
            n, c, t, p = name_ent.get().strip(), cat_combo.get(), tat_ent.get().strip(), prc_ent.get().strip()
            if not n or not p:
                messagebox.showerror("Error", "Required fields cannot hold blank values.", parent=win)
                return

            try:
                formatted_price = f"₱{float(p.replace('₱', '').replace(',', '')):,.2f}"
            except ValueError:
                formatted_price = f"₱{p}"

            for idx, item in enumerate(self.all_services):
                if item[0] == old_name:
                    self.all_services[idx] = [n, c, t, formatted_price]
                    break

            self._recalculate_global_metrics()
            messagebox.showinfo("Modified", "Catalog specifications committed to database engine.", parent=win)
            win.destroy()
            self._refresh_table_view(CATEGORY_CONFIG[self._active_cat_idx][0])

        tk.Button(btn_box, text="Commit Changes", command=update, font=("Segoe UI", 10, "bold"), bg=TEAL_DARK, fg=WHITE,
                  activebackground=TEAL_MID, relief="flat", cursor="hand2", padx=16, pady=6).pack(side="right")
        tk.Button(btn_box, text="Remove Record", command=delete, font=("Segoe UI", 10), bg=RED_BG, fg=RED_FG,
                  activebackground="#fca5a5", relief="flat", cursor="hand2", padx=12, pady=6).pack(side="left")
        tk.Button(btn_box, text="Cancel", command=win.destroy, font=("Segoe UI", 10), bg=WHITE, fg=TEXT_MUTED,
                  highlightbackground=BORDER, highlightthickness=1, activebackground="#f8fafc", relief="flat",
                  cursor="hand2", padx=12, pady=6).pack(side="right", padx=8)

    # ── Structural UI Utility Helper Components Block ──────────────────────────────────
    def _workspace_header(self, parent, title, subtitle, bg, fg):
        wrapper = tk.Frame(parent, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        wrapper.pack(fill="x", pady=(0, 10))

        strip = tk.Frame(wrapper, bg=fg, width=6)
        strip.pack(side="left", fill="y")

        inner = tk.Frame(wrapper, bg=WHITE)
        inner.pack(fill="x", side="left", padx=14, pady=10)
        tk.Label(inner, text=title.upper(), font=("Segoe UI", 11, "bold"), bg=WHITE, fg=fg).pack(anchor="w")
        tk.Label(inner, text=subtitle, font=("Segoe UI", 9), bg=WHITE, fg=TEXT_MUTED).pack(anchor="w")

    def _create_metric_node(self, parent, bold_val, title_lbl, bg_hex, fg_hex):
        box = tk.Frame(parent, bg=bg_hex, highlightbackground=BORDER, highlightthickness=1)
        box.pack(side="left", padx=5)

        lbl_frame = tk.Frame(box, bg=bg_hex)
        lbl_frame.pack(padx=12, pady=6)

        counter_lbl = tk.Label(lbl_frame, text=bold_val, font=("Segoe UI", 11, "bold"), bg=bg_hex, fg=fg_hex)
        counter_lbl.pack(side="left")

        tk.Label(lbl_frame, text=f"  {title_lbl}", font=("Segoe UI", 9), bg=bg_hex, fg=fg_hex).pack(side="left")
        return counter_lbl

    def _card(self, parent):
        return tk.Frame(parent, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)

    def _solid_btn(self, parent, text, cmd):
        return tk.Button(parent, text=text, command=cmd, font=("Segoe UI", 10, "bold"), bg=TEAL_DARK, fg=WHITE,
                         activebackground=TEAL_MID, relief="flat", cursor="hand2", padx=14, pady=6)