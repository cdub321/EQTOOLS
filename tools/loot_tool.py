import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sys
import os
from PIL import Image, ImageTk
import glob
# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.theme import set_dark_theme
from dictionaries import (SLOT_BITMASK_DISPLAY, ITEM_STAT_DISPLAY_CONFIG, NPC_TYPES_COLUMNS)
from lookup_data import (
    class_lookup as CLASS_LOOKUP_SEED,
    race_lookup as RACE_LOOKUP_SEED,
)
class LootManagerTool:
    """Loot Manager Tool - modular version for tabbed interface"""
    def __init__(self, parent_frame, db_manager, notes_db_manager):
        self.parent = parent_frame
        self.db_manager = db_manager
        self.conn = db_manager.connect()
        self.cursor = db_manager.get_cursor()
        self.notes_db = notes_db_manager
        self.class_bitmask_display = {}
        self.race_bitmask_display = {}
        self.load_lookup_data()
    def load_lookup_data(self):
        """Load race and class bitmask displays with seed fallbacks."""
        def _fetch(fetcher, seed):
            rows = []
            if self.notes_db:
                try:
                    rows = fetcher()
                except Exception as exc:
                    print(f"Warning: lookup fetch failed ({exc}); using seed data.")
            if not rows:
                rows = [{'id': sid, **data} for sid, data in seed.items()]
            return rows
        class_rows = _fetch(
            lambda: self.notes_db.get_class_bitmasks(),
            CLASS_LOOKUP_SEED,
        )
        self.class_bitmask_display = {
            row['bit_value']: row.get('abbr') or row['name'] for row in class_rows
        }
        self.class_bitmask_display[65535] = 'ALL'
        race_rows = _fetch(
            lambda: self.notes_db.get_race_bitmasks(),
            RACE_LOOKUP_SEED,
        )
        self.race_bitmask_display = {
            row['bit_value']: row.get('abbr') or row['name'] for row in race_rows
        }
        self.race_bitmask_display[65535] = 'ALL'
        # Configure parent frame grid
        self.parent.grid_rowconfigure(0, weight=1)
        self.parent.grid_columnconfigure(0, weight=1)
        # Create main container frame
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        # Initialize UI components
        self.create_ui()
        # Load initial data safely
        try:
            self.find_unused_ids()
            print("Loot tool initialized successfully")
        except Exception as e:
            print(f"Warning: Could not initialize loot tool data: {e}")
    def create_ui(self):
        """Create the complete Loot Manager UI"""
        # Configure main frame grid to match the original layout
        self.main_frame.grid_rowconfigure(0, weight=0)  # Top frame - fixed height
        self.main_frame.grid_rowconfigure(1, weight=1)  # Middle frame - expandable
        self.main_frame.grid_rowconfigure(2, weight=0)  # Bottom frame - fixed height
        self.main_frame.grid_columnconfigure(0, weight=1)
        # Create the main sections following the original structure
        self.create_top_section()     # Search, unused IDs, and images
        self.create_middle_section()  # Loot tables and loot drops
        self.create_bottom_section()  # NPC list and editor
    def create_top_section(self):
        """Create top section with search, unused IDs, and image displays"""
        # Top root frame
        self.top_root = ttk.Frame(self.main_frame, relief=tk.SUNKEN, borderwidth=1)
        self.top_root.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        # Configure grid for 4 columns: search, unused IDs, main image, item image
        self.top_root.grid_columnconfigure(0, weight=0)  # Search frame
        self.top_root.grid_columnconfigure(1, weight=0)  # Unused IDs frame
        self.top_root.grid_columnconfigure(2, weight=0)  # Main image frame
        self.top_root.grid_columnconfigure(3, weight=0)  # Item image frame
        self.create_search_frame()
        self.create_unused_ids_frame()
        self.create_image_frames()
    def create_search_frame(self):
        """Create search functionality frame"""
        # Search Frame
        search_frame = ttk.Frame(self.top_root, relief=tk.SUNKEN, borderwidth=2)
        search_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        # Zone Search
        ttk.Label(search_frame, text="Enter Zone Shortname:").grid(row=0, column=0, sticky=tk.W)
        self.zone_entry = ttk.Entry(search_frame, width=20)
        self.zone_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(search_frame, text="Version:").grid(row=0, column=2, sticky=tk.E, padx=(10, 4))
        self.version_var = tk.StringVar(value="0")
        self.version_menu = ttk.Combobox(search_frame, textvariable=self.version_var, width=3, state="readonly", values=[str(i) for i in range(6)])
        self.version_menu.grid(row=0, column=3, padx=4, pady=5, sticky=tk.W)
        ttk.Button(search_frame, text="Search Zone", command=self.search_zone).grid(row=0, column=4, padx=5, pady=5)
        # NPC Name Search
        ttk.Label(search_frame, text="Enter NPC Name:").grid(row=1, column=0, sticky=tk.W)
        self.npc_name_entry = ttk.Entry(search_frame, width=20)
        self.npc_name_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(search_frame, text="Search NPC Name", command=self.search_npc_name).grid(row=1, column=2, padx=5, pady=5)
        # Loottable ID Search
        ttk.Label(search_frame, text="Enter Loottable ID:").grid(row=2, column=0, sticky=tk.W)
        self.loottable_id_entry = ttk.Entry(search_frame, width=20)
        self.loottable_id_entry.grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(search_frame, text="Search Loottable", command=self.search_loottable_id).grid(row=2, column=2, padx=5, pady=5)
        # Clear Buttons
        ttk.Label(search_frame, text="").grid(row=3, column=0)
        ttk.Button(search_frame, text="Clear All Windows", command=lambda: self.clear_results("all")).grid(row=4, column=0, pady=5, padx=5, columnspan=2)
        ttk.Button(search_frame, text="Clear Search Windows", command=lambda: self.clear_results("search")).grid(row=4, column=2, pady=5, padx=5)
    def create_unused_ids_frame(self):
        """Create unused IDs lookup frame"""
        find_unused_frame = ttk.Frame(self.top_root, relief=tk.SUNKEN, borderwidth=2)
        find_unused_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        ttk.Label(find_unused_frame, text="Unused IDs").grid(row=0, column=1, columnspan=2, sticky="w")
        ttk.Button(find_unused_frame, text="Refresh", command=self.find_unused_ids).grid(row=0, column=0, pady=5, sticky="e")
        ttk.Label(find_unused_frame, text="Unused Loot Table IDs:").grid(row=1, column=0, sticky=tk.E)
        self.unused_loottable_label = ttk.Label(find_unused_frame, text="...")
        self.unused_loottable_label.grid(row=1, column=1, columnspan=2, pady=5, padx=5, sticky=tk.W)
        ttk.Label(find_unused_frame, text="Unused Lootdrop IDs:").grid(row=2, column=0, sticky=tk.E)
        self.unused_lootdrop_label = ttk.Label(find_unused_frame, text="...")
        self.unused_lootdrop_label.grid(row=2, column=1, columnspan=2, pady=5, padx=5, sticky=tk.W)
        ttk.Button(find_unused_frame, text="Create", command=self.add_lootdrop_to_loottable).grid(row=5, column=0, pady=5, padx=5, columnspan=3)
        ttk.Label(find_unused_frame, text="").grid(row=7, column=0)
        ttk.Button(find_unused_frame, text="View All Loot Tables", command=self.view_all_loottables).grid(row=8, column=0, padx=5, pady=2, columnspan=3)
    def create_image_frames(self):
        """Create image display frames"""
        # Main image frame
        image_frame = ttk.Frame(self.top_root, relief=tk.SUNKEN, borderwidth=2)
        image_frame.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        try:
            backingimage2 = Image.open("images/other/default.jpg")
            self.bg2_image = ImageTk.PhotoImage(backingimage2)
            self.main_canvas = tk.Canvas(image_frame, width=self.bg2_image.width(), height=self.bg2_image.height(), highlightthickness=0)
            self.main_canvas.grid(row=0, column=0, sticky="nsew")
            self.main_canvas.create_image(0, 0, anchor="nw", image=self.bg2_image)
        except Exception as e:
            print(f"Could not load main background image: {e}")
            self.bg2_image = None
            self.main_canvas = tk.Canvas(image_frame, width=200, height=150, highlightthickness=0, bg="#3c3c3c")
            self.main_canvas.grid(row=0, column=0, sticky="nsew")
        # Item image frame
        item_frame = ttk.Frame(self.top_root, relief=tk.SUNKEN, borderwidth=2)
        item_frame.grid(row=0, column=3, sticky="nsew", padx=5, pady=5)
        try:
            backingimage = Image.open("images/other/itemback.png")
            self.bg_image = ImageTk.PhotoImage(backingimage)
            self.canvas = tk.Canvas(item_frame, width=self.bg_image.width(), height=self.bg_image.height(), highlightthickness=0)
            self.canvas.grid(row=0, column=0, sticky="nsew")
            self.canvas.create_image(0, 0, anchor="nw", image=self.bg_image)
        except Exception as e:
            print(f"Could not load item background image: {e}")
            self.bg_image = None
            self.canvas = tk.Canvas(item_frame, width=200, height=150, highlightthickness=0, bg="#3c3c3c")
            self.canvas.grid(row=0, column=0, sticky="nsew")
    def create_middle_section(self):
        """Create middle section with loot tables and loot drops"""
        # Middle root frame
        self.middle_root_frame = ttk.Frame(self.main_frame, relief=tk.SUNKEN, borderwidth=1)
        self.middle_root_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        # Configure grid: row 0 = modification bar (spans all columns)
        # row 1 = three columns: Loot Table tree | middle buttons | Loot Drop tree
        self.middle_root_frame.grid_columnconfigure(0, weight=1)
        self.middle_root_frame.grid_columnconfigure(1, weight=0)
        self.middle_root_frame.grid_columnconfigure(2, weight=1)
        self.middle_root_frame.grid_rowconfigure(0, weight=0)
        self.middle_root_frame.grid_rowconfigure(1, weight=1)
        self.create_loottable_section()
        self.create_lootdrop_section()
    def create_loottable_section(self):
        """Create loot table management section"""
        # Loot table frame (top modification bar spanning full width)
        loottable_frame = ttk.Frame(self.middle_root_frame)
        loottable_frame.grid(row=0, column=0, columnspan=3, padx=5, sticky="ew")
        # Loot table modification frame
        loottable_mod_frame = ttk.Frame(loottable_frame, relief=tk.SUNKEN, borderwidth=2)
        loottable_mod_frame.grid(row=0, column=0, sticky="ew", pady=5)
        loottable_mod_frame.grid_columnconfigure(0, weight=0)
        # Make the entire bar a single row of fields/buttons
        # Loot table ID variable
        self.loot_id_var = tk.StringVar(value="Loot Table ID: ")
        ttk.Label(loottable_mod_frame, textvariable=self.loot_id_var, font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="w")
        # Loot table entries
        ttk.Label(loottable_mod_frame, text="Loot Table Name:").grid(row=0, column=1, sticky="w")
        self.loottable_name_entry = ttk.Entry(loottable_mod_frame, width=20)
        self.loottable_name_entry.grid(row=0, column=2, padx=5)
        ttk.Label(loottable_mod_frame, text="Avg Coin:").grid(row=0, column=3, sticky="w")
        self.avgcoin_entry = ttk.Entry(loottable_mod_frame, width=8)
        self.avgcoin_entry.grid(row=0, column=4, padx=5, pady=3, sticky="w")
        ttk.Label(loottable_mod_frame, text="Min Cash:").grid(row=0, column=5, sticky="w")
        self.mincash_entry = ttk.Entry(loottable_mod_frame, width=5)
        self.mincash_entry.grid(row=0, column=6, padx=5, sticky="w")
        ttk.Label(loottable_mod_frame, text="Max Cash:").grid(row=0, column=7, sticky="w")
        self.maxcash_entry = ttk.Entry(loottable_mod_frame, width=8)
        self.maxcash_entry.grid(row=0, column=8, padx=5, pady=3, sticky="w")
        ttk.Label(loottable_mod_frame, text="Min Xpac:").grid(row=0, column=9, sticky="w")
        self.minexpac_entry = ttk.Entry(loottable_mod_frame, width=5)
        self.minexpac_entry.grid(row=0, column=10, padx=5, sticky="w")
        ttk.Label(loottable_mod_frame, text="Max Xpac:").grid(row=0, column=11, sticky="w")
        self.maxexpac_entry = ttk.Entry(loottable_mod_frame, width=5)
        self.maxexpac_entry.grid(row=0, column=12, padx=5, pady=3, sticky="w")
        ttk.Label(loottable_mod_frame, text="Update Changes").grid(row=0, column=13, padx=10, sticky="w")
        ttk.Button(loottable_mod_frame, text="Update", command=self.update_loottable).grid(row=0, column=14, padx=10, pady=3, sticky="w")
        # Middle buttons between trees (create/remove/add lootdrop) in column 1
        loottable_mod_frame2 = ttk.Frame(self.middle_root_frame, relief=tk.SUNKEN, borderwidth=2)
        loottable_mod_frame2.grid(row=1, column=1, sticky="ns", pady=5, padx=3)
        loottable_mod_frame2.grid_columnconfigure(0, weight=1)
        ttk.Button(loottable_mod_frame2, text="Create Lootdrop & Add", command=self.add_new_lootdrop).grid(row=0, column=0, padx=3, pady=2, sticky="ew")
        ttk.Button(loottable_mod_frame2, text="Remove Selected Lootdrop", command=self.remove_selected_lootdrop).grid(row=1, column=0, padx=3, pady=2, sticky="ew")
        ttk.Button(loottable_mod_frame2, text="Add Existing Lootdrop ID:", command=self.add_existing_lootdrop_to_loottable).grid(row=2, column=0, padx=3, pady=(6,2), sticky="ew")
        self.lootdrop_id_entry = ttk.Entry(loottable_mod_frame2, width=12)
        self.lootdrop_id_entry.grid(row=3, column=0, padx=3, pady=(0,2), sticky="ew")
        # Loot table tree placed alongside Loot Drop Entries (same row in middle_root_frame)
        loottable_tree_frame = ttk.Frame(self.middle_root_frame, relief=tk.SUNKEN, borderwidth=2)
        loottable_tree_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        loottable_tree_frame.grid_rowconfigure(1, weight=1)
        loottable_tree_frame.grid_columnconfigure(0, weight=1)
        ttk.Label(loottable_tree_frame, text="Loot Table Entries", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="w")
        self.loot_tree = ttk.Treeview(loottable_tree_frame, height=6,
                                     columns=("LootDrop ID", "LootDrop Name", "Multiplier", "MinDrop", "DropLimit", "Probability"),
                                     show="headings")
        for col in self.loot_tree["columns"]:
            self.loot_tree.heading(col, text=col)
            self.loot_tree.column(col, width=100, stretch=True)
        # Set specific column widths
        self.loot_tree.column("LootDrop ID", width=80, stretch=False)
        self.loot_tree.column("LootDrop Name", width=160, stretch=True)
        self.loot_tree.column("Multiplier", width=65, stretch=False)
        self.loot_tree.column("MinDrop", width=65, stretch=False)
        self.loot_tree.column("DropLimit", width=65, stretch=False)
        self.loot_tree.column("Probability", width=69, stretch=False)
        # Hidden vertical scrollbar (no visible widget) to enable scroll mechanics
        try:
            vbar_lt = ttk.Scrollbar(loottable_tree_frame, orient="vertical", command=self.loot_tree.yview)
            self.loot_tree.configure(yscrollcommand=vbar_lt.set)
            # Do not grid the scrollbar to keep it hidden, but keep a reference
            if not hasattr(self, "_hidden_scrollbars"):
                self._hidden_scrollbars = []
            self._hidden_scrollbars.append(vbar_lt)
        except Exception:
            pass
        self.loot_tree.grid(row=1, column=0, sticky="nsew")
        # Bind events
        self.loot_tree.bind("<<TreeviewSelect>>", self.on_lootdrop_select)
        self.loot_tree.bind("<Double-1>", self.on_loottable_edit)
        self.setup_treeview_sorting(self.loot_tree)
        self._enable_tree_mousewheel(self.loot_tree)
    def create_lootdrop_section(self):
        """Create loot drop management section"""
        # Loot drop frame (placed in same row as the Loot Table tree)
        lootdrop_frame = ttk.Frame(self.middle_root_frame)
        lootdrop_frame.grid(row=1, column=2, sticky="nsew", padx=5)
        # Make two columns: tree (expands) + right controls (fixed)
        lootdrop_frame.grid_columnconfigure(0, weight=1)
        lootdrop_frame.grid_columnconfigure(1, weight=0)
        lootdrop_frame.grid_rowconfigure(0, weight=1)
        # Loot drop tree frame
        loot_tree2_frame = ttk.Frame(lootdrop_frame, relief=tk.SUNKEN, borderwidth=2)
        # Frame fills available space similar to other tree frames
        loot_tree2_frame.grid(row=0, column=0, sticky="nsew", padx=(5,0), pady=5)
        loot_tree2_frame.grid_rowconfigure(1, weight=1)
        loot_tree2_frame.grid_columnconfigure(0, weight=1)
        ttk.Label(loot_tree2_frame, text="Loot Drop Entries", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="w")
        self.loot_tree2 = ttk.Treeview(loot_tree2_frame,
                                      columns=("Item ID", "Item Name", "Charges", "Equip", "Chance",
                                              "  Triv \nMinLvl", "  Triv \nMaxLvl", "Multiplier",
                                              " NPC \nMinLvl", " NPC \nMaxLvl", "Min\nXpac", "Max\nXpac"),
                                      show="headings")
        for col in self.loot_tree2["columns"]:
            self.loot_tree2.heading(col, text=col)
            self.loot_tree2.column(col, width=100, stretch=True)
        # Set tightened column widths
        self.loot_tree2.column("Item ID", width=50, stretch=False)
        self.loot_tree2.column("Item Name", width=120, stretch=True)
        self.loot_tree2.column("Charges", width=45, stretch=False)
        self.loot_tree2.column("Equip", width=45, stretch=False)
        self.loot_tree2.column("Chance", width=45, stretch=False)
        self.loot_tree2.column("  Triv \nMinLvl", width=50, stretch=False)
        self.loot_tree2.column("  Triv \nMaxLvl", width=50, stretch=False)
        self.loot_tree2.column("Multiplier", width=55, stretch=False)
        self.loot_tree2.column(" NPC \nMinLvl", width=50, stretch=False)
        self.loot_tree2.column(" NPC \nMaxLvl", width=50, stretch=False)
        self.loot_tree2.column("Min\nXpac", width=50, stretch=False)
        self.loot_tree2.column("Max\nXpac", width=50, stretch=False)
        # Hidden vertical scrollbar (no visible widget) to enable scroll mechanics
        try:
            vbar_ld = ttk.Scrollbar(loot_tree2_frame, orient="vertical", command=self.loot_tree2.yview)
            self.loot_tree2.configure(yscrollcommand=vbar_ld.set)
            if not hasattr(self, "_hidden_scrollbars"):
                self._hidden_scrollbars = []
            self._hidden_scrollbars.append(vbar_ld)
        except Exception:
            pass
        # Place tree; fill within its frame like other trees
        self.loot_tree2.grid(row=1, column=0, sticky="nsew")
        # Enable mousewheel scrolling without visible scrollbars
        self._enable_tree_mousewheel(self.loot_tree2)
        # Compact button style for smaller controls
        style = ttk.Style()
        try:
            style.configure("Small.TButton", padding=(4, 2), font=("Arial", 9))
        except Exception:
            # Fallback in case theme not initialized yet
            style.configure("Small.TButton", padding=(4, 2))
        # Custom styles to match dark theme for bordered group and placeholder entry
        try:
            entry_bg = style.lookup("TEntry", "fieldbackground") or "#3c3c3c"
            entry_fg = style.lookup("TEntry", "foreground") or "#ffffff"
            frame_bg = style.lookup("TFrame", "background") or "#2d2d2d"
        except Exception:
            entry_bg, entry_fg, frame_bg = "#3c3c3c", "#ffffff", "#2d2d2d"
        placeholder_fg = "#aaaaaa"
        style.configure("Placeholder.TEntry", fieldbackground=entry_bg, foreground=placeholder_fg, insertcolor=entry_fg)
        style.configure("Bordered.TFrame", background=frame_bg, borderwidth=1, relief="sunken")
        # Right-side controls panel anchored to far right of the page section
        lootdrop_side_frame = ttk.Frame(lootdrop_frame)
        lootdrop_side_frame.grid(row=0, column=1, sticky="ns", padx=(0,5), pady=5)
        lootdrop_side_frame.grid_columnconfigure(0, weight=1)
        ttk.Button(lootdrop_side_frame, text="Add Random Item", style="Small.TButton", command=self.add_item_to_lootdrop).grid(row=0, column=0, pady=2, padx=2, sticky="ew")
        ttk.Button(lootdrop_side_frame, text="Remove Selected", style="Small.TButton", command=self.remove_item_from_lootdrop).grid(row=1, column=0, pady=2, padx=2, sticky="ew")
        ttk.Button(lootdrop_side_frame, text="Lookup Item by ID", style="Small.TButton", command=self.lookup_item_by_id).grid(row=2, column=0, pady=2, padx=2, sticky="ew")
        # Item ID input group with small border matching theme
        item_input_frame = ttk.Frame(lootdrop_side_frame, style="Bordered.TFrame")
        item_input_frame.grid(row=3, column=0, padx=2, pady=(8,2), sticky="ew")
        item_input_frame.grid_columnconfigure(0, weight=1)
        # Entry with placeholder text (formerly separate label)
        self.item_id_placeholder = "Item ID:"
        self.item_id_entry = ttk.Entry(item_input_frame, width=14, style="Placeholder.TEntry")
        self.item_id_entry.grid(row=0, column=0, padx=4, pady=4, sticky="ew")
        self.item_id_entry.insert(0, self.item_id_placeholder)
        def _clear_item_id_placeholder(event):
            if self.item_id_entry.get() == self.item_id_placeholder:
                self.item_id_entry.delete(0, tk.END)
                try:
                    self.item_id_entry.configure(style="TEntry")
                except Exception:
                    pass
        def _restore_item_id_placeholder(event):
            if not self.item_id_entry.get():
                self.item_id_entry.insert(0, self.item_id_placeholder)
                try:
                    self.item_id_entry.configure(style="Placeholder.TEntry")
                except Exception:
                    pass
        self.item_id_entry.bind("<FocusIn>", _clear_item_id_placeholder)
        self.item_id_entry.bind("<FocusOut>", _restore_item_id_placeholder)
        # Button inside the bordered frame
        ttk.Button(item_input_frame, text="Add Specific Item", style="Small.TButton", command=self.add_specific_item_to_lootdrop).grid(row=1, column=0, padx=4, pady=(0,4), sticky="ew")
        # Bind events
        self.loot_tree2.bind("<<TreeviewSelect>>", self.on_item_select)
        self.loot_tree2.bind("<Double-1>", self.on_lootdrop_edit)
        self.setup_treeview_sorting(self.loot_tree2)
    def create_bottom_section(self):
        """Create bottom section with NPC list and editor"""
        # Bottom frame
        bottom_frame = ttk.Frame(self.main_frame, relief=tk.SUNKEN, borderwidth=1)
        bottom_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        bottom_frame.grid_rowconfigure(0, weight=1)
        bottom_frame.grid_columnconfigure(0, weight=1)
        npc_mod_frame = ttk.Frame(bottom_frame, relief=tk.SUNKEN, borderwidth=2)
        npc_mod_frame.grid(row=0, column=0, sticky="nsew", pady=5, padx=5)
        npc_mod_frame.grid_rowconfigure(1, weight=1)
        npc_mod_frame.grid_columnconfigure(0, weight=1)
        npc_tree_frame = ttk.Frame(npc_mod_frame)
        npc_tree_frame.grid(row=0, column=0, sticky="nsew")
        npc_tree_frame.grid_rowconfigure(1, weight=1)
        npc_tree_frame.grid_columnconfigure(0, weight=1)
        ttk.Label(npc_tree_frame, text="NPC List and Editor", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="w")
        # NPC tree with all the columns from the original
        npc_columns = ("ID", "Name", "Lvl", "Race", "Class", "Body", "HP", "Mana",
                      "Gender", "Texture", "Helm\nTexture", "Size", "  Loot\nTable ID", "Spells\n  ID", "Faction\n   ID",
                      "Min\ndmg", "Max\ndmg", "Npcspecial\n  attks", "Special\nAbilities", "MR", "CR", "DR", "FR", "PR", "AC",
                      "Attk Delay", "STR", "STA", "DEX", "AGI", "_INT", "WIS", "Maxlevel",
                      "Skip Global Loot", "Exp Mod")
        self.npc_tree = ttk.Treeview(npc_tree_frame, columns=npc_columns, show="headings")
        # Define column widths like the original
        column_widths = {
            "ID": 50, "Name": 250, "Lvl": 45, "Race": 45, "Class": 45, "Body": 36, "HP": 25, "Mana": 35,
            "Gender": 45, "Texture": 50, "Helm\nTexture": 40, "Size": 45, "  Loot\nTable ID": 50, "Spells\n  ID": 50,
            "Faction\n   ID": 45, "Min\ndmg": 40, "Max\ndmg": 40, "Npcspecial\n  attks": 55, "Special\nAbilities": 50,
            "MR": 35, "CR": 35, "DR": 35, "FR": 35, "PR": 35, "AC": 35, "Attk Delay": 55,
            "STR": 35, "STA": 35, "DEX": 35, "AGI": 35, "_INT": 35, "WIS": 35, "Maxlevel": 45,
            "Skip Global Loot": 60, "Exp Mod": 50
        }
        for col in npc_columns:
            self.npc_tree.heading(col, text=col)
            width = column_widths.get(col, 50)
            self.npc_tree.column(col, width=width, stretch=False)
        self.npc_tree.grid(row=1, column=0, sticky="nsew")
        # Bind events
        self.npc_tree.bind("<<TreeviewSelect>>", self.on_npc_select)
        self.npc_tree.bind("<Double-1>", self.on_npc_edit)
        self.setup_treeview_sorting(self.npc_tree)
    def find_unused_ids(self):
        """Find unused loot table and loot drop IDs"""

        def _collect_unused(table_name, max_needed=9):
            query = f"SELECT id FROM {table_name} ORDER BY id ASC"
            try:
                rows = self.db_manager.execute_query(query)
            except Exception as exc:
                print(f"Could not query unused IDs for {table_name}: {exc}")
                return [str(i) for i in range(1, max_needed + 1)]

            ids = []
            for row in rows:
                value = row.get("id") if isinstance(row, dict) else row[0]
                try:
                    ids.append(int(value))
                except (TypeError, ValueError):
                    continue
            unused = []
            expected = 1
            for current in ids:
                if current < expected:
                    continue
                while expected < current and len(unused) < max_needed:
                    unused.append(str(expected))
                    expected += 1
                if current == expected:
                    expected += 1
                if len(unused) >= max_needed:
                    break
            while len(unused) < max_needed:
                unused.append(str(expected))
                expected += 1
            return unused

        unused_loottable_ids = _collect_unused("loottable")
        unused_lootdrop_ids = _collect_unused("lootdrop")

        self.unused_loottable_label.config(text=", ".join(unused_loottable_ids))
        self.unused_lootdrop_label.config(text=", ".join(unused_lootdrop_ids))

        first_unused_loottable_id = int(unused_loottable_ids[0]) if unused_loottable_ids else None
        first_unused_lootdrop_id = int(unused_lootdrop_ids[0]) if unused_lootdrop_ids else None

        return first_unused_loottable_id, first_unused_lootdrop_id
    def clear_results(self, clear_type="all"):
        """Clear search results and forms"""
        self.zone_entry.delete(0, tk.END)
        self.npc_name_entry.delete(0, tk.END)
        self.loottable_id_entry.delete(0, tk.END)
        if clear_type == "all":
            for item in self.npc_tree.get_children():
                self.npc_tree.delete(item)
            for item in self.loot_tree.get_children():
                self.loot_tree.delete(item)
            for item in self.loot_tree2.get_children():
                self.loot_tree2.delete(item)
            self.loot_id_var.set("Loot Table ID: ")
            self.loottable_name_entry.delete(0, tk.END)
            self.mincash_entry.delete(0, tk.END)
            self.maxcash_entry.delete(0, tk.END)
            self.avgcoin_entry.delete(0, tk.END)
            self.minexpac_entry.delete(0, tk.END)
            self.maxexpac_entry.delete(0, tk.END)
            self.item_id_entry.delete(0, tk.END)
            try:
                # Restore placeholder example after clearing
                if hasattr(self, 'item_id_placeholder'):
                    self.item_id_entry.insert(0, self.item_id_placeholder)
                    # Ensure placeholder style is applied to match theme
                    self.item_id_entry.configure(style="Placeholder.TEntry")
            except Exception:
                pass
            self.lootdrop_id_entry.delete(0, tk.END)
    def search_zone(self):
        """Search NPCs by zone"""
        zone = self.zone_entry.get().strip()
        try:
            version = int(self.version_var.get())
        except Exception:
            version = 0
        if not zone:
            return
        # Clear existing items
        for item in self.npc_tree.get_children():
            self.npc_tree.delete(item)
        query = """
            SELECT DISTINCT npc_types.id, npc_types.name, npc_types.level, npc_types.race, npc_types.class, npc_types.bodytype, npc_types.hp, npc_types.mana,
                   npc_types.gender, npc_types.texture, npc_types.helmtexture, npc_types.size, npc_types.loottable_id, npc_types.npc_spells_id, npc_types.npc_faction_id,
                   npc_types.mindmg, npc_types.maxdmg, npc_types.npcspecialattks, npc_types.special_abilities, npc_types.MR, npc_types.CR, npc_types.DR, npc_types.FR, npc_types.PR, npc_types.AC,
                   npc_types.attack_delay, npc_types.STR, npc_types.STA, npc_types.DEX, npc_types.AGI, npc_types._INT, npc_types.WIS,
                   npc_types.maxlevel, npc_types.skip_global_loot, npc_types.exp_mod
            FROM spawn2
            JOIN spawnentry ON spawn2.spawngroupID = spawnentry.spawngroupID
            JOIN npc_types ON spawnentry.npcID = npc_types.id
            WHERE spawn2.zone = %s AND spawn2.version = %s
        """
        npcs = self.db_manager.execute_query(query, (zone, version))
        for npc in npcs:
            # Convert dictionary to tuple of values ordered by columns
            if isinstance(npc, dict):
                # Extract values in the same order as the treeview columns
                npc_values = [
                    npc.get('id'), npc.get('name'), npc.get('level'), npc.get('race'), npc.get('class'),
                    npc.get('bodytype'), npc.get('hp'), npc.get('mana'), npc.get('gender'),
                    npc.get('texture'), npc.get('helmtexture'), npc.get('size'), npc.get('loottable_id'),
                    npc.get('npc_spells_id'), npc.get('npc_faction_id'), npc.get('mindmg'), npc.get('maxdmg'),
                    npc.get('npcspecialattks'), npc.get('special_abilities'), npc.get('MR'), npc.get('CR'),
                    npc.get('DR'), npc.get('FR'), npc.get('PR'), npc.get('AC'), npc.get('attack_delay'),
                    npc.get('STR'), npc.get('STA'), npc.get('DEX'), npc.get('AGI'), npc.get('_INT'),
                    npc.get('WIS'), npc.get('maxlevel'), npc.get('skip_global_loot'), npc.get('exp_mod')
                ]
                self.npc_tree.insert("", tk.END, values=npc_values)
            else:
                self.npc_tree.insert("", tk.END, values=npc)
        print(f"Found {len(npcs)} NPCs in zone '{zone}'")
    def search_npc_name(self):
        """Search NPCs by name"""
        npc_name = self.npc_name_entry.get().strip()
        if not npc_name:
            return
        # Clear existing items
        for item in self.npc_tree.get_children():
            self.npc_tree.delete(item)
        query = """
            SELECT DISTINCT id, name, level, race, class, bodytype, hp, mana,
                   gender, texture, helmtexture, size, loottable_id, npc_spells_id, npc_faction_id,
                   mindmg, maxdmg, npcspecialattks, special_abilities, MR, CR, DR, FR, PR, AC,
                   attack_delay, STR, STA, DEX, AGI, _INT, WIS,
                   maxlevel, skip_global_loot, exp_mod
            FROM npc_types
            WHERE name LIKE %s
        """
        npcs = self.db_manager.execute_query(query, (f"%{npc_name}%",))
        for npc in npcs:
            # Convert dictionary to tuple of values ordered by columns
            if isinstance(npc, dict):
                # Extract values in the same order as the treeview columns
                npc_values = [
                    npc.get('id'), npc.get('name'), npc.get('level'), npc.get('race'), npc.get('class'),
                    npc.get('bodytype'), npc.get('hp'), npc.get('mana'), npc.get('gender'),
                    npc.get('texture'), npc.get('helmtexture'), npc.get('size'), npc.get('loottable_id'),
                    npc.get('npc_spells_id'), npc.get('npc_faction_id'), npc.get('mindmg'), npc.get('maxdmg'),
                    npc.get('npcspecialattks'), npc.get('special_abilities'), npc.get('MR'), npc.get('CR'),
                    npc.get('DR'), npc.get('FR'), npc.get('PR'), npc.get('AC'), npc.get('attack_delay'),
                    npc.get('STR'), npc.get('STA'), npc.get('DEX'), npc.get('AGI'), npc.get('_INT'),
                    npc.get('WIS'), npc.get('maxlevel'), npc.get('skip_global_loot'), npc.get('exp_mod')
                ]
                self.npc_tree.insert("", tk.END, values=npc_values)
            else:
                self.npc_tree.insert("", tk.END, values=npc)
        print(f"Found {len(npcs)} NPCs matching '{npc_name}'")
    def search_loottable_id(self):
        """Search by loot table ID"""
        loottable_id = self.loottable_id_entry.get().strip()
        if not loottable_id:
            return
        try:
            loottable_id = int(loottable_id)
        except ValueError:
            messagebox.showerror("Error", "Loot table ID must be a number")
            return
        # Clear existing loot trees
        for item in self.loot_tree.get_children():
            self.loot_tree.delete(item)
        for item in self.loot_tree2.get_children():
            self.loot_tree2.delete(item)
        # Load loot table data
        self.load_loottable_data(loottable_id)
        # Load NPCs that use this loot table
        for item in self.npc_tree.get_children():
            self.npc_tree.delete(item)
        query = """
            SELECT id, name, level, race, class, bodytype, hp, mana,
                   gender, texture, helmtexture, size, loottable_id, npc_spells_id, npc_faction_id,
                   mindmg, maxdmg, npcspecialattks, special_abilities, MR, CR, DR, FR, PR, AC,
                   attack_delay, STR, STA, DEX, AGI, _INT, WIS,
                   maxlevel, skip_global_loot, exp_mod
            FROM npc_types
            WHERE loottable_id = %s
        """
        npcs = self.db_manager.execute_query(query, (loottable_id,))
        for npc in npcs:
            # Convert dictionary to tuple of values ordered by columns
            if isinstance(npc, dict):
                # Extract values in the same order as the treeview columns
                npc_values = [
                    npc.get('id'), npc.get('name'), npc.get('level'), npc.get('race'), npc.get('class'),
                    npc.get('bodytype'), npc.get('hp'), npc.get('mana'), npc.get('gender'),
                    npc.get('texture'), npc.get('helmtexture'), npc.get('size'), npc.get('loottable_id'),
                    npc.get('npc_spells_id'), npc.get('npc_faction_id'), npc.get('mindmg'), npc.get('maxdmg'),
                    npc.get('npcspecialattks'), npc.get('special_abilities'), npc.get('MR'), npc.get('CR'),
                    npc.get('DR'), npc.get('FR'), npc.get('PR'), npc.get('AC'), npc.get('attack_delay'),
                    npc.get('STR'), npc.get('STA'), npc.get('DEX'), npc.get('AGI'), npc.get('_INT'),
                    npc.get('WIS'), npc.get('maxlevel'), npc.get('skip_global_loot'), npc.get('exp_mod')
                ]
                self.npc_tree.insert("", tk.END, values=npc_values)
            else:
                self.npc_tree.insert("", tk.END, values=npc)
    def load_loottable_data(self, loottable_id):
        """Load loot table data into the interface"""
        # Load loot table info
        table_query = """
            SELECT name, mincash, maxcash, avgcoin, done, min_expansion, max_expansion
            FROM loottable
            WHERE id = %s
        """
        table_data = self.db_manager.execute_query(table_query, (loottable_id,), fetch_all=False)
        if table_data:
            if isinstance(table_data, dict):
                name = table_data.get("name")
                mincash = table_data.get("mincash")
                maxcash = table_data.get("maxcash")
                avgcoin = table_data.get("avgcoin")
                min_expansion = table_data.get("min_expansion")
                max_expansion = table_data.get("max_expansion")
            else:
                name = table_data[0]
                mincash = table_data[1]
                maxcash = table_data[2]
                avgcoin = table_data[3]
                min_expansion = table_data[5]
                max_expansion = table_data[6]
            self.loot_id_var.set(f"Loot Table ID: {loottable_id}")
            self.loottable_name_entry.delete(0, tk.END)
            self.loottable_name_entry.insert(0, name or "")
            self.mincash_entry.delete(0, tk.END)
            self.mincash_entry.insert(0, str(mincash or 0))
            self.maxcash_entry.delete(0, tk.END)
            self.maxcash_entry.insert(0, str(maxcash or 0))
            self.avgcoin_entry.delete(0, tk.END)
            self.avgcoin_entry.insert(0, str(avgcoin or 0))
            self.minexpac_entry.delete(0, tk.END)
            self.minexpac_entry.insert(0, str(min_expansion or 0))
            self.maxexpac_entry.delete(0, tk.END)
            self.maxexpac_entry.insert(0, str(max_expansion or 0))
        # Load loot drops
        drops_query = """
            SELECT lde.lootdrop_id, ld.name, lde.multiplier, lde.droplimit, lde.mindrop, lde.probability
            FROM loottable_entries lde
            LEFT JOIN lootdrop ld ON lde.lootdrop_id = ld.id
            WHERE lde.loottable_id = %s
            ORDER BY lde.lootdrop_id
        """
        drops = self.db_manager.execute_query(drops_query, (loottable_id,))
        for drop in drops:
            if isinstance(drop, dict):
                drop_values = [
                    drop.get("lootdrop_id"),
                    drop.get("name"),
                    drop.get("multiplier"),
                    drop.get("mindrop"),
                    drop.get("droplimit"),
                    drop.get("probability"),
                ]
            else:
                drop_values = (
                    drop[0],
                    drop[1],
                    drop[2],
                    drop[4],
                    drop[3],
                    drop[5],
                )
            self.loot_tree.insert("", tk.END, values=drop_values)
        self.current_loottable_id = loottable_id
    def add_lootdrop_to_loottable(self):
        """Create a new loot table with an initial loot drop."""
        loot_table_id, loot_drop_id = self.find_unused_ids()
        if not loot_table_id or not loot_drop_id:
            messagebox.showerror("Error", "Could not determine unused IDs.")
            return
        try:
            self.db_manager.execute_update(
                """
                INSERT INTO loottable (id, name, mincash, maxcash, avgcoin, done, min_expansion, max_expansion)
                VALUES (%s, %s, 0, 0, 0, 0, -1, -1)
                """,
                (loot_table_id, f"New Loot Table {loot_table_id}"),
            )
            self.db_manager.execute_update(
                """
                INSERT INTO lootdrop (id, name, min_expansion, max_expansion)
                VALUES (%s, %s, -1, -1)
                """,
                (loot_drop_id, f"New Loot Drop {loot_drop_id}"),
            )
            self.db_manager.execute_update(
                """
                INSERT INTO loottable_entries (loottable_id, lootdrop_id, multiplier, droplimit, mindrop, probability)
                VALUES (%s, %s, 1, 1, 1, 100)
                """,
                (loot_table_id, loot_drop_id),
            )
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to create loot table: {exc}")
            return
        self.current_loottable_id = loot_table_id
        self.load_loottable_data(loot_table_id)
        self.find_unused_ids()
        messagebox.showinfo("Success", f"Created loot table {loot_table_id} with loot drop {loot_drop_id}")
    def view_all_loottables(self):
        """Show a selector with every loot table so one can be loaded quickly."""
        query = """
            SELECT id, name, mincash, maxcash, avgcoin, min_expansion, max_expansion
            FROM loottable
            ORDER BY id
        """
        try:
            loottables = self.db_manager.execute_query(query)
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to load loot tables: {exc}")
            return
        if not loottables:
            messagebox.showinfo("Info", "No loot tables found.")
            return
        if getattr(self, "_loottable_browser", None) and self._loottable_browser.winfo_exists():
            self._loottable_browser.lift()
            return
        browser = tk.Toplevel(self.parent)
        browser.title("All Loot Tables")
        browser.geometry("720x420")
        browser.transient(self.parent.winfo_toplevel())
        self._loottable_browser = browser
        columns = ("ID", "Name", "Min Cash", "Max Cash", "Avg Coin", "Min Xpac", "Max Xpac")
        tree = ttk.Treeview(browser, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            width = 80 if col == "ID" else 120
            tree.column(col, width=width, stretch=True)
        tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(browser, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")
        browser.grid_rowconfigure(0, weight=1)
        browser.grid_columnconfigure(0, weight=1)
        for row in loottables:
            if isinstance(row, dict):
                values = (
                    row.get("id"),
                    row.get("name"),
                    row.get("mincash"),
                    row.get("maxcash"),
                    row.get("avgcoin"),
                    row.get("min_expansion"),
                    row.get("max_expansion"),
                )
            else:
                values = row[:7]
            tree.insert("", tk.END, values=values)
        def _close_browser():
            self._loottable_browser = None
            browser.destroy()
        def _load_selected(event=None):
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Warning", "Select a loot table first.")
                return
            loottable_id = tree.item(selected[0], "values")[0]
            try:
                loottable_id = int(loottable_id)
            except (TypeError, ValueError):
                messagebox.showerror("Error", "Invalid loot table id selected.")
                return
            # Refresh UI with the selection
            self.load_loottable_data(loottable_id)
            self.current_loottable_id = loottable_id
            self.loottable_id_entry.delete(0, tk.END)
            self.loottable_id_entry.insert(0, str(loottable_id))
            # Repopulate the NPC list just like search_loottable_id does
            for node in self.npc_tree.get_children():
                self.npc_tree.delete(node)
            npc_query = """
                SELECT id, name, level, race, class, bodytype, hp, mana,
                       gender, texture, helmtexture, size, loottable_id, npc_spells_id, npc_faction_id,
                       mindmg, maxdmg, npcspecialattks, special_abilities, MR, CR, DR, FR, PR, AC,
                       attack_delay, STR, STA, DEX, AGI, _INT, WIS,
                       maxlevel, skip_global_loot, exp_mod
                FROM npc_types
                WHERE loottable_id = %s
            """
            npcs = self.db_manager.execute_query(npc_query, (loottable_id,))
            for npc in npcs:
                if isinstance(npc, dict):
                    npc_values = [
                        npc.get('id'), npc.get('name'), npc.get('level'), npc.get('race'), npc.get('class'),
                        npc.get('bodytype'), npc.get('hp'), npc.get('mana'), npc.get('gender'),
                        npc.get('texture'), npc.get('helmtexture'), npc.get('size'), npc.get('loottable_id'),
                        npc.get('npc_spells_id'), npc.get('npc_faction_id'), npc.get('mindmg'), npc.get('maxdmg'),
                        npc.get('npcspecialattks'), npc.get('special_abilities'), npc.get('MR'), npc.get('CR'),
                        npc.get('DR'), npc.get('FR'), npc.get('PR'), npc.get('AC'), npc.get('attack_delay'),
                        npc.get('STR'), npc.get('STA'), npc.get('DEX'), npc.get('AGI'), npc.get('_INT'),
                        npc.get('WIS'), npc.get('maxlevel'), npc.get('skip_global_loot'), npc.get('exp_mod')
                    ]
                else:
                    npc_values = npc
                self.npc_tree.insert("", tk.END, values=npc_values)
            _close_browser()
        ttk.Button(browser, text="Load Selected", command=_load_selected).grid(row=1, column=0, pady=6, padx=6, sticky="e")
        tree.bind("<Double-1>", _load_selected)
        browser.protocol("WM_DELETE_WINDOW", _close_browser)
    def update_loottable(self):
        """Update loot table information"""
        if not hasattr(self, 'current_loottable_id'):
            messagebox.showwarning("Warning", "No loot table selected")
            return

        name = self.loottable_name_entry.get().strip()

        def _to_int(entry_widget):
            value = entry_widget.get().strip()
            if value == "":
                return 0
            try:
                return int(value)
            except ValueError:
                raise

        try:
            avgcoin = _to_int(self.avgcoin_entry)
            mincash = _to_int(self.mincash_entry)
            maxcash = _to_int(self.maxcash_entry)
            min_expansion = _to_int(self.minexpac_entry)
            max_expansion = _to_int(self.maxexpac_entry)
        except ValueError:
            messagebox.showerror("Error", "Cash and expansion fields must be numeric")
            return

        update_query = """
            UPDATE loottable
            SET name = %s,
                avgcoin = %s,
                mincash = %s,
                maxcash = %s,
                min_expansion = %s,
                max_expansion = %s
            WHERE id = %s
        """

        params = (
            name,
            avgcoin,
            mincash,
            maxcash,
            min_expansion,
            max_expansion,
            self.current_loottable_id,
        )

        try:
            self.db_manager.execute_update(update_query, params)
            self.load_loottable_data(self.current_loottable_id)
            messagebox.showinfo("Success", "Loot table updated")
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to update loot table: {exc}")
    def add_new_lootdrop(self):
        """Add new loot drop to current loot table"""
        if not hasattr(self, 'current_loottable_id'):
            messagebox.showwarning("Warning", "No loot table selected")
            return
        # Find unused loot drop ID
        unused_ids = self.find_unused_ids()
        if not unused_ids[1]:
            messagebox.showerror("Error", "Could not find unused loot drop ID")
            return
        lootdrop_id = unused_ids[1]
        # Create new loot drop
        drop_query = """
            INSERT INTO lootdrop (id, name, min_expansion, max_expansion)
            VALUES (%s, %s, -1, -1)
        """
        # Link to current loot table
        entry_query = """
            INSERT INTO loottable_entries (loottable_id, lootdrop_id, multiplier, droplimit, mindrop, probability)
            VALUES (%s, %s, 1, 1, 1, 100)
        """
        try:
            self.db_manager.execute_update(drop_query, (lootdrop_id, f"New Loot Drop {lootdrop_id}"))
            self.db_manager.execute_update(entry_query, (self.current_loottable_id, lootdrop_id))
            # Refresh the loot table display
            self.load_loottable_data(self.current_loottable_id)
            messagebox.showinfo("Success", f"Created loot drop {lootdrop_id}")
            self.find_unused_ids()  # Refresh unused IDs
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create loot drop: {e}")
    def remove_selected_lootdrop(self):
        """Remove selected loot drop from loot table"""
        selected_item = self.loot_tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "No loot drop selected")
            return
        if not hasattr(self, 'current_loottable_id'):
            messagebox.showwarning("Warning", "No loot table selected")
            return
        lootdrop_id = self.loot_tree.item(selected_item, "values")[0]
        lootdrop_name = self.loot_tree.item(selected_item, "values")[1]
        # Confirm deletion
        if not messagebox.askyesno("Confirm", f"Remove loot drop '{lootdrop_name}' from loot table?"):
            return
        query = "DELETE FROM loottable_entries WHERE loottable_id = %s AND lootdrop_id = %s"
        try:
            self.db_manager.execute_update(query, (self.current_loottable_id, lootdrop_id))
            messagebox.showinfo("Success", f"Removed loot drop from loot table")
            # Remove from treeview
            self.loot_tree.delete(selected_item)
            # Clear loot drop contents
            for item in self.loot_tree2.get_children():
                self.loot_tree2.delete(item)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to remove loot drop: {e}")
    def add_existing_lootdrop_to_loottable(self):
        """Add existing loot drop to current loot table"""
        if not hasattr(self, 'current_loottable_id'):
            messagebox.showwarning("Warning", "No loot table selected")
            return
        lootdrop_id = self.lootdrop_id_entry.get().strip()
        if not lootdrop_id:
            messagebox.showwarning("Warning", "Please enter a loot drop ID")
            return
        try:
            lootdrop_id = int(lootdrop_id)
        except ValueError:
            messagebox.showerror("Error", "Loot drop ID must be a number")
            return
        # Check if loot drop exists
        check_query = "SELECT id, name FROM lootdrop WHERE id = %s"
        result = self.db_manager.execute_query(check_query, (lootdrop_id,), fetch_all=False)
        if not result:
            messagebox.showerror("Error", f"Loot drop ID {lootdrop_id} not found")
            return
        if isinstance(result, dict):
            lootdrop_name = result.get("name", "")
        else:
            lootdrop_name = result[1] if len(result) > 1 else ""
        # Check if already linked
        link_check = "SELECT lootdrop_id FROM loottable_entries WHERE loottable_id = %s AND lootdrop_id = %s"
        existing = self.db_manager.execute_query(link_check, (self.current_loottable_id, lootdrop_id), fetch_all=False)
        if existing:
            messagebox.showwarning("Warning", "Loot drop already linked to this loot table")
            return
        # Add link
        entry_query = """
            INSERT INTO loottable_entries (loottable_id, lootdrop_id, multiplier, droplimit, mindrop, probability)
            VALUES (%s, %s, 1, 1, 1, 100)
        """
        try:
            self.db_manager.execute_update(entry_query, (self.current_loottable_id, lootdrop_id))
            # Refresh the loot table display
            self.load_loottable_data(self.current_loottable_id)
            messagebox.showinfo("Success", f"Added loot drop {lootdrop_name} to loot table")
            self.lootdrop_id_entry.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add loot drop: {e}")
    def add_item_to_lootdrop_by_id(self, item_id):
        """Add item to loot drop by ID"""
        if not hasattr(self, 'current_lootdrop_id'):
            messagebox.showwarning("Warning", "No loot drop selected")
            return
        # Check if item exists
        item_query = "SELECT id, Name FROM items WHERE id = %s"
        item_result = self.db_manager.execute_query(item_query, (item_id,), fetch_all=False)
        if not item_result:
            messagebox.showerror("Error", f"Item ID {item_id} not found")
            return
        if isinstance(item_result, dict):
            item_name = item_result.get("Name", "")
        else:
            item_name = item_result[1] if len(item_result) > 1 else ""
        # Check if item already exists in loot drop
        check_query = "SELECT item_id FROM lootdrop_entries WHERE lootdrop_id = %s AND item_id = %s"
        existing = self.db_manager.execute_query(check_query, (self.current_lootdrop_id, item_id), fetch_all=False)
        if existing:
            messagebox.showwarning("Warning", "Item already exists in this loot drop")
            return
        # Add item to loot drop
        insert_query = """
            INSERT INTO lootdrop_entries (
                lootdrop_id,
                item_id,
                item_charges,
                equip_item,
                chance,
                trivial_min_level,
                trivial_max_level,
                multiplier,
                npc_min_level,
                npc_max_level,
                min_expansion,
                max_expansion
            )
            VALUES (%s, %s, 1, 1, 100, 0, 0, 1, 0, 0, -1, -1)
        """
        try:
            self.db_manager.execute_update(insert_query, (self.current_lootdrop_id, item_id))
            messagebox.showinfo("Success", f"Added item {item_name} to loot drop")
            # Refresh the loot drop display
            self.on_lootdrop_select(None)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add item: {e}")
    def on_lootdrop_select(self, event):
        """Handle loot drop selection"""
        selected_item = self.loot_tree.selection()
        if not selected_item:
            return
        lootdrop_values = self.loot_tree.item(selected_item, "values")
        if not lootdrop_values:
            return
        lootdrop_id = lootdrop_values[0]
        if not lootdrop_id:
            return
        try:
            self.current_lootdrop_id = int(lootdrop_id)
        except (TypeError, ValueError):
            self.current_lootdrop_id = lootdrop_id
        for item in self.loot_tree2.get_children():
            self.loot_tree2.delete(item)
        entries_query = """
            SELECT lde.item_id, i.Name AS item_name, lde.item_charges, lde.equip_item, lde.chance,
                   lde.trivial_min_level, lde.trivial_max_level, lde.multiplier,
                   lde.npc_min_level, lde.npc_max_level, lde.min_expansion, lde.max_expansion
            FROM lootdrop_entries lde
            LEFT JOIN items i ON lde.item_id = i.id
            WHERE lde.lootdrop_id = %s
            ORDER BY lde.item_id
        """
        entries = self.db_manager.execute_query(entries_query, (lootdrop_id,))
        for entry in entries:
            if isinstance(entry, dict):
                equip_val = entry.get("equip_item")
                entry_values = [
                    entry.get("item_id"),
                    entry.get("item_name") or entry.get("Name"),
                    entry.get("item_charges"),
                    "Yes" if equip_val in (1, True, "1", "Yes") else "No",
                    entry.get("chance"),
                    entry.get("trivial_min_level"),
                    entry.get("trivial_max_level"),
                    entry.get("multiplier"),
                    entry.get("npc_min_level"),
                    entry.get("npc_max_level"),
                    entry.get("min_expansion"),
                    entry.get("max_expansion"),
                ]
            else:
                equip_val = entry[3] if len(entry) > 3 else 0
                entry_values = [
                    entry[0],
                    entry[1],
                    entry[2],
                    "Yes" if equip_val else "No",
                    entry[4],
                    entry[5],
                    entry[6],
                    entry[7],
                    entry[8],
                    entry[9],
                    entry[10],
                    entry[11],
                ]
            self.loot_tree2.insert("", tk.END, values=entry_values)
    def on_loottable_edit(self, event):
        """Handle loot table editing"""
        tree = event.widget
        region = tree.identify_region(event.x, event.y)
        if region != "cell":
            return

        column = tree.identify_column(event.x)
        item = tree.identify_row(event.y)
        if not item or not column:
            return

        column_index = int(column[1:]) - 1
        item_values = list(tree.item(item, "values"))
        current_value = item_values[column_index]
        bbox = tree.bbox(item, column)
        if not bbox:
            return

        entry = tk.Entry(tree)
        entry.insert(0, current_value)
        entry.select_range(0, tk.END)
        entry.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])
        entry.focus_set()

        def save_edit(event=None):
            new_value = entry.get()
            if not hasattr(self, 'current_loottable_id'):
                entry.destroy()
                return

            lootdrop_id = tree.item(item, "values")[0]
            if not lootdrop_id:
                entry.destroy()
                return

            lootdrop_id = int(lootdrop_id)

            lootdrop_fields = {1: "name"}
            entry_fields = {
                2: "multiplier",
                3: "mindrop",
                4: "droplimit",
                5: "probability",
            }

            if column_index in lootdrop_fields:
                field_name = lootdrop_fields[column_index]
                value_for_db = new_value.strip()
                if not value_for_db:
                    messagebox.showerror("Error", "Name cannot be empty")
                    entry.destroy()
                    return
                query = f"UPDATE lootdrop SET {field_name} = %s WHERE id = %s"
                params = (value_for_db, lootdrop_id)
            elif column_index in entry_fields:
                field_name = entry_fields[column_index]
                try:
                    value_for_db = int(new_value)
                except ValueError:
                    messagebox.showerror("Error", f"{field_name} must be numeric")
                    entry.destroy()
                    return
                query = (
                    f"UPDATE loottable_entries SET {field_name} = %s "
                    "WHERE loottable_id = %s AND lootdrop_id = %s"
                )
                params = (value_for_db, self.current_loottable_id, lootdrop_id)
            else:
                entry.destroy()
                return

            try:
                self.db_manager.execute_update(query, params)
                item_values[column_index] = new_value
                tree.item(item, values=item_values)
            except Exception as exc:
                messagebox.showerror("Error", f"Failed to update loot table entry: {exc}")
            finally:
                entry.destroy()

        def cancel_edit(event=None):
            entry.destroy()

        entry.bind("<Return>", save_edit)
        entry.bind("<Escape>", cancel_edit)
        entry.bind("<FocusOut>", save_edit)
    def remove_item_from_lootdrop(self):
        """Remove the currently selected item from the active loot drop."""
        if not hasattr(self, 'current_lootdrop_id'):
            messagebox.showwarning("Warning", "No loot drop selected.")
            return
        selected_item = self.loot_tree2.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "No loot drop item selected.")
            return
        item_values = self.loot_tree2.item(selected_item, "values")
        if not item_values:
            return
        item_id = item_values[0]
        item_name = item_values[1]
        if not messagebox.askyesno(
            "Confirm",
            f"Remove item '{item_name}' ({item_id}) from this loot drop?"
        ):
            return
        delete_query = """
            DELETE FROM lootdrop_entries
            WHERE lootdrop_id = %s AND item_id = %s
        """
        try:
            self.db_manager.execute_update(delete_query, (self.current_lootdrop_id, item_id))
            self.loot_tree2.delete(selected_item)
            messagebox.showinfo("Success", f"Removed {item_name} from loot drop.")
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to remove item: {exc}")
    def add_item_to_lootdrop(self):
        """Add a random item from the items table to the active loot drop."""
        if not hasattr(self, 'current_lootdrop_id'):
            messagebox.showwarning("Warning", "No loot drop selected.")
            return
        query = """
            SELECT id, Name
            FROM items
            WHERE id NOT IN (
                SELECT item_id FROM lootdrop_entries WHERE lootdrop_id = %s
            )
            ORDER BY RAND()
            LIMIT 1
        """
        try:
            result = self.db_manager.execute_query(query, (self.current_lootdrop_id,), fetch_all=False)
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to select random item: {exc}")
            return
        if not result:
            messagebox.showinfo("Info", "No available items to add.")
            return
        item_id = result.get("id") if isinstance(result, dict) else result[0]
        self.add_item_to_lootdrop_by_id(item_id)
    def lookup_item_by_id(self):
        """Lookup an item by ID and display it on the preview pane."""
        item_id_text = self.item_id_entry.get().strip()
        if not item_id_text or item_id_text == getattr(self, 'item_id_placeholder', ''):
            messagebox.showwarning("Warning", "Enter an item ID first.")
            return
        try:
            item_id = int(item_id_text)
        except ValueError:
            messagebox.showerror("Error", "Item ID must be a number.")
            return
        if not self._display_item_details(item_id):
            messagebox.showerror("Error", f"Item ID {item_id} not found.")
    def add_specific_item_to_lootdrop(self):
        """Add a user supplied item ID to the active loot drop."""
        if not hasattr(self, 'current_lootdrop_id'):
            messagebox.showwarning("Warning", "No loot drop selected.")
            return
        item_id_text = self.item_id_entry.get().strip()
        if not item_id_text or item_id_text == getattr(self, 'item_id_placeholder', ''):
            messagebox.showwarning("Warning", "Enter an item ID first.")
            return
        try:
            item_id = int(item_id_text)
        except ValueError:
            messagebox.showerror("Error", "Item ID must be a number.")
            return
        self.add_item_to_lootdrop_by_id(item_id)
        self.item_id_entry.delete(0, tk.END)
    # Notes button moved to main window; handler removed from this tool
    def on_item_select(self, event):
        """CRITICAL: Handle item selection and display stats on image overlay"""
        selected_loot_item = self.loot_tree2.selection()
        if not selected_loot_item:
            return
        item_id = self.loot_tree2.item(selected_loot_item, "values")[0]
        self._display_item_details(item_id)
    def _display_item_details(self, item_id):
        """Render item stats and icon for the supplied item ID on the preview canvas."""
        if item_id in ("", None):
            return False
        try:
            item_id = int(item_id)
        except (TypeError, ValueError):
            return False
        for canvas_item in self.canvas.find_all():
            self.canvas.delete(canvas_item)
        if hasattr(self, 'bg_image') and self.bg_image:
            self.canvas.create_image(0, 0, anchor="nw", image=self.bg_image)
        query = """
            SELECT DISTINCT Name, aagi, ac, accuracy, acha, adex, aint, asta, astr, attack, augrestrict,
                   augtype, avoidance, awis, bagsize, bagslots, bagtype, bagwr, banedmgamt, banedmgraceamt,
                   banedmgbody, banedmgrace, classes, color, combateffects, extradmgskill, extradmgamt, cr, damage,
                   damageshield, deity, delay, dotshielding, dr, elemdmgtype, elemdmgamt, endur, fr, fvnodrop,
                   haste, hp, regen, icon, itemclass, itemtype, lore, loregroup, magic, mana, manaregen, enduranceregen, mr, nodrop, norent, pr, races,
                   `range`, reclevel, recskill, reqlevel, shielding, size, skillmodtype, skillmodvalue,
                   slots, clickeffect, spellshield, strikethrough, stunresist, weight, attuneable, svcorruption, skillmodmax,
                   heroic_str, heroic_int, heroic_wis, heroic_agi, heroic_dex,
                   heroic_sta, heroic_cha, heroic_pr, heroic_dr, heroic_fr,
                   heroic_cr, heroic_mr, heroic_svcorrup, healamt, spelldmg, clairvoyance, backstabdmg
            FROM items
            WHERE id = %s
        """
        try:
            self.cursor.execute(query, (item_id,))
            item_data = self.cursor.fetchone()
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to load item: {exc}")
            return False
        if not item_data:
            return False
        if isinstance(item_data, dict):
            item_stats = item_data
        else:
            columns = [
                "Name", "aagi", "ac", "accuracy", "acha", "adex", "aint", "asta", "astr", "attack", "augrestrict",
                "augtype", "avoidance", "awis", "bagsize", "bagslots", "bagtype", "bagwr", "banedmgamt", "banedmgraceamt",
                "banedmgbody", "banedmgrace", "classes", "color", "combateffects", "extradmgskill", "extradmgamt", "cr", "damage",
                "damageshield", "deity", "delay", "dotshielding", "dr", "elemdmgtype", "elemdmgamt", "endur", "fr", "fvnodrop",
                "haste", "hp", "regen", "icon", "itemclass", "itemtype", "lore", "loregroup", "magic", "mana", "manaregen", "enduranceregen", "mr", "nodrop", "norent", "pr", "races",
                "range", "reclevel", "recskill", "reqlevel", "shielding", "size", "skillmodtype", "skillmodvalue",
                "slots", "clickeffect", "spellshield", "strikethrough", "stunresist", "weight", "attuneable", "svcorruption", "skillmodmax",
                "heroic_str", "heroic_int", "heroic_wis", "heroic_agi", "heroic_dex",
                "heroic_sta", "heroic_cha", "heroic_pr", "heroic_dr", "heroic_fr",
                "heroic_cr", "heroic_mr", "heroic_svcorrup", "healamt", "spelldmg", "clairvoyance", "backstabdmg"
            ]
            item_stats = dict(zip(columns, item_data))
        classes_bitmask = item_stats.get("classes")
        if classes_bitmask is not None:
            if classes_bitmask == 65535:
                item_stats["classes"] = "ALL"
            else:
                class_names = []
                for bit_value, class_name in self.class_bitmask_display.items():
                    if bit_value != 65535 and classes_bitmask & bit_value:
                        class_names.append(class_name)
                item_stats["classes"] = ", ".join(class_names)
        races_bitmask = item_stats.get("races")
        if races_bitmask is not None:
            if races_bitmask == 65535:
                item_stats["races"] = "ALL"
            else:
                race_names = []
                for bit_value, race_name in self.race_bitmask_display.items():
                    if bit_value != 65535 and races_bitmask & bit_value:
                        race_names.append(race_name)
                item_stats["races"] = ", ".join(race_names)
        slots_bitmask = item_stats.get("slots")
        if slots_bitmask is not None:
            slot_names = []
            for bit_value, slot_name in SLOT_BITMASK_DISPLAY.items():
                if slots_bitmask & bit_value and slot_name not in slot_names:
                    slot_names.append(slot_name)
            item_stats["slots"] = ", ".join(slot_names)
        icon_id = item_stats.get("icon")
        if icon_id:
            try:
                icon_path = f"images/icons/item_{icon_id}.gif"
                item_icon = Image.open(icon_path)
                item_photo = ImageTk.PhotoImage(item_icon)
                self.canvas.item_photo = item_photo
                self.canvas.create_image(28, 57, image=item_photo)
            except Exception as icon_exc:
                print(f"Could not load icon: {icon_exc}")
        if not self.notes_db:
            display_text = f"{item_stats.get('Name')} (ID: {item_id})"
            self.canvas.create_text(5, 5, text=display_text, fill="white", anchor="nw", font=("Arial", 10, "bold"))
        config = ITEM_STAT_DISPLAY_CONFIG
        for stat_name, pos_config in config["header_positions"].items():
            if stat_name in item_stats and item_stats[stat_name] not in (None, ""):
                value = item_stats[stat_name]
                if pos_config.get("label") is None:
                    stat_text = f"{value}"
                else:
                    stat_text = f"{pos_config['label']}: {value}"
                self.canvas.create_text(
                    pos_config["x"],
                    pos_config["y"],
                    text=stat_text,
                    fill=pos_config["color"],
                    anchor="nw",
                    font=pos_config["font"]
                )
        property_config = config["property_row"]
        items_placed = 0
        for prop_name, prop_config in property_config["properties"].items():
            if prop_name in item_stats and item_stats[prop_name] is not None:
                value = item_stats[prop_name]
                if "format" in prop_config:
                    formatted_value = prop_config["format"](value)
                    if not formatted_value:
                        continue
                    value = formatted_value
                elif value == "":
                    continue
                current_x = property_config["base_x"] + (items_placed * property_config["spacing"])
                self.canvas.create_text(
                    current_x,
                    property_config["y"],
                    text=str(value),
                    fill=prop_config["color"],
                    anchor="nw",
                    font=prop_config["font"]
                )
                items_placed += 1
        def display_column_stats(column_config, stats):
            x = column_config["x"]
            y = column_config["y"]
            spacing = column_config["spacing"]
            for stat in column_config["stats"]:
                stat_name = stat["name"]
                stat_label = stat["label"]
                stat_color = stat["color"]
                if stat_name in stats and stats[stat_name] != 0:
                    value = stats[stat_name]
                    stat_text = f"{stat_label}: {value}"
                    self.canvas.create_text(
                        x,
                        y,
                        text=stat_text,
                        fill=stat_color,
                        anchor="nw",
                        font=("Arial", 8)
                    )
                    if "heroic_stats" in column_config:
                        for heroic_stat in column_config["heroic_stats"]:
                            if heroic_stat["label"] == stat_label:
                                heroic_stat_name = heroic_stat["name"]
                                if heroic_stat_name in stats and stats[heroic_stat_name] != 0:
                                    heroic_value = stats[heroic_stat_name]
                                    heroic_text = f" ({heroic_value})"
                                    try:
                                        bbox = self.canvas.bbox(self.canvas.find_all()[-1])
                                        heroic_x = bbox[2] if bbox else x + 50
                                    except Exception:
                                        heroic_x = x + 50
                                    self.canvas.create_text(
                                        heroic_x,
                                        y,
                                        text=heroic_text,
                                        fill="gold",
                                        anchor="nw",
                                        font=("Arial", 9)
                                    )
                    y += spacing
        for column in config["stat_columns"]:
            display_column_stats(column, item_stats)
        return True
    def on_lootdrop_edit(self, event):
        """Handle loot drop editing"""
        tree = event.widget
        region = tree.identify_region(event.x, event.y)
        if region != "cell":
            return
        column = tree.identify_column(event.x)
        item = tree.identify_row(event.y)
        if not item or not column:
            return
        # Get column index (1-based to 0-based)
        column_index = int(column[1:]) - 1
        # Get current values
        item_values = list(tree.item(item, "values"))
        current_value = item_values[column_index]
        # Get cell bbox relative to tree
        bbox = tree.bbox(item, column)
        if not bbox:
            return
        # Create entry widget
        entry = tk.Entry(tree)
        entry.insert(0, current_value)
        entry.select_range(0, tk.END)
        # Position entry widget
        entry.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])
        entry.focus_set()
        def save_edit(event=None):
            new_value = entry.get()
            # Get item ID and current loot drop ID
            item_id = item_values[0]
            if hasattr(self, 'current_lootdrop_id'):
                try:
                    # Map column index to database field (simplified)
                    field_map = {
                        2: "item_charges",  # Charges
                        3: "equip_item",    # Equip (needs conversion)
                        4: "chance",        # Chance
                        5: "trivial_min_level",
                        6: "trivial_max_level",
                        7: "multiplier",
                        8: "npc_min_level",
                        9: "npc_max_level",
                        10: "min_expansion",
                        11: "max_expansion"
                    }
                    if column_index in field_map:
                        field_name = field_map[column_index]
                        # Convert "Yes"/"No" to 1/0 for equip_item
                        if field_name == "equip_item":
                            new_value = 1 if new_value.lower() in ["yes", "1", "true"] else 0
                        # Update database
                        update_query = f"UPDATE lootdrop_entries SET {field_name} = %s WHERE lootdrop_id = %s AND item_id = %s"
                        self.db_manager.execute_update(update_query, (new_value, self.current_lootdrop_id, item_id))
                        # Update treeview
                        item_values[column_index] = new_value
                        tree.item(item, values=item_values)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to update loot drop entry: {e}")
            entry.destroy()
        def cancel_edit(event=None):
            entry.destroy()
        entry.bind("<Return>", save_edit)
        entry.bind("<Escape>", cancel_edit)
        entry.bind("<FocusOut>", save_edit)
    def on_npc_select(self, event):
        """Handle NPC selection"""
        selected_item = self.npc_tree.selection()
        if not selected_item:
            return
        npc_data = self.npc_tree.item(selected_item, "values")
        print(f"DEBUG: NPC data has {len(npc_data)} columns: {npc_data[:5]}...")  # Debug info
        if len(npc_data) < 13:
            print(f"ERROR: Expected at least 13 columns, got {len(npc_data)}")
            return
        # Attempt to update background image based on NPC race (and gender if available)
        try:
            race_id = int(npc_data[3]) if npc_data[3] != '' else None
        except Exception:
            race_id = None
        try:
            gender_val = int(npc_data[8]) if len(npc_data) > 8 and npc_data[8] != '' else None
        except Exception:
            gender_val = None
        if race_id is not None:
            self._set_background_image_for_race(race_id, gender_val)
        loottable_id = npc_data[12]  # Loot Table ID column (0-indexed: id, name, level, race, class, bodytype, hp, mana, gender, texture, helmtexture, size, loottable_id)
        if loottable_id and loottable_id != "0":
            # Clear existing trees
            for item in self.loot_tree.get_children():
                self.loot_tree.delete(item)
            for item in self.loot_tree2.get_children():
                self.loot_tree2.delete(item)
            self.load_loottable_data(int(loottable_id))
    def on_npc_edit(self, event):
        """Handle NPC editing"""
        tree = event.widget
        region = tree.identify_region(event.x, event.y)
        if region != "cell":
            return

        column = tree.identify_column(event.x)
        item = tree.identify_row(event.y)
        if not item or not column:
            return

        column_index = int(column[1:]) - 1
        column_name = tree["columns"][column_index]

        item_values = list(tree.item(item, "values"))
        current_value = item_values[column_index]

        bbox = tree.bbox(item, column)
        if not bbox:
            return

        entry = tk.Entry(tree)
        entry.insert(0, current_value)
        entry.select_range(0, tk.END)
        entry.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])
        entry.focus_set()

        def save_edit(event=None):
            new_value = entry.get()

            if column_name == "ID":
                entry.destroy()
                return

            npc_id = item_values[0]

            numeric_fields = {
                "Lvl",
                "Race",
                "Class",
                "HP",
                "Mana",
                "  Loot\nTable ID",
            }

            try:
                if column_name in numeric_fields:
                    new_value = int(new_value)
            except ValueError:
                messagebox.showerror("Error", f"{column_name} must be numeric")
                entry.destroy()
                return

            field_map = {
                "Name": "name",
                "Lvl": "level",
                "Race": "race",
                "Class": "class",
                "HP": "hp",
                "Mana": "mana",
                "  Loot\nTable ID": "loottable_id",
            }

            field_name = field_map.get(column_name)
            if not field_name:
                entry.destroy()
                return

            update_query = f"UPDATE npc_types SET {field_name} = %s WHERE id = %s"

            try:
                self.db_manager.execute_update(update_query, (new_value, npc_id))
                item_values[column_index] = new_value
                tree.item(item, values=item_values)
            except Exception as exc:
                messagebox.showerror("Error", f"Failed to update NPC: {exc}")
            finally:
                entry.destroy()

        def cancel_edit(event=None):
            entry.destroy()

        entry.bind("<Return>", save_edit)
        entry.bind("<Escape>", cancel_edit)
        entry.bind("<FocusOut>", save_edit)
    def setup_treeview_sorting(self, tree):
        """Setup treeview column sorting"""
        def sort_treeview(col, reverse=False):
            columns = tree["columns"]
            col_index = columns.index(col)
            def convert_value(value):
                try:
                    return float(value)
                except ValueError:
                    return str(value).lower()
            items = [(tuple(convert_value(tree.set(item, column)) for column in columns), item)
                     for item in tree.get_children("")]
            items.sort(key=lambda x: x[0][col_index], reverse=reverse)
            for index, (_, item) in enumerate(items):
                tree.move(item, "", index)
            tree.heading(col, command=lambda: sort_treeview(col, not reverse))
        for col in tree["columns"]:
            tree.heading(col, text=col, command=lambda c=col: sort_treeview(c))
    def _set_background_image_for_race(self, race_id, gender=None):
        """Update the MAIN background (default.jpg) based on race; do NOT touch item viewer."""
        try:
            pattern = os.path.join("images", "raceimages", f"{race_id}_*.jpg")
            candidates = sorted(glob.glob(pattern))
            def score(path):
                base = os.path.basename(path)
                parts = base.split("_")
                s = 0
                if len(parts) >= 2 and parts[1] == '2':
                    s += 10
                if gender is not None and len(parts) >= 2 and parts[1].isdigit() and int(parts[1]) == gender:
                    s += 5
                return -s
            if candidates:
                candidates.sort(key=score)
                chosen = candidates[0]
                img = Image.open(chosen)
                self.bg2_image = ImageTk.PhotoImage(img)
                if hasattr(self, 'main_canvas') and self.main_canvas:
                    try:
                        self.main_canvas.configure(width=self.bg2_image.width(), height=self.bg2_image.height())
                    except Exception:
                        pass
                    for item in self.main_canvas.find_all():
                        self.main_canvas.delete(item)
                    self.main_canvas.create_image(0, 0, anchor="nw", image=self.bg2_image)
        except Exception as e:
            print(f"Warning: could not set race background: {e}")
    def _enable_tree_mousewheel(self, tree):
        """Enable mousewheel scrolling on a Treeview without showing scrollbars."""
        def _on_mousewheel(event):
            try:
                delta = int(-1 * (event.delta / 120))
                tree.yview_scroll(delta, "units")
            except Exception:
                pass
            return "break"
        def _on_linux_scroll_up(event):
            tree.yview_scroll(-1, "units")
            return "break"
        def _on_linux_scroll_down(event):
            tree.yview_scroll(1, "units")
            return "break"
        try:
            tree.bind("<MouseWheel>", _on_mousewheel, add=True)
            tree.bind("<Button-4>", _on_linux_scroll_up, add=True)
            tree.bind("<Button-5>", _on_linux_scroll_down, add=True)
        except Exception:
            pass

