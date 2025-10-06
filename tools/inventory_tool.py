import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
from PIL import Image, ImageTk

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.theme import set_dark_theme
from dictionaries import (CLASS_BITMASK_DISPLAY, RACE_BITMASK_DISPLAY, SLOT_BITMASK_DISPLAY, 
                         ITEM_STAT_DISPLAY_CONFIG)

# ID to name mappings for display
CLASS_ID_TO_NAME = {
    1: "Warrior", 2: "Cleric", 3: "Paladin", 4: "Ranger", 5: "Shadow Knight",
    6: "Druid", 7: "Monk", 8: "Bard", 9: "Rogue", 10: "Shaman",
    11: "Necromancer", 12: "Wizard", 13: "Magician", 14: "Enchanter",
    15: "Beastlord", 16: "Berserker"
}

RACE_ID_TO_NAME = {
    1: "Human", 2: "Barbarian", 3: "Erudite", 4: "Wood Elf", 5: "High Elf",
    6: "Dark Elf", 7: "Half Elf", 8: "Dwarf", 9: "Troll", 10: "Ogre",
    11: "Halfling", 12: "Gnome", 128: "Iksar", 130: "Vah Shir", 330: "Froglok"
}

# Slot ID to name mapping for inventory display
SLOT_ID_TO_NAME = {
    0: "Charm", 1: "Left Ear", 2: "Head", 3: "Face", 4: "Right Ear",
    5: "Neck", 6: "Shoulders", 7: "Arms", 8: "Back", 9: "Left Wrist",
    10: "Right Wrist", 11: "Range", 12: "Hands", 13: "Primary Hand",
    14: "Secondary Hand", 15: "Left Ring", 16: "Right Ring", 17: "Chest",
    18: "Legs", 19: "Feet", 20: "Waist", 21: "Powersource", 9999: "Cursor"
}

