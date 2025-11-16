import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sys
import os
from typing import Dict, List

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.theme import set_dark_theme
from shared.notes_db import NotesDBManager
from lookup_data import (
    race_lookup as RACE_LOOKUP_SEED,
    class_lookup as CLASS_LOOKUP_SEED,
    deity_lookup as DEITY_LOOKUP_SEED,
)


class _TreeviewScrollMixin:
    """Provide invisible scrollbar behaviour for scrollable widgets."""

    @staticmethod
    def _make_treeview_invisible_scroll(tree: ttk.Treeview):
        _TreeviewScrollMixin._make_widget_invisible_scroll(tree, allow_horizontal=True)

    @staticmethod
    def _make_widget_invisible_scroll(widget, allow_horizontal: bool = False):
        configure_kwargs = {}
        if hasattr(widget, "yview"):
            configure_kwargs["yscrollcommand"] = lambda *args: None
        if allow_horizontal and hasattr(widget, "xview"):
            configure_kwargs["xscrollcommand"] = lambda *args: None
        if configure_kwargs:
            widget.configure(**configure_kwargs)

        def _on_mousewheel(event, horizontal=False):
            delta = event.delta
            if delta == 0:
                num = getattr(event, "num", 0)
                delta = 120 if num == 4 else -120
            direction = -1 if delta > 0 else 1
            try:
                if horizontal and allow_horizontal and hasattr(widget, "xview_scroll"):
                    widget.xview_scroll(direction, "units")
                elif hasattr(widget, "yview_scroll"):
                    widget.yview_scroll(direction, "units")
            except tk.TclError:
                pass
            return "break"

        widget.bind("<MouseWheel>", lambda event: _on_mousewheel(event))
        widget.bind("<Button-4>", lambda event: _on_mousewheel(event))
        widget.bind("<Button-5>", lambda event: _on_mousewheel(event))
        if allow_horizontal:
            widget.bind("<Shift-MouseWheel>", lambda event: _on_mousewheel(event, horizontal=True))
            widget.bind("<Shift-Button-4>", lambda event: _on_mousewheel(event, horizontal=True))
            widget.bind("<Shift-Button-5>", lambda event: _on_mousewheel(event, horizontal=True))

