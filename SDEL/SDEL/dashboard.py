import tkinter as tk
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import db

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Import all modules
from modules.dashboard_mod import DashboardModule
from modules.patients import PatientsModule
from modules.appointments import AppointmentsModule
from modules.billing import BillingModule
from modules.services import ServicesModule
from modules.reports import ReportsModule

# ========== CONFIGURATION ==========
CLINIC_LOGO_PATH = "assets/purehealth_logo.png"
DB_PATH = "purehealthDb.db"
# ===================================


class MainDashboard:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PureHealth Diagnostic Center Inc.")
        self.root.state("zoomed")

        self.current_frame = None   # tracks the active content frame

        # Image references
        self.clinic_logo_img = None

        # Sidebar button references for highlight tracking
        self.sidebar_buttons = {}
        self.active_module = None

        self.create_top_bar()
        self.create_sidebar()
        self.show_dashboard()       # default view on launch
        self.root.mainloop()

    # ---------- Image Loader ----------
    def load_image(self, path, width, height):
        """Load a PNG/JPG with PIL if available, otherwise return None."""
        if not PIL_AVAILABLE:
            return None
        try:
            if path and os.path.exists(path):
                img = Image.open(path).convert("RGBA")
                img = img.resize((width, height), Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Image load error: {e}")
        return None

    # ---------- Sidebar Highlight ----------
    def set_active_button(self, active_text):
        """Highlight the currently selected sidebar button."""
        for text, btn in self.sidebar_buttons.items():
            if text == active_text:
                btn.config(bg="#0cb0a9", fg="#073b4c")
            else:
                btn.config(bg="#0c637f", fg="white")
        self.active_module = active_text

    # ---------- Top Bar ----------
    def create_top_bar(self):
        top = tk.Frame(self.root, bg="#073b4c", height=70)
        top.pack(fill="x")
        top.pack_propagate(False)

        # Clinic logo (emoji fallback if image missing)
        self.clinic_logo_img = self.load_image(CLINIC_LOGO_PATH, 50, 50)
        if self.clinic_logo_img:
            logo_label = tk.Label(top, image=self.clinic_logo_img, bg="#073b4c")
        else:
            logo_label = tk.Label(top, text="🏥", font=("Segoe UI", 30),
                                  bg="#073b4c", fg="white")
        logo_label.pack(side="left", padx=(10, 5), pady=5)

        # Clinic name
        info_frame = tk.Frame(top, bg="#073b4c")
        info_frame.pack(side="left", padx=10, pady=5)
        tk.Label(info_frame, text="PureHealth", font=("Arial", 20, "bold"),
                 fg="#06d6a0", bg="#073b4c").pack(anchor="w")
        tk.Label(info_frame, text="Diagnostic Center Inc. — GMA, Cavite",
                 font=("Arial", 11), fg="white", bg="#073b4c").pack(anchor="w")

    # ---------- Sidebar ----------
    def create_sidebar(self):
        sidebar = tk.Frame(self.root, bg="#0c637f", width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        menus = {
            "Dashboard":          self.show_dashboard,
            "Patients":           self.show_patients,
            "Appointments":       self.show_appointments,
            "Billing & Payments": self.show_billing,
            "Services & Pricing": self.show_services,
            "Reports":            self.show_reports,
        }

        for text, command in menus.items():
            btn = tk.Button(sidebar, text=text, bg="#0c637f", fg="white",
                            relief="flat", font=("Arial", 11), anchor="w",
                            padx=20, pady=12, command=command)
            btn.pack(fill="x", pady=2)
            self.sidebar_buttons[text] = btn

        # Exit button
        tk.Button(sidebar, text="Exit", bg="#c0392b", fg="white",
                  relief="flat", font=("Arial", 11, "bold"),
                  padx=15, pady=8,
                  command=self.root.quit).pack(side="bottom", fill="x",
                                               pady=15, padx=10)

    # ---------- Module Switchers ----------
    def show_dashboard(self):
        self._switch(DashboardModule, "Dashboard")

    def show_patients(self):
        self._switch(PatientsModule, "Patients")

    def show_appointments(self):
        self._switch(AppointmentsModule, "Appointments")

    def show_billing(self):
        self._switch(BillingModule, "Billing & Payments")

    def show_services(self):
        self._switch(ServicesModule, "Services & Pricing")

    def show_reports(self):
        self._switch(ReportsModule, "Reports")

    # ---------- Core Switcher ----------
    def _switch(self, ModuleClass, button_label):
        """
        Destroy the current content frame, create a fresh one,
        instantiate the module, call show(), and highlight the sidebar button.
        """

        if self.current_frame is not None:
            self.current_frame.destroy()

        self.current_frame = tk.Frame(self.root, bg="white")
        self.current_frame.pack(side="right", fill="both", expand=True)


        module = ModuleClass(self.current_frame)
        module.show()

        self.set_active_button(button_label)


if __name__ == "__main__":
    app = MainDashboard()