class InventoryManagerTool:
    """Inventory Manager Tool - modular version for tabbed interface"""
    
    def __init__(self, parent_frame, db_manager):
        self.parent = parent_frame
        self.db_manager = db_manager
        self.conn = db_manager.connect()
        self.cursor = db_manager.get_cursor()
        
        # Sorting variables
        self.sort_column = None
        self.sort_reverse = False
        
        # Configure parent frame grid
        self.parent.grid_rowconfigure(0, weight=1)
        self.parent.grid_columnconfigure(0, weight=1)
        
        # Create main container frame
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Initialize UI components
        self.create_ui()
        
        # Load initial data
        self.load_players()
    
    def create_ui(self):
        """Create the complete Inventory Manager UI"""
        # Configure main frame grid
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=2)
        self.main_frame.grid_columnconfigure(2, weight=1)
        
        # Create three panels
        self.left_panel = ttk.Frame(self.main_frame, width=300)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.left_panel.grid_rowconfigure(2, weight=1)
        self.left_panel.grid_columnconfigure(0, weight=1)

        self.middle_panel = ttk.Frame(self.main_frame, width=500)
        self.middle_panel.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.middle_panel.grid_rowconfigure(1, weight=1)
        self.middle_panel.grid_columnconfigure(0, weight=1)

        self.right_panel = ttk.Frame(self.main_frame, width=400)
        self.right_panel.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)
        self.right_panel.grid_rowconfigure(1, weight=1)
        self.right_panel.grid_columnconfigure(0, weight=1)
        
        # Create three panels
        self.create_left_panel()
        self.create_middle_panel()
        self.create_right_panel()
    
    def create_left_panel(self):
        # Left Panel - Player List
        left_label = ttk.Label(self.left_panel, text="Players", font=("Arial", 12, "bold"))
        left_label.grid(row=0, column=0, pady=5)
        
        # Search frame for players
        search_frame = ttk.Frame(self.left_panel)
        search_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        search_frame.grid_columnconfigure(1, weight=1)

        search_label = ttk.Label(search_frame, text="Search:")
        search_label.grid(row=0, column=0, padx=5)

        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.grid(row=0, column=1, sticky="ew", padx=5)

        warning_label = ttk.Label(search_frame, text="Edit values at your own risk (Use full class/race name)", foreground="red")
        warning_label.grid(row=0, column=2, padx=5)

        # Player list treeview
        player_columns = ["ID", "Name", "Level", "Class", "Race", "Zone", "Time\nPlayed", "AA\nSpent", "AA\nPoints", 
                         "Plat", "Gold", "Plat\nBank", "Gold\nBank", "Plat\nCursor", "Gold\nCursor", "Shared\nItems"]
        self.player_tree = ttk.Treeview(self.left_panel, columns=player_columns, show="headings", selectmode="browse")

        # Set column headings and widths
        column_widths = {
            "ID": 40,
            "Name": 85,
            "Level": 40,
            "Class": 45,
            "Race": 45,
            "Zone": 40,
            "Time\nPlayed": 55,
            "AA\nSpent": 50,
            "AA\nPoints": 50,
            "Plat": 40,
            "Gold": 40,
            "Plat\nBank": 40,
            "Gold\nBank": 40,
            "Plat\nCursor": 50,
            "Gold\nCursor": 50,
            "Shared\nItems": 60
        }
        
        for col in player_columns:
            self.player_tree.heading(col, text=col, command=lambda c=col: self.sort_treeview(c))
            self.player_tree.column(col, width=column_widths.get(col, 50))

        # Add player tree to grid
        self.player_tree.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
    
    def create_middle_panel(self):
        # Middle Panel - Inventory
        middle_label = ttk.Label(self.middle_panel, text="Inventory", font=("Arial", 12, "bold"))
        middle_label.grid(row=0, column=0, pady=5)
        
        # Create notebook for different inventory sections
        self.inventory_notebook = ttk.Notebook(self.middle_panel)
        self.inventory_notebook.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # Worn equipment tab
        worn_frame = ttk.Frame(self.inventory_notebook)
        self.inventory_notebook.add(worn_frame, text="Worn Equipment")
        worn_frame.grid_rowconfigure(0, weight=1)
        worn_frame.grid_columnconfigure(0, weight=1)

        # Worn equipment treeview
        worn_columns = ["Slot", "Item ID", "Item Name", "Charges"]
        self.worn_tree = ttk.Treeview(worn_frame, columns=worn_columns, show="headings", selectmode="browse")

        # Set column headings
        for col in worn_columns:
            self.worn_tree.heading(col, text=col)
            self.worn_tree.column(col, width=70)

        self.worn_tree.column("Item Name", width=200)

        # Add worn tree to grid
        self.worn_tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Bagged items tab
        bagged_frame = ttk.Frame(self.inventory_notebook)
        self.inventory_notebook.add(bagged_frame, text="Bagged Items")
        bagged_frame.grid_rowconfigure(0, weight=1)
        bagged_frame.grid_columnconfigure(0, weight=1)

        # Bagged items treeview
        bagged_columns = ["Slot", "Item ID", "Item Name", "Charges"]
        self.bagged_tree = ttk.Treeview(bagged_frame, columns=bagged_columns, show="headings", selectmode="browse")

        # Set column headings
        for col in bagged_columns:
            self.bagged_tree.heading(col, text=col)
            self.bagged_tree.column(col, width=70)

        self.bagged_tree.column("Item Name", width=200)

        # Add bagged tree to grid
        self.bagged_tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
    
    def create_right_panel(self):
        # Right Panel - Character Details
        right_label = ttk.Label(self.right_panel, text="Character Details", font=("Arial", 12, "bold"))
        right_label.grid(row=0, column=0, pady=5)

        # Create a frame to hold all character details
        char_details_container = ttk.Frame(self.right_panel)
        char_details_container.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        char_details_container.grid_rowconfigure(0, weight=1)
        char_details_container.grid_columnconfigure(0, weight=1)

        # Character info frame
        char_info_frame = ttk.LabelFrame(char_details_container, text="Basic Info")
        char_info_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        # Character info labels
        self.char_info_labels = {}
        char_info_fields = ["Name", "Level", "Class", "Race", "Deity", "Guild", "Last Login", "Time Played", 
                           "HP", "Mana", "Endurance", "STR", "STA", "CHA", "DEX", "INT", "AGI", "WIS"]

        for i, field in enumerate(char_info_fields):
            frame = ttk.Frame(char_info_frame)
            frame.grid(row=i, column=0, sticky="ew", padx=5, pady=2)
            frame.grid_columnconfigure(1, weight=1)
            
            label = ttk.Label(frame, text=f"{field}:", width=15, anchor="w")
            label.grid(row=0, column=0, sticky="w")
            
            value = ttk.Label(frame, text="", anchor="w")
            value.grid(row=0, column=1, sticky="ew")
            
            self.char_info_labels[field] = value

        # Item details frame - sophisticated item display like loot tool
        item_details_frame = ttk.LabelFrame(char_details_container, text="Item Details")
        item_details_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        # Canvas for item display with background image
        try:
            backingimage = Image.open("images/other/itemback.png")
            self.bg_image = ImageTk.PhotoImage(backingimage)
            
            self.canvas = tk.Canvas(item_details_frame, width=self.bg_image.width(), height=self.bg_image.height(), highlightthickness=0)
            self.canvas.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
            self.canvas.create_image(0, 0, anchor="nw", image=self.bg_image)
        except Exception as e:
            print(f"Could not load item background image: {e}")
            self.bg_image = None
            self.canvas = tk.Canvas(item_details_frame, width=400, height=350, highlightthickness=0, bg="#3c3c3c")
            self.canvas.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Character buffs frame
        buffs_frame = ttk.LabelFrame(char_details_container, text="Active Buffs")
        buffs_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        buffs_frame.grid_rowconfigure(0, weight=1)
        buffs_frame.grid_columnconfigure(0, weight=1)

        # Buffs treeview
        buffs_columns = ["Spell ID", "Spell Name"]
        self.buffs_tree = ttk.Treeview(buffs_frame, columns=buffs_columns, show="headings", selectmode="browse")

        # Set column headings
        for col in buffs_columns:
            self.buffs_tree.heading(col, text=col)
            self.buffs_tree.column(col, width=100)

        # Adjust column widths for better visibility
        self.buffs_tree.column("Spell ID", width=70)
        self.buffs_tree.column("Spell Name", width=200)

        # Add buffs tree to grid
        self.buffs_tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Add delete button
        delete_button = ttk.Button(self.middle_panel, text="Delete Selected Item", command=self.delete_selected_item)
        delete_button.grid(row=2, column=0, pady=5)
        
        # Bind events
        self.player_tree.bind("<<TreeviewSelect>>", self.load_inventory)
        self.player_tree.bind("<Double-1>", self.edit_cell)
        self.worn_tree.bind("<<TreeviewSelect>>", self.display_item_details)
        self.bagged_tree.bind("<<TreeviewSelect>>", self.display_item_details)
        self.search_var.trace("w", self.filter_players)
    
    def load_players(self):
        """Load players into the treeview"""
        # Clear existing items
        for item in self.player_tree.get_children():
            self.player_tree.delete(item)
        
        # Fetch players from character_data - exclude level 0, deleted chars, and empty inventories
        query = """
            SELECT DISTINCT cd.id, cd.name, cd.level, 
                   CASE cd.class
                       WHEN 1 THEN 'Warrior' WHEN 2 THEN 'Cleric' WHEN 3 THEN 'Paladin' WHEN 4 THEN 'Ranger' 
                       WHEN 5 THEN 'Shadow Knight' WHEN 6 THEN 'Druid' WHEN 7 THEN 'Monk' WHEN 8 THEN 'Bard' 
                       WHEN 9 THEN 'Rogue' WHEN 10 THEN 'Shaman' WHEN 11 THEN 'Necromancer' WHEN 12 THEN 'Wizard' 
                       WHEN 13 THEN 'Magician' WHEN 14 THEN 'Enchanter' WHEN 15 THEN 'Beastlord' WHEN 16 THEN 'Berserker'
                       ELSE CONCAT('Unknown (', cd.class, ')') END as class,
                   CASE cd.race
                       WHEN 1 THEN 'Human' WHEN 2 THEN 'Barbarian' WHEN 3 THEN 'Erudite' WHEN 4 THEN 'Wood Elf' 
                       WHEN 5 THEN 'High Elf' WHEN 6 THEN 'Dark Elf' WHEN 7 THEN 'Half Elf' WHEN 8 THEN 'Dwarf' 
                       WHEN 9 THEN 'Troll' WHEN 10 THEN 'Ogre' WHEN 11 THEN 'Halfling' WHEN 12 THEN 'Gnome' 
                       WHEN 128 THEN 'Iksar' WHEN 130 THEN 'Vah Shir' WHEN 330 THEN 'Froglok'
                       ELSE CONCAT('Unknown (', cd.race, ')') END as race,
                   cd.zone_id, cd.time_played, cd.aa_points_spent, cd.aa_points,
                   COALESCE(cc.platinum, 0) as platinum, COALESCE(cc.gold, 0) as gold,
                   COALESCE(cc.platinum_bank, 0) as platinum_bank, COALESCE(cc.gold_bank, 0) as gold_bank,
                   COALESCE(cc.platinum_cursor, 0) as platinum_cursor, COALESCE(cc.gold_cursor, 0) as gold_cursor,
                   COUNT(DISTINCT sb.item_id) as shared_items_count
            FROM character_data cd
            INNER JOIN inventory i ON cd.id = i.character_id
            LEFT JOIN character_currency cc ON cd.id = cc.id
            LEFT JOIN sharedbank sb ON cd.account_id = sb.account_id AND sb.item_id > 0
            WHERE cd.level > 0 
                AND cd.name NOT LIKE '%%-deleted%%'
                AND i.item_id > 0
            GROUP BY cd.id, cd.name, cd.level, cd.class, cd.race, cd.zone_id, cd.time_played, 
                     cd.aa_points_spent, cd.aa_points, cc.platinum, cc.gold, cc.platinum_bank, cc.gold_bank, cc.platinum_cursor, cc.gold_cursor
            ORDER BY cd.name
        """
        players = self.db_manager.execute_query(query)
        
        # Insert players into treeview
        for player in players:
            # Convert dictionary to tuple of values ordered by columns
            if isinstance(player, dict):
                # Extract values in the same order as the treeview columns
                player_values = [
                    player.get('id'), player.get('name'), player.get('level'), player.get('class'), player.get('race'),
                    player.get('zone_id'), player.get('time_played'), player.get('aa_points_spent'), player.get('aa_points'),
                    player.get('platinum'), player.get('gold'), player.get('platinum_bank'), player.get('gold_bank'),
                    player.get('platinum_cursor'), player.get('gold_cursor'),
                    player.get('shared_items_count', 0)
                ]
                self.player_tree.insert("", tk.END, values=player_values)
            else:
                self.player_tree.insert("", tk.END, values=player)
        
        # Update status (we'll add a status bar later if needed)
        print(f"Loaded {len(players)} players")
    
    def filter_players(self, *args):
        """Filter players based on search"""
        search_term = self.search_var.get().lower()
        
        # Clear existing items
        for item in self.player_tree.get_children():
            self.player_tree.delete(item)
        
        # Fetch players from character_data - exclude level 0, deleted chars, and empty inventories
        query = """
            SELECT DISTINCT cd.id, cd.name, cd.level, 
                   CASE cd.class
                       WHEN 1 THEN 'Warrior' WHEN 2 THEN 'Cleric' WHEN 3 THEN 'Paladin' WHEN 4 THEN 'Ranger' 
                       WHEN 5 THEN 'Shadow Knight' WHEN 6 THEN 'Druid' WHEN 7 THEN 'Monk' WHEN 8 THEN 'Bard' 
                       WHEN 9 THEN 'Rogue' WHEN 10 THEN 'Shaman' WHEN 11 THEN 'Necromancer' WHEN 12 THEN 'Wizard' 
                       WHEN 13 THEN 'Magician' WHEN 14 THEN 'Enchanter' WHEN 15 THEN 'Beastlord' WHEN 16 THEN 'Berserker'
                       ELSE CONCAT('Unknown (', cd.class, ')') END as class,
                   CASE cd.race
                       WHEN 1 THEN 'Human' WHEN 2 THEN 'Barbarian' WHEN 3 THEN 'Erudite' WHEN 4 THEN 'Wood Elf' 
                       WHEN 5 THEN 'High Elf' WHEN 6 THEN 'Dark Elf' WHEN 7 THEN 'Half Elf' WHEN 8 THEN 'Dwarf' 
                       WHEN 9 THEN 'Troll' WHEN 10 THEN 'Ogre' WHEN 11 THEN 'Halfling' WHEN 12 THEN 'Gnome' 
                       WHEN 128 THEN 'Iksar' WHEN 130 THEN 'Vah Shir' WHEN 330 THEN 'Froglok'
                       ELSE CONCAT('Unknown (', cd.race, ')') END as race,
                   cd.zone_id, cd.time_played, cd.aa_points_spent, cd.aa_points,
                   COALESCE(cc.platinum, 0) as platinum, COALESCE(cc.gold, 0) as gold,
                   COALESCE(cc.platinum_bank, 0) as platinum_bank, COALESCE(cc.gold_bank, 0) as gold_bank,
                   COALESCE(cc.platinum_cursor, 0) as platinum_cursor, COALESCE(cc.gold_cursor, 0) as gold_cursor,
                   COUNT(DISTINCT sb.item_id) as shared_items_count
            FROM character_data cd
            INNER JOIN inventory i ON cd.id = i.character_id
            LEFT JOIN character_currency cc ON cd.id = cc.id
            LEFT JOIN sharedbank sb ON cd.account_id = sb.account_id AND sb.item_id > 0
            WHERE cd.level > 0 
                AND cd.name NOT LIKE '%%-deleted%%'
                AND i.item_id > 0
                AND LOWER(cd.name) LIKE %s
            GROUP BY cd.id, cd.name, cd.level, cd.class, cd.race, cd.zone_id, cd.time_played, 
                     cd.aa_points_spent, cd.aa_points, cc.platinum, cc.gold, cc.platinum_bank, cc.gold_bank, cc.platinum_cursor, cc.gold_cursor
            ORDER BY cd.name
        """
        players = self.db_manager.execute_query(query, (f"%{search_term}%",))
        
        # Insert filtered players into treeview
        for player in players:
            # Convert dictionary to tuple of values ordered by columns
            if isinstance(player, dict):
                # Extract values in the same order as the treeview columns
                player_values = [
                    player.get('id'), player.get('name'), player.get('level'), player.get('class'), player.get('race'),
                    player.get('zone_id'), player.get('time_played'), player.get('aa_points_spent'), player.get('aa_points'),
                    player.get('platinum'), player.get('gold'), player.get('platinum_bank'), player.get('gold_bank'),
                    player.get('platinum_cursor'), player.get('gold_cursor'),
                    player.get('shared_items_count', 0)
                ]
                self.player_tree.insert("", tk.END, values=player_values)
            else:
                self.player_tree.insert("", tk.END, values=player)
        
        print(f"Found {len(players)} players matching '{search_term}'")
    
    def edit_cell(self, event):
        """Handle double-click to edit cell"""
        # Get the item and column that was clicked
        item = self.player_tree.selection()[0] if self.player_tree.selection() else None
        if not item:
            return
        
        # Get the column that was clicked
        column = self.player_tree.identify_column(event.x)
        if not column:
            return
        
        # Convert column index to column name
        col_index = int(column[1:]) - 1  # Column format is '#1', '#2', etc.
        if col_index >= len(self.player_tree['columns']):
            return
        
        col_name = self.player_tree['columns'][col_index]
        
        # Don't allow editing of certain columns
        readonly_columns = ["ID", "Shared\nItems"]  # ID is primary key, Shared Items is calculated
        if col_name in readonly_columns:
            return
        
        # Get current value
        current_value = self.player_tree.set(item, col_name)
        
        # Get the bounding box for the cell
        bbox = self.player_tree.bbox(item, col_name)
        if not bbox:
            return
        
        # Create entry widget for editing
        self.edit_entry = ttk.Entry(self.player_tree)
        self.edit_entry.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])
        self.edit_entry.insert(0, current_value)
        self.edit_entry.select_range(0, tk.END)
        self.edit_entry.focus()
        
        # Store edit context
        self.edit_item = item
        self.edit_column = col_name
        
        # Bind events for saving/canceling
        self.edit_entry.bind('<Return>', self.save_edit)
        self.edit_entry.bind('<Escape>', self.cancel_edit)
        self.edit_entry.bind('<FocusOut>', self.save_edit)
    
    def save_edit(self, event=None):
        """Save the edited cell value"""
        if not hasattr(self, 'edit_entry') or not self.edit_entry.winfo_exists():
            return
        
        new_value = self.edit_entry.get()
        old_value = self.player_tree.set(self.edit_item, self.edit_column)
        
        # Get character ID for database update
        char_id = self.player_tree.set(self.edit_item, "ID")
        
        # Validate and convert data based on column type
        try:
            validated_value = self.validate_cell_data(self.edit_column, new_value)
        except ValueError as e:
            messagebox.showerror("Invalid Value", str(e))
            self.cancel_edit()
            return
        
        # Update database
        if self.update_database(char_id, self.edit_column, validated_value):
            # Update treeview display
            self.player_tree.set(self.edit_item, self.edit_column, new_value)
            print(f"Updated {self.edit_column} for character {char_id}: {old_value} -> {new_value}")
        else:
            messagebox.showerror("Database Error", "Failed to update database")
        
        self.cancel_edit()
    
    def cancel_edit(self, event=None):
        """Cancel editing and remove entry widget"""
        if hasattr(self, 'edit_entry') and self.edit_entry.winfo_exists():
            self.edit_entry.destroy()
        if hasattr(self, 'edit_item'):
            delattr(self, 'edit_item')
        if hasattr(self, 'edit_column'):
            delattr(self, 'edit_column')
    
    def validate_cell_data(self, column, value):
        """Validate and convert cell data based on column type"""
        # Numeric columns
        numeric_columns = ["Level", "Zone", "Time\nPlayed", "AA\nSpent", "AA\nPoints", 
                          "Plat", "Gold", "Plat\nBank", "Gold\nBank", "Plat\nCursor", "Gold\nCursor"]
        
        if column in numeric_columns:
            try:
                return int(value) if value else 0
            except ValueError:
                raise ValueError(f"{column} must be a valid number")
        
        # Text columns - basic validation
        elif column in ["Name"]:
            if not value or value.strip() == "":
                raise ValueError("Name cannot be empty")
            if len(value) > 64:  # EQ character name limit
                raise ValueError("Name is too long (max 64 characters)")
            return value.strip()
        
        # Class validation
        elif column == "Class":
            class_names = list(CLASS_ID_TO_NAME.values())
            if value not in class_names:
                raise ValueError(f"Class must be one of: {', '.join(class_names)}")
            return value
        
        # Race validation  
        elif column == "Race":
            race_names = list(RACE_ID_TO_NAME.values())
            if value not in race_names:
                raise ValueError(f"Race must be one of: {', '.join(race_names)}")
            return value
        
        return value
    
    def update_database(self, char_id, column, value):
        """Update the database with the new value"""
        try:
            # Map display column names to database column names
            column_mapping = {
                "Name": "name",
                "Level": "level", 
                "Class": "class",
                "Race": "race",
                "Zone": "zone_id",
                "Time\nPlayed": "time_played",
                "AA\nSpent": "aa_points_spent", 
                "AA\nPoints": "aa_points",
                "Plat": "platinum",
                "Gold": "gold",
                "Plat\nBank": "platinum_bank",
                "Gold\nBank": "gold_bank",
                "Plat\nCursor": "platinum_cursor",
                "Gold\nCursor": "gold_cursor"
            }
            
            db_column = column_mapping.get(column)
            if not db_column:
                return False
            
            # Determine which table to update
            if db_column in ["platinum", "gold", "platinum_bank", "gold_bank", "platinum_cursor", "gold_cursor"]:
                # Update character_currency table
                table = "character_currency"
                where_column = "id"
                
                # For class and race, we need to convert names back to IDs
                if column == "Class":
                    name_to_id = {v: k for k, v in CLASS_ID_TO_NAME.items()}
                    value = name_to_id[value]
                elif column == "Race":
                    name_to_id = {v: k for k, v in RACE_ID_TO_NAME.items()}
                    value = name_to_id[value]
                    
            else:
                # Update character_data table
                table = "character_data"
                where_column = "id"
                
                # For class and race, we need to convert names back to IDs
                if column == "Class":
                    name_to_id = {v: k for k, v in CLASS_ID_TO_NAME.items()}
                    value = name_to_id[value]
                elif column == "Race":
                    name_to_id = {v: k for k, v in RACE_ID_TO_NAME.items()}
                    value = name_to_id[value]
            
            # Execute update query
            query = f"UPDATE {table} SET {db_column} = %s WHERE {where_column} = %s"
            result = self.db_manager.execute_update(query, (value, char_id))
            
            return result is not None
            
        except Exception as e:
            print(f"Database update error: {e}")
            return False
    
    def sort_treeview(self, col):
        """Sort treeview by column"""
        # Toggle sort direction if clicking same column
        if self.sort_column == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = col
            self.sort_reverse = False
        
        # Get all items from treeview
        items = [(self.player_tree.set(child, col), child) for child in self.player_tree.get_children('')]
        
        # Sort items - handle numeric columns specially
        numeric_columns = ["ID", "Level", "Zone", "Time\nPlayed", "AA\nSpent", "AA\nPoints", 
                          "Plat", "Gold", "Plat\nBank", "Gold\nBank", "Plat\nCursor", "Gold\nCursor", 
                          "Shared\nItems"]
        # Class and Race are now text columns, so they'll be sorted alphabetically
        
        if col in numeric_columns:
            # Sort numerically, handling None/empty values
            items.sort(key=lambda x: float(x[0]) if x[0] and str(x[0]).replace('.','',1).isdigit() else 0, reverse=self.sort_reverse)
        else:
            # Sort alphabetically
            items.sort(key=lambda x: str(x[0]).lower(), reverse=self.sort_reverse)
        
        # Rearrange items in treeview
        for index, (val, child) in enumerate(items):
            self.player_tree.move(child, '', index)
        
        # Update column heading to show sort direction
        for column in self.player_tree['columns']:
            if column == col:
                direction = " ↓" if self.sort_reverse else " ↑"
                self.player_tree.heading(column, text=column + direction)
            else:
                self.player_tree.heading(column, text=column)
    
    def load_inventory(self, event=None):
        """Load inventory for selected player"""
        selected_item = self.player_tree.selection()
        if not selected_item:
            return
        
        # Get character ID
        char_id = self.player_tree.item(selected_item, "values")[0]
        
        # Clear existing items
        for item in self.worn_tree.get_children():
            self.worn_tree.delete(item)
        for item in self.bagged_tree.get_children():
            self.bagged_tree.delete(item)
        
        # Fetch inventory for character (only slots with actual items)
        query = """
            SELECT i.slot_id, i.item_id, COALESCE(it.Name, 'Unknown Item') as item_name, i.charges
            FROM inventory i
            LEFT JOIN items it ON i.item_id = it.id
            WHERE i.character_id = %s AND i.item_id > 0
            ORDER BY i.slot_id
        """
        inventory = self.db_manager.execute_query(query, (char_id,))
        
        # DEBUG: Print what we're getting from the database
        print(f"DEBUG: Query returned {len(inventory)} items for character {char_id}")
        if inventory:
            print(f"DEBUG: First item data: {inventory[0]}")
            print(f"DEBUG: First item type: {type(inventory[0])}")
            if isinstance(inventory[0], dict):
                print(f"DEBUG: Dictionary keys: {list(inventory[0].keys())}")
        
        # Insert items into appropriate treeview
        for item in inventory:
            # Convert dictionary to tuple of values ordered by columns
            if isinstance(item, dict):
                slot_id = item.get('slot_id')
                slot_name = SLOT_ID_TO_NAME.get(slot_id, f"Slot {slot_id}")
                
                # Extract values in the same order as the treeview columns: ["Slot", "Item ID", "Item Name", "Charges"]
                item_values = [
                    slot_name, item.get('item_id'), item.get('item_name'), item.get('charges', 0)
                ]
                print(f"DEBUG: Inserting into treeview: {item_values}")
            else:
                slot_id = item[0]
                slot_name = SLOT_ID_TO_NAME.get(slot_id, f"Slot {slot_id}")
                item_values = [slot_name, item[1], item[2], item[3] if len(item) > 3 else 0]
                print(f"DEBUG: Inserting tuple into treeview: {item_values}")
            
            # Worn equipment slots (0-21)
            if 0 <= slot_id <= 21:
                self.worn_tree.insert("", tk.END, values=item_values)
            # Bagged items (22+)
            else:
                self.bagged_tree.insert("", tk.END, values=item_values)
        
        # Load character details
        self.load_character_details(char_id)
        
        print(f"Loaded inventory for character ID {char_id}")
    
    def load_character_details(self, char_id):
        """Load character details"""
        # Fetch character data
        query = """
            SELECT name, level, class, race, deity, last_login, time_played, 
                   cur_hp, mana, endurance, str, sta, cha, dex, `int`, agi, wis
            FROM character_data
            WHERE id = %s
        """
        char_data = self.db_manager.execute_query(query, (char_id,), fetch_all=False)
        
        if char_data:
            # Handle both dictionary and tuple results
            if isinstance(char_data, dict):
                # Character data is already a dictionary
                char_data_dict = {
                    "Name": char_data.get('name'),
                    "Level": char_data.get('level'),
                    "Class": char_data.get('class'),
                    "Race": char_data.get('race'),
                    "Deity": char_data.get('deity'),
                    "Last Login": char_data.get('last_login'),
                    "Time Played": char_data.get('time_played'),
                    "HP": char_data.get('cur_hp'),
                    "Mana": char_data.get('mana'),
                    "Endurance": char_data.get('endurance'),
                    "STR": char_data.get('str'),
                    "STA": char_data.get('sta'),
                    "CHA": char_data.get('cha'),
                    "DEX": char_data.get('dex'),
                    "INT": char_data.get('int'),
                    "AGI": char_data.get('agi'),
                    "WIS": char_data.get('wis')
                }
            else:
                # Character data is a tuple
                char_data_dict = {
                    "Name": char_data[0],
                    "Level": char_data[1],
                    "Class": char_data[2],
                    "Race": char_data[3],
                    "Deity": char_data[4],
                    "Last Login": char_data[5],
                    "Time Played": char_data[6],
                    "HP": char_data[7],
                    "Mana": char_data[8],
                    "Endurance": char_data[9],
                    "STR": char_data[10],
                    "STA": char_data[11],
                    "CHA": char_data[12],
                    "DEX": char_data[13],
                    "INT": char_data[14],
                    "AGI": char_data[15],
                    "WIS": char_data[16]
                }
            
            # Update character info labels
            for field in self.char_info_labels.keys():
                if field == "Guild":
                    # Fetch guild information from guild_members and guilds tables
                    guild_query = """
                        SELECT g.name, gm.rank
                        FROM guild_members gm
                        JOIN guilds g ON gm.guild_id = g.id
                        WHERE gm.char_id = %s
                    """
                    guild_result = self.db_manager.execute_query(guild_query, (char_id,), fetch_all=False)
                    
                    if guild_result:
                        if isinstance(guild_result, dict):
                            guild_name = guild_result.get('name')
                            guild_rank = guild_result.get('rank')
                        else:
                            guild_name, guild_rank = guild_result
                        value = f"{guild_name} (Rank: {guild_rank})"
                    else:
                        value = "None"
                else:
                    value = char_data_dict.get(field, "Unknown")
                    
                    # Apply formatting for specific fields
                    if field == "Class":
                        # Convert class ID to name
                        class_names = {
                            1: "Warrior", 2: "Cleric", 3: "Paladin", 4: "Ranger", 5: "Shadow Knight",
                            6: "Druid", 7: "Monk", 8: "Bard", 9: "Rogue", 10: "Shaman",
                            11: "Necromancer", 12: "Wizard", 13: "Magician", 14: "Enchanter",
                            15: "Beastlord", 16: "Berserker"
                        }
                        value = class_names.get(value, f"Unknown ({value})")
                    elif field == "Race":
                        # Convert race ID to name
                        race_names = {
                            1: "Human", 2: "Barbarian", 3: "Erudite", 4: "Wood Elf", 5: "High Elf",
                            6: "Dark Elf", 7: "Half Elf", 8: "Dwarf", 9: "Troll", 10: "Ogre",
                            11: "Halfling", 12: "Gnome", 128: "Iksar", 130: "Vah Shir", 330: "Froglok"
                        }
                        value = race_names.get(value, f"Unknown ({value})")
                    elif field == "Time Played":
                        # Format time played (in seconds)
                        if value and value != "Unknown":
                            hours = value // 3600
                            minutes = (value % 3600) // 60
                            value = f"{hours}h {minutes}m"
                        else:
                            value = "Unknown"
                
                self.char_info_labels[field].config(text=str(value))
        
        # Load character buffs
        self.load_character_buffs(char_id)
    
    def load_character_buffs(self, char_id):
        """Load character buffs"""
        # Clear existing items
        for item in self.buffs_tree.get_children():
            self.buffs_tree.delete(item)
        
        # Fetch character buffs
        query = """
            SELECT cb.spell_id, sn.name
            FROM character_buffs cb
            LEFT JOIN spells_new sn ON cb.spell_id = sn.id
            WHERE cb.character_id = %s
            ORDER BY sn.name
        """
        buffs = self.db_manager.execute_query(query, (char_id,))
        
        # Insert buffs into treeview
        for buff in buffs:
            # Convert dictionary to tuple of values ordered by columns
            if isinstance(buff, dict):
                # Extract values in the same order as the treeview columns: ["Spell ID", "Spell Name"]
                buff_values = [
                    buff.get('spell_id'), buff.get('name')
                ]
                self.buffs_tree.insert("", tk.END, values=buff_values)
            else:
                self.buffs_tree.insert("", tk.END, values=buff)
    
    def display_item_details(self, event=None):
        """CRITICAL: Handle item selection and display stats on image overlay - EXACT COPY from loot tool"""
        # Determine which treeview triggered the event
        if event.widget == self.worn_tree:
            tree = self.worn_tree
        elif event.widget == self.bagged_tree:
            tree = self.bagged_tree
        else:
            return
        
        selected_item = tree.selection()
        if not selected_item:
            return
       
        item_id = tree.item(selected_item, "values")[1]
       
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
            # Create item_stats dictionary from item_data
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
            
            # Handle both dict and tuple results
            if isinstance(item_data, dict):
                item_stats = item_data
            else:
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
                # Convert to int if it's a string
                if isinstance(classes_bitmask, str):
                    classes_bitmask = int(classes_bitmask)
                
                if classes_bitmask == 65535:
                    item_stats["classes"] = "ALL"
                else:
                    class_names = []
                    for bit_value, class_name in CLASS_BITMASK_DISPLAY.items():
                        if bit_value != 65535 and classes_bitmask & bit_value:
                            class_names.append(class_name)
                    item_stats["classes"] = ", ".join(class_names)
            
            # Handle races bitmask using centralized dictionary
            races_bitmask = item_stats.get("races")
            if races_bitmask is not None:
                # Convert to int if it's a string
                if isinstance(races_bitmask, str):
                    races_bitmask = int(races_bitmask)
                    
                if races_bitmask == 65535:
                    item_stats["races"] = "ALL"
                else:
                    race_names = []
                    for bit_value, race_name in RACE_BITMASK_DISPLAY.items():
                        if bit_value != 65535 and races_bitmask & bit_value:
                            race_names.append(race_name)
                    item_stats["races"] = ", ".join(race_names)
    
            # Handle item slots bitmask using centralized dictionary
            slots_bitmask = item_stats.get("slots")  
            if slots_bitmask is not None:
                # Convert to int if it's a string
                if isinstance(slots_bitmask, str):
                    slots_bitmask = int(slots_bitmask)
                    
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
    
    def delete_selected_item(self):
        """Delete selected item"""
        # Determine which treeview has selection
        if self.worn_tree.selection():
            tree = self.worn_tree
        elif self.bagged_tree.selection():
            tree = self.bagged_tree
        else:
            messagebox.showwarning("Warning", "No item selected.")
            return
        
        selected_item = tree.selection()
        if not selected_item:
            return
        
        values = tree.item(selected_item, "values")
        slot_name, item_id, item_name, charges = values[0], values[1], values[2], values[3]
        
        # Convert slot name back to slot ID for database operations
        slot_id = None
        for sid, sname in SLOT_ID_TO_NAME.items():
            if sname == slot_name:
                slot_id = sid
                break
        
        if slot_id is None:
            messagebox.showerror("Error", f"Could not find slot ID for {slot_name}")
            return
        
        # Get character ID
        selected_player = self.player_tree.selection()
        if not selected_player:
            return
        
        char_id = self.player_tree.item(selected_player, "values")[0]
        
        # Confirm Deletion
        confirm = messagebox.askyesno("Confirm", f"Delete {item_name} (ID: {item_id}, Charges: {charges}) from character {char_id}, {slot_name}?")
        if not confirm:
            return
        
        # Delete from Database
        delete_query = "DELETE FROM inventory WHERE character_id = %s AND slot_id = %s AND item_id = %s"
        self.db_manager.execute_update(delete_query, (char_id, slot_id, item_id))
        
        # Remove from GUI
        tree.delete(selected_item)
        
        print(f"Deleted item {item_id} from character {char_id}, {slot_name} (slot {slot_id})") 