class TreeviewEdit:
    """Cell editing functionality for Treeview widgets"""
    def __init__(self, tree, editable_columns=None, update_callback=None):
        self.tree = tree
        self.editable_columns = editable_columns or []
        self.update_callback = update_callback
        self.editing = False
        self.edit_cell = None
        self.edit_entry = None
        
        # Bind double-click to start editing
        self.tree.bind("<Double-1>", self.start_edit)
        # Bind Escape to cancel editing
        self.tree.bind("<Escape>", self.cancel_edit)
        
    def start_edit(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        
        column = self.tree.identify_column(event.x)
        column_index = int(column.replace('#', '')) - 1
        
        if column_index not in self.editable_columns:
            return
            
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return
            
        current_value = self.tree.item(item_id, "values")[column_index]
        
        x, y, width, height = self.tree.bbox(item_id, column)
        
        self.edit_entry = ttk.Entry(self.tree)
        self.edit_entry.insert(0, current_value)
        self.edit_entry.select_range(0, tk.END)
        self.edit_entry.place(x=x, y=y, width=width, height=height)
        self.edit_entry.focus_set()
        
        self.edit_entry.bind("<Return>", lambda e: self.save_edit(item_id, column_index))
        self.edit_entry.bind("<FocusOut>", lambda e: self.cancel_edit(e))
        
        self.editing = True
        self.edit_cell = (item_id, column_index)
    
    def save_edit(self, item_id, column_index):
        if not self.editing:
            return
            
        new_value = self.edit_entry.get()
        values = list(self.tree.item(item_id, "values"))
        
        try:
            # For numeric columns, convert to appropriate type
            if column_index in [0, 2, 3, 4, 5]:  # ID and numeric columns
                new_value = int(new_value)
            elif column_index in [6]:  # Float columns
                new_value = float(new_value)
        except ValueError:
            messagebox.showerror("Invalid Value", "Please enter a valid value.")
            self.edit_entry.focus_set()
            return
        
        values[column_index] = new_value
        self.tree.item(item_id, values=values)
        
        if self.update_callback:
            self.update_callback(self.tree, item_id, column_index, new_value)
        
        self.cleanup()
        
    def cancel_edit(self, event=None):
        if not self.editing:
            return
        self.cleanup()
        
    def cleanup(self):
        if self.edit_entry:
            self.edit_entry.destroy()
            self.edit_entry = None
        self.editing = False
        self.edit_cell = None

class FactionManagerTool(_TreeviewScrollMixin):
    """Faction Manager Tool - modular version for tabbed interface"""
    
    def __init__(self, parent_frame, db_manager, notes_db_manager: NotesDBManager):
        self.parent = parent_frame
        self.db_manager = db_manager
        self.conn = db_manager.connect()
        self.cursor = db_manager.get_cursor()
        if not isinstance(notes_db_manager, NotesDBManager):
            raise ValueError("FactionManagerTool requires a NotesDBManager instance")
        self.notes_db: NotesDBManager = notes_db_manager
        self.race_bitmask_display = {}
        self.class_bitmask_display = {}
        self.deity_name_to_bit = {}
        self.sorted_deity_names = []
        self.load_lookup_data()
        self._auto_updating_npc_group_name = False
        self._npc_group_name_user_modified = False
        self._last_autogenerated_npc_group_name = ""
        
        # Configure parent frame grid
        self.parent.grid_rowconfigure(0, weight=1)
        self.parent.grid_columnconfigure(0, weight=1)
        
        # Create main container frame
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Initialize UI components
        self.create_ui()
        
        # Load initial data
        try:
            self.load_factions()
            print("Faction tool initialized successfully")
        except Exception as e:
            print(f"Warning: Could not initialize faction tool data: {e}")

    def load_lookup_data(self):
        """Load race, class, and deity lookup data with seed fallbacks."""
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
        self.class_bitmask_display[65535] = "ALL"

        race_rows = _fetch(
            lambda: self.notes_db.get_race_bitmasks(),
            RACE_LOOKUP_SEED,
        )
        self.race_bitmask_display = {
            row['bit_value']: row.get('abbr') or row['name'] for row in race_rows
        }
        self.race_bitmask_display[65535] = "ALL"

        deity_rows = _fetch(
            lambda: self.notes_db.get_deity_bitmasks(),
            DEITY_LOOKUP_SEED,
        )
        self.deity_name_to_bit = {
            row['name']: row['bit_value'] for row in deity_rows
        }
        self.sorted_deity_names = sorted(self.deity_name_to_bit.keys())
    
    def create_ui(self):
        """Create the complete Faction Manager UI"""
        # Configure main frame grid - 2 columns, 2 rows
        self.main_frame.grid_rowconfigure(0, weight=0)  # Top area 
        self.main_frame.grid_rowconfigure(1, weight=1)  # Bottom area (NPC list)
        self.main_frame.grid_columnconfigure(0, weight=0)  # Left column (faction list)
        self.main_frame.grid_columnconfigure(1, weight=1)  # Right column (everything else)
        
        # Create the main sections
        self.create_left_column()    # Faction list spanning full height
        self.create_top_right()      # Faction details, modifiers, associations, groups
        self.create_bottom_area()    # NPC list across full width
    
    def create_left_column(self):
        """Create left column with faction list spanning full height"""
        # Faction list frame spanning both rows
        faction_list_frame = ttk.LabelFrame(self.main_frame, text="Faction List", padding="5")
        faction_list_frame.grid(row=0, column=0, rowspan=2, padx=5, pady=5, sticky="nsew")
        faction_list_frame.grid_rowconfigure(2, weight=1)
        faction_list_frame.grid_columnconfigure(0, weight=1)
        
        # Search controls
        search_frame = ttk.Frame(faction_list_frame)
        search_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        search_frame.grid_columnconfigure(0, weight=1)
        
        ttk.Label(search_frame, text="Search Factions:").grid(row=0, column=0, sticky="w")
        self.faction_search_var = tk.StringVar()
        self.faction_search_entry = ttk.Entry(search_frame, textvariable=self.faction_search_var, width=25)
        self.faction_search_entry.grid(row=1, column=0, sticky="ew", pady=(2, 0))
        self.faction_search_var.trace("w", self.filter_factions)
        
        # Filter controls
        filter_frame = ttk.Frame(faction_list_frame)
        filter_frame.grid(row=1, column=0, sticky="ew", pady=(0, 5))
        
        ttk.Button(filter_frame, text="Show All", command=self.show_all_factions).grid(row=0, column=0, padx=(0, 2))
        ttk.Button(filter_frame, text="Clear", command=self.clear_search).grid(row=0, column=1)
        
        # Faction Treeview (two columns, sortable). No extra scrollbars added.
        self.faction_tree = ttk.Treeview(faction_list_frame, columns=("id", "name"), show="headings")
        self._make_treeview_invisible_scroll(self.faction_tree)
        self.faction_tree.heading("id", text="ID")
        self.faction_tree.heading("name", text="Name")
        self.faction_tree.column("id", width=60, anchor="center")
        self.faction_tree.column("name", width=180, anchor="w")
        self.faction_tree.grid(row=2, column=0, sticky="nsew")
        self.faction_tree.bind('<<TreeviewSelect>>', self.on_faction_select)
        
        # Sorting handlers
        def sort_tree(col, reverse=False):
            data = [(self.faction_tree.set(k, col), k) for k in self.faction_tree.get_children("")]
            if col == 'id':
                data.sort(key=lambda t: int(t[0]) if t[0].isdigit() else 0, reverse=reverse)
            else:
                data.sort(key=lambda t: t[0].lower(), reverse=reverse)
            for idx, (_, k) in enumerate(data):
                self.faction_tree.move(k, '', idx)
            self.faction_tree.heading(col, command=lambda: sort_tree(col, not reverse))
        self.faction_tree.heading('id', command=lambda: sort_tree('id', False))
        self.faction_tree.heading('name', command=lambda: sort_tree('name', False))
    
    def create_top_right(self):
        """Create top right area with all faction details and data"""
        # Main container for top right
        top_right_frame = ttk.Frame(self.main_frame)
        top_right_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        top_right_frame.grid_rowconfigure(0, weight=0)  # Basic info
        top_right_frame.grid_rowconfigure(1, weight=0)  # Settings row
        top_right_frame.grid_rowconfigure(2, weight=1)  # Faction groups/entries row
        top_right_frame.grid_columnconfigure(0, weight=1)
        
        # Basic faction information (top) - merged with Base Data Settings
        info_frame = ttk.LabelFrame(top_right_frame, text="Basic Faction Information", padding="5")
        info_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        # Keep columns fixed to avoid over-expansion of Name
        for c in range(0, 12):
            info_frame.grid_columnconfigure(c, weight=0)
        
        # Basic faction info in 2 columns
        ttk.Label(info_frame, text="ID:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.faction_id_var = tk.StringVar()
        self.faction_id_entry = ttk.Entry(info_frame, textvariable=self.faction_id_var, state="readonly", width=10)
        self.faction_id_entry.grid(row=0, column=1, sticky="ew", padx=(0, 20))
        
        ttk.Label(info_frame, text="Name:").grid(row=0, column=2, sticky="w", padx=(0, 5))
        self.faction_name_var = tk.StringVar()
        self.faction_name_entry = ttk.Entry(info_frame, textvariable=self.faction_name_var, width=24)
        self.faction_name_entry.grid(row=0, column=3, sticky="w")
        self.faction_name_var.trace_add("write", self._handle_faction_name_change)

        ttk.Label(info_frame, text="Base Value:").grid(row=1, column=0, sticky="w", padx=(0, 5), pady=(5, 0))
        self.faction_base_var = tk.StringVar()
        self.faction_base_entry = ttk.Entry(info_frame, textvariable=self.faction_base_var, width=8)
        self.faction_base_entry.grid(row=1, column=1, sticky="ew", pady=(5, 0), padx=(0, 10))

        # Merged Base Data Settings (Min/Max) into this section
        ttk.Label(info_frame, text="Min Value:").grid(row=1, column=2, sticky="w", padx=(0, 5))
        self.min_value_var = getattr(self, 'min_value_var', tk.StringVar())
        self.min_value_entry = ttk.Entry(info_frame, textvariable=self.min_value_var, width=8)
        self.min_value_entry.grid(row=1, column=3, sticky="w", padx=(0, 10))

        ttk.Label(info_frame, text="Max Value:").grid(row=1, column=4, sticky="w", padx=(0, 5))
        self.max_value_var = getattr(self, 'max_value_var', tk.StringVar())
        self.max_value_entry = ttk.Entry(info_frame, textvariable=self.max_value_var, width=8)
        self.max_value_entry.grid(row=1, column=5, sticky="w", padx=(0, 10))

        ttk.Label(info_frame, text="NPC Group ID:").grid(row=1, column=6, sticky="w", padx=(0, 5))
        self.npc_faction_group_id_var = tk.StringVar()
        self.npc_faction_group_id_entry = ttk.Entry(
            info_frame, textvariable=self.npc_faction_group_id_var, state="readonly", width=8
        )
        self.npc_faction_group_id_entry.grid(row=1, column=7, sticky="ew", padx=(0, 10))

        ttk.Label(info_frame, text="NPC Group Name:").grid(row=1, column=8, sticky="w", padx=(0, 5))
        self.npc_faction_group_name_var = tk.StringVar()
        self.npc_faction_group_name_entry = ttk.Entry(
            info_frame, textvariable=self.npc_faction_group_name_var, width=18
        )
        self.npc_faction_group_name_entry.grid(row=1, column=9, sticky="w")
        self.npc_faction_group_name_var.trace_add("write", self._handle_npc_group_name_change)

        self.ignore_primary_assist_var = tk.IntVar(value=0)
        ttk.Checkbutton(
            info_frame,
            text="Ignore Primary Assist",
            variable=self.ignore_primary_assist_var
        ).grid(row=1, column=10, sticky="w", padx=(10, 0))
        
        # Buttons
        button_frame = ttk.Frame(info_frame)
        # Place buttons on the top row, right side
        button_frame.grid(row=0, column=7, columnspan=5, sticky="e", pady=(0, 0), padx=(10, 0))
        
        ttk.Button(button_frame, text="Save Changes", command=self.save_faction).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(button_frame, text="New Faction", command=self.new_faction).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(button_frame, text="Delete Faction", command=self.delete_faction).grid(row=0, column=2)
        ttk.Button(button_frame, text="Guide", command=self.open_faction_guide).grid(row=0, column=3, padx=(10, 0))
        
        # Settings row (explainer, modifiers, associations)
        settings_frame = ttk.Frame(top_right_frame)
        settings_frame.grid(row=1, column=0, sticky="ew", pady=(0, 5))
        settings_frame.grid_columnconfigure(0, weight=1)
        settings_frame.grid_columnconfigure(1, weight=1)
        settings_frame.grid_columnconfigure(2, weight=1)

        # Faction information (left)
        self.faction_info_frame = ttk.LabelFrame(settings_frame, text="Faction Information", padding="5")
        self.faction_info_frame.grid(row=0, column=0, padx=(0, 3), sticky="nsew")
        self.faction_info_frame.grid_rowconfigure(0, weight=1)
        self.faction_info_frame.grid_columnconfigure(0, weight=1)
        self.faction_info_var = tk.StringVar(value="Select a faction to view information.")
        ttk.Label(
            self.faction_info_frame,
            textvariable=self.faction_info_var,
            wraplength=360,
            justify=tk.LEFT
        ).grid(row=0, column=0, sticky="nw")
        
        # Race/Class modifiers (center) 
        mod_frame = ttk.LabelFrame(settings_frame, text="Race/Class/Deity Modifiers", padding="5")
        mod_frame.grid(row=0, column=1, padx=3, sticky="nsew")
        mod_frame.grid_rowconfigure(0, weight=1)
        mod_frame.grid_columnconfigure(0, weight=1)
        
        # Modifier treeview
        self.mod_tree = ttk.Treeview(mod_frame, columns=("mod", "mod_name"), show="headings", height=4)
        self._make_treeview_invisible_scroll(self.mod_tree)
        self.mod_tree.heading("#1", text="Modifier")
        self.mod_tree.heading("#2", text="Race/Class")
        self.mod_tree.column("#1", width=70)
        self.mod_tree.column("#2", width=100)
        self.mod_tree.grid(row=0, column=0, sticky="nsew")
        
        # Modifier editing
        self.mod_editor = TreeviewEdit(self.mod_tree, [0], self.update_modifier)
        # Modifier controls row
        mod_btns = ttk.Frame(mod_frame)
        mod_btns.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        ttk.Button(mod_btns, text="Add Race", command=lambda: self.open_modifier_picker('race')).pack(side=tk.LEFT, padx=(0, 3))
        ttk.Button(mod_btns, text="Add Class", command=lambda: self.open_modifier_picker('class')).pack(side=tk.LEFT, padx=(0, 3))
        ttk.Button(mod_btns, text="Add Deity", command=lambda: self.open_modifier_picker('deity')).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(mod_btns, text="Remove Selected", command=self.remove_selected_modifier).pack(side=tk.LEFT)
        ttk.Button(mod_btns, text="Bitmask Lookup", command=self.open_bitmask_lookup).pack(side=tk.RIGHT)
        
        # Faction associations (right)
        assoc_frame = ttk.LabelFrame(settings_frame, text="Faction Associations", padding="5")
        assoc_frame.grid(row=0, column=2, padx=(3, 0), sticky="nsew")
        assoc_frame.grid_rowconfigure(0, weight=1)
        assoc_frame.grid_columnconfigure(0, weight=1)
        
        # Association treeview
        self.assoc_tree = ttk.Treeview(assoc_frame, columns=("faction_id", "faction_name", "modifier"), show="headings", height=4)
        self._make_treeview_invisible_scroll(self.assoc_tree)
        self.assoc_tree.heading("#1", text="Associated Faction ID")
        self.assoc_tree.heading("#2", text="Faction Name")
        self.assoc_tree.heading("#3", text="Modifier")
        self.assoc_tree.column("#1", width=80)
        self.assoc_tree.column("#2", width=100)
        self.assoc_tree.column("#3", width=60)
        self.assoc_tree.grid(row=0, column=0, sticky="nsew")
        
        # Association editing - allow editing of faction ID (0) and modifier (2)
        self.assoc_editor = TreeviewEdit(self.assoc_tree, [0, 2], self.update_association)
        assoc_btns = ttk.Frame(assoc_frame)
        assoc_btns.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        ttk.Button(assoc_btns, text="Add Association", command=self.add_association).pack(side=tk.LEFT)
        ttk.Button(assoc_btns, text="Remove Selected", command=self.remove_selected_association).pack(side=tk.LEFT, padx=(5, 0))
        
        # Faction groups and entries row
        groups_frame = ttk.Frame(top_right_frame)
        groups_frame.grid(row=2, column=0, sticky="nsew")
        groups_frame.grid_rowconfigure(0, weight=1)
        groups_frame.grid_columnconfigure(0, weight=1)
        groups_frame.grid_columnconfigure(1, weight=1)
        
        # NPC Faction Groups (left)
        faction_groups_frame = ttk.LabelFrame(groups_frame, text="NPC Faction Groups", padding="5")
        faction_groups_frame.grid(row=0, column=0, padx=(0, 3), sticky="nsew")
        faction_groups_frame.grid_rowconfigure(0, weight=1)
        faction_groups_frame.grid_columnconfigure(0, weight=1)
        
        # Faction groups treeview
        self.faction_groups_tree = ttk.Treeview(
            faction_groups_frame,
            columns=("id", "name", "primaryfaction", "primary_faction_name", "ignore_primary_assist"),
            show="headings",
            height=8,
        )
        self._make_treeview_invisible_scroll(self.faction_groups_tree)
        self.faction_groups_tree.heading("#1", text="Group ID")
        self.faction_groups_tree.heading("#2", text="Name")
        self.faction_groups_tree.heading("#3", text="Primary Faction ID")
        self.faction_groups_tree.heading("#4", text="Primary Faction Name")
        self.faction_groups_tree.heading("#5", text="Ignore Primary Assist")
        
        self.faction_groups_tree.column("#1", width=70)
        self.faction_groups_tree.column("#2", width=120)
        self.faction_groups_tree.column("#3", width=80)
        self.faction_groups_tree.column("#4", width=120)
        self.faction_groups_tree.column("#5", width=100)
        
        self.faction_groups_tree.grid(row=0, column=0, sticky="nsew")
        self.faction_groups_tree.bind('<<TreeviewSelect>>', self.on_faction_group_select)
        
        # NPC Faction Entries (right)
        faction_entries_frame = ttk.LabelFrame(groups_frame, text="Faction Entries for Selected Group", padding="5")
        faction_entries_frame.grid(row=0, column=1, padx=(3, 0), sticky="nsew")
        faction_entries_frame.grid_rowconfigure(0, weight=1)
        faction_entries_frame.grid_columnconfigure(0, weight=1)
        
        # Faction entries treeview
        self.faction_entries_tree = ttk.Treeview(
            faction_entries_frame,
            columns=("npc_faction_id", "faction_id", "faction_name", "value", "npc_value", "temp"),
            show="headings",
            height=8,
        )
        self._make_treeview_invisible_scroll(self.faction_entries_tree)
        self.faction_entries_tree.heading("#1", text="NPC Faction ID")
        self.faction_entries_tree.heading("#2", text="Faction ID")
        self.faction_entries_tree.heading("#3", text="Faction Name")
        self.faction_entries_tree.heading("#4", text="Faction Hit")
        self.faction_entries_tree.heading("#5", text="NPC Reaction")
        self.faction_entries_tree.heading("#6", text="Temporary")
        
        self.faction_entries_tree.column("#1", width=90)
        self.faction_entries_tree.column("#2", width=70)
        self.faction_entries_tree.column("#3", width=150)
        self.faction_entries_tree.column("#4", width=50)
        self.faction_entries_tree.column("#5", width=70)
        self.faction_entries_tree.column("#6", width=40)
        
        self.faction_entries_tree.grid(row=0, column=0, sticky="nsew")
    
    def create_bottom_area(self):
        """Create bottom area with NPC list across full width"""
        # NPC list frame spanning full width
        npc_frame = ttk.LabelFrame(self.main_frame, text="NPCs Using This Faction", padding="5")
        npc_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=(0, 5), sticky="nsew")
        npc_frame.grid_rowconfigure(1, weight=1)
        npc_frame.grid_columnconfigure(0, weight=1)
        
        # Inline controls now appear with buttons below the tree
        
        # NPC treeview with all columns from loot_tool plus faction name
        npc_columns = ("ID", "Name", "Lvl", "Race", "Class", "Body", "HP", "Mana",
                      "Gender", "Texture", "Helm\nTexture", "Size", "  Loot\nTable ID", "Spells\n  ID", "Faction\n   ID", "Faction\nName",
                      "Min\ndmg", "Max\ndmg", "Npcspecial\n  attks", "Special\nAbilities", "MR", "CR", "DR", "FR", "PR", "AC",
                      "Attk Delay", "STR", "STA", "DEX", "AGI", "_INT", "WIS", "Maxlevel",
                      "Skip Global Loot", "Exp Mod")
        
        self.npc_tree = ttk.Treeview(npc_frame, columns=npc_columns, show="headings", height=18)
        self._make_treeview_invisible_scroll(self.npc_tree)
        
        # Define column widths like the original
        column_widths = {
            "ID": 50, "Name": 150, "Lvl": 25, "Race": 35, "Class": 39, "Body": 36, "HP": 25, "Mana": 35,
            "Gender": 45, "Texture": 45, "Helm\nTexture": 40, "Size": 45, "  Loot\nTable ID": 50, "Spells\n  ID": 50, 
            "Faction\n   ID": 45, "Faction\nName": 120, "Min\ndmg": 40, "Max\ndmg": 40, "Npcspecial\n  attks": 55, "Special\nAbilities": 50,
            "MR": 35, "CR": 35, "DR": 35, "FR": 35, "PR": 35, "AC": 35, "Attk Delay": 50,
            "STR": 35, "STA": 35, "DEX": 35, "AGI": 35, "_INT": 35, "WIS": 35, "Maxlevel": 45,
            "Skip Global Loot": 60, "Exp Mod": 45
        }
        
        # Set up columns
        for col in npc_columns:
            self.npc_tree.heading(col, text=col)
            self.npc_tree.column(col, width=column_widths.get(col, 80))
        
        self.npc_tree.grid(row=1, column=0, sticky="nsew")
        
        # NPC editing disabled per request (view-only)
        
        # Buttons + inline search
        npc_button_frame = ttk.Frame(npc_frame)
        npc_button_frame.grid(row=2, column=0, sticky="ew", pady=(5, 0))
        npc_button_frame.grid_columnconfigure(0, weight=0)
        npc_button_frame.grid_columnconfigure(1, weight=0)
        npc_button_frame.grid_columnconfigure(2, weight=1)

        ttk.Button(npc_button_frame, text="Refresh NPCs", command=self.refresh_npcs).grid(row=0, column=0)
        ttk.Button(npc_button_frame, text="Show All NPCs", command=self.show_all_npcs).grid(row=0, column=1, padx=(5, 0))

        # Search entry with placeholder inside the box
        self.npc_search_placeholder = "Search NPCs"
        self.npc_search_var = tk.StringVar()
        self.npc_search_entry = ttk.Entry(npc_button_frame, textvariable=self.npc_search_var)
        self.npc_search_entry.grid(row=0, column=2, sticky="ew", padx=(10, 0))
        self.npc_search_entry.insert(0, self.npc_search_placeholder)

        def _npc_search_clear_placeholder(event):
            if self.npc_search_entry.get() == self.npc_search_placeholder:
                self.npc_search_entry.delete(0, tk.END)

        def _npc_search_restore_placeholder(event):
            if not self.npc_search_entry.get():
                self.npc_search_entry.insert(0, self.npc_search_placeholder)

        self.npc_search_entry.bind("<FocusIn>", _npc_search_clear_placeholder)
        self.npc_search_entry.bind("<FocusOut>", _npc_search_restore_placeholder)

        # Wire live filtering; ignore placeholder value inside handler
        self.npc_search_var.trace("w", self.filter_npcs)
    
    def load_factions(self):
        """Load factions from database"""
        try:
            query = "SELECT id, name, base FROM faction_list ORDER BY name"
            factions = self.db_manager.execute_query(query)
            
            # Clear tree and local cache
            if hasattr(self, 'faction_tree'):
                for item in self.faction_tree.get_children():
                    self.faction_tree.delete(item)
            self.factions = {}
            
            for faction in factions:
                # Insert into treeview with two columns
                if hasattr(self, 'faction_tree'):
                    self.faction_tree.insert('', 'end', values=(faction['id'], faction['name']))
                self.factions[faction['id']] = faction
                
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to load factions: {e}")
    
    def filter_factions(self, *args):
        """Filter faction list based on search term"""
        search_term = self.faction_search_var.get().lower()
        
        if not hasattr(self, 'faction_tree'):
            return
        # Rebuild filtered rows
        for item in self.faction_tree.get_children():
            self.faction_tree.delete(item)
        for faction_id, faction in self.factions.items():
            if search_term in str(faction['id']).lower() or search_term in faction['name'].lower():
                self.faction_tree.insert('', 'end', values=(faction['id'], faction['name']))
    
    def clear_search(self):
        """Clear search and show all factions"""
        self.faction_search_var.set("")
        self.show_all_factions()
    
    def show_all_factions(self):
        """Show all factions in list"""
        if not hasattr(self, 'faction_tree'):
            return
        for item in self.faction_tree.get_children():
            self.faction_tree.delete(item)
        for faction_id, faction in self.factions.items():
            self.faction_tree.insert('', 'end', values=(faction['id'], faction['name']))
    
    def on_faction_select(self, event):
        """Handle faction selection"""
        if not hasattr(self, 'faction_tree'):
            return
        sel = self.faction_tree.selection()
        if not sel:
            return
        values = self.faction_tree.item(sel[0], 'values')
        if not values:
            return
        faction_id = int(values[0])
        
        self.load_faction_details(faction_id)
        self.load_faction_modifiers(faction_id)
        self.load_faction_base_data(faction_id)
        self.load_faction_associations(faction_id)
        self.load_faction_groups(faction_id)
        self.load_faction_npcs(faction_id)
    
    def load_faction_details(self, faction_id):
        """Load faction details into form"""
        faction = self.factions.get(faction_id)
        if faction:
            self.faction_id_var.set(str(faction['id']))
            self.faction_name_var.set(faction['name'])
            self.faction_base_var.set(str(faction['base']))
            # Ensure association slot map resets
            self.assoc_row_to_slot = {}
            self.load_primary_npc_group(faction_id)
            self.refresh_faction_information(faction_id)
        else:
            self.faction_id_var.set("")
            self.faction_name_var.set("")
            self.faction_base_var.set("")
            self.assoc_row_to_slot = {}
            self.load_primary_npc_group(None)
            self.refresh_faction_information(None)
            self.refresh_faction_information(None)

    def load_primary_npc_group(self, faction_id):
        """Load npc_faction group information for the given faction."""
        if faction_id is None:
            self._auto_updating_npc_group_name = True
            try:
                self.npc_faction_group_id_var.set("")
                self.npc_faction_group_name_var.set("")
            finally:
                self._auto_updating_npc_group_name = False
            self.ignore_primary_assist_var.set(0)
            self._npc_group_name_user_modified = False
            self._last_autogenerated_npc_group_name = ""
            return

        row = self.db_manager.execute_query(
            """
            SELECT id, name, ignore_primary_assist
            FROM npc_faction
            WHERE primaryfaction = %s
            ORDER BY id
            LIMIT 1
            """,
            (faction_id,),
            fetch_all=False
        )

        if row:
            group_id = row.get('id')
            name = row.get('name') or ""
            ignore_primary_assist = int(row.get('ignore_primary_assist') or 0)
            self.npc_faction_group_id_var.set(str(group_id) if group_id is not None else "")
            self._auto_updating_npc_group_name = True
            try:
                self.npc_faction_group_name_var.set(name)
            finally:
                self._auto_updating_npc_group_name = False
            self.ignore_primary_assist_var.set(ignore_primary_assist)
            self._npc_group_name_user_modified = bool(name)
            self._last_autogenerated_npc_group_name = name
        else:
            self._auto_updating_npc_group_name = True
            try:
                self.npc_faction_group_id_var.set("")
                self.npc_faction_group_name_var.set("")
            finally:
                self._auto_updating_npc_group_name = False
            self.ignore_primary_assist_var.set(0)
            self._npc_group_name_user_modified = False
            self._last_autogenerated_npc_group_name = ""

    def load_faction_modifiers(self, faction_id):
        """Load faction modifiers"""
        try:
            query = "SELECT `mod`, `mod_name` FROM faction_list_mod WHERE faction_id = %s"
            modifiers = self.db_manager.execute_query(query, (faction_id,))
            
            # Clear existing items
            for item in self.mod_tree.get_children():
                self.mod_tree.delete(item)
            
            # Add modifiers
            for mod in modifiers:
                self.mod_tree.insert("", "end", values=(mod['mod'], mod['mod_name']))
                
        except Exception as e:
            print(f"Error loading faction modifiers: {e}")
    
    def load_faction_base_data(self, faction_id):
        """Load faction base data settings"""
        try:
            query = "SELECT min, max FROM faction_base_data WHERE client_faction_id = %s"
            base_data = self.db_manager.execute_query(query, (faction_id,), fetch_all=False)
            
            if base_data:
                self.min_value_var.set(str(base_data['min']))
                self.max_value_var.set(str(base_data['max']))
            else:
                self.min_value_var.set("-2000")
                self.max_value_var.set("2000")
                
        except Exception as e:
            print(f"Error loading faction base data: {e}")
    
    def load_faction_associations(self, faction_id):
        """Load faction associations"""
        try:
            # Clear existing items
            for item in self.assoc_tree.get_children():
                self.assoc_tree.delete(item)
            # Reset slot mapping
            self.assoc_row_to_slot = {}
            
            # Load associations from faction_association table with faction names
            query = """
                SELECT id_1, mod_1, id_2, mod_2, id_3, mod_3, id_4, mod_4, id_5, mod_5
                FROM faction_association 
                WHERE id = %s
            """
            associations = self.db_manager.execute_query(query, (faction_id,), fetch_all=False)
            
            if associations:
                # Add each non-null association as a separate row
                for i in range(1, 6):  # id_1 through id_5
                    faction_id_key = f'id_{i}'
                    mod_key = f'mod_{i}'
                    
                    if associations.get(faction_id_key) and associations[faction_id_key] != 0:
                        # Get faction name for this associated faction
                        assoc_faction_id = associations[faction_id_key]
                        faction_name_query = "SELECT name FROM faction_list WHERE id = %s"
                        faction_name_result = self.db_manager.execute_query(faction_name_query, (assoc_faction_id,), fetch_all=False)
                        faction_name = faction_name_result['name'] if faction_name_result else 'Unknown'
                        item = self.assoc_tree.insert("", "end", values=(
                            associations[faction_id_key], 
                            faction_name,
                            associations[mod_key]
                        ))
                        # Track which slot this row maps to
                        self.assoc_row_to_slot[item] = i

        except Exception as e:
            print(f"Error loading faction associations: {e}")
        finally:
            self.refresh_faction_information(faction_id)
    
    def load_faction_groups(self, faction_id):
        """Load NPC faction groups that contain this faction"""
        try:
            # Clear existing items
            for item in self.faction_groups_tree.get_children():
                self.faction_groups_tree.delete(item)
            
            # Load faction groups that have entries for this faction
            query = """
                SELECT DISTINCT nf.id, nf.name, nf.primaryfaction, fl.name as primary_faction_name, nf.ignore_primary_assist
                FROM npc_faction nf
                LEFT JOIN faction_list fl ON nf.primaryfaction = fl.id
                JOIN npc_faction_entries nfe ON nf.id = nfe.npc_faction_id
                WHERE nfe.faction_id = %s
                ORDER BY nf.id
            """
            groups = self.db_manager.execute_query(query, (faction_id,))
            
            for group in groups:
                self.faction_groups_tree.insert("", "end", values=(
                    group['id'],
                    group['name'] or '',
                    group['primaryfaction'],
                    group['primary_faction_name'] or 'Unknown',
                    group['ignore_primary_assist']
                ))
                
        except Exception as e:
            print(f"Error loading faction groups: {e}")
    
    def on_faction_group_select(self, event):
        """Handle faction group selection to load entries"""
        selection = self.faction_groups_tree.selection()
        if not selection:
            return
            
        item = selection[0]
        values = self.faction_groups_tree.item(item, "values")
        npc_faction_id = values[0]
        
        self.load_faction_entries(npc_faction_id)

    def add_association(self):
        """Add a new association into the next free slot (1..5)."""
        faction_id = self.faction_id_var.get()
        if not faction_id:
            messagebox.showwarning("No Selection", "Select a faction first")
            return
        # Find next free slot by reading row
        row = self.db_manager.execute_query(
            "SELECT id_1, id_2, id_3, id_4, id_5 FROM faction_association WHERE id = %s",
            (int(faction_id),), fetch_all=False
        )
        # If no row, create one with all zeros
        if not row:
            self.db_manager.execute_update(
                "INSERT INTO faction_association (id, id_1, mod_1, id_2, mod_2, id_3, mod_3, id_4, mod_4, id_5, mod_5) VALUES (%s,0,0,0,0,0,0,0,0,0,0)",
                (int(faction_id),)
            )
            row = {f'id_{i}': 0 for i in range(1,6)}
        slot = None
        for i in range(1,6):
            if (row.get(f'id_{i}') or 0) == 0:
                slot = i
                break
        if not slot:
            messagebox.showinfo("Full", "All 5 association slots are used")
            return
        # Pick a faction to associate
        picker = tk.Toplevel(self.parent)
        picker.title("Add Association")
        picker.geometry("360x440")
        picker.transient(self.parent)
        picker.grab_set()
        ttk.Label(picker, text="Search Factions:").pack(anchor='w', padx=6, pady=(6,2))
        s = tk.StringVar()
        e = ttk.Entry(picker, textvariable=s)
        e.pack(fill=tk.X, padx=6)
        lb = tk.Listbox(picker)
        lb.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        # Load factions
        all_f = self.db_manager.execute_query("SELECT id, name FROM faction_list ORDER BY name")
        def feed():
            term = s.get().lower()
            lb.delete(0, tk.END)
            for f in all_f:
                txt = f"{f['id']}: {f['name']}"
                if term in txt.lower():
                    lb.insert(tk.END, txt)
        s.trace_add('write', lambda *a: feed())
        feed()
        mod_var = tk.IntVar(value=0)
        frm = ttk.Frame(picker)
        frm.pack(fill=tk.X, padx=6, pady=(0,6))
        ttk.Label(frm, text="Modifier:").pack(side=tk.LEFT)
        ttk.Entry(frm, textvariable=mod_var, width=8).pack(side=tk.LEFT, padx=(6,0))
        def add():
            sel = lb.curselection()
            if not sel:
                return
            sel_txt = lb.get(sel[0])
            assoc_id = int(sel_txt.split(':',1)[0])
            self.db_manager.execute_update(
                f"UPDATE faction_association SET id_{slot} = %s, mod_{slot} = %s WHERE id = %s",
                (assoc_id, int(mod_var.get()), int(faction_id))
            )
            # reload view
            self.load_faction_associations(int(faction_id))
            picker.destroy()
        ttk.Button(picker, text="Add", command=add).pack(pady=(0,8))
        e.focus_set()

    def remove_selected_association(self):
        """Remove currently selected association row (zero out its slot)."""
        faction_id = self.faction_id_var.get()
        if not faction_id:
            return
        sel = self.assoc_tree.selection()
        if not sel:
            return
        item = sel[0]
        slot = self.assoc_row_to_slot.get(item)
        if not slot:
            return
        try:
            self.db_manager.execute_update(
                f"UPDATE faction_association SET id_{slot} = 0, mod_{slot} = 0 WHERE id = %s",
                (int(faction_id),)
            )
            self.assoc_tree.delete(item)
            self.refresh_faction_information(faction_id)
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to remove association: {e}")

    def refresh_faction_information(self, faction_id=None):
        """Populate the faction information panel with relationship details."""
        if not hasattr(self, "faction_info_var"):
            return
        if faction_id is None:
            faction_id = self.faction_id_var.get()
        if not faction_id:
            self.faction_info_var.set("Select a faction to view information.")
            return
        try:
            fid = int(faction_id)
        except (TypeError, ValueError):
            self.faction_info_var.set("Select a faction to view information.")
            return
        try:
            groups = self.db_manager.execute_query(
                """
                SELECT COUNT(DISTINCT nf.id) AS cnt
                FROM npc_faction nf
                JOIN npc_faction_entries nfe ON nf.id = nfe.npc_faction_id
                WHERE nfe.faction_id = %s
                """,
                (fid,), fetch_all=False
            )
            group_cnt = groups['cnt'] if groups else 0

            npcs = self.db_manager.execute_query(
                """
                SELECT COUNT(DISTINCT nt.id) AS cnt
                FROM npc_types nt
                WHERE nt.npc_faction_id IN (
                    SELECT nfc.id
                    FROM npc_faction nfc
                    JOIN npc_faction_entries nfe ON nfc.id = nfe.npc_faction_id
                    WHERE nfe.faction_id = %s
                )
                """,
                (fid,), fetch_all=False
            )
            npc_cnt = npcs['cnt'] if npcs else 0

            assoc = self.db_manager.execute_query(
                "SELECT * FROM faction_association WHERE id = %s",
                (fid,), fetch_all=False
            )
            assoc_lines = []
            if assoc:
                for i in range(1, 6):
                    aid = assoc.get(f"id_{i}")
                    if aid and aid != 0:
                        nm = self.db_manager.execute_query(
                            "SELECT name FROM faction_list WHERE id = %s",
                            (aid,), fetch_all=False
                        )
                        assoc_lines.append(
                            f"Slot {i}: {aid} - {(nm['name'] if nm else 'Unknown')} (mod {assoc.get(f'mod_{i}', 0)})"
                        )
            info_lines = [
                f"Faction {fid} relationships:",
                f"- Groups containing this faction: {group_cnt}",
                f"- NPCs using those groups: {npc_cnt}",
                "- Associations:"
            ]
            if assoc_lines:
                info_lines.extend(f"  {line}" for line in assoc_lines)
            else:
                info_lines.append("  None")
            self.faction_info_var.set("\n".join(info_lines))
        except Exception as exc:
            self.faction_info_var.set(f"Could not load faction info: {exc}")

    def open_faction_guide(self):
        """Open a developer-focused guide with concrete, flow-style examples."""
        guide = tk.Toplevel(self.parent)
        guide.title("Faction System Guide")
        guide.geometry("800x680")
        guide.transient(self.parent)

        container = ttk.Frame(guide)
        container.pack(fill=tk.BOTH, expand=True)

        # Use a Text widget for better formatting and scrolling
        text = tk.Text(container, wrap=tk.WORD)
        try:
            # Apply dark theme text styling if available
            style = getattr(self, 'style', None)
            if style and hasattr(style, 'configure_text_widget'):
                style.configure_text_widget(text)
        except Exception:
            pass

        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        # Minimal scrollbar for large content
        sb = ttk.Scrollbar(container, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        # Load content from factionisdumb.MD at project root
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            md_path = os.path.join(project_root, "factionisdumb.MD")
            with open(md_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            # Fallback message if file missing/unreadable
            content = "Faction guide file not found (factionisdumb.MD)."

        text.insert("1.0", content)
        text.config(state=tk.DISABLED)
        ttk.Button(guide, text="Close", command=guide.destroy).pack(pady=(4,8))
    
    def load_faction_entries(self, npc_faction_id):
        """Load faction entries for a specific NPC faction group"""
        try:
            # Clear existing items
            for item in self.faction_entries_tree.get_children():
                self.faction_entries_tree.delete(item)
            
            # Load faction entries for this group
            query = """
                SELECT nfe.npc_faction_id, nfe.faction_id, fl.name as faction_name, 
                       nfe.value, nfe.npc_value, nfe.temp
                FROM npc_faction_entries nfe
                LEFT JOIN faction_list fl ON nfe.faction_id = fl.id
                WHERE nfe.npc_faction_id = %s
                ORDER BY nfe.faction_id
            """
            entries = self.db_manager.execute_query(query, (npc_faction_id,))
            
            for entry in entries:
                self.faction_entries_tree.insert("", "end", values=(
                    entry['npc_faction_id'],
                    entry['faction_id'],
                    entry['faction_name'] or 'Unknown',
                    entry['value'],
                    entry['npc_value'],
                    entry['temp']
                ))
                
        except Exception as e:
            print(f"Error loading faction entries: {e}")
    
    def load_faction_npcs(self, faction_id):
        """Load NPCs that use this faction"""
        try:
            # Prepare cache and clear existing items
            all_rows = []
            for item in self.npc_tree.get_children():
                self.npc_tree.delete(item)
            
            # Load NPCs with faction assignments - using same query structure as loot_tool plus faction name
            query = """
                SELECT DISTINCT nt.id, nt.name, nt.level, nt.race, nt.class, nt.bodytype, nt.hp, nt.mana,
                       nt.gender, nt.texture, nt.helmtexture, nt.size, nt.loottable_id, nt.npc_spells_id, nt.npc_faction_id,
                       nf.name as faction_group_name,
                       nt.mindmg, nt.maxdmg, nt.npcspecialattks, nt.special_abilities, nt.MR, nt.CR, nt.DR, nt.FR, nt.PR, nt.AC,
                       nt.attack_delay, nt.STR, nt.STA, nt.DEX, nt.AGI, nt._INT, nt.WIS,
                       nt.maxlevel, nt.skip_global_loot, nt.exp_mod
                FROM npc_types nt
                LEFT JOIN npc_faction nf ON nt.npc_faction_id = nf.id
                WHERE nt.npc_faction_id IN (
                    SELECT nfc.id 
                    FROM npc_faction nfc 
                    JOIN npc_faction_entries nfe ON nfc.id = nfe.npc_faction_id 
                    WHERE nfe.faction_id = %s
                )
                ORDER BY nt.name
                LIMIT 1000
            """
            npcs = self.db_manager.execute_query(query, (faction_id,))
            
            for npc in npcs:
                npc_values = [
                    npc.get('id'), npc.get('name'), npc.get('level'), npc.get('race'), npc.get('class'),
                    npc.get('bodytype'), npc.get('hp'), npc.get('mana'), npc.get('gender'), npc.get('texture'),
                    npc.get('helmtexture'), npc.get('size'), npc.get('loottable_id'), npc.get('npc_spells_id'),
                    npc.get('npc_faction_id'), npc.get('faction_group_name') or 'Unknown', npc.get('mindmg'), npc.get('maxdmg'),
                    npc.get('npcspecialattks'), npc.get('special_abilities'), npc.get('MR'), npc.get('CR'), 
                    npc.get('DR'), npc.get('FR'), npc.get('PR'), npc.get('AC'), npc.get('attack_delay'), 
                    npc.get('STR'), npc.get('STA'), npc.get('DEX'), npc.get('AGI'), npc.get('_INT'), 
                    npc.get('WIS'), npc.get('maxlevel'), npc.get('skip_global_loot'), npc.get('exp_mod')
                ]
                all_rows.append(tuple(npc_values))
            # Cache and (re)build tree respecting current filter
            self._npc_all_rows = all_rows
            self.filter_npcs()
                
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to load NPCs: {e}")
    
    def save_faction(self):
        """Save faction changes"""
        try:
            faction_id_raw = self.faction_id_var.get()
            name = (self.faction_name_var.get() or "").strip()
            base_raw = self.faction_base_var.get()
            
            if not faction_id_raw or not name:
                messagebox.showwarning("Invalid Data", "Faction ID and Name are required")
                return
            try:
                faction_id = int(faction_id_raw)
            except ValueError:
                messagebox.showerror("Invalid ID", "Faction ID must be a number.")
                return
            try:
                base = int(base_raw)
            except (TypeError, ValueError):
                messagebox.showerror("Invalid Base Value", "Base value must be a number.")
                return

            is_new_faction = faction_id not in self.factions

            npc_group_id_raw = (self.npc_faction_group_id_var.get() or "").strip()
            npc_group_name = (self.npc_faction_group_name_var.get() or "").strip()
            ignore_primary_assist = 1 if self.ignore_primary_assist_var.get() else 0

            npc_group_id = None
            sanitized_npc_group_name = ""
            if npc_group_id_raw or is_new_faction:
                if not npc_group_id_raw:
                    messagebox.showwarning(
                        "Missing NPC Group",
                        "NPC faction group ID is required for new factions."
                    )
                    return
                try:
                    npc_group_id = int(npc_group_id_raw)
                except ValueError:
                    messagebox.showerror("Invalid NPC Group ID", "NPC faction group ID must be a number.")
                    return
                sanitized_npc_group_name = self._sanitize_npc_group_name(npc_group_name)
                if not sanitized_npc_group_name:
                    messagebox.showwarning(
                        "Invalid NPC Group Name",
                        "NPC faction group name is required. Underscores are substituted for spaces automatically."
                    )
                    return
                if sanitized_npc_group_name != npc_group_name:
                    self._auto_updating_npc_group_name = True
                    try:
                        self.npc_faction_group_name_var.set(sanitized_npc_group_name)
                    finally:
                        self._auto_updating_npc_group_name = False
                npc_group_name = sanitized_npc_group_name
                self._npc_group_name_user_modified = bool(npc_group_name)
                self._last_autogenerated_npc_group_name = npc_group_name
           
            # Upsert faction_list
            self.db_manager.execute_update(
                """
                INSERT INTO faction_list (id, name, base)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE name = VALUES(name), base = VALUES(base)
                """,
                (faction_id, name, base)
            )
            
            # Update base data if exists
            min_val = self.min_value_var.get() or "-2000"
            max_val = self.max_value_var.get() or "2000"
            
            self.db_manager.execute_update(
                """
                INSERT INTO faction_base_data (client_faction_id, min, max)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE min = VALUES(min), max = VALUES(max)
                """,
                (faction_id, int(min_val), int(max_val))
            )

            if npc_group_id is not None:
                self.db_manager.execute_update(
                    """
                    INSERT INTO npc_faction (id, name, primaryfaction, ignore_primary_assist)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                        name = VALUES(name),
                        primaryfaction = VALUES(primaryfaction),
                        ignore_primary_assist = VALUES(ignore_primary_assist)
                    """,
                    (npc_group_id, npc_group_name, faction_id, ignore_primary_assist)
                )
                self.db_manager.execute_update(
                    """
                    INSERT INTO npc_faction_entries (npc_faction_id, faction_id, `value`, npc_value, temp)
                    VALUES (%s, %s, 0, 0, 0)
                    ON DUPLICATE KEY UPDATE 
                        `value` = VALUES(`value`),
                        npc_value = VALUES(npc_value),
                        temp = VALUES(temp)
                    """,
                    (npc_group_id, faction_id)
                )
            
            messagebox.showinfo("Success", "Faction saved successfully")
            self.load_factions()  # Refresh the list
            self._reselect_faction_in_tree(faction_id)
            self.load_faction_details(faction_id)
            self.load_faction_modifiers(faction_id)
            self.load_faction_base_data(faction_id)
            self.load_faction_associations(faction_id)
            self.load_faction_groups(faction_id)
            self.load_faction_npcs(faction_id)
            
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to save faction: {e}")
    
    def new_faction(self):
        """Create new faction"""
        # Auto-assign next available ID, allow override
        faction_id = self.find_next_available_faction_id()
        if faction_id is None:
            messagebox.showerror("Error", "Could not determine next available faction ID")
            return
        # Let user confirm or adjust
        faction_id = simpledialog.askinteger("New Faction", "Enter new faction ID:", initialvalue=faction_id)
        if not faction_id:
            return
        if faction_id in self.factions:
            messagebox.showwarning("ID Exists", "This faction ID already exists")
            return

        npc_group_id = self.find_next_available_npc_faction_id()
        if npc_group_id is None:
            messagebox.showerror("Error", "Could not determine next available NPC faction ID")
            return
        npc_group_id = simpledialog.askinteger(
            "New NPC Faction Group",
            "Enter new NPC faction group ID:",
            initialvalue=npc_group_id
        )
        if not npc_group_id:
            return
            
        self.faction_id_var.set(str(faction_id))
        self.faction_name_var.set("")
        self.faction_base_var.set("0")
        self.min_value_var.set("-2000")
        self.max_value_var.set("2000")
        self.npc_faction_group_id_var.set(str(npc_group_id))
        self._npc_group_name_user_modified = False
        self._last_autogenerated_npc_group_name = ""
        self.npc_faction_group_name_var.set("")
        self.ignore_primary_assist_var.set(0)
        self.refresh_faction_information(None)
        
        # Clear modifiers and NPCs
        for item in self.mod_tree.get_children():
            self.mod_tree.delete(item)
        for item in self.npc_tree.get_children():
            self.npc_tree.delete(item)

    def find_next_available_faction_id(self, start_id=1):
        """Find the smallest available faction_list.id >= start_id"""
        try:
            row = self.db_manager.execute_query(
                """
                SELECT MIN(t.id) AS next_id FROM (
                    SELECT %s AS id
                    UNION ALL
                    SELECT id + 1 FROM faction_list
                ) AS t
                LEFT JOIN faction_list f ON t.id = f.id
                WHERE t.id >= %s AND f.id IS NULL
                LIMIT 1
                """,
                (start_id, start_id),
                fetch_all=False,
            )
            return row['next_id'] if row and row.get('next_id') is not None else start_id
        except Exception:
            # Fallback: linear scan (safe if table not huge)
            existing = self.db_manager.execute_query("SELECT id FROM faction_list ORDER BY id")
            used = {r['id'] for r in existing}
            cur = start_id
            while cur in used:
                cur += 1
            return cur
    
    def find_next_available_npc_faction_id(self, start_id=1):
        """Find the next available npc_faction.id >= start_id (max + 1)."""
        try:
            row = self.db_manager.execute_query(
                "SELECT MAX(id) AS max_id FROM npc_faction",
                fetch_all=False,
            )
            if row and row.get('max_id') is not None:
                return max(row['max_id'] + 1, start_id)
            return start_id
        except Exception:
            existing = self.db_manager.execute_query("SELECT id FROM npc_faction ORDER BY id")
            ids = [r['id'] for r in existing]
            next_id = max(ids) + 1 if ids else start_id
            return next_id if next_id >= start_id else start_id
    
    def delete_faction(self):
        """Delete selected faction"""
        faction_id = self.faction_id_var.get()
        if not faction_id:
            messagebox.showwarning("No Selection", "No faction selected")
            return
        try:
            faction_id_int = int(faction_id)
        except ValueError:
            messagebox.showerror("Invalid ID", "Faction ID is not a valid number.")
            return
            
        if messagebox.askyesno("Confirm Delete", f"Delete faction {faction_id}? This will also delete all associated data."):
            try:
                # Delete direct rows
                self.db_manager.execute_update("DELETE FROM faction_list_mod WHERE faction_id = %s", (faction_id_int,))
                self.db_manager.execute_update("DELETE FROM faction_base_data WHERE client_faction_id = %s", (faction_id_int,))
                self.db_manager.execute_update("DELETE FROM npc_faction_entries WHERE faction_id = %s", (faction_id_int,))
                npc_groups = self.db_manager.execute_query(
                    "SELECT id FROM npc_faction WHERE primaryfaction = %s",
                    (faction_id_int,)
                )
                for group in npc_groups:
                    group_id = group.get('id')
                    if group_id is None:
                        continue
                    self.db_manager.execute_update(
                        "DELETE FROM npc_faction_entries WHERE npc_faction_id = %s",
                        (group_id,)
                    )
                    self.db_manager.execute_update(
                        "DELETE FROM npc_faction WHERE id = %s",
                        (group_id,)
                    )
                # Delete association row for this faction
                self.db_manager.execute_update("DELETE FROM faction_association WHERE id = %s", (faction_id_int,))
                # Scrub other associations referencing this faction (slots 1..5)
                for i in range(1, 6):
                    self.db_manager.execute_update(
                        f"UPDATE faction_association SET id_{i} = 0, mod_{i} = 0 WHERE id_{i} = %s",
                        (faction_id_int,)
                    )
                # Finally delete the faction
                self.db_manager.execute_update("DELETE FROM faction_list WHERE id = %s", (faction_id_int,))
                messagebox.showinfo("Success", "Faction deleted successfully")
                self.load_factions()
                
                # Clear form
                self.faction_id_var.set("")
                self.faction_name_var.set("")
                self.faction_base_var.set("")
                self.npc_faction_group_id_var.set("")
                self.npc_faction_group_name_var.set("")
                self.ignore_primary_assist_var.set(0)
                self._npc_group_name_user_modified = False
                self._last_autogenerated_npc_group_name = ""
                self.refresh_faction_information(None)
                
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to delete faction: {e}")
    
    def update_modifier(self, tree, item_id, column_index, new_value):
        """Update faction modifier in database"""
        try:
            faction_id = self.faction_id_var.get()
            if not faction_id:
                return
                
            values = tree.item(item_id, "values")
            mod_name = values[1]
            
            self.db_manager.execute_update(
                "UPDATE faction_list_mod SET mod = %s WHERE faction_id = %s AND mod_name = %s",
                (int(new_value), int(faction_id), mod_name)
            )
            
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to update modifier: {e}")

    def open_modifier_picker(self, kind):
        """Open a modal to pick a Race/Class/Deity to add as modifier with default 0."""
        faction_id = self.faction_id_var.get()
        if not faction_id:
            messagebox.showwarning("No Selection", "Select a faction first")
            return
        picker = tk.Toplevel(self.parent)
        picker.title(f"Add {kind.capitalize()} Modifier")
        picker.geometry("340x420")
        picker.transient(self.parent)
        picker.grab_set()
        ttk.Label(picker, text="Search:").pack(anchor='w', padx=6, pady=(6,2))
        search = tk.StringVar()
        entry = ttk.Entry(picker, textvariable=search)
        entry.pack(fill=tk.X, padx=6)
        listbox = tk.Listbox(picker)
        listbox.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        # Build options
        if kind == 'race':
            options = sorted(self.race_bitmask_display.items(), key=lambda x: x[1])
            items = [name for _, name in options if name != 'ALL']
        elif kind == 'class':
            options = sorted(self.class_bitmask_display.items(), key=lambda x: x[1])
            items = [name for _, name in options if name != 'ALL']
        else:  # deity
            items = list(self.sorted_deity_names)
        def refresh():
            term = search.get().lower()
            listbox.delete(0, tk.END)
            for name in items:
                if term in name.lower():
                    listbox.insert(tk.END, name)
        search.trace_add('write', lambda *a: refresh())
        refresh()
        def add_selected():
            sel = listbox.curselection()
            if not sel:
                return
            name = listbox.get(sel[0])
            try:
                # Insert if not exists
                self.db_manager.execute_update(
                    """
                    INSERT INTO faction_list_mod (faction_id, mod, mod_name)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE mod = mod
                    """,
                    (int(faction_id), 0, name)
                )
                # Refresh modifiers view
                self.load_faction_modifiers(int(faction_id))
                picker.destroy()
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to add modifier: {e}")
        ttk.Button(picker, text="Add", command=add_selected).pack(pady=(0,8))
        entry.focus_set()

    def remove_selected_modifier(self):
        """Remove the selected modifier row."""
        faction_id = self.faction_id_var.get()
        if not faction_id:
            return
        sel = self.mod_tree.selection()
        if not sel:
            return
        values = self.mod_tree.item(sel[0], 'values')
        mod_name = values[1]
        try:
            self.db_manager.execute_update(
                "DELETE FROM faction_list_mod WHERE faction_id = %s AND mod_name = %s",
                (int(faction_id), mod_name)
            )
            self.mod_tree.delete(sel[0])
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to remove modifier: {e}")

    def open_bitmask_lookup(self):
        """Helper dialog to compute bitmasks for Race/Class/Deity selections."""
        dlg = tk.Toplevel(self.parent)
        dlg.title("Bitmask Lookup")
        dlg.geometry("420x480")
        dlg.transient(self.parent)
        dlg.grab_set()
        nb = ttk.Notebook(dlg)
        nb.pack(fill=tk.BOTH, expand=True)
        frames = {}
        for tab in ('Race','Class','Deity'):
            f = ttk.Frame(nb)
            nb.add(f, text=tab)
            frames[tab] = f
        # Race
        race_vars = []
        race_frame = frames['Race']
        for val,name in sorted(self.race_bitmask_display.items()):
            if name=='ALL':
                continue
            v=tk.IntVar()
            chk=ttk.Checkbutton(race_frame,text=f"{name} ({val})",variable=v)
            chk.pack(anchor='w')
            race_vars.append((v,val))
        # Class
        class_vars=[]
        class_frame = frames['Class']
        for val,name in sorted(self.class_bitmask_display.items()):
            if name=='ALL':
                continue
            v=tk.IntVar()
            chk=ttk.Checkbutton(class_frame,text=f"{name} ({val})",variable=v)
            chk.pack(anchor='w')
            class_vars.append((v,val))
        # Deity (use names only; show bit values)
        deity_vars=[]
        deity_frame = frames['Deity']
        for name,val in sorted(self.deity_name_to_bit.items(), key=lambda x:x[0]):
            v=tk.IntVar()
            chk=ttk.Checkbutton(deity_frame,text=f"{name} ({val})",variable=v)
            chk.pack(anchor='w')
            deity_vars.append((v,val))
        # Output
        out = tk.StringVar(value="Race=0, Class=0, Deity=0")
        ttk.Label(dlg,textvariable=out).pack(pady=6)
        def compute():
            rv=sum(val for v,val in race_vars if v.get())
            cv=sum(val for v,val in class_vars if v.get())
            dv=sum(val for v,val in deity_vars if v.get())
            out.set(f"Race={rv}, Class={cv}, Deity={dv}")
        ttk.Button(dlg,text="Compute",command=compute).pack(pady=(0,8))
    
    def update_npc_faction(self, tree, item_id, column_index, new_value):
        """Update NPC faction assignment"""
        try:
            values = tree.item(item_id, "values")
            npc_id = values[0]
            
            cursor = self.db_manager.get_cursor()
            query = "UPDATE npc_types SET npc_faction_id = %s WHERE id = %s"
            cursor.execute(query, (new_value, npc_id))
            self.conn.commit()
            
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to update NPC faction: {e}")
    
    def update_association(self, tree, item_id, column_index, new_value):
        """Update faction association"""
        try:
            current_faction_id = self.faction_id_var.get()
            if not current_faction_id:
                return
                
            values = tree.item(item_id, "values")
            # Determine slot for this row
            slot = None
            if hasattr(self, 'assoc_row_to_slot'):
                slot = self.assoc_row_to_slot.get(item_id)
            if not slot:
                # Fallback: try to locate slot by current values
                slot = 1
            
            if column_index == 0:  # Associated Faction ID changed
                # Update id_slot to new_value
                field = f"id_{slot}"
                self.db_manager.execute_update(
                    f"UPDATE faction_association SET {field} = %s WHERE id = %s",
                    (int(new_value), int(current_faction_id))
                )
                # Also update the displayed faction name
                name_row = self.db_manager.execute_query("SELECT name FROM faction_list WHERE id = %s", (int(new_value),), fetch_all=False)
                new_name = name_row['name'] if name_row else 'Unknown'
                updated = list(values)
                updated[1] = new_name
                tree.item(item_id, values=updated)
            elif column_index == 2:  # Modifier changed
                field = f"mod_{slot}"
                self.db_manager.execute_update(
                    f"UPDATE faction_association SET {field} = %s WHERE id = %s",
                    (int(new_value), int(current_faction_id))
                )
            
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to update association: {e}")
    
    def refresh_npcs(self):
        """Refresh NPC list"""
        faction_id = self.faction_id_var.get()
        if faction_id:
            self.load_faction_npcs(int(faction_id))
    
    def show_all_npcs(self):
        """Show all NPCs regardless of faction"""
        try:
            # Prepare cache and clear existing items
            all_rows = []
            for item in self.npc_tree.get_children():
                self.npc_tree.delete(item)
            
            query = """
                SELECT DISTINCT nt.id, nt.name, nt.level, nt.race, nt.class, nt.bodytype, nt.hp, nt.mana,
                       nt.gender, nt.texture, nt.helmtexture, nt.size, nt.loottable_id, nt.npc_spells_id, nt.npc_faction_id,
                       nf.name as faction_group_name,
                       nt.mindmg, nt.maxdmg, nt.npcspecialattks, nt.special_abilities, nt.MR, nt.CR, nt.DR, nt.FR, nt.PR, nt.AC,
                       nt.attack_delay, nt.STR, nt.STA, nt.DEX, nt.AGI, nt._INT, nt.WIS,
                       nt.maxlevel, nt.skip_global_loot, nt.exp_mod
                FROM npc_types nt
                LEFT JOIN npc_faction nf ON nt.npc_faction_id = nf.id
                WHERE nt.npc_faction_id IS NOT NULL AND nt.npc_faction_id != 0
                ORDER BY nt.name
                LIMIT 1000
            """
            npcs = self.db_manager.execute_query(query)
            
            for npc in npcs:
                npc_values = [
                    npc.get('id'), npc.get('name'), npc.get('level'), npc.get('race'), npc.get('class'),
                    npc.get('bodytype'), npc.get('hp'), npc.get('mana'), npc.get('gender'), npc.get('texture'),
                    npc.get('helmtexture'), npc.get('size'), npc.get('loottable_id'), npc.get('npc_spells_id'),
                    npc.get('npc_faction_id'), npc.get('faction_group_name') or 'Unknown', npc.get('mindmg'), npc.get('maxdmg'),
                    npc.get('npcspecialattks'), npc.get('special_abilities'), npc.get('MR'), npc.get('CR'), 
                    npc.get('DR'), npc.get('FR'), npc.get('PR'), npc.get('AC'), npc.get('attack_delay'), 
                    npc.get('STR'), npc.get('STA'), npc.get('DEX'), npc.get('AGI'), npc.get('_INT'), 
                    npc.get('WIS'), npc.get('maxlevel'), npc.get('skip_global_loot'), npc.get('exp_mod')
                ]
                all_rows.append(tuple(npc_values))
            # Cache and show according to current filter (or all if empty)
            self._npc_all_rows = all_rows
            # Clear placeholder to display all if it's currently shown
            if hasattr(self, 'npc_search_entry') and hasattr(self, 'npc_search_placeholder'):
                if self.npc_search_entry.get() == self.npc_search_placeholder:
                    self.npc_search_var.set("")
            self.filter_npcs()
                
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to load NPCs: {e}")
    
    def _rebuild_npc_tree(self, rows):
        """Clear and rebuild the NPC tree with provided rows."""
        # Clear existing items
        for item in self.npc_tree.get_children():
            self.npc_tree.delete(item)
        # Insert rows
        for vals in rows:
            self.npc_tree.insert("", "end", values=vals)

    def _sanitize_npc_group_name(self, name: str) -> str:
        """Convert arbitrary faction names into npc_faction-safe identifiers."""
        sanitized = (name or "").strip().replace(" ", "_")
        sanitized = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in sanitized)
        while "__" in sanitized:
            sanitized = sanitized.replace("__", "_")
        return sanitized

    def _handle_faction_name_change(self, *args):
        """Auto-sync NPC faction group name from faction name when not overridden."""
        if self._npc_group_name_user_modified:
            return
        sanitized = self._sanitize_npc_group_name(self.faction_name_var.get())
        self._auto_updating_npc_group_name = True
        try:
            self.npc_faction_group_name_var.set(sanitized)
        finally:
            self._auto_updating_npc_group_name = False
        self._last_autogenerated_npc_group_name = sanitized

    def _handle_npc_group_name_change(self, *args):
        """Ensure NPC faction group name stays sanitized and track user overrides."""
        if self._auto_updating_npc_group_name:
            return
        current = self.npc_faction_group_name_var.get()
        sanitized = self._sanitize_npc_group_name(current)
        if sanitized != current:
            self._auto_updating_npc_group_name = True
            try:
                self.npc_faction_group_name_var.set(sanitized)
            finally:
                self._auto_updating_npc_group_name = False
            current = sanitized
        self._npc_group_name_user_modified = bool(current)
        if not current:
            self._last_autogenerated_npc_group_name = ""

    def _reselect_faction_in_tree(self, faction_id):
        """Helper to reselect a faction in the treeview after saving."""
        if not hasattr(self, 'faction_tree'):
            return
        faction_id_str = str(faction_id)
        for item in self.faction_tree.get_children():
            if self.faction_tree.set(item, "id") == faction_id_str:
                self.faction_tree.selection_set(item)
                self.faction_tree.see(item)
                break

    def filter_npcs(self, *args):
        """Filter NPC list based on search term (rebuild from cached rows)."""
        if not hasattr(self, '_npc_all_rows'):
            return
        term = ""
        if hasattr(self, 'npc_search_var') and self.npc_search_var.get() is not None:
            term = self.npc_search_var.get().strip().lower()
        # Ignore placeholder
        if hasattr(self, 'npc_search_placeholder') and term == self.npc_search_placeholder.lower():
            term = ""
        if not term:
            self._rebuild_npc_tree(self._npc_all_rows)
            return
        # Filter by name contains
        filtered = [row for row in self._npc_all_rows if len(row) > 1 and term in str(row[1]).lower()]
        self._rebuild_npc_tree(filtered)
