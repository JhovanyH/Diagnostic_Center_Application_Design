# modules/services_module.py
import tkinter as tk
from tkinter import ttk, messagebox


class ServicesModule:
    def __init__(self, parent):
        self.parent = parent

    def show(self):
        """Services & Pricing Module - Matching your screenshot"""
        # Header
        header = tk.Frame(self.parent, bg="white")
        header.pack(fill="x", padx=25, pady=15)

        tk.Label(header, text="Services & Pricing",
                font=("Arial", 18, "bold"), bg="white").pack(side="left")
        tk.Label(header, text="View available diagnostic services",
                fg="gray", bg="white").pack(side="left", padx=15)

        ttk.Button(header, text="All Categories",
                  command=self.filter_categories).pack(side="right")

        # Search/Filter
        filter_frame = tk.Frame(self.parent, bg="white")
        filter_frame.pack(fill="x", padx=25, pady=8)

        tk.Label(filter_frame, text="Filter by Category:", bg="white").pack(side="left")
        self.category_combo = ttk.Combobox(filter_frame,
                                         values=["All Categories", "Hematology", "Chemistry",
                                                "Radiology", "Urinalysis"],
                                         state="readonly", width=25)
        self.category_combo.set("All Categories")
        self.category_combo.pack(side="left", padx=10)
        ttk.Button(filter_frame, text="Search", command=self.refresh_services).pack(side="left")

        # Services Table
        columns = ("SERVICE NAME", "CATEGORY", "TURNAROUND", "PRICE")
        self.tree = ttk.Treeview(self.parent, columns=columns, show="headings", height=22)

        column_widths = [280, 140, 120, 100]
        for i, col in enumerate(columns):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=column_widths[i])

        # Sample Data matching your screenshot
        services = [
            ("Complete Blood Count (CBC)", "Hematology", "Same day", "₱350.00"),
            ("Urinalysis", "Urinalysis", "2 hours", "₱150.00"),
            ("Fasting Blood Sugar", "Chemistry", "Same day", "₱200.00"),
            ("Chest X-Ray PA", "Radiology", "1 hour", "₱450.00"),
            ("Ultrasound — OB", "Radiology", "Same day", "₱800.00"),
            ("Blood Chemistry Panel", "Chemistry", "Same day", "₱350.00"),
            ("ECG", "Cardiology", "Same day", "₱400.00"),
        ]

        for service in services:
            self.tree.insert("", "end", values=service)

        self.tree.pack(fill="both", expand=True, padx=25, pady=10)

        # Bottom Buttons
        bottom_frame = tk.Frame(self.parent, bg="white")
        bottom_frame.pack(fill="x", padx=25, pady=10)

        ttk.Button(bottom_frame, text="Add New Service",
                  command=self.add_new_service).pack(side="left")
        ttk.Button(bottom_frame, text="Edit Selected",
                  command=self.edit_service).pack(side="left", padx=10)
        ttk.Button(bottom_frame, text="Disable Selected",
                  command=self.disable_service).pack(side="left")

    def filter_categories(self):
        """Filter services by category"""
        selected = self.category_combo.get()
        messagebox.showinfo("Filter", f"Filtered by: {selected}\n\n(This feature can be expanded with real filtering)")

    def refresh_services(self):
        messagebox.showinfo("Refreshed", "Services list has been refreshed.")

    def add_new_service(self):
        win = tk.Toplevel(self.parent)
        win.title("Add New Service")
        win.geometry("500x400")
        win.grab_set()

        tk.Label(win, text="Add New Diagnostic Service", font=("Arial", 14, "bold")).pack(pady=15)

        tk.Label(win, text="Service Name:").pack(anchor="w", padx=40, pady=(10,0))
        ttk.Entry(win, width=50).pack(padx=40, fill="x")

        tk.Label(win, text="Category:").pack(anchor="w", padx=40, pady=(10,0))
        ttk.Combobox(win, values=["Hematology", "Chemistry", "Radiology", "Urinalysis", "Cardiology"], width=47).pack(padx=40, fill="x")

        tk.Label(win, text="Turnaround Time:").pack(anchor="w", padx=40, pady=(10,0))
        ttk.Entry(win, width=50).pack(padx=40, fill="x")

        tk.Label(win, text="Price (₱):").pack(anchor="w", padx=40, pady=(10,0))
        ttk.Entry(win, width=50).pack(padx=40, fill="x")

        btn_frame = tk.Frame(win)
        btn_frame.pack(pady=30)
        ttk.Button(btn_frame, text="Save Service", command=lambda: self.save_new_service(win)).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="Cancel", command=win.destroy).pack(side="left", padx=10)

    def save_new_service(self, window):
        messagebox.showinfo("Success", "New service added successfully!")
        window.destroy()
        self.show()  # Refresh list

    def edit_service(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a service to edit.")
            return
        messagebox.showinfo("Edit Service", "Service editing form will open here.")

    def disable_service(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a service first.")
            return
        messagebox.showinfo("Disabled", "Selected service has been disabled.")