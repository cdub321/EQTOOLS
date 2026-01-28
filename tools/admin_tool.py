import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys

# Ensure shared modules available
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.settings import SettingsManager


class _InvisibleScrollMixin:
    """Provide invisible scrollbar behaviour for simple scrollable widgets."""

    @staticmethod
    def _make_widget_invisible_scroll(widget):
        if hasattr(widget, "configure") and hasattr(widget, "yview"):
            widget.configure(yscrollcommand=lambda *args: None)

        def _on_mousewheel(event):
            delta = event.delta
            if delta == 0:
                num = getattr(event, "num", 0)
                delta = 120 if num == 4 else -120
            direction = -1 if delta > 0 else 1
            try:
                widget.yview_scroll(direction, "units")
            except tk.TclError:
                pass
            return "break"

        widget.bind("<MouseWheel>", _on_mousewheel)
        widget.bind("<Button-4>", _on_mousewheel)
        widget.bind("<Button-5>", _on_mousewheel)


class AdminTool(_InvisibleScrollMixin):
    """Administrative utilities: client settings, server info, and user management."""

    def __init__(self, parent_frame, settings_manager: SettingsManager, on_settings_updated=None):
        self.parent = parent_frame
        self.settings = settings_manager
        self.on_settings_updated = on_settings_updated

        self.parent.grid_rowconfigure(0, weight=1)
        self.parent.grid_columnconfigure(0, weight=1)

        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.grid(row=0, column=0, sticky="nsew")

        # Tk variables
        self.client_dir_var = tk.StringVar()
        self.server_ip_var = tk.StringVar()
        self.server_user_var = tk.StringVar()
        self.server_pass_var = tk.StringVar()
        self.server_db_var = tk.StringVar()
        self.new_user_var = tk.StringVar()
        self.new_pass_var = tk.StringVar()

        self.create_ui()
        self.load_settings()
        self.refresh_user_list()

    # ------------------------------------------------------------------
    # UI creation
    # ------------------------------------------------------------------
    def create_ui(self):
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=0)
        self.main_frame.grid_rowconfigure(1, weight=0)
        self.main_frame.grid_rowconfigure(2, weight=1)

        self.create_client_settings_frame()
        self.create_server_settings_frame()
        self.create_user_management_frame()

    def create_client_settings_frame(self):
        frame = ttk.LabelFrame(self.main_frame, text="Client Settings", padding="5")
        frame.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 2))
        frame.grid_columnconfigure(1, weight=0)

        ttk.Label(frame, text="Client Directory:").grid(row=0, column=0, sticky="w")
        entry = ttk.Entry(frame, textvariable=self.client_dir_var, width=40)
        entry.grid(row=0, column=1, sticky="w", padx=(5, 5))
        ttk.Button(frame, text="Browse", command=self.select_client_directory, width=10).grid(row=0, column=2)
        ttk.Button(frame, text="Save", command=self.save_client_settings, width=8).grid(row=0, column=3, padx=(5, 0))

    def create_server_settings_frame(self):
        frame = ttk.LabelFrame(self.main_frame, text="Server Configuration", padding="5")
        frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        frame.grid_columnconfigure(1, weight=0)

        ttk.Label(frame, text="Server IP:").grid(row=0, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.server_ip_var, width=22).grid(row=0, column=1, sticky="w", padx=(5, 0))

        ttk.Label(frame, text="DB User:").grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(frame, textvariable=self.server_user_var, width=18).grid(row=1, column=1, sticky="w", padx=(5, 0), pady=(6, 0))

        ttk.Label(frame, text="DB Password:").grid(row=2, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(frame, textvariable=self.server_pass_var, show="*", width=18).grid(
            row=2, column=1, sticky="w", padx=(5, 0), pady=(6, 0)
        )

        ttk.Label(frame, text="Database:").grid(row=3, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(frame, textvariable=self.server_db_var, width=18).grid(row=3, column=1, sticky="w", padx=(5, 0), pady=(6, 0))

        ttk.Button(frame, text="Save Server Settings", command=self.save_server_settings, width=20).grid(
            row=4, column=0, columnspan=2, pady=(8, 0)
        )

    def create_user_management_frame(self):
        frame = ttk.LabelFrame(self.main_frame, text="User Management", padding="5")
        frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=(0, 5))
        frame.grid_columnconfigure(0, weight=0)
        frame.grid_rowconfigure(1, weight=1)

        ttk.Label(frame, text="Existing Users:").grid(row=0, column=0, sticky="w")
        self.user_listbox = tk.Listbox(frame, height=8)
        self._make_widget_invisible_scroll(self.user_listbox)
        self.user_listbox.grid(row=1, column=0, sticky="w", pady=(2, 5))

        controls = ttk.Frame(frame)
        controls.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        controls.grid_columnconfigure(1, weight=0)

        ttk.Label(controls, text="Username:").grid(row=0, column=0, sticky="w")
        ttk.Entry(controls, textvariable=self.new_user_var, width=20).grid(row=0, column=1, sticky="w", padx=(5, 0))

        ttk.Label(controls, text="Password:").grid(row=1, column=0, sticky="w", pady=(5, 0))
        ttk.Entry(controls, textvariable=self.new_pass_var, show="*", width=20).grid(
            row=1, column=1, sticky="w", padx=(5, 0), pady=(5, 0)
        )

        button_row = ttk.Frame(frame)
        button_row.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        ttk.Button(button_row, text="Create User", command=self.create_user, width=14).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(button_row, text="Delete Selected", command=self.delete_selected_user, width=16).grid(
            row=0, column=1
        )

    # ------------------------------------------------------------------
    # Data interactions
    # ------------------------------------------------------------------
    def load_settings(self):
        self.client_dir_var.set(self.settings.client_directory)
        self.server_ip_var.set(self.settings.server_ip)
        self.server_user_var.set(self.settings.server_user)
        self.server_pass_var.set(self.settings.server_password)
        self.server_db_var.set(self.settings.server_db)

    def save_client_settings(self):
        directory = self.client_dir_var.get().strip()
        if directory and not os.path.isdir(directory):
            messagebox.showerror("Invalid Directory", "The specified client directory does not exist.")
            return
        self.settings.client_directory = directory
        self._notify_update()
        messagebox.showinfo("Client Settings", "Client directory saved.")

    def save_server_settings(self):
        self.settings.server_ip = self.server_ip_var.get().strip()
        self.settings.server_user = self.server_user_var.get().strip()
        self.settings.server_password = self.server_pass_var.get()
        self.settings.server_db = self.server_db_var.get().strip()
        self._notify_update()
        messagebox.showinfo("Server Settings", "Server settings saved.")

    def select_client_directory(self):
        start_dir = self.client_dir_var.get() or os.path.expanduser("~")
        directory = filedialog.askdirectory(parent=self.main_frame, title="Select EQ Client Directory", initialdir=start_dir)
        if directory:
            self.client_dir_var.set(directory)

    def refresh_user_list(self):
        self.user_listbox.delete(0, tk.END)
        for username in self.settings.list_users():
            self.user_listbox.insert(tk.END, username)

    def create_user(self):
        username = self.new_user_var.get().strip()
        password = self.new_pass_var.get().strip()
        if not username or not password:
            messagebox.showerror("Missing Fields", "Username and password are required.")
            return
        if self.settings.create_user(username, password):
            self.new_user_var.set("")
            self.new_pass_var.set("")
            self.refresh_user_list()
            messagebox.showinfo("User Created", f"User '{username}' created.")
        else:
            messagebox.showerror("User Exists", f"User '{username}' already exists.")

    def delete_selected_user(self):
        selection = self.user_listbox.curselection()
        if not selection:
            messagebox.showinfo("No Selection", "Select a user to delete.")
            return
        username = self.user_listbox.get(selection[0])
        if not messagebox.askyesno("Confirm Delete", f"Delete user '{username}'?"):
            return
        self.settings.delete_user(username)
        self.refresh_user_list()
        messagebox.showinfo("User Deleted", f"User '{username}' removed.")

    def _notify_update(self):
        if callable(self.on_settings_updated):
            self.on_settings_updated()
