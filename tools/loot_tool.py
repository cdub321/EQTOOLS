import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sys
import os
from PIL import Image, ImageTk

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
        
        # Configure grid for two columns: loot table and loot drop
        self.middle_root_frame.grid_columnconfigure(0, weight=1)
        self.middle_root_frame.grid_columnconfigure(1, weight=1)
        
        self.create_loottable_section()
        self.create_lootdrop_section()
    
    def create_loottable_section(self):
        """Create loot table management section"""
        # Loot table frame
        loottable_frame = ttk.Frame(self.middle_root_frame)
        loottable_frame.grid(row=0, column=0, padx=5, sticky="nsew")
        
        # Loot table modification frame
        loottable_mod_frame = ttk.Frame(loottable_frame, relief=tk.SUNKEN, borderwidth=2)
        loottable_mod_frame.grid(row=0, column=0, sticky="ew", pady=5)
        
        # Loot table ID variable
        self.loot_id_var = tk.StringVar(value="Loot Table ID: ")
        ttk.Label(loottable_mod_frame, textvariable=self.loot_id_var, font=("Arial", 12, "bold")).grid(row=0, sticky="w", columnspan=2)
        
        # Loot table entries
        ttk.Label(loottable_mod_frame, text="Loot Table Name:").grid(row=1, column=0, sticky="w")
        self.loottable_name_entry = ttk.Entry(loottable_mod_frame, width=20)
        self.loottable_name_entry.grid(row=1, column=1, padx=5)
        
        ttk.Label(loottable_mod_frame, text="Avg Coin:").grid(row=1, column=2, sticky="w")
        self.avgcoin_entry = ttk.Entry(loottable_mod_frame, width=8)
        self.avgcoin_entry.grid(row=1, column=3, padx=5, pady=3, sticky="w")
        
        ttk.Label(loottable_mod_frame, text="Min Cash:").grid(row=2, column=0, sticky="w")
        self.mincash_entry = ttk.Entry(loottable_mod_frame, width=5)
        self.mincash_entry.grid(row=2, column=1, padx=5, sticky="w")
        
        ttk.Label(loottable_mod_frame, text="Max Cash:").grid(row=2, column=2, sticky="w")
        self.maxcash_entry = ttk.Entry(loottable_mod_frame, width=8)
        self.maxcash_entry.grid(row=2, column=3, padx=5, pady=3, sticky="w")
        
        ttk.Label(loottable_mod_frame, text="Min Xpac:").grid(row=3, column=0, sticky="w")
        self.minexpac_entry = ttk.Entry(loottable_mod_frame, width=5)
        self.minexpac_entry.grid(row=3, column=1, padx=5, sticky="w")
        
        ttk.Label(loottable_mod_frame, text="Max Xpac:").grid(row=3, column=2, sticky="w")
        self.maxexpac_entry = ttk.Entry(loottable_mod_frame, width=5)
        self.maxexpac_entry.grid(row=3, column=3, padx=5, pady=3, sticky="w")
        
        ttk.Label(loottable_mod_frame, text="Update Changes").grid(row=1, column=4, padx=17, sticky="nsew")
        ttk.Button(loottable_mod_frame, text="Update", command=self.update_loottable).grid(row=2, column=4, padx=25, pady=3, sticky="n", rowspan=2)
        
        # Loot table modification buttons frame
        loottable_mod_frame2 = ttk.Frame(loottable_frame, relief=tk.SUNKEN, borderwidth=2)
        loottable_mod_frame2.grid(row=1, column=0, sticky="ew", pady=5)
        
        ttk.Button(loottable_mod_frame2, text="Create Lootdrop & Add", command=self.add_new_lootdrop).grid(row=0, column=0, padx=3)
        ttk.Button(loottable_mod_frame2, text="Remove Selected Lootdrop", command=self.remove_selected_lootdrop).grid(row=0, column=2, padx=3)
        ttk.Button(loottable_mod_frame2, text="Add Existing Lootdrop ID:", command=self.add_existing_lootdrop_to_loottable).grid(row=0, column=3, pady=5, padx=3)
        
        self.lootdrop_id_entry = ttk.Entry(loottable_mod_frame2, width=10)
        self.lootdrop_id_entry.grid(row=0, column=4, pady=5, padx=2)
        
        # Loot table tree
        loottable_tree_frame = ttk.Frame(loottable_frame, relief=tk.SUNKEN, borderwidth=2)
        loottable_tree_frame.grid(row=2, column=0, sticky="nsew", pady=5)
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
        self.loot_tree.column("LootDrop Name", width=160, stretch=False)
        self.loot_tree.column("Multiplier", width=65, stretch=False)
        self.loot_tree.column("MinDrop", width=65, stretch=False)
        self.loot_tree.column("DropLimit", width=65, stretch=False)
        self.loot_tree.column("Probability", width=69, stretch=False)
        
        self.loot_tree.grid(row=1, column=0, sticky="nsew")
        
        # Bind events
        self.loot_tree.bind("<<TreeviewSelect>>", self.on_lootdrop_select)
        self.loot_tree.bind("<Double-1>", self.on_loottable_edit)
        self.setup_treeview_sorting(self.loot_tree)
    
    def create_lootdrop_section(self):
        """Create loot drop management section"""
        # Loot drop frame
        lootdrop_frame = ttk.Frame(self.middle_root_frame)
        lootdrop_frame.grid(row=0, column=1, sticky="nsew", padx=5)
        
        # Loot drop tree frame
        loot_tree2_frame = ttk.Frame(lootdrop_frame, relief=tk.SUNKEN, borderwidth=2)
        loot_tree2_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5, columnspan=2)
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
        
        # Set specific column widths
        self.loot_tree2.column("Item ID", width=55, stretch=False)
        self.loot_tree2.column("Item Name", width=150, stretch=False)
        self.loot_tree2.column("Charges", width=50, stretch=False)
        self.loot_tree2.column("Equip", width=50, stretch=False)
        self.loot_tree2.column("Chance", width=50, stretch=False)
        self.loot_tree2.column("  Triv \nMinLvl", width=55, stretch=False)
        self.loot_tree2.column("  Triv \nMaxLvl", width=55, stretch=False)
        self.loot_tree2.column("Multiplier", width=60, stretch=False)
        self.loot_tree2.column(" NPC \nMinLvl", width=58, stretch=False)
        self.loot_tree2.column(" NPC \nMaxLvl", width=55, stretch=False)
        self.loot_tree2.column("Min\nXpac", width=55, stretch=False)
        self.loot_tree2.column("Max\nXpac", width=55, stretch=False)
        
        self.loot_tree2.grid(row=1, column=0, sticky="nsew", columnspan=2)
        
        # Loot drop modification frame
        lootdrop_mod_frame = ttk.Frame(lootdrop_frame, relief=tk.SUNKEN, borderwidth=2)
        lootdrop_mod_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        ttk.Button(lootdrop_mod_frame, text="Remove Selected Item from Lootdrop", command=self.remove_item_from_lootdrop).grid(row=0, column=1, pady=5, columnspan=2, padx=10)
        ttk.Button(lootdrop_mod_frame, text="Add Random Item ID to selected Lootdrop", command=self.add_item_to_lootdrop).grid(row=0, column=0, pady=5, padx=5)
        ttk.Button(lootdrop_mod_frame, text="Lookup Item by ID", command=self.lookup_item_by_id).grid(row=0, column=3, pady=5, padx=3)
        
        ttk.Label(lootdrop_mod_frame, text="------------> Item ID:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.item_id_entry = ttk.Entry(lootdrop_mod_frame)
        self.item_id_entry.grid(row=1, column=1, padx=2, pady=5, sticky="w")
        
        ttk.Button(lootdrop_mod_frame, text="Add Specific Item", command=self.add_specific_item_to_lootdrop).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ttk.Button(lootdrop_mod_frame, text="Notes", command=self.open_notes_window).grid(row=1, column=2, pady=5)
        
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
            "ID": 50, "Name": 150, "Lvl": 25, "Race": 35, "Class": 39, "Body": 36, "HP": 25, "Mana": 35,
            "Gender": 45, "Texture": 45, "Helm\nTexture": 40, "Size": 45, "  Loot\nTable ID": 50, "Spells\n  ID": 50, 
            "Faction\n   ID": 45, "Min\ndmg": 40, "Max\ndmg": 40, "Npcspecial\n  attks": 55, "Special\nAbilities": 50,
            "MR": 35, "CR": 35, "DR": 35, "FR": 35, "PR": 35, "AC": 35, "Attk Delay": 50,
            "STR": 35, "STA": 35, "DEX": 35, "AGI": 35, "_INT": 35, "WIS": 35, "Maxlevel": 45,
            "Skip Global Loot": 60, "Exp Mod": 45
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
        # Simplified query to find next available ID
        unused_loottable_query = """
            SELECT (COALESCE(MAX(id), 0) + 1) as next_id, 
                   (COALESCE(MAX(id), 0) + 2) as next_id2,
                   (COALESCE(MAX(id), 0) + 3) as next_id3
            FROM loottable 
            LIMIT 1
        """
        # Simplified query to find next available ID
        unused_lootdrop_query = """
            SELECT (COALESCE(MAX(id), 0) + 1) as next_id,
                   (COALESCE(MAX(id), 0) + 2) as next_id2,
                   (COALESCE(MAX(id), 0) + 3) as next_id3
            FROM lootdrop 
            LIMIT 1
        """
        
        try:
            unused_loottable_result = self.db_manager.execute_query(unused_loottable_query, fetch_all=False)
            if unused_loottable_result:
                if isinstance(unused_loottable_result, dict):
                    unused_loottable_ids = [
                        str(unused_loottable_result.get("next_id", 1)),
                        str(unused_loottable_result.get("next_id2", 2)),
                        str(unused_loottable_result.get("next_id3", 3)),
                    ]
                else:
                    unused_loottable_ids = [
                        str(unused_loottable_result[0]),
                        str(unused_loottable_result[1]),
                        str(unused_loottable_result[2]),
                    ]
            else:
                unused_loottable_ids = ["1", "2", "3"]
            
            unused_lootdrop_result = self.db_manager.execute_query(unused_lootdrop_query, fetch_all=False)
            if unused_lootdrop_result:
                if isinstance(unused_lootdrop_result, dict):
                    unused_lootdrop_ids = [
                        str(unused_lootdrop_result.get("next_id", 1)),
                        str(unused_lootdrop_result.get("next_id2", 2)),
                        str(unused_lootdrop_result.get("next_id3", 3)),
                    ]
                else:
                    unused_lootdrop_ids = [
                        str(unused_lootdrop_result[0]),
                        str(unused_lootdrop_result[1]),
                        str(unused_lootdrop_result[2]),
                    ]
            else:
                unused_lootdrop_ids = ["1", "2", "3"]
        except Exception as e:
            print(f"Could not query unused IDs: {e}")
            unused_loottable_ids = ["1", "2", "3"]
            unused_lootdrop_ids = ["1", "2", "3"]
        
        max_display_ids = 9
        if len(unused_loottable_ids) > max_display_ids:
            unused_loottable_ids = unused_loottable_ids[:max_display_ids] + ["..."]
        if len(unused_lootdrop_ids) > max_display_ids:
            unused_lootdrop_ids = unused_lootdrop_ids[:max_display_ids] + ["..."]
        
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
        """Add loot drop to loot table"""
        pass
    
    def view_all_loottables(self):
        """View all loot tables"""
        pass
    
    def update_loottable(self):
        """Update loot table information"""
        pass
    
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
            INSERT INTO lootdrop_entries (lootdrop_id, item_id, item_charges, equip_item, chance, disabled, trivial_min_level, trivial_max_level, multiplier, npc_min_level, npc_max_level, min_expansion, max_expansion)
            VALUES (%s, %s, 1, 1, 100, 0, 0, 0, 1, 0, 0, -1, -1)
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
        # Similar to NPC editing but for loot table entries
        tree = event.widget
        region = tree.identify_region(event.x, event.y)
        if region != "cell":
            return
            
        selected_item = tree.selection()
        if not selected_item:
            return
        
        # Get the selected loot drop for editing
        lootdrop_id = tree.item(selected_item, "values")[0]
        
        # For now, just select the loot drop to show its contents
        self.on_lootdrop_select(event)
    
    def remove_item_from_lootdrop(self):
        """Remove item from loot drop"""
        pass
    
    def add_item_to_lootdrop(self):
        """Add item to loot drop"""
        pass
    
    def lookup_item_by_id(self):
        """Lookup item by ID"""
        pass
    
    def add_specific_item_to_lootdrop(self):
        """Add specific item to loot drop"""
        pass
    
    def open_notes_window(self):
        """Open notes management window"""
        pass
    
    def on_item_select(self, event):
        """CRITICAL: Handle item selection and display stats on image overlay"""
        selected_loot_item = self.loot_tree2.selection()
        if not selected_loot_item:
            return
       
        item_id = self.loot_tree2.item(selected_loot_item, "values")[0]
       
        for item in self.canvas.find_all():  # Clear previous item image and stats
            self.canvas.delete(item) 
        
        if hasattr(self, 'bg_image') and self.bg_image:
            self.canvas.create_image(0, 0, anchor="nw", image=self.bg_image)  # Redraw the background image
       
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
        self.cursor.execute(query, (item_id,))
        item_data = self.cursor.fetchone()
        
        if item_data:
            # Since cursor is returning a dictionary, use it directly instead of creating a new dict
            if isinstance(item_data, dict):
                item_stats = item_data
            else:
                # Fallback for tuple results
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
            
            # Handle icon - display item image
            icon_id = item_stats.get("icon")
            if icon_id:
                try:
                    # Load icon image based on icon_id
                    icon_path = f"images/icons/item_{icon_id}.gif"  # Adjust path format as needed
                    item_icon = Image.open(icon_path)
                    item_photo = ImageTk.PhotoImage(item_icon)
                    
                    # Save reference to prevent garbage collection
                    self.canvas.item_photo = item_photo  
                    
                    # Display icon at specific pixel location
                    self.canvas.create_image(28, 57, image=item_photo)
                except Exception as e:
                    print(f"Could not load icon: {e}")
            
            # Handle classes bitmask using centralized dictionary
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
            
            # Handle races bitmask using centralized dictionary
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
    
            # Handle item slots bitmask using centralized dictionary
            slots_bitmask = item_stats.get("slots")  
            if slots_bitmask is not None:
                slot_names = []
                for bit_value, slot_name in SLOT_BITMASK_DISPLAY.items():
                    if slots_bitmask & bit_value:
                        if slot_name not in slot_names:
                            slot_names.append(slot_name)
                item_stats["slots"] = ", ".join(slot_names)
            
            # Use the centralized display configuration
            config = ITEM_STAT_DISPLAY_CONFIG
            
            # Display header information
            for stat_name, pos_config in config["header_positions"].items():
                if stat_name in item_stats and item_stats[stat_name] is not None:
                    value = item_stats[stat_name]
                    if value == "":
                        continue
                    
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
    
            # Display special property row
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
    
                    self.canvas.create_text(current_x, property_config["y"], text=value, 
                                          fill=prop_config["color"], anchor="nw", font=prop_config["font"])
    
                    items_placed += 1
            
            # Display stat columns
            def display_column_stats(column_config, item_stats):
                x = column_config["x"]
                y = column_config["y"]
                spacing = column_config["spacing"]
                
                for stat in column_config["stats"]:
                    stat_name = stat["name"]
                    stat_label = stat["label"]
                    stat_color = stat["color"]
                    
                    if stat_name in item_stats and item_stats[stat_name] != 0:
                        value = item_stats[stat_name]
                        stat_text = f"{stat_label}: {value}"
                        
                        self.canvas.create_text(
                            x, y, 
                            text=stat_text, 
                            fill=stat_color, 
                            anchor="nw", 
                            font=("Arial", 8)
                        )
                        
                        if "heroic_stats" in column_config:
                            for heroic_stat in column_config["heroic_stats"]:
                                if heroic_stat["label"] == stat_label:
                                    heroic_stat_name = heroic_stat["name"]
                                    if heroic_stat_name in item_stats and item_stats[heroic_stat_name] != 0:
                                        heroic_value = item_stats[heroic_stat_name]
                                        heroic_text = f" ({heroic_value})"
                                        
                                        try:
                                            bbox = self.canvas.bbox(self.canvas.find_all()[-1])
                                            if bbox:
                                                heroic_x = bbox[2]
                                            else:
                                                heroic_x = x + 50
                                        except:
                                            heroic_x = x + 50
                                        
                                        self.canvas.create_text(
                                            heroic_x, y, 
                                            text=heroic_text, 
                                            fill="gold", 
                                            anchor="nw", 
                                            font=("Arial", 9)
                                        )
    
                        y += spacing
            
            for column in config["stat_columns"]:
                display_column_stats(column, item_stats)
    
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
                        
                        messagebox.showinfo("Success", f"Updated loot drop entry")
                    
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
        
        # Get column index (1-based to 0-based)
        column_index = int(column[1:]) - 1
        
        # Get the column name from the treeview
        column_name = tree["columns"][column_index]
        
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
            
            # Get the NPC ID from the first column
            npc_id = item_values[0]
            
            try:
                # Map column names to database fields (simplified mapping)
                column_to_field = {
                    "ID": "id", "Name": "name", "Lvl": "level", "Race": "race",
                    "Class": "class", "HP": "hp", "Mana": "mana", "  Loot\nTable ID": "loottable_id"
                }
                
                if column_name in column_to_field:
                    field_name = column_to_field[column_name]
                    
                    # Update database
                    update_query = f"UPDATE npc_types SET {field_name} = %s WHERE id = %s"
                    self.db_manager.execute_update(update_query, (new_value, npc_id))
                    
                    # Update treeview
                    item_values[column_index] = new_value
                    tree.item(item, values=item_values)
                    
                    messagebox.showinfo("Success", f"Updated {column_name} for NPC {npc_id}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update NPC: {e}")
            
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
