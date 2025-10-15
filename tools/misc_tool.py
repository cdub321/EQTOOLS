import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.theme import set_dark_theme


class _TreeviewScrollMixin:
    """Provide invisible scrollbar behaviour for scrollable widgets."""

    @staticmethod
    def _make_treeview_invisible_scroll(tree):
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

class MiscManagerTool(_TreeviewScrollMixin):
    """Miscellaneous Manager Tool - fishing, foraging, and level experience modifiers"""
    
    def __init__(self, parent_frame, db_manager):
        self.parent = parent_frame
        self.db_manager = db_manager
        self.conn = db_manager.connect()
        self.cursor = db_manager.get_cursor()
        
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
            self.load_fishing_data()
            self.load_forage_data()
            self.load_exp_mods_data()
            print("Misc tool initialized successfully")
        except Exception as e:
            print(f"Warning: Could not initialize misc tool data: {e}")
    
    def create_ui(self):
        """Create the complete Misc Manager UI"""
        # Configure main frame grid for three columns
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)  # Level EXP Mods (left)
        self.main_frame.grid_columnconfigure(1, weight=2)  # Fishing (center)
        self.main_frame.grid_columnconfigure(2, weight=2)  # Foraging (right)
        
        # Create the three panels
        self.create_exp_mods_panel()
        self.create_fishing_panel()
        self.create_forage_panel()
    
    def create_fishing_panel(self):
        """Create fishing management panel (center column)"""
        # Create fishing frame
        fishing_frame = ttk.LabelFrame(self.main_frame, text="Fishing", padding="5")
        fishing_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        fishing_frame.grid_rowconfigure(1, weight=1)
        fishing_frame.grid_columnconfigure(0, weight=1)
        
        # Search and controls frame
        controls_frame = ttk.Frame(fishing_frame)
        controls_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        controls_frame.grid_columnconfigure(1, weight=1)
        
        # Search controls
        ttk.Label(controls_frame, text="Search:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.fishing_search_var = tk.StringVar()
        self.fishing_search_entry = ttk.Entry(controls_frame, textvariable=self.fishing_search_var, width=20)
        self.fishing_search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        self.fishing_search_var.trace("w", self.filter_fishing)
        
        # Buttons
        button_frame = ttk.Frame(controls_frame)
        button_frame.grid(row=0, column=2, sticky="e")
        
        ttk.Button(button_frame, text="Add", command=self.add_fishing_entry, width=8).grid(row=0, column=0, padx=(0, 2))
        ttk.Button(button_frame, text="Delete", command=self.delete_fishing_entry, width=8).grid(row=0, column=1, padx=(0, 2))
        ttk.Button(button_frame, text="Refresh", command=self.load_fishing_data, width=8).grid(row=0, column=2)
        
        # Fishing treeview
        fishing_columns = ("id", "zoneid", "itemid", "item_name", "skill_level", "chance", 
                          "npc_id", "npc_chance", "min_expansion", "max_expansion")
        
        self.fishing_tree = ttk.Treeview(fishing_frame, columns=fishing_columns, show="headings")
        self._make_treeview_invisible_scroll(self.fishing_tree)
        
        # Set up fishing columns with smaller widths
        column_widths = {
            "id": 40, "zoneid": 50, "itemid": 50, "item_name": 150, "skill_level": 60,
            "chance": 50, "npc_id": 50, "npc_chance": 60, "min_expansion": 70, "max_expansion": 70
        }
        
        for col in fishing_columns:
            self.fishing_tree.heading(col, text=col.replace("_", " ").title())
            self.fishing_tree.column(col, width=column_widths.get(col, 60), minwidth=30)
        
        # Place treeview directly in fishing_frame
        self.fishing_tree.grid(row=1, column=0, sticky="nsew")
        
        # Fishing editing - bind double-click event
        self.fishing_tree.bind("<Double-1>", self.on_fishing_edit)
    
    def create_forage_panel(self):
        """Create foraging management panel (right column)"""
        # Create forage frame
        forage_frame = ttk.LabelFrame(self.main_frame, text="Foraging", padding="5")
        forage_frame.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)
        
        forage_frame.grid_rowconfigure(1, weight=1)
        forage_frame.grid_columnconfigure(0, weight=1)
        
        # Search and controls frame
        controls_frame = ttk.Frame(forage_frame)
        controls_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        controls_frame.grid_columnconfigure(1, weight=1)
        
        # Search controls
        ttk.Label(controls_frame, text="Search:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.forage_search_var = tk.StringVar()
        self.forage_search_entry = ttk.Entry(controls_frame, textvariable=self.forage_search_var, width=20)
        self.forage_search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        self.forage_search_var.trace("w", self.filter_forage)
        
        # Buttons
        button_frame = ttk.Frame(controls_frame)
        button_frame.grid(row=0, column=2, sticky="e")
        
        ttk.Button(button_frame, text="Add", command=self.add_forage_entry, width=8).grid(row=0, column=0, padx=(0, 2))
        ttk.Button(button_frame, text="Delete", command=self.delete_forage_entry, width=8).grid(row=0, column=1, padx=(0, 2))
        ttk.Button(button_frame, text="Refresh", command=self.load_forage_data, width=8).grid(row=0, column=2)
        
        # Forage treeview
        forage_columns = ("id", "zoneid", "itemid", "item_name", "level", "chance", 
                         "min_expansion", "max_expansion")
        
        self.forage_tree = ttk.Treeview(forage_frame, columns=forage_columns, show="headings")
        self._make_treeview_invisible_scroll(self.forage_tree)
        
        # Set up forage columns with smaller widths
        column_widths = {
            "id": 40, "zoneid": 50, "itemid": 50, "item_name": 150, "level": 40,
            "chance": 50, "min_expansion": 70, "max_expansion": 70
        }
        
        for col in forage_columns:
            self.forage_tree.heading(col, text=col.replace("_", " ").title())
            self.forage_tree.column(col, width=column_widths.get(col, 60), minwidth=30)
        
        # Place treeview directly in forage_frame
        self.forage_tree.grid(row=1, column=0, sticky="nsew")
        
        # Forage editing - bind double-click event
        self.forage_tree.bind("<Double-1>", self.on_forage_edit)
    
    def create_exp_mods_panel(self):
        """Create level experience modifiers panel (left column)"""
        # Create exp mods frame
        exp_frame = ttk.LabelFrame(self.main_frame, text="Level EXP Modifiers", padding="5")
        exp_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        exp_frame.grid_rowconfigure(2, weight=1)
        exp_frame.grid_columnconfigure(0, weight=1)
        
        # Level range controls
        range_frame = ttk.Frame(exp_frame)
        range_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        ttk.Label(range_frame, text="From:").grid(row=0, column=0, sticky="w")
        self.level_from_var = tk.StringVar(value="1")
        level_from_entry = ttk.Entry(range_frame, textvariable=self.level_from_var, width=5)
        level_from_entry.grid(row=0, column=1, padx=(5, 10))
        
        ttk.Label(range_frame, text="To:").grid(row=0, column=2, sticky="w")
        self.level_to_var = tk.StringVar(value="100")
        level_to_entry = ttk.Entry(range_frame, textvariable=self.level_to_var, width=5)
        level_to_entry.grid(row=0, column=3, padx=(5, 10))
        
        ttk.Button(range_frame, text="Filter", command=self.filter_exp_mods, width=8).grid(row=0, column=4)
        
        # Buttons frame
        button_frame = ttk.Frame(exp_frame)
        button_frame.grid(row=1, column=0, sticky="ew", pady=(0, 5))
        
        ttk.Button(button_frame, text="Add Level", command=self.add_exp_mod_entry, width=12).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(button_frame, text="Delete Level", command=self.delete_exp_mod_entry, width=12).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(button_frame, text="Refresh", command=self.load_exp_mods_data, width=12).grid(row=0, column=2)
        
        # Experience modifiers treeview - skinny design
        exp_columns = ("level", "exp_mod", "aa_exp_mod")
        
        self.exp_tree = ttk.Treeview(exp_frame, columns=exp_columns, show="headings")
        self._make_treeview_invisible_scroll(self.exp_tree)
        
        # Set up exp columns - narrow widths for left panel
        column_widths = {"level": 40, "exp_mod": 60, "aa_exp_mod": 70}
        
        for col in exp_columns:
            self.exp_tree.heading(col, text=col.replace("_", " ").title())
            self.exp_tree.column(col, width=column_widths.get(col, 70), minwidth=50)
        
        # Place treeview directly in exp_frame
        self.exp_tree.grid(row=2, column=0, sticky="nsew")
        
        # Exp editing - bind double-click event
        self.exp_tree.bind("<Double-1>", self.on_exp_mod_edit)
    
    # Data loading methods
    def load_fishing_data(self):
        """Load fishing data from database"""
        try:
            query = """
            SELECT f.id, f.zoneid, f.Itemid, COALESCE(i.Name, 'Unknown Item') as item_name, f.skill_level, f.chance,
                   f.npc_id, f.npc_chance, f.min_expansion, f.max_expansion
            FROM fishing f
            LEFT JOIN items i ON f.Itemid = i.id
            ORDER BY f.zoneid, f.skill_level, f.chance DESC
            """
            
            results = self.db_manager.execute_query(query)
            
            # Clear existing data
            for item in self.fishing_tree.get_children():
                self.fishing_tree.delete(item)
            
            # Add fishing entries
            for row in results:
                self.fishing_tree.insert("", tk.END, values=(
                    row['id'], row['zoneid'], row['Itemid'], 
                    row['item_name'] or f"Item {row['Itemid']}", 
                    row['skill_level'], row['chance'], row['npc_id'], 
                    row['npc_chance'], row['min_expansion'], row['max_expansion']
                ))
            
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to load fishing data: {e}")
    
    def load_forage_data(self):
        """Load foraging data from database"""
        try:
            query = """
            SELECT f.id, f.zoneid, f.Itemid, COALESCE(i.Name, 'Unknown Item') as item_name, f.level, f.chance,
                   f.min_expansion, f.max_expansion
            FROM forage f
            LEFT JOIN items i ON f.Itemid = i.id
            ORDER BY f.zoneid, f.level, f.chance DESC
            """
            
            results = self.db_manager.execute_query(query)
            
            # Clear existing data
            for item in self.forage_tree.get_children():
                self.forage_tree.delete(item)
            
            # Add forage entries
            for row in results:
                self.forage_tree.insert("", tk.END, values=(
                    row['id'], row['zoneid'], row['Itemid'], 
                    row['item_name'] or f"Item {row['Itemid']}", 
                    row['level'], row['chance'], row['min_expansion'], row['max_expansion']
                ))
            
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to load foraging data: {e}")
    
    def load_exp_mods_data(self):
        """Load level experience modifiers from database"""
        try:
            query = "SELECT level, exp_mod, aa_exp_mod FROM level_exp_mods ORDER BY level"
            results = self.db_manager.execute_query(query)
            
            # Clear existing data
            for item in self.exp_tree.get_children():
                self.exp_tree.delete(item)
            
            # Add exp mod entries
            for row in results:
                self.exp_tree.insert("", tk.END, values=(
                    row['level'], row['exp_mod'] or 1.0, row['aa_exp_mod'] or 1.0
                ))
            
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to load experience modifiers: {e}")
    
    # Filter methods
    def filter_fishing(self, *args):
        """Filter fishing entries based on search term"""
        search_term = self.fishing_search_var.get().lower()
        if not search_term:
            self.load_fishing_data()
            return
        
        try:
            query = """
            SELECT f.id, f.zoneid, f.Itemid, COALESCE(i.Name, 'Unknown Item') as item_name, f.skill_level, f.chance,
                   f.npc_id, f.npc_chance, f.min_expansion, f.max_expansion
            FROM fishing f
            LEFT JOIN items i ON f.Itemid = i.id
            WHERE LOWER(i.Name) LIKE ? OR f.zoneid = ? OR f.Itemid = ?
            ORDER BY f.zoneid, f.skill_level, f.chance DESC
            """
            
            # Try to parse search term as number for zone/item ID searches
            try:
                search_num = int(search_term)
                results = self.db_manager.execute_query(query, (f'%{search_term}%', search_num, search_num))
            except ValueError:
                results = self.db_manager.execute_query(query, (f'%{search_term}%', -1, -1))
            
            # Clear and repopulate
            for item in self.fishing_tree.get_children():
                self.fishing_tree.delete(item)
            
            for row in results:
                self.fishing_tree.insert("", tk.END, values=(
                    row['id'], row['zoneid'], row['Itemid'], 
                    row['item_name'] or f"Item {row['Itemid']}", 
                    row['skill_level'], row['chance'], row['npc_id'], 
                    row['npc_chance'], row['min_expansion'], row['max_expansion']
                ))
            
        except Exception as e:
            print(f"Error filtering fishing data: {e}")
    
    def filter_forage(self, *args):
        """Filter forage entries based on search term"""
        search_term = self.forage_search_var.get().lower()
        if not search_term:
            self.load_forage_data()
            return
        
        try:
            query = """
            SELECT f.id, f.zoneid, f.Itemid, COALESCE(i.Name, 'Unknown Item') as item_name, f.level, f.chance,
                   f.min_expansion, f.max_expansion
            FROM forage f
            LEFT JOIN items i ON f.Itemid = i.id
            WHERE LOWER(i.Name) LIKE ? OR f.zoneid = ? OR f.Itemid = ?
            ORDER BY f.zoneid, f.level, f.chance DESC
            """
            
            # Try to parse search term as number for zone/item ID searches
            try:
                search_num = int(search_term)
                results = self.db_manager.execute_query(query, (f'%{search_term}%', search_num, search_num))
            except ValueError:
                results = self.db_manager.execute_query(query, (f'%{search_term}%', -1, -1))
            
            # Clear and repopulate
            for item in self.forage_tree.get_children():
                self.forage_tree.delete(item)
            
            for row in results:
                self.forage_tree.insert("", tk.END, values=(
                    row['id'], row['zoneid'], row['Itemid'], 
                    row['item_name'] or f"Item {row['Itemid']}", 
                    row['level'], row['chance'], row['min_expansion'], row['max_expansion']
                ))
            
        except Exception as e:
            print(f"Error filtering forage data: {e}")
    
    def filter_exp_mods(self):
        """Filter experience modifiers by level range"""
        try:
            level_from = int(self.level_from_var.get())
            level_to = int(self.level_to_var.get())
            
            query = """
            SELECT level, exp_mod, aa_exp_mod 
            FROM level_exp_mods 
            WHERE level BETWEEN ? AND ? 
            ORDER BY level
            """
            
            results = self.db_manager.execute_query(query, (level_from, level_to))
            
            # Clear and repopulate
            for item in self.exp_tree.get_children():
                self.exp_tree.delete(item)
            
            for row in results:
                self.exp_tree.insert("", tk.END, values=(
                    row['level'], row['exp_mod'] or 1.0, row['aa_exp_mod'] or 1.0
                ))
            
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid level numbers.")
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to filter experience modifiers: {e}")
    
    # Edit methods for treeview editing (following loot_tool pattern)
    def on_fishing_edit(self, event):
        """Handle fishing entry editing"""
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
        
        # Only allow editing certain columns (not id or item_name)
        editable_columns = [1, 2, 4, 5, 6, 7, 8, 9]  # zoneid, itemid, skill_level, chance, npc_id, npc_chance, min_expansion, max_expansion
        if column_index not in editable_columns:
            return
        
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
            
            # Get the fishing ID from the first column
            fishing_id = item_values[0]
            
            try:
                # Map column index to database field
                field_map = {1: "zoneid", 2: "Itemid", 4: "skill_level", 5: "chance", 
                            6: "npc_id", 7: "npc_chance", 8: "min_expansion", 9: "max_expansion"}
                
                if column_index in field_map:
                    field_name = field_map[column_index]
                    
                    # Update database
                    update_query = f"UPDATE fishing SET {field_name} = %s WHERE id = %s"
                    self.db_manager.execute_update(update_query, (new_value, fishing_id))
                    
                    # Update treeview
                    item_values[column_index] = new_value
                    tree.item(item, values=item_values)
                    
                    messagebox.showinfo("Success", f"Updated fishing entry {field_name}")
                    
                    # Reload to refresh item names if item ID changed
                    if field_name == "Itemid":
                        self.load_fishing_data()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update fishing entry: {e}")
            
            entry.destroy()
        
        def cancel_edit(event=None):
            entry.destroy()
        
        entry.bind("<Return>", save_edit)
        entry.bind("<Escape>", cancel_edit)
        entry.bind("<FocusOut>", save_edit)
    
    def on_forage_edit(self, event):
        """Handle forage entry editing"""
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
        
        # Only allow editing certain columns (not id or item_name)
        editable_columns = [1, 2, 4, 5, 6, 7]  # zoneid, itemid, level, chance, min_expansion, max_expansion
        if column_index not in editable_columns:
            return
        
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
            
            # Get the forage ID from the first column
            forage_id = item_values[0]
            
            try:
                # Map column index to database field
                field_map = {1: "zoneid", 2: "Itemid", 4: "level", 5: "chance", 
                            6: "min_expansion", 7: "max_expansion"}
                
                if column_index in field_map:
                    field_name = field_map[column_index]
                    
                    # Update database
                    update_query = f"UPDATE forage SET {field_name} = %s WHERE id = %s"
                    self.db_manager.execute_update(update_query, (new_value, forage_id))
                    
                    # Update treeview
                    item_values[column_index] = new_value
                    tree.item(item, values=item_values)
                    
                    messagebox.showinfo("Success", f"Updated forage entry {field_name}")
                    
                    # Reload to refresh item names if item ID changed
                    if field_name == "Itemid":
                        self.load_forage_data()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update forage entry: {e}")
            
            entry.destroy()
        
        def cancel_edit(event=None):
            entry.destroy()
        
        entry.bind("<Return>", save_edit)
        entry.bind("<Escape>", cancel_edit)
        entry.bind("<FocusOut>", save_edit)
    
    def on_exp_mod_edit(self, event):
        """Handle experience modifier editing"""
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
        
        # Only allow editing modifier columns
        editable_columns = [1, 2]  # exp_mod, aa_exp_mod
        if column_index not in editable_columns:
            return
        
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
            
            # Get the level from the first column
            level = item_values[0]
            
            try:
                # Map column index to database field
                field_map = {1: "exp_mod", 2: "aa_exp_mod"}
                
                if column_index in field_map:
                    field_name = field_map[column_index]
                    
                    # Update database
                    update_query = f"UPDATE level_exp_mods SET {field_name} = %s WHERE level = %s"
                    self.db_manager.execute_update(update_query, (new_value, level))
                    
                    # Update treeview
                    item_values[column_index] = new_value
                    tree.item(item, values=item_values)
                    
                    messagebox.showinfo("Success", f"Updated level {level} {field_name}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update experience modifier: {e}")
            
            entry.destroy()
        
        def cancel_edit(event=None):
            entry.destroy()
        
        entry.bind("<Return>", save_edit)
        entry.bind("<Escape>", cancel_edit)
        entry.bind("<FocusOut>", save_edit)
    
    # Add/Delete methods
    def add_fishing_entry(self):
        """Add new fishing entry"""
        dialog = FishingEntryDialog(self.parent, "Add Fishing Entry")
        if dialog.result:
            try:
                query = """
                INSERT INTO fishing (zoneid, Itemid, skill_level, chance, npc_id, npc_chance, 
                                   min_expansion, max_expansion) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                if self.db_manager.execute_update(query, dialog.result):
                    messagebox.showinfo("Success", "Fishing entry added successfully")
                    self.load_fishing_data()
                else:
                    messagebox.showerror("Error", "Failed to add fishing entry")
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to add fishing entry: {e}")
    
    def delete_fishing_entry(self):
        """Delete selected fishing entry"""
        selection = self.fishing_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a fishing entry to delete")
            return
        
        item = selection[0]
        values = self.fishing_tree.item(item, "values")
        entry_id = values[0]
        
        if messagebox.askyesno("Confirm Delete", f"Delete fishing entry ID {entry_id}?"):
            try:
                if self.db_manager.execute_update("DELETE FROM fishing WHERE id = ?", (entry_id,)):
                    messagebox.showinfo("Success", "Fishing entry deleted successfully")
                    self.load_fishing_data()
                else:
                    messagebox.showerror("Error", "Failed to delete fishing entry")
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to delete fishing entry: {e}")
    
    def add_forage_entry(self):
        """Add new forage entry"""
        dialog = ForageEntryDialog(self.parent, "Add Forage Entry")
        if dialog.result:
            try:
                query = """
                INSERT INTO forage (zoneid, Itemid, level, chance, min_expansion, max_expansion) 
                VALUES (?, ?, ?, ?, ?, ?)
                """
                
                if self.db_manager.execute_update(query, dialog.result):
                    messagebox.showinfo("Success", "Forage entry added successfully")
                    self.load_forage_data()
                else:
                    messagebox.showerror("Error", "Failed to add forage entry")
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to add forage entry: {e}")
    
    def delete_forage_entry(self):
        """Delete selected forage entry"""
        selection = self.forage_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a forage entry to delete")
            return
        
        item = selection[0]
        values = self.forage_tree.item(item, "values")
        entry_id = values[0]
        
        if messagebox.askyesno("Confirm Delete", f"Delete forage entry ID {entry_id}?"):
            try:
                if self.db_manager.execute_update("DELETE FROM forage WHERE id = ?", (entry_id,)):
                    messagebox.showinfo("Success", "Forage entry deleted successfully")
                    self.load_forage_data()
                else:
                    messagebox.showerror("Error", "Failed to delete forage entry")
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to delete forage entry: {e}")
    
    def add_exp_mod_entry(self):
        """Add new experience modifier entry"""
        level = simpledialog.askinteger("Add Level", "Enter level (1-255):", minvalue=1, maxvalue=255)
        if level is not None:
            try:
                query = "INSERT INTO level_exp_mods (level, exp_mod, aa_exp_mod) VALUES (?, 1.0, 1.0)"
                if self.db_manager.execute_update(query, (level,)):
                    messagebox.showinfo("Success", f"Level {level} added successfully")
                    self.load_exp_mods_data()
                else:
                    messagebox.showerror("Error", "Failed to add level entry")
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to add level entry: {e}")
    
    def delete_exp_mod_entry(self):
        """Delete selected experience modifier entry"""
        selection = self.exp_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a level to delete")
            return
        
        item = selection[0]
        values = self.exp_tree.item(item, "values")
        level = values[0]
        
        if messagebox.askyesno("Confirm Delete", f"Delete level {level} experience modifiers?"):
            try:
                if self.db_manager.execute_update("DELETE FROM level_exp_mods WHERE level = ?", (level,)):
                    messagebox.showinfo("Success", "Level entry deleted successfully")
                    self.load_exp_mods_data()
                else:
                    messagebox.showerror("Error", "Failed to delete level entry")
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to delete level entry: {e}")

# Dialog classes for adding new entries
class FishingEntryDialog:
    """Dialog for adding new fishing entries"""
    def __init__(self, parent, title):
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x300")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        self.create_widgets()
        
        # Wait for dialog to close
        self.dialog.wait_window()
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Entry fields
        ttk.Label(main_frame, text="Zone ID:").grid(row=0, column=0, sticky="w", pady=2)
        self.zoneid_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.zoneid_var).grid(row=0, column=1, sticky="ew", padx=(5, 0), pady=2)
        
        ttk.Label(main_frame, text="Item ID:").grid(row=1, column=0, sticky="w", pady=2)
        self.itemid_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.itemid_var).grid(row=1, column=1, sticky="ew", padx=(5, 0), pady=2)
        
        ttk.Label(main_frame, text="Skill Level:").grid(row=2, column=0, sticky="w", pady=2)
        self.skill_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.skill_var).grid(row=2, column=1, sticky="ew", padx=(5, 0), pady=2)
        
        ttk.Label(main_frame, text="Chance:").grid(row=3, column=0, sticky="w", pady=2)
        self.chance_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.chance_var).grid(row=3, column=1, sticky="ew", padx=(5, 0), pady=2)
        
        ttk.Label(main_frame, text="NPC ID (0 for none):").grid(row=4, column=0, sticky="w", pady=2)
        self.npcid_var = tk.StringVar(value="0")
        ttk.Entry(main_frame, textvariable=self.npcid_var).grid(row=4, column=1, sticky="ew", padx=(5, 0), pady=2)
        
        ttk.Label(main_frame, text="NPC Chance:").grid(row=5, column=0, sticky="w", pady=2)
        self.npc_chance_var = tk.StringVar(value="0")
        ttk.Entry(main_frame, textvariable=self.npc_chance_var).grid(row=5, column=1, sticky="ew", padx=(5, 0), pady=2)
        
        ttk.Label(main_frame, text="Min Expansion (-1 for any):").grid(row=6, column=0, sticky="w", pady=2)
        self.min_exp_var = tk.StringVar(value="-1")
        ttk.Entry(main_frame, textvariable=self.min_exp_var).grid(row=6, column=1, sticky="ew", padx=(5, 0), pady=2)
        
        ttk.Label(main_frame, text="Max Expansion (-1 for any):").grid(row=7, column=0, sticky="w", pady=2)
        self.max_exp_var = tk.StringVar(value="-1")
        ttk.Entry(main_frame, textvariable=self.max_exp_var).grid(row=7, column=1, sticky="ew", padx=(5, 0), pady=2)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=8, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Add", command=self.ok_clicked).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel_clicked).grid(row=0, column=1, padx=5)
        
        main_frame.grid_columnconfigure(1, weight=1)
    
    def ok_clicked(self):
        try:
            self.result = (
                int(self.zoneid_var.get()),
                int(self.itemid_var.get()),
                int(self.skill_var.get()),
                int(self.chance_var.get()),
                int(self.npcid_var.get()),
                int(self.npc_chance_var.get()),
                int(self.min_exp_var.get()),
                int(self.max_exp_var.get())
            )
            self.dialog.destroy()
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numeric values")
    
    def cancel_clicked(self):
        self.dialog.destroy()

class ForageEntryDialog:
    """Dialog for adding new forage entries"""
    def __init__(self, parent, title):
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x250")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        self.create_widgets()
        
        # Wait for dialog to close
        self.dialog.wait_window()
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Entry fields
        ttk.Label(main_frame, text="Zone ID:").grid(row=0, column=0, sticky="w", pady=2)
        self.zoneid_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.zoneid_var).grid(row=0, column=1, sticky="ew", padx=(5, 0), pady=2)
        
        ttk.Label(main_frame, text="Item ID:").grid(row=1, column=0, sticky="w", pady=2)
        self.itemid_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.itemid_var).grid(row=1, column=1, sticky="ew", padx=(5, 0), pady=2)
        
        ttk.Label(main_frame, text="Level:").grid(row=2, column=0, sticky="w", pady=2)
        self.level_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.level_var).grid(row=2, column=1, sticky="ew", padx=(5, 0), pady=2)
        
        ttk.Label(main_frame, text="Chance:").grid(row=3, column=0, sticky="w", pady=2)
        self.chance_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.chance_var).grid(row=3, column=1, sticky="ew", padx=(5, 0), pady=2)
        
        ttk.Label(main_frame, text="Min Expansion (-1 for any):").grid(row=4, column=0, sticky="w", pady=2)
        self.min_exp_var = tk.StringVar(value="-1")
        ttk.Entry(main_frame, textvariable=self.min_exp_var).grid(row=4, column=1, sticky="ew", padx=(5, 0), pady=2)
        
        ttk.Label(main_frame, text="Max Expansion (-1 for any):").grid(row=5, column=0, sticky="w", pady=2)
        self.max_exp_var = tk.StringVar(value="-1")
        ttk.Entry(main_frame, textvariable=self.max_exp_var).grid(row=5, column=1, sticky="ew", padx=(5, 0), pady=2)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Add", command=self.ok_clicked).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel_clicked).grid(row=0, column=1, padx=5)
        
        main_frame.grid_columnconfigure(1, weight=1)
    
    def ok_clicked(self):
        try:
            self.result = (
                int(self.zoneid_var.get()),
                int(self.itemid_var.get()),
                int(self.level_var.get()),
                int(self.chance_var.get()),
                int(self.min_exp_var.get()),
                int(self.max_exp_var.get())
            )
            self.dialog.destroy()
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numeric values")
    
    def cancel_clicked(self):
        self.dialog.destroy()
