import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
from PIL import Image, ImageTk

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shared.database import DatabaseManager
from shared.theme import set_dark_theme
from shared.notes_db import NotesDBManager
from dictionaries import *
from notebook import NotebookManager
from tools.aa_tool import AAManagerTool
from tools.inventory_tool import InventoryManagerTool
from tools.loot_tool import LootManagerTool
from tools.tradeskill_tool import TradeskillManagerTool
from tools.faction_tool import FactionManagerTool
from tools.guild_tool import GuildManagerTool
from tools.misc_tool import MiscManagerTool
from tools.log_tool import LogManagerTool
from tools.admin_tool import AdminTool
from shared.settings import SettingsManager

class EQToolsSuite:
    """Main application window with tabbed interface for EQ Tools"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("EQEmu Server Management Suite")
        self.root.geometry("1678x832")

        # Apply your exact dark theme
        self.style = set_dark_theme(self.root)

        # Settings manager (client directory, future settings)
        self.settings = SettingsManager()

        # Initialize managers (lazy activation later)
        self.db_manager = DatabaseManager()
        self.db_manager.configure(self.settings)
        self.notes_db = NotesDBManager()
        self.notebook_manager = None

        self.interface_initialized = False
        self.authenticated = False
        self.tab_buttons = {}
        self.tab_frames = {}
        self.current_tab = None
        self.status_var = None

        # Bind close event to cleanup
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Prompt for login after window initializes
        self.root.after(100, self.show_login_dialog)
    
    def test_database_connection(self):
        """Test the database connection on startup"""
        return self.db_manager.connect() is not None

    def show_login_dialog(self):
        if self.interface_initialized or self.authenticated:
            self.initialize_application()
            return

        self.login_window = tk.Toplevel(self.root)
        self.login_window.title("Login")
        self.login_window.transient(self.root)
        self.login_window.grab_set()
        self.login_window.resizable(False, False)

        frame = ttk.Frame(self.login_window, padding=20)
        frame.grid(row=0, column=0)
        frame.grid_columnconfigure(1, weight=1)

        ttk.Label(frame, text="Username:").grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.login_username_var = tk.StringVar(value="admin")
        username_entry = ttk.Entry(frame, textvariable=self.login_username_var)
        username_entry.grid(row=0, column=1, sticky="ew", pady=(0, 5))

        ttk.Label(frame, text="Password:").grid(row=1, column=0, sticky="w")
        self.login_password_var = tk.StringVar(value="admin")
        password_entry = ttk.Entry(frame, textvariable=self.login_password_var, show="*")
        password_entry.grid(row=1, column=1, sticky="ew")

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0))

        ttk.Button(button_frame, text="Login", command=self.attempt_login, width=12).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(button_frame, text="Exit", command=self.root.destroy, width=12).grid(row=0, column=1)

        password_entry.bind("<Return>", lambda event: self.attempt_login())
        username_entry.focus_set()

    def attempt_login(self):
        username = self.login_username_var.get().strip()
        password = self.login_password_var.get().strip()
        if not username or not password:
            messagebox.showerror("Login Failed", "Username and password are required.", parent=self.login_window)
            return

        if self.settings.verify_user(username, password):
            self.authenticated = True
            if self.login_window:
                self.login_window.grab_release()
                self.login_window.destroy()
            self.post_login_flow()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.", parent=self.login_window)

    def post_login_flow(self):
        if not self.settings.server_ip.strip():
            self.show_configuration_dialog(required=True)
        else:
            self.initialize_application()

    def show_configuration_dialog(self, required=False):
        if hasattr(self, "config_window") and self.config_window and self.config_window.winfo_exists():
            self.config_window.lift()
            return

        self.config_window = tk.Toplevel(self.root)
        self.config_window.title("Server Configuration")
        self.config_window.transient(self.root)
        self.config_window.grab_set()
        self.config_window.resizable(False, False)

        frame = ttk.Frame(self.config_window, padding=20)
        frame.grid(row=0, column=0)
        frame.grid_columnconfigure(1, weight=1)

        ttk.Label(frame, text="Server IP Address:").grid(row=0, column=0, sticky="w")
        self.config_ip_var = tk.StringVar(value=self.settings.server_ip)
        ip_entry = ttk.Entry(frame, textvariable=self.config_ip_var)
        ip_entry.grid(row=0, column=1, sticky="ew", padx=(10, 0))

        ttk.Button(frame, text="Save", command=lambda: self.save_server_ip_and_continue(required), width=10).grid(
            row=1, column=0, columnspan=2, pady=(15, 0)
        )

        def on_close():
            if required:
                messagebox.showinfo("Configuration Required", "Server IP must be set before continuing.", parent=self.config_window)
            else:
                self.config_window.destroy()

        self.config_window.protocol("WM_DELETE_WINDOW", on_close)
        ip_entry.focus_set()

    def save_server_ip_and_continue(self, required=False):
        ip_address = self.config_ip_var.get().strip()
        if not ip_address:
            messagebox.showerror("Invalid IP", "Please enter a valid server IP address.", parent=self.config_window)
            return

        self.settings.server_ip = ip_address
        self.config_window.grab_release()
        self.config_window.destroy()
        self.handle_settings_updated()
        if required:
            self.initialize_application()

    def initialize_application(self):
        if self.interface_initialized:
            self.handle_settings_updated()
            return

        if not self.authenticated:
            self.show_login_dialog()
            return

        if not self.settings.server_ip.strip():
            self.show_configuration_dialog(required=True)
            return

        if not self.test_database_connection():
            self.show_configuration_dialog(required=True)
            return

        # Initialize notes.db with lookup tables on first run
        try:
            self.notes_db.initialize_database()
        except Exception as e:
            print(f"Warning: Could not initialize notes.db: {e}")

        if self.notebook_manager is None:
            self.notebook_manager = NotebookManager()

        # Configure root grid for main interface
        self.create_main_interface()
        self.interface_initialized = True
        self.switch_tab("aa")
        self.append_client_dir_to_status()

    def handle_settings_updated(self):
        # Update status bar text and logs tab when settings change
        self.append_client_dir_to_status()
        if hasattr(self, 'log_tool'):
            self.log_tool.set_client_directory(self.settings.client_directory)

        if self.interface_initialized:
            # Ensure database uses latest IP on next query
            self.db_manager.close()
            self.test_database_connection()
    
    def create_main_interface(self):
        """Create the main tabbed interface"""

        self.tab_buttons = {}
        self.tab_frames = {}

        # Configure root grid
        self.root.grid_rowconfigure(0, weight=0)  # Header row - fixed height
        self.root.grid_rowconfigure(1, weight=1)  # Content row - expands
        self.root.grid_rowconfigure(2, weight=0)  # Status row - fixed height
        self.root.grid_columnconfigure(0, weight=1)
        
        # Create status bar first (needed for switch_tab method)
        self.create_status_bar()
        
        # Create combined header/tab frame
        self.create_header_tab_frame()
        
        # Create main content area - just a simple frame, no notebook
        self.content_frame = ttk.Frame(self.root)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))
        
        # Create placeholder tabs for now
        self.create_placeholder_tabs()

        # Apply client directory status if available
        self.update_status_with_client_dir()

    def create_header_tab_frame(self):
        """Create combined header and tab bar frame"""
        # Main header frame with sunken border to match your style
        header_frame = ttk.Frame(self.root, relief=tk.SUNKEN, borderwidth=1)
        header_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        # Inner frame for content
        inner_frame = ttk.Frame(header_frame)
        inner_frame.grid(row=0, column=0, sticky="ew", padx=2, pady=2)
        
        # Configure header frame grid
        header_frame.grid_columnconfigure(0, weight=1)
        
        # Configure grid - 3 columns: tabs | title/actions | logo
        inner_frame.grid_columnconfigure(0, weight=0)
        inner_frame.grid_columnconfigure(1, weight=1)
        inner_frame.grid_columnconfigure(2, weight=0)

        # Column 0: Tab buttons (left side)
        tab_frame = ttk.Frame(inner_frame)
        tab_frame.grid(row=0, column=0, sticky="w", padx=(0, 10))

        # Create custom tab buttons
        self.tab_buttons = {}
        self.create_custom_tabs(tab_frame)

        # Column 1: Title and notebook button
        title_frame = ttk.Frame(inner_frame)
        title_frame.grid(row=0, column=1, sticky="ew")
        title_frame.grid_columnconfigure(0, weight=1)
        title_frame.grid_columnconfigure(1, weight=0)

        title_label = ttk.Label(title_frame, text="EQEmulator Tool Suite", font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, sticky="w")

        notebook_button = ttk.Button(title_frame, text="📝 Notes", command=self.open_notebook, width=10)
        notebook_button.grid(row=0, column=1, padx=(10, 0))

        # Column 2: Logo (right side)
        try:
            logo_path = os.path.join(os.path.dirname(__file__), "images", "other", "default.jpg")
            if os.path.exists(logo_path):
                logo_image = Image.open(logo_path)
                logo_image.thumbnail((90, 65), Image.Resampling.LANCZOS)
                self.logo_photo = ImageTk.PhotoImage(logo_image)
                logo_label = ttk.Label(inner_frame, image=self.logo_photo)
                logo_label.grid(row=0, column=2, sticky="e")
            else:
                logo_label = ttk.Label(inner_frame, text="EQ", font=("Arial", 12, "bold"))
                logo_label.grid(row=0, column=2, sticky="e")
        except Exception:
            logo_label = ttk.Label(inner_frame, text="EQ", font=("Arial", 12, "bold"))
            logo_label.grid(row=0, column=2, sticky="e")
    
    def create_custom_tabs(self, parent):
        """Create custom tab buttons"""
        tabs = [
            ("AA Manager", "aa"),
            ("Inventory", "inventory"), 
            ("Tradeskill", "tradeskill"),
            ("Loot Tables", "loot"),
            ("Factions", "faction"),
            ("Guilds", "guild"),
            ("Misc", "misc"),
            ("Logs", "log"),
            ("Admin", "admin")
        ]
        
        self.current_tab = "aa"  # Default tab
        
        for i, (name, key) in enumerate(tabs):
            btn = ttk.Button(parent, text=name, 
                           command=lambda k=key: self.switch_tab(k))
            btn.grid(row=0, column=i, sticky="w", padx=(0, 2))
            
            self.tab_buttons[key] = btn
        
        # Configure selected button style
        self.style.configure("Selected.TButton", 
                           background="#4c4c4c",  # Lighter for selected
                           relief="sunken")
    
    def switch_tab(self, tab_key):
        """Switch to a different tab"""
        # Update button styles
        for key, btn in self.tab_buttons.items():
            if key == tab_key:
                btn.configure(style="Selected.TButton")
                self.current_tab = key
            else:
                btn.configure(style="TButton")
        
        # Hide all tab frames and show the selected one
        for frame in self.tab_frames.values():
            frame.grid_forget()
        
        if tab_key in self.tab_frames:
            self.tab_frames[tab_key].grid(row=0, column=0, sticky="nsew")
        
        # Update status (if status bar exists)
        if hasattr(self, 'status_var') and self.status_var is not None:
            tab_names = {"aa": "AA Manager", "inventory": "Inventory", 
                        "tradeskill": "Tradeskill", "loot": "Loot Tables", 
                        "faction": "Faction Manager", "guild": "Guild Manager", "misc": "Misc Manager",
                        "log": "Log Manager", "admin": "Admin"}
            self.status_var.set(f"Entelion's EQEmulator Tool Suite - {tab_names[tab_key]}")
            self.append_client_dir_to_status()
    
    def create_placeholder_tabs(self):
        """Create placeholder tabs to test the interface"""
        
        # Configure content frame grid
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        # Dictionary to hold all tab frames
        self.tab_frames = {}
        
        # AA Manager Tab - Replace placeholder with actual tool
        aa_frame = ttk.Frame(self.content_frame)
        aa_frame.grid_rowconfigure(0, weight=1)
        aa_frame.grid_columnconfigure(0, weight=1)
        
        # Create the actual AA Manager tool
        self.aa_tool = AAManagerTool(aa_frame, self.db_manager, self.notes_db)
        self.tab_frames["aa"] = aa_frame
        
        # Inventory Manager Tab - Replace placeholder with actual tool
        inventory_frame = ttk.Frame(self.content_frame)
        inventory_frame.grid_rowconfigure(0, weight=1)
        inventory_frame.grid_columnconfigure(0, weight=1)
        
        # Create the actual Inventory Manager tool
        self.inventory_tool = InventoryManagerTool(inventory_frame, self.db_manager, self.notes_db)
        self.tab_frames["inventory"] = inventory_frame
        
        # Tradeskill Manager Tab - Replace placeholder with actual tool
        tradeskill_frame = ttk.Frame(self.content_frame)
        tradeskill_frame.grid_rowconfigure(0, weight=1)
        tradeskill_frame.grid_columnconfigure(0, weight=1)
        
        # Create the actual Tradeskill Manager tool
        self.tradeskill_tool = TradeskillManagerTool(tradeskill_frame, self.db_manager, self.notes_db)
        self.tab_frames["tradeskill"] = tradeskill_frame
        
        # Loot Tables Tab
        loot_frame = ttk.Frame(self.content_frame)
        loot_frame.grid_rowconfigure(0, weight=1)
        loot_frame.grid_columnconfigure(0, weight=1)
        self.loot_tool = LootManagerTool(loot_frame, self.db_manager, self.notes_db)
        self.tab_frames["loot"] = loot_frame
        
        # Faction Manager Tab
        faction_frame = ttk.Frame(self.content_frame)
        faction_frame.grid_rowconfigure(0, weight=1)
        faction_frame.grid_columnconfigure(0, weight=1)
        self.faction_tool = FactionManagerTool(faction_frame, self.db_manager, self.notes_db)
        self.tab_frames["faction"] = faction_frame
        
        # Guild Manager Tab
        guild_frame = ttk.Frame(self.content_frame)
        guild_frame.grid_rowconfigure(0, weight=1)
        guild_frame.grid_columnconfigure(0, weight=1)
        self.guild_tool = GuildManagerTool(guild_frame, self.db_manager, self.notes_db)
        self.tab_frames["guild"] = guild_frame
        
        # Misc Manager Tab
        misc_frame = ttk.Frame(self.content_frame)
        misc_frame.grid_rowconfigure(0, weight=1)
        misc_frame.grid_columnconfigure(0, weight=1)
        self.misc_tool = MiscManagerTool(misc_frame, self.db_manager)
        self.tab_frames["misc"] = misc_frame

        # Log Manager Tab
        log_frame = ttk.Frame(self.content_frame)
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        self.log_tool = LogManagerTool(log_frame, self.db_manager)
        self.log_tool.set_client_directory(self.settings.client_directory)
        self.tab_frames["log"] = log_frame

        # Admin Tab
        admin_frame = ttk.Frame(self.content_frame)
        admin_frame.grid_rowconfigure(0, weight=1)
        admin_frame.grid_columnconfigure(0, weight=1)
        self.admin_tool = AdminTool(admin_frame, self.settings, on_settings_updated=self.handle_settings_updated)
        self.tab_frames["admin"] = admin_frame
        
        # Show the first tab by default
        self.switch_tab("aa")
    
    def create_status_bar(self):
        """Create status bar at bottom of window"""
        self.status_var = tk.StringVar()
        self.status_var.set("Entelion's EQEmulator Tool Suite - Ready")
        
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, 
                                   relief="sunken", anchor="w")
        self.status_bar.grid(row=2, column=0, sticky="ew", padx=5, pady=(0, 5))
    
    def open_notebook(self):
        """Open the notebook window"""
        if self.notebook_manager is None:
            self.notebook_manager = NotebookManager()
        self.notebook_manager.show_notebook(self.root)
    
    def on_closing(self):
        """Handle application closing"""
        # Close database connection
        self.db_manager.close()

        # Close settings connection
        if hasattr(self, 'settings'):
            self.settings.close()

        # Destroy the main window
        self.root.destroy()
    
    def run(self):
        """Start the application"""
        # Start the main loop
        self.root.mainloop()

    def append_client_dir_to_status(self):
        """Append client directory info to status bar if available"""
        if not hasattr(self, 'status_var') or self.status_var is None:
            return
        base_text = self.status_var.get().split(" | Client Dir:")[0]
        client_dir = self.settings.client_directory
        if client_dir:
            self.status_var.set(f"{base_text} | Client Dir: {client_dir}")
        else:
            self.status_var.set(base_text)

    def update_status_with_client_dir(self):
        """Refresh status bar after UI creation to show client directory"""
        if hasattr(self, 'status_var') and self.status_var is not None:
            self.append_client_dir_to_status()

def main():
    """Main entry point"""
    try:
        app = EQToolsSuite()
        app.run()
    except Exception as e:
        messagebox.showerror("Application Error", f"Failed to start application:\n{str(e)}")

if __name__ == "__main__":
    main()
