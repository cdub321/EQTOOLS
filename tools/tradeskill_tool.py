import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import random
from PIL import Image, ImageTk

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.theme import set_dark_theme
from dictionaries import (
    SLOT_BITMASK_DISPLAY,
    ITEM_STAT_DISPLAY_CONFIG,
)

class TreeviewEdit:
    """Cell editing functionality for Treeview widgets"""
    def __init__(self, tree, editable_columns=None, numeric_columns=None, update_callback=None):
        self.tree = tree
        self.editable_columns = editable_columns or []  # List of column indices that can be edited
        self.numeric_columns = set(numeric_columns or [])
        self.update_callback = update_callback  # Callback for database updates
        self.editing = False
        self.edit_cell = None
        self.edit_entry = None
        
        # Bind double-click to start editing
        self.tree.bind("<Double-1>", self.start_edit)
        # Bind Escape to cancel editing
        self.tree.bind("<Escape>", self.cancel_edit)
        
    def start_edit(self, event):
        # Identify the item and column that was clicked
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        
        column = self.tree.identify_column(event.x)
        column_index = int(column.replace('#', '')) - 1
        
        # Check if this column is editable
        if column_index not in self.editable_columns:
            return
            
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return
            
        # Get the current value
        current_value = self.tree.item(item_id, "values")[column_index]
        
        # Calculate position for the entry widget
        x, y, width, height = self.tree.bbox(item_id, column)
        
        # Create an entry widget
        self.edit_entry = ttk.Entry(self.tree)
        self.edit_entry.insert(0, current_value)
        self.edit_entry.select_range(0, tk.END)
        self.edit_entry.place(x=x, y=y, width=width, height=height)
        self.edit_entry.focus_set()
        
        # Bind events to save or cancel
        self.edit_entry.bind("<Return>", lambda e: self.save_edit(item_id, column_index))
        self.edit_entry.bind("<FocusOut>", lambda e: self.cancel_edit(e))
        
        self.editing = True
        self.edit_cell = (item_id, column_index)
    
    def save_edit(self, item_id, column_index):
        if not self.editing:
            return
            
        # Get the new value from the entry widget
        new_value = self.edit_entry.get()
        
        # Get all values from the tree item
        values = list(self.tree.item(item_id, "values"))
        
        # Validate the new value based on the column type
        try:
            # For numeric columns, try to convert to int
            if column_index in self.numeric_columns:
                new_value = int(new_value)
        except ValueError:
            messagebox.showerror("Invalid Value", "Please enter a valid numeric value.")
            self.edit_entry.focus_set()
            return
        
        # Update the value in the tree
        values[column_index] = new_value
        self.tree.item(item_id, values=values)
        
        # Call the update callback if provided
        if self.update_callback:
            self.update_callback(self.tree, item_id, column_index, new_value)
        
        # Clean up
        if self.edit_entry:
            self.edit_entry.destroy()
        self.editing = False
        self.edit_cell = None
    
    def cancel_edit(self, event):
        if self.editing and self.edit_entry:
            self.edit_entry.destroy()
            self.editing = False
            self.edit_cell = None

class TradeskillManagerTool:
    """Tradeskill Manager Tool - modular version for tabbed interface"""
    
    def __init__(self, parent_frame, db_manager, notes_db_manager):
        self.parent = parent_frame
        self.db_manager = db_manager
        self.notes_db = notes_db_manager
        
        # Configure parent frame grid
        self.parent.grid_rowconfigure(0, weight=1)
        self.parent.grid_columnconfigure(0, weight=1)
        
        # Create main container frame
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Initialize variables
        self.tradeskill_var = tk.StringVar()
        self.search_var = tk.StringVar()
        self.comp_itemid_var = tk.StringVar()
        self.contain_itemid_var = tk.StringVar()
        self.result_itemid_var = tk.StringVar()
        self.recipe_tradeskill_placeholder = "Select Tradeskill"
        self.recipe_tradeskill_var = tk.StringVar(value=self.recipe_tradeskill_placeholder)
        self.current_recipe_id = None
        self.current_recipe_tradeskill_id = None
        self.item_canvas = None
        self.item_bg_image = None
        self.sort_states = {}

        # Lookup caches populated from notes.db
        self.tradeskill_lookup = {}
        self.tradeskill_name_to_id = {}
        self.tradeskill_names = []
        self.container_lookup = {}
        self.container_ids = []
        self.class_bitmask_display = {}
        self.race_bitmask_display = {}
        self.all_class_mask = 0
        self.all_race_mask = 0

        self.load_lookup_data()
        
        # Initialize UI components
        self.create_ui()
        
        # Load initial data
        self.clear_all_entries()

    def load_lookup_data(self):
        """Load lookup data from notes.db into local caches"""
        if not self.notes_db:
            print("Warning: Notes database manager not available for tradeskill lookups.")
            return

        try:
            tradeskills = self.notes_db.get_all_tradeskills()
        except Exception as exc:
            print(f"Warning: Could not load tradeskill lookup data: {exc}")
            tradeskills = []

        self.tradeskill_lookup = {row['id']: row['name'] for row in tradeskills}
        self.tradeskill_name_to_id = {name: ts_id for ts_id, name in self.tradeskill_lookup.items()}
        self.tradeskill_names = [self.tradeskill_lookup[ts_id] for ts_id in sorted(self.tradeskill_lookup)]

        try:
            containers = self.notes_db.get_all_containers()
        except Exception as exc:
            print(f"Warning: Could not load container lookup data: {exc}")
            containers = []

        self.container_lookup = {row['id']: row['name'] for row in containers}
        self.container_ids = sorted(self.container_lookup)

        try:
            class_bitmasks = self.notes_db.get_class_bitmasks()
        except Exception as exc:
            print(f"Warning: Could not load class bitmask lookup data: {exc}")
            class_bitmasks = []

        self.class_bitmask_display = {
            row['bit_value']: row.get('abbr') or row['name']
            for row in class_bitmasks
        }

        try:
            race_bitmasks = self.notes_db.get_race_bitmasks()
        except Exception as exc:
            print(f"Warning: Could not load race bitmask lookup data: {exc}")
            race_bitmasks = []

        self.race_bitmask_display = {
            row['bit_value']: row.get('abbr') or row['name']
            for row in race_bitmasks
        }
        self.all_class_mask = self._compute_all_mask(self.class_bitmask_display, explicit_all=65535)
        self.all_race_mask = self._compute_all_mask(self.race_bitmask_display, explicit_all=65535)

    def _compute_all_mask(self, mapping, explicit_all=None):
        """Compute a combined mask of all individual bits in a lookup mapping."""
        combined = 0
        for bit_value in mapping.keys():
            try:
                bit_int = int(bit_value)
            except (TypeError, ValueError):
                continue
            if explicit_all is not None and bit_int == explicit_all:
                continue
            if bit_int <= 0:
                continue
            combined |= bit_int
        return combined
    
    def create_ui(self):
        """Create the complete Tradeskill Manager UI"""
        
        # Configure main frame grid
        self.main_frame.grid_rowconfigure(0, weight=0)  # Top frame - fixed height
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1)
        for col_index in range(5):
            self.main_frame.grid_columnconfigure(col_index, weight=1 if col_index <= 3 else 1)

        # Build layout in the required order so treeviews exist before editing setup
        self.create_top_frame()
        self.create_containers_panel(row=0, column=4)
        self.create_middle_frame()
        self.create_components_panel(row=1, column=4)
        self.create_results_panel(row=2, column=4)
        self.create_instructions()
        self.setup_editing()
    
    def create_top_frame(self):
        """Create top frame with search controls"""
        self.top_frame = ttk.Frame(self.main_frame, relief=tk.SUNKEN, borderwidth=1)
        self.top_frame.grid(row=0, column=0, columnspan=4, padx=5, pady=5, sticky="ew")
        for col_index in range(4):
            self.top_frame.grid_columnconfigure(col_index, weight=1)
        
        # Search Frame
        search_frame = ttk.Frame(self.top_frame, relief=tk.SUNKEN, borderwidth=2)
        search_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        search_frame.grid_columnconfigure(0, weight=1)
        
        # Tradeskill dropdown
        ttk.Label(search_frame, text="List Recipes By\n   Tradeskill").grid(row=0, column=0)
        self.tradeskill_dropdown = ttk.Combobox(search_frame, textvariable=self.tradeskill_var, state="readonly")
        self.tradeskill_dropdown["values"] = ["Select a Tradeskill"] + self.tradeskill_names
        self.tradeskill_dropdown.current(0)
        self.tradeskill_dropdown.grid(row=1, column=0, padx=5, pady=(2, 6))
        self.tradeskill_dropdown.bind("<<ComboboxSelected>>", self.load_recipes)
        
        ttk.Label(search_frame, text=" Search Recipe by\nName or Recipe ID:").grid(row=2, column=0)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=24)
        search_entry.grid(row=3, column=0, padx=5, pady=(2, 4))
        search_button = ttk.Button(search_frame, text="Search", command=self.search_recipes)
        search_button.grid(row=4, column=0, padx=5, pady=(0, 5))
        
        # Item search frame
        find_byitem_frame = ttk.Frame(self.top_frame, relief=tk.SUNKEN, borderwidth=2)
        find_byitem_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        find_byitem_frame.grid_columnconfigure(0, weight=1)
        
        ttk.Button(find_byitem_frame, text="Create New Recipe", command=self.create_new_recipe).grid(row=0, column=0, padx=5, pady=(5, 2))
        ttk.Button(find_byitem_frame, text="Duplicate Selected Recipe", command=self.duplicate_selected_recipe).grid(row=1, column=0, padx=5, pady=2)
        ttk.Button(find_byitem_frame, text="Delete Selected Recipe", command=self.delete_selected_recipe).grid(row=2, column=0, padx=5, pady=2)
        ttk.Label(find_byitem_frame, text="Search Recipe\n    by Item:").grid(row=3, column=0, pady=(6, 0))
        ttk.Button(find_byitem_frame, text="Search by Item ID", command=self.open_item_search).grid(row=4, column=0, padx=5, pady=(2, 5))

        # Selected recipe tradeskill frame
        update_tradeskill_frame = ttk.Frame(self.top_frame, relief=tk.SUNKEN, borderwidth=2)
        update_tradeskill_frame.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")

        ttk.Label(update_tradeskill_frame, text="Change Selected Recipe Tradeskill").grid(row=0, column=0, columnspan=2, pady=(0, 5))

        self.recipe_tradeskill_dropdown = ttk.Combobox(
            update_tradeskill_frame,
            textvariable=self.recipe_tradeskill_var,
            state="readonly"
        )
        self.recipe_tradeskill_dropdown["values"] = [self.recipe_tradeskill_placeholder] + self.tradeskill_names
        self.recipe_tradeskill_dropdown.current(0)
        self.recipe_tradeskill_dropdown.grid(row=1, column=0, padx=5, pady=5)

        ttk.Button(update_tradeskill_frame, text="Update", command=self.update_selected_recipe_tradeskill).grid(
            row=1, column=1, padx=5, pady=5
        )

        update_tradeskill_frame.grid_columnconfigure(0, weight=1)

        # Item viewer frame
        viewer_style = ttk.Style(self.top_frame)
        viewer_style.configure("ItemViewer.TFrame", background="#2b2b2b")
        viewer_style.configure("ItemViewerHeading.TLabel", background="#2b2b2b", foreground="white")

        item_viewer_frame = ttk.Frame(self.top_frame, relief=tk.SUNKEN, borderwidth=2, style="ItemViewer.TFrame")
        item_viewer_frame.grid(row=0, column=3, padx=5, pady=5, sticky="nsew")
        item_viewer_frame.grid_rowconfigure(1, weight=1)
        item_viewer_frame.grid_columnconfigure(0, weight=1)

        try:
            backing_image = Image.open("images/other/itemback.png")
            self.item_bg_image = ImageTk.PhotoImage(backing_image)
            display_height = min(260, self.item_bg_image.height())
            self.item_canvas = tk.Canvas(
                item_viewer_frame,
                width=self.item_bg_image.width(),
                height=display_height,
                highlightthickness=0,
                bg="#2b2b2b",
            )
            self.item_canvas.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
            self.item_canvas.configure(scrollregion=(0, 0, self.item_bg_image.width(), self.item_bg_image.height()))
            self.item_canvas.create_image(0, 0, anchor="nw", image=self.item_bg_image)
            self.item_canvas.create_text(
                self.item_bg_image.width() // 2,
                10,
                text="Select an item to view details.",
                fill="white",
                anchor="n",
                font=("Arial", 10, "italic"),
            )
        except Exception as exc:
            print(f"Could not load item background image: {exc}")
            self.item_bg_image = None
            self.item_canvas = tk.Canvas(item_viewer_frame, width=400, height=260, highlightthickness=0, bg="#2b2b2b")
            self.item_canvas.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
            self.item_canvas.create_text(
                200,
                10,
                text="Select an item to view details.",
                fill="white",
                anchor="n",
                font=("Arial", 10, "italic"),
            )

        # Containers treeview now lives in the right column panel

    def create_containers_panel(self, row, column):
        """Create containers management frame"""
        containers_frame = ttk.Frame(self.main_frame, relief=tk.SUNKEN, borderwidth=2)
        containers_frame.grid(row=row, column=column, padx=5, pady=5, sticky="nsew")
        containers_frame.grid_columnconfigure(0, weight=1)

        container_controls = ttk.Frame(containers_frame)
        container_controls.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 2))
        container_controls.grid_columnconfigure(2, weight=1)

        ttk.Button(container_controls, text="Delete Selected", command=self.delete_selected_container).grid(row=0, column=0, padx=2, pady=2, sticky="w")
        ttk.Button(container_controls, text="Add Random", command=self.add_stock_container).grid(row=0, column=1, padx=2, pady=2, sticky="w")
        ttk.Button(container_controls, text="Add Container by ID:", command=self.add_specific_container).grid(row=0, column=2, padx=2, pady=2, sticky="e")
        ttk.Entry(container_controls, textvariable=self.contain_itemid_var, width=10).grid(row=0, column=3, padx=2, pady=2, sticky="e")
        ttk.Button(container_controls, text="List Containers", command=self.open_container_list).grid(row=0, column=4, padx=2, pady=2, sticky="e")

        ttk.Label(containers_frame, text="Containers", font=("Arial", 12, "bold")).grid(row=1, column=0, pady=(2, 2))

        container_columns = [
            ("entry_id", "Entry ID", 110, False, "numeric"),
            ("container_id", "Container ID", 80, False, "numeric"),
            ("container_name", "Container Name", 200, True, "text"),
        ]

        self.containers_tree = ttk.Treeview(
            containers_frame,
            columns=("entry_id", "container_id", "container_name"),
            show="headings",
            height=4,
        )

        for col_id, heading, width, stretch, sort_type in container_columns:
            self.containers_tree.heading(
                col_id,
                text=heading,
                command=lambda c=col_id, st=sort_type: self.sort_treeview(self.containers_tree, c, st),
            )
            self.containers_tree.column(col_id, width=width, stretch=stretch, anchor="center")

        self.containers_tree.grid(row=2, column=0, sticky="new", padx=5, pady=5)
        self.bind_treeview_scrolling(self.containers_tree)
        self.containers_tree.bind("<<TreeviewSelect>>", self.handle_item_tree_selection)

    def create_middle_frame(self):
        """Create middle frame with recipe treeview"""
        self.middle_frame = ttk.Frame(self.main_frame, relief=tk.SUNKEN, borderwidth=1)
        self.middle_frame.grid(row=1, column=0, rowspan=2, columnspan=4, padx=5, pady=5, sticky="nsew")
        self.middle_frame.grid_rowconfigure(0, weight=1)
        self.middle_frame.grid_rowconfigure(1, weight=1)
        for col_index in range(4):
            self.middle_frame.grid_columnconfigure(col_index, weight=1)
        
        # Recipe view frame
        recipe_view_frame = ttk.Frame(self.middle_frame, relief=tk.SUNKEN, borderwidth=2)
        recipe_view_frame.grid(row=0, column=0, sticky="nsew", columnspan=4, rowspan=2, pady=5, padx=5)
        for col_index in range(4):
            recipe_view_frame.grid_columnconfigure(col_index, weight=1)
        recipe_view_frame.grid_rowconfigure(1, weight=1)
        
        # Recipe treeview
        self.recipe_tree = ttk.Treeview(
            recipe_view_frame,
            columns=(
                "id", "name", "skillneeded", "trivial", "nofail", "replace_container",
                "notes", "must_learn", "learned_by_item_id", "quest", "enabled", "min_expansion", "max_expansion",
            ),
            show="headings",
        )
        
        # Configure columns
        column_configs = [
            ("id", "ID", 70, False, "numeric"),
            ("name", "Name", 170, False, "text"),
            ("skillneeded", "Skill Needed", 75, False, "numeric"),
            ("trivial", "Triv", 45, False, "numeric"),
            ("nofail", "NoFail", 55, False, "numeric"),
            ("replace_container", "ReplCont", 75, False, "numeric"),
            ("notes", "Notes", 180, False, "text"),
            ("must_learn", "MustLearn", 75, False, "numeric"),
            ("learned_by_item_id", "LearnItemID", 85, False, "numeric"),
            ("quest", "Quest", 50, False, "numeric"),
            ("enabled", "Enabled", 70, False, "numeric"),
            ("min_expansion", "MinXp", 55, False, "numeric"),
            ("max_expansion", "MaxXp", 55, False, "numeric"),
        ]
        
        for col_id, heading, width, stretch, sort_type in column_configs:
            self.recipe_tree.heading(
                col_id,
                text=heading,
                command=lambda c=col_id, st=sort_type: self.sort_treeview(self.recipe_tree, c, st),
            )
            self.recipe_tree.column(col_id, width=width, stretch=stretch, anchor="center")
        
        self.recipe_tree.configure(height=18)
        self.recipe_tree.grid(row=1, column=0, sticky="nsew", columnspan=4, rowspan=2, padx=5, pady=5)
        self.recipe_tree.bind("<<TreeviewSelect>>", self.load_recipe_entries)
        self.bind_treeview_scrolling(self.recipe_tree)
        
        # Configure recipe view frame grid


    def create_components_panel(self, row, column):
        """Create components management frame"""
        components_frame = ttk.Frame(self.main_frame, relief=tk.SUNKEN, borderwidth=2)
        components_frame.grid(row=row, column=column, padx=5, pady=5, sticky="nsew")
        
        # Components header and controls
        components_frame.grid_columnconfigure(2, weight=1)
        ttk.Button(components_frame, text="Delete Selected", command=self.delete_selected_comp).grid(row=0, column=0, padx=2, pady=2, sticky="w")
        ttk.Button(components_frame, text="Add Random", command=self.add_random_comp).grid(row=0, column=1, padx=2, pady=2, sticky="w")
        ttk.Button(components_frame, text="Add Item by ID:", command=self.add_specific_comp).grid(row=0, column=2, padx=2, pady=2, sticky="e")
        ttk.Entry(components_frame, textvariable=self.comp_itemid_var, width=10).grid(row=0, column=3, padx=2, pady=2, sticky="e")
        ttk.Label(components_frame, text="Components", font=("Arial", 12, "bold")).grid(row=1, column=0, pady=3, columnspan=4)
        
        # Components treeview
        self.components_tree = ttk.Treeview(
            components_frame,
            columns=("entry_id", "item_id", "item_name", "component_count", "fail_count", "salvage_count"),
            show="headings",
        )
        
        component_columns = [
            ("entry_id", "Entry\nID", 60, False, "numeric"),
            ("item_id", "Item\nID", 65, False, "numeric"),
            ("item_name", "Item Name", 220, True, "text"),
            ("component_count", "Component\nCount", 80, True, "numeric"),
            ("fail_count", "Fail\nCount", 70, True, "numeric"),
            ("salvage_count", "Salvage\nCount", 80, True, "numeric"),
        ]
        
        for col_id, heading, width, stretch, sort_type in component_columns:
            self.components_tree.heading(
                col_id,
                text=heading,
                command=lambda c=col_id, st=sort_type: self.sort_treeview(self.components_tree, c, st),
            )
            self.components_tree.column(col_id, width=width, stretch=stretch, anchor="center")
        
        self.components_tree.configure(height=7)
        self.components_tree.grid(row=2, column=0, sticky="nsew", padx=5, pady=5, columnspan=4)
        self.bind_treeview_scrolling(self.components_tree)
        self.components_tree.bind("<<TreeviewSelect>>", self.handle_item_tree_selection)
        
        # Configure components frame grid
    def create_results_panel(self, row, column):
        """Create results management frame"""
        results_frame = ttk.Frame(self.main_frame, relief=tk.SUNKEN, borderwidth=2)
        results_frame.grid(row=row, column=column, padx=5, pady=5, sticky="nsew")
        results_frame.grid_columnconfigure(0, weight=0)
        results_frame.grid_columnconfigure(1, weight=0)
        results_frame.grid_columnconfigure(2, weight=1)
        results_frame.grid_columnconfigure(3, weight=0)
        results_frame.grid_rowconfigure(2, weight=1)
        
        # Results header and controls
        ttk.Button(results_frame, text="Delete Selected", command=self.delete_selected_result).grid(row=0, column=0, padx=2, pady=2, sticky="w")
        ttk.Button(results_frame, text="Add Random", command=self.add_random_result).grid(row=0, column=1, padx=2, pady=2, sticky="w")
        ttk.Button(results_frame, text="Add Item by ID:", command=self.add_specific_result).grid(row=0, column=2, padx=2, pady=2, sticky="e")
        ttk.Entry(results_frame, textvariable=self.result_itemid_var, width=10).grid(row=0, column=3, padx=2, pady=2, sticky="e")
        ttk.Label(results_frame, text="Results", font=("Arial", 12, "bold")).grid(row=1, column=0, pady=3, columnspan=4)
        
        # Results treeview
        self.results_tree = ttk.Treeview(
            results_frame,
            columns=("entry_id", "item_id", "item_name", "success_count"),
            show="headings",
        )
        
        result_columns = [
            ("entry_id", "Entry\nID", 60, False, "numeric"),
            ("item_id", "Item\nID", 60, False, "numeric"),
            ("item_name", "Item Name", 260, True, "text"),
            ("success_count", "Success\nCount", 90, True, "numeric"),
        ]
        
        for col_id, heading, width, stretch, sort_type in result_columns:
            self.results_tree.heading(
                col_id,
                text=heading,
                command=lambda c=col_id, st=sort_type: self.sort_treeview(self.results_tree, c, st),
            )
            self.results_tree.column(col_id, width=width, stretch=stretch, anchor="center")
        
        self.results_tree.configure(height=6)
        self.results_tree.grid(row=2, column=0, sticky="nsew", padx=5, pady=5, columnspan=4)
        self.bind_treeview_scrolling(self.results_tree)
        self.results_tree.bind("<<TreeviewSelect>>", self.handle_item_tree_selection)

    def create_instructions(self):
        """Create instructions label"""
        edit_label = ttk.Label(
            self.main_frame,
            text="Double-click most cells to edit. Press Enter to save.",
            font=("Arial", 10, "italic"),
        )
        edit_label.grid(row=3, column=0, columnspan=5, padx=5, pady=5, sticky="w")
    
    def setup_editing(self):
        """Setup inline editing for all treeviews"""
        # Recipe editor
        self.recipe_editor = TreeviewEdit(
            self.recipe_tree,
            editable_columns=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            numeric_columns=[2, 3, 4, 5, 7, 8, 9, 10, 11, 12],
            update_callback=self.update_database
        )
        
        # Components editor
        self.components_editor = TreeviewEdit(
            self.components_tree,
            editable_columns=[3, 4, 5],
            numeric_columns=[3, 4, 5],
            update_callback=self.update_database
        )
        
        # Containers editor
        self.containers_editor = TreeviewEdit(
            self.containers_tree,
            editable_columns=[],
            numeric_columns=[],
            update_callback=self.update_database
        )
        
        # Results editor
        self.results_editor = TreeviewEdit(
            self.results_tree,
            editable_columns=[3],
            numeric_columns=[3],
            update_callback=self.update_database
        )

    def sort_treeview(self, tree, column, sort_type):
        """Sort a treeview column when its header is clicked."""
        descending = self.sort_states.get((tree, column), False)
        items = []
        for index, item in enumerate(tree.get_children("")):
            raw_value = tree.set(item, column)
            sort_value = self._prepare_sort_value(raw_value, sort_type)
            items.append((sort_value, index, item))
        items.sort(reverse=descending)
        for new_index, (_, _, item) in enumerate(items):
            tree.move(item, "", new_index)
        self.sort_states[(tree, column)] = not descending

    def _prepare_sort_value(self, value, sort_type):
        """Normalize cell value to support numeric and text sorting."""
        if sort_type == "numeric":
            try:
                return float(value)
            except (TypeError, ValueError):
                return float("-inf")
        if value is None:
            return ""
        return str(value).lower()
    
    def bind_treeview_scrolling(self, tree):
        """Enable mouse-wheel scrolling for a treeview without visible scrollbars."""
        tree.bind("<MouseWheel>", lambda event, t=tree: self._on_tree_mousewheel(t, event))
        tree.bind("<Shift-MouseWheel>", lambda event, t=tree: self._on_tree_shift_mousewheel(t, event))
        tree.bind("<Button-4>", lambda event, t=tree: self._on_tree_button_scroll(t, -1))
        tree.bind("<Button-5>", lambda event, t=tree: self._on_tree_button_scroll(t, 1))
        tree.bind("<Shift-Button-4>", lambda event, t=tree: self._on_tree_button_scroll_horizontal(t, -1))
        tree.bind("<Shift-Button-5>", lambda event, t=tree: self._on_tree_button_scroll_horizontal(t, 1))

    def _on_tree_mousewheel(self, tree, event):
        """Scroll vertically when the mouse wheel is used."""
        delta = getattr(event, "delta", 0)
        if delta == 0:
            return
        direction = -1 if delta > 0 else 1
        tree.yview_scroll(direction, "units")
        return "break"

    def _on_tree_shift_mousewheel(self, tree, event):
        """Scroll horizontally when the mouse wheel is used with Shift held."""
        delta = getattr(event, "delta", 0)
        if delta == 0:
            return
        direction = -1 if delta > 0 else 1
        tree.xview_scroll(direction, "units")
        return "break"

    def _on_tree_button_scroll(self, tree, direction):
        """Support vertical scrolling on Linux button-4/5 events."""
        tree.yview_scroll(direction, "units")
        return "break"

    def _on_tree_button_scroll_horizontal(self, tree, direction):
        """Support horizontal scrolling on Linux when Shift+scroll is used."""
        tree.xview_scroll(direction, "units")
        return "break"
    
    # Database helper functions
    def fetch_data(self, query, params=(), fetch_all=True):
        """Fetch data from the database"""
        return self.db_manager.execute_query(query, params, fetch_all)
    
    def execute_update(self, query, params=()):
        """Execute an update query (INSERT, UPDATE, DELETE)"""
        return self.db_manager.execute_update(query, params)
    
    # Recipe and entry loading functions
    def load_recipes(self, event=None):
        """Load recipes based on the selected tradeskill"""
        self.recipe_tree.delete(*self.recipe_tree.get_children())
        self.clear_recipe_entries()
        tradeskill_name = self.tradeskill_var.get()
        tradeskill_id = self.tradeskill_name_to_id.get(tradeskill_name)
        if tradeskill_id:
            data = self.fetch_data(
                "SELECT id, name, skillneeded, trivial, nofail, replace_container, notes, must_learn, learned_by_item_id, quest, enabled, min_expansion, max_expansion FROM tradeskill_recipe WHERE tradeskill = %s", 
                (tradeskill_id,)
            )
            for row in data:
                self.recipe_tree.insert("", "end", values=(
                    row['id'], row['name'], row['skillneeded'], row['trivial'], row['nofail'], 
                    row['replace_container'], row['notes'], row['must_learn'], row['learned_by_item_id'], 
                    row['quest'], row['enabled'], row['min_expansion'], row['max_expansion']
                ))
    
    def clear_recipe_entries(self):
        """Clear all recipe entry subtrees"""
        for subtree in [self.components_tree, self.containers_tree, self.results_tree]:
            subtree.delete(*subtree.get_children())
        self.current_recipe_id = None
        self.set_selected_recipe_tradeskill(None)
        self.clear_item_viewer("Select an item to view details.")
    
    def clear_all_entries(self):
        """Clear all trees"""
        for subtree in [self.recipe_tree, self.components_tree, self.containers_tree, self.results_tree]:
            subtree.delete(*subtree.get_children())
        self.current_recipe_id = None
        self.set_selected_recipe_tradeskill(None)
    
    def load_recipe_entries(self, event=None):
        """Load recipe entries for the selected recipe"""
        self.clear_recipe_entries()
        selected = self.recipe_tree.selection()
        if selected:
            recipe_value = self.recipe_tree.item(selected[0], "values")[0]
            try:
                recipe_id = int(recipe_value)
            except (TypeError, ValueError):
                recipe_id = recipe_value
            self.current_recipe_id = recipe_id
            recipe_meta = self.fetch_data("SELECT tradeskill FROM tradeskill_recipe WHERE id = %s", (recipe_id,), fetch_all=False)
            if recipe_meta:
                self.set_selected_recipe_tradeskill(recipe_meta['tradeskill'])
            else:
                self.set_selected_recipe_tradeskill(None)
            query = """
            SELECT tre.id, tre.item_id, COALESCE(i.name, 'No Name') AS name, tre.successcount, tre.failcount, tre.componentcount, tre.salvagecount, tre.iscontainer
            FROM tradeskill_recipe_entries tre
            LEFT JOIN items i ON tre.item_id = i.id
            WHERE tre.recipe_id = %s
            """
            data = self.fetch_data(query, (recipe_id,))
            for row in data:
                entry_id = row['id']
                item_id = row['item_id']
                item_name = row['name']
                successcount = row['successcount']
                failcount = row['failcount']
                componentcount = row['componentcount']
                salvagecount = row['salvagecount']
                iscontainer = row['iscontainer']
                
                if iscontainer:
                    container_name = self.get_container_name(item_id)
                    self.containers_tree.insert("", "end", values=(entry_id, item_id, container_name))
                elif successcount > 0:
                    self.results_tree.insert("", "end", values=(entry_id, item_id, item_name, successcount))
                else:
                    self.components_tree.insert("", "end", values=(entry_id, item_id, item_name, componentcount, failcount, salvagecount))
    
    def get_container_name(self, container_id):
        """Get container name from ID"""
        if container_id in self.container_lookup:
            return self.container_lookup[container_id]
        item_name = self.fetch_data("SELECT name FROM items WHERE id = %s", (container_id,), fetch_all=False)
        return item_name['name'] if item_name else f"Unknown Container (ID: {container_id})"

    def clear_item_viewer(self, message=None):
        """Reset the item viewer canvas."""
        if not self.item_canvas:
            return
        self.item_canvas.configure(bg="#2b2b2b")
        self.item_canvas.delete("all")
        if self.item_bg_image:
            self.item_canvas.create_image(0, 0, anchor="nw", image=self.item_bg_image)
            self.item_canvas.configure(scrollregion=(0, 0, self.item_bg_image.width(), self.item_bg_image.height()))
        if message:
            canvas_width = self.item_bg_image.width() if self.item_bg_image else self.item_canvas.winfo_reqwidth()
            self.item_canvas.create_text(
                canvas_width // 2,
                10,
                text=message,
                fill="white",
                anchor="n",
                font=("Arial", 10, "italic"),
            )
        # Ensure icon references do not keep stale images alive
        self.item_canvas.item_photo = None

    def handle_item_tree_selection(self, event):
        """Display item details when an item tree selection changes."""
        tree = event.widget
        if tree not in {self.components_tree, self.containers_tree, self.results_tree}:
            return
        selected = tree.selection()
        if not selected:
            return
        values = tree.item(selected[0], "values")
        if len(values) < 2:
            self.clear_item_viewer("Item details unavailable.")
            return
        item_id = values[1]
        self.display_item_in_viewer(item_id)

    def display_item_in_viewer(self, item_id):
        """Populate the item viewer with stats for the provided item ID."""
        if not self.item_canvas:
            return

        try:
            item_id_int = int(item_id)
        except (TypeError, ValueError):
            self.clear_item_viewer("Item details unavailable.")
            return

        item_query = """
            SELECT DISTINCT Name, aagi, ac, accuracy, acha, adex, aint, asta, astr, attack, augrestrict,
                   augtype, avoidance, awis, bagsize, bagslots, bagtype, bagwr, banedmgamt, banedmgraceamt,
                   banedmgbody, banedmgrace, classes, color, combateffects, extradmgskill, extradmgamt, cr, damage,
                   damageshield, deity, delay, dotshielding, dr, elemdmgtype, elemdmgamt, endur, fr, fvnodrop,
                   haste, hp, regen, icon, itemclass, itemtype, lore, loregroup, magic, mana, manaregen, enduranceregen, mr,
                   nodrop, norent, pr, races, `range`, reclevel, recskill, reqlevel, shielding, size, skillmodtype, skillmodvalue,
                   slots, clickeffect, spellshield, strikethrough, stunresist, weight, attuneable, svcorruption, skillmodmax,
                   heroic_str, heroic_int, heroic_wis, heroic_agi, heroic_dex,
                   heroic_sta, heroic_cha, heroic_pr, heroic_dr, heroic_fr,
                   heroic_cr, heroic_mr, heroic_svcorrup, healamt, spelldmg, clairvoyance, backstabdmg
            FROM items
            WHERE id = %s
        """
        item_data = self.fetch_data(item_query, (item_id_int,), fetch_all=False)
        if not item_data:
            self.clear_item_viewer(f"Item ID {item_id_int} not found.")
            return

        self.clear_item_viewer(None)

        # Support both dict and sequence results
        columns = [
            "Name", "aagi", "ac", "accuracy", "acha", "adex", "aint", "asta", "astr", "attack", "augrestrict",
            "augtype", "avoidance", "awis", "bagsize", "bagslots", "bagtype", "bagwr", "banedmgamt", "banedmgraceamt",
            "banedmgbody", "banedmgrace", "classes", "color", "combateffects", "extradmgskill", "extradmgamt", "cr", "damage",
            "damageshield", "deity", "delay", "dotshielding", "dr", "elemdmgtype", "elemdmgamt", "endur", "fr", "fvnodrop",
            "haste", "hp", "regen", "icon", "itemclass", "itemtype", "lore", "loregroup", "magic", "mana", "manaregen", "enduranceregen", "mr",
            "nodrop", "norent", "pr", "races", "range", "reclevel", "recskill", "reqlevel", "shielding", "size", "skillmodtype", "skillmodvalue",
            "slots", "clickeffect", "spellshield", "strikethrough", "stunresist", "weight", "attuneable", "svcorruption", "skillmodmax",
            "heroic_str", "heroic_int", "heroic_wis", "heroic_agi", "heroic_dex",
            "heroic_sta", "heroic_cha", "heroic_pr", "heroic_dr", "heroic_fr",
            "heroic_cr", "heroic_mr", "heroic_svcorrup", "healamt", "spelldmg", "clairvoyance", "backstabdmg"
        ]

        if isinstance(item_data, dict):
            item_stats = dict(item_data)
        else:
            item_stats = dict(zip(columns, item_data))

        # Display icon if available
        icon_id = item_stats.get("icon")
        if icon_id:
            try:
                icon_path = f"images/icons/item_{icon_id}.gif"
                icon_image = Image.open(icon_path)
                icon_photo = ImageTk.PhotoImage(icon_image)
                self.item_canvas.item_photo = icon_photo
                self.item_canvas.create_image(28, 57, image=icon_photo)
            except Exception as exc:
                print(f"Could not load icon: {exc}")

        # Decode class, race, and slot bitmasks for readability
        classes_bitmask = item_stats.get("classes")
        if classes_bitmask is not None:
            if isinstance(classes_bitmask, str):
                try:
                    classes_bitmask = int(classes_bitmask)
                except ValueError:
                    classes_bitmask = None
            if classes_bitmask is not None:
                mask_value = classes_bitmask
                if mask_value == 65535 or (self.all_class_mask and (mask_value & self.all_class_mask) == self.all_class_mask):
                    item_stats["classes"] = "ALL"
                else:
                    class_names = []
                    for bit_value, class_name in self.class_bitmask_display.items():
                        try:
                            bit_int = int(bit_value)
                        except (TypeError, ValueError):
                            continue
                        if bit_int == 65535 or bit_int <= 0:
                            continue
                        if mask_value & bit_int:
                            class_names.append(class_name)
                    item_stats["classes"] = ", ".join(class_names) if class_names else str(mask_value)

        races_bitmask = item_stats.get("races")
        if races_bitmask is not None:
            if isinstance(races_bitmask, str):
                try:
                    races_bitmask = int(races_bitmask)
                except ValueError:
                    races_bitmask = None
            if races_bitmask is not None:
                mask_value = races_bitmask
                if mask_value == 65535 or (self.all_race_mask and (mask_value & self.all_race_mask) == self.all_race_mask):
                    item_stats["races"] = "ALL"
                else:
                    race_names = []
                    for bit_value, race_name in self.race_bitmask_display.items():
                        try:
                            bit_int = int(bit_value)
                        except (TypeError, ValueError):
                            continue
                        if bit_int == 65535 or bit_int <= 0:
                            continue
                        if mask_value & bit_int:
                            race_names.append(race_name)
                    item_stats["races"] = ", ".join(race_names) if race_names else str(mask_value)

        slots_bitmask = item_stats.get("slots")
        if slots_bitmask is not None:
            if isinstance(slots_bitmask, str):
                try:
                    slots_bitmask = int(slots_bitmask)
                except ValueError:
                    slots_bitmask = None
            if slots_bitmask is not None:
                slot_names = [
                    slot_name for bit_value, slot_name in SLOT_BITMASK_DISPLAY.items() if slots_bitmask & bit_value
                ]
                item_stats["slots"] = ", ".join(dict.fromkeys(slot_names))

        config = ITEM_STAT_DISPLAY_CONFIG
        def _has_value(val):
            if val in (None, "", 0, 0.0):
                return False
            if isinstance(val, str):
                stripped = val.strip()
                if stripped == "":
                    return False
                try:
                    return float(stripped) != 0
                except ValueError:
                    return True
            return True

        # Header information
        for stat_name, pos_config in config["header_positions"].items():
            if stat_name in item_stats and item_stats[stat_name] not in (None, ""):
                value = item_stats[stat_name]
                if pos_config.get("label") is None:
                    stat_text = f"{value}"
                else:
                    stat_text = f"{pos_config['label']}: {value}"
                self.item_canvas.create_text(
                    pos_config["x"],
                    pos_config["y"],
                    text=stat_text,
                    fill=pos_config["color"],
                    anchor="nw",
                    font=pos_config["font"],
                )

        # Property row
        property_config = config["property_row"]
        items_placed = 0
        for prop_name, prop_config in property_config["properties"].items():
            if prop_name in item_stats and _has_value(item_stats[prop_name]):
                value = item_stats[prop_name]
                if "format" in prop_config:
                    value = prop_config["format"](value)
                    if not value:
                        continue
                current_x = property_config["base_x"] + (items_placed * property_config["spacing"])
                self.item_canvas.create_text(
                    current_x,
                    property_config["y"],
                    text=value,
                    fill=prop_config["color"],
                    anchor="nw",
                    font=prop_config["font"],
                )
                items_placed += 1

        # Stat columns
        def display_column_stats(column_config, stats):
            x = column_config["x"]
            y = column_config["y"]
            spacing = column_config["spacing"]
            for stat in column_config["stats"]:
                stat_name = stat["name"]
                stat_label = stat["label"]
                stat_color = stat["color"]
                if stat_name in stats and _has_value(stats[stat_name]):
                    value = stats[stat_name]
                    stat_text = f"{stat_label}: {value}"
                    self.item_canvas.create_text(
                        x,
                        y,
                        text=stat_text,
                        fill=stat_color,
                        anchor="nw",
                        font=("Arial", 8),
                    )

                    if "heroic_stats" in column_config:
                        for heroic_stat in column_config["heroic_stats"]:
                            if heroic_stat["label"] == stat_label:
                                heroic_name = heroic_stat["name"]
                                if heroic_name in stats and _has_value(stats[heroic_name]):
                                    heroic_value = stats[heroic_name]
                                    try:
                                        bbox = self.item_canvas.bbox(self.item_canvas.find_all()[-1])
                                        heroic_x = bbox[2] if bbox else x + 50
                                    except Exception:
                                        heroic_x = x + 50
                                    self.item_canvas.create_text(
                                        heroic_x,
                                        y,
                                        text=f" ({heroic_value})",
                                        fill="gold",
                                        anchor="nw",
                                        font=("Arial", 9),
                                    )
                    y += spacing

        for column in config["stat_columns"]:
            display_column_stats(column, item_stats)

    def get_tradeskill_id_from_name(self, tradeskill_name):
        """Resolve a tradeskill name to its numeric ID."""
        return self.tradeskill_name_to_id.get(tradeskill_name)

    def set_selected_recipe_tradeskill(self, tradeskill_id):
        """Update the selected recipe tradeskill dropdown to reflect the current recipe."""
        if tradeskill_id is None:
            self.current_recipe_tradeskill_id = None
            self.recipe_tradeskill_var.set(self.recipe_tradeskill_placeholder)
            return
        tradeskill_name = self.tradeskill_lookup.get(tradeskill_id)
        if tradeskill_name:
            self.current_recipe_tradeskill_id = tradeskill_id
            self.recipe_tradeskill_var.set(tradeskill_name)
        else:
            self.current_recipe_tradeskill_id = None
            self.recipe_tradeskill_var.set(self.recipe_tradeskill_placeholder)

    def update_selected_recipe_tradeskill(self):
        """Persist the selected tradeskill change for the active recipe."""
        if self.current_recipe_id is None:
            messagebox.showwarning("No Recipe Selected", "Please select a recipe before updating its tradeskill.")
            return
        recipe_id = self.current_recipe_id

        selected_name = self.recipe_tradeskill_var.get()
        if selected_name == self.recipe_tradeskill_placeholder:
            messagebox.showwarning("Select Tradeskill", "Please choose a tradeskill to assign to the recipe.")
            return

        tradeskill_id = self.get_tradeskill_id_from_name(selected_name)
        if tradeskill_id is None:
            messagebox.showerror("Invalid Tradeskill", "The selected tradeskill could not be resolved.")
            return

        if tradeskill_id == self.current_recipe_tradeskill_id:
            messagebox.showinfo("No Change", "The recipe is already assigned to this tradeskill.")
            return

        if self.execute_update("UPDATE tradeskill_recipe SET tradeskill = %s WHERE id = %s", (tradeskill_id, recipe_id)):
            self.current_recipe_tradeskill_id = tradeskill_id
            self.tradeskill_var.set(selected_name)
            self.load_recipes()

            for child in self.recipe_tree.get_children():
                if str(self.recipe_tree.item(child, "values")[0]) == str(recipe_id):
                    self.recipe_tree.selection_set(child)
                    self.recipe_tree.focus(child)
                    self.recipe_tree.see(child)
                    self.load_recipe_entries()
                    break

            messagebox.showinfo("Success", f"Recipe {recipe_id} tradeskill updated to {selected_name}.")
        else:
            messagebox.showerror("Error", "Failed to update the recipe tradeskill.")
    
    # Search functions
    def search_recipes(self):
        """Search recipes by name or ID"""
        search_term = self.search_var.get().strip()
        if not search_term:
            self.recipe_tree.delete(*self.recipe_tree.get_children())
            return
        self.recipe_tree.delete(*self.recipe_tree.get_children())
        query = """
        SELECT id, name, skillneeded, trivial, nofail, replace_container, notes, must_learn, learned_by_item_id, quest, enabled, min_expansion, max_expansion
        FROM tradeskill_recipe
        WHERE name LIKE %s OR id = %s
        """
        data = self.fetch_data(query, (f"%{search_term}%", search_term if search_term.isdigit() else -1))
        for row in data:
            self.recipe_tree.insert("", "end", values=(
                row['id'], row['name'], row['skillneeded'], row['trivial'], row['nofail'], 
                row['replace_container'], row['notes'], row['must_learn'], row['learned_by_item_id'], 
                row['quest'], row['enabled'], row['min_expansion'], row['max_expansion']
            ))
    
    def create_new_recipe(self):
        """Create new recipe with default values"""
        # Default values
        default_name = "New Recipe"
        default_tradeskill = 55  # Fishing (ID 1 in the list, but actual ID is 55)
        default_skillneeded = 0
        default_trivial = 10
        default_nofail = 0
        default_replace_container = 0
        default_notes = "None"
        default_must_learn = 0
        default_learned_by_item_id = 0
        default_quest = 0
        default_enabled = 1
        default_min_expansion = -1
        default_max_expansion = -1

        # Insert new recipe into database
        query = """
        INSERT INTO tradeskill_recipe
        (name, tradeskill, skillneeded, trivial, nofail, replace_container, notes, must_learn,
         learned_by_item_id, quest, enabled, min_expansion, max_expansion)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            default_name, default_tradeskill, default_skillneeded, default_trivial,
            default_nofail, default_replace_container, default_notes, default_must_learn,
            default_learned_by_item_id, default_quest, default_enabled,
            default_min_expansion, default_max_expansion
        )

        if self.execute_update(query, params):
            # Get the newly created recipe ID
            new_recipe_id = self.fetch_data("SELECT LAST_INSERT_ID() as id", fetch_all=False)['id']

            # Set the tradeskill dropdown to match the new recipe's tradeskill
            tradeskill_name = self.tradeskill_lookup.get(default_tradeskill, "Fishing")
            self.tradeskill_var.set(tradeskill_name)

            # Reload recipes for that tradeskill
            self.load_recipes()

            # Find and select the newly created recipe in the tree
            for child in self.recipe_tree.get_children():
                item_values = self.recipe_tree.item(child, "values")
                if str(item_values[0]) == str(new_recipe_id):
                    self.recipe_tree.selection_set(child)
                    self.recipe_tree.focus(child)
                    self.recipe_tree.see(child)
                    # Load the recipe entries (will be empty but ready for additions)
                    self.load_recipe_entries()
                    break

            messagebox.showinfo("Success", f"New recipe created with ID {new_recipe_id}!\n\nYou can now edit the recipe details and add components/containers/results.")
        else:
            messagebox.showerror("Error", "Failed to create new recipe.")
    
    def delete_selected_recipe(self):
        """Delete the selected recipe and its associated entries."""
        selected = self.recipe_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a recipe to delete.")
            return

        values = self.recipe_tree.item(selected[0], "values")
        if not values:
            messagebox.showwarning("No Selection", "Unable to determine the selected recipe.")
            return

        recipe_id_raw = values[0]
        recipe_name = values[1] if len(values) > 1 else "Unnamed Recipe"
        try:
            recipe_id = int(recipe_id_raw)
        except (TypeError, ValueError):
            recipe_id = recipe_id_raw

        if not messagebox.askyesno(
            "Confirm Deletion",
            f"Delete recipe '{recipe_name}' (ID {recipe_id})?\n\nAll associated entries will also be removed."
        ):
            return

        # Remove associated entries, then the recipe itself.
        self.execute_update("DELETE FROM tradeskill_recipe_entries WHERE recipe_id = %s", (recipe_id,))
        if self.execute_update("DELETE FROM tradeskill_recipe WHERE id = %s", (recipe_id,)):
            messagebox.showinfo("Success", f"Recipe '{recipe_name}' (ID {recipe_id}) deleted.")
            self.load_recipes()
        else:
            messagebox.showerror("Error", f"Failed to delete recipe '{recipe_name}' (ID {recipe_id}).")

    def duplicate_selected_recipe(self):
        """Duplicate the selected recipe and its entries."""
        selected = self.recipe_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a recipe to duplicate.")
            return

        values = self.recipe_tree.item(selected[0], "values")
        if not values:
            messagebox.showwarning("No Selection", "Unable to determine the selected recipe.")
            return

        recipe_id_raw = values[0]
        try:
            recipe_id = int(recipe_id_raw)
        except (TypeError, ValueError):
            messagebox.showerror("Error", "Invalid recipe ID selected.")
            return

        recipe_row = self.fetch_data(
            """
            SELECT name, tradeskill, skillneeded, trivial, nofail, replace_container, notes, must_learn,
                   learned_by_item_id, quest, enabled, min_expansion, max_expansion
            FROM tradeskill_recipe
            WHERE id = %s
            """,
            (recipe_id,),
            fetch_all=False,
        )

        if not recipe_row:
            messagebox.showerror("Error", f"Recipe ID {recipe_id} not found.")
            return

        base_name = recipe_row["name"] or "Unnamed Recipe"
        copy_name = f"{base_name} (Copy)"

        insert_query = """
        INSERT INTO tradeskill_recipe
        (name, tradeskill, skillneeded, trivial, nofail, replace_container, notes, must_learn,
         learned_by_item_id, quest, enabled, min_expansion, max_expansion)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        insert_params = (
            copy_name,
            recipe_row["tradeskill"],
            recipe_row["skillneeded"],
            recipe_row["trivial"],
            recipe_row["nofail"],
            recipe_row["replace_container"],
            recipe_row["notes"],
            recipe_row["must_learn"],
            recipe_row["learned_by_item_id"],
            recipe_row["quest"],
            recipe_row["enabled"],
            recipe_row["min_expansion"],
            recipe_row["max_expansion"],
        )

        if not self.execute_update(insert_query, insert_params):
            messagebox.showerror("Error", "Failed to duplicate recipe.")
            return

        new_recipe_id = self.fetch_data("SELECT LAST_INSERT_ID() as id", fetch_all=False)["id"]

        self.execute_update(
            """
            INSERT INTO tradeskill_recipe_entries
                (recipe_id, item_id, successcount, failcount, componentcount, salvagecount, iscontainer)
            SELECT %s, item_id, successcount, failcount, componentcount, salvagecount, iscontainer
            FROM tradeskill_recipe_entries
            WHERE recipe_id = %s
            """,
            (new_recipe_id, recipe_id),
        )

        tradeskill_name = self.tradeskill_lookup.get(recipe_row["tradeskill"])
        if tradeskill_name:
            self.tradeskill_var.set(tradeskill_name)
        self.load_recipes()

        for child in self.recipe_tree.get_children():
            item_values = self.recipe_tree.item(child, "values")
            if str(item_values[0]) == str(new_recipe_id):
                self.recipe_tree.selection_set(child)
                self.recipe_tree.focus(child)
                self.recipe_tree.see(child)
                self.load_recipe_entries()
                break

        messagebox.showinfo("Success", f"Recipe duplicated as '{copy_name}' (ID {new_recipe_id}).")
    
    def open_item_search(self):
        """Open item search popup window"""
        popout = tk.Toplevel(self.main_frame)
        popout.title("Search Item by ID")
        popout.geometry("600x400")
        popout.configure(bg="#2b2b2b")

        style = ttk.Style(popout)
        style.configure("Popout.TFrame", background="#2b2b2b")
        style.configure("Popout.TLabel", background="#2b2b2b", foreground="white")
        style.configure("Popout.TButton", padding=4)
        style.configure("Popout.TEntry", fieldbackground="#3a3a3a", foreground="white")

        popout.grid_rowconfigure(0, weight=1)
        popout.grid_columnconfigure(0, weight=1)

        content_frame = ttk.Frame(popout, style="Popout.TFrame")
        content_frame.grid(row=0, column=0, sticky="nsew")
        content_frame.grid_rowconfigure(2, weight=1)
        content_frame.grid_rowconfigure(4, weight=1)
        content_frame.grid_columnconfigure(1, weight=0)
        
        item_id_var = tk.StringVar()
        ttk.Label(content_frame, text="Item ID:", style="Popout.TLabel").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        item_id_entry = ttk.Entry(content_frame, textvariable=item_id_var, style="Popout.TEntry", width=10)
        item_id_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        def search_item():
            item_id = item_id_var.get().strip()
            if not item_id.isdigit():
                messagebox.showerror("Error", "Please enter a valid numeric Item ID.")
                return
            
            item_id = int(item_id)
            
            # Clear previous results
            for subtree in [components_results_tree, results_results_tree]:
                subtree.delete(*subtree.get_children())
            
            # Fetch item name
            item_name_result = self.fetch_data("SELECT name FROM items WHERE id = %s", (item_id,), fetch_all=False)
            if not item_name_result:
                messagebox.showerror("Error", f"Item ID {item_id} not found in the database.")
                return
            item_name = item_name_result['name']
            
            # Fetch occurrences in Components
            components_data = self.fetch_data("""
            SELECT tre.recipe_id, r.name, tre.componentcount
            FROM tradeskill_recipe_entries tre
            JOIN tradeskill_recipe r ON tre.recipe_id = r.id
            WHERE tre.item_id = %s AND tre.iscontainer = 0 AND tre.successcount = 0
            """, (item_id,))
            for row in components_data:
                components_results_tree.insert("", "end", values=(row['recipe_id'], row['name'], row['componentcount']))
            
            # Fetch occurrences in Results
            results_data = self.fetch_data("""
            SELECT tre.recipe_id, r.name, tre.successcount
            FROM tradeskill_recipe_entries tre
            JOIN tradeskill_recipe r ON tre.recipe_id = r.id
            WHERE tre.item_id = %s AND tre.successcount > 0
            """, (item_id,))
            for row in results_data:
                results_results_tree.insert("", "end", values=(row['recipe_id'], row['name'], row['successcount']))
            
            # Update headers
            components_header.config(text=f"Components (Item: {item_name})")
            results_header.config(text=f"Results (Item: {item_name})")
        
        ttk.Button(content_frame, text="Search", command=search_item, style="Popout.TButton").grid(row=0, column=2, padx=5, pady=5)
        
        def link_to_recipe(event):
            selected_tree = event.widget
            selected_item = selected_tree.selection()
            if selected_item:
                recipe_id = selected_tree.item(selected_item[0], "values")[0]
                
                # Fetch the tradeskill for the selected recipe
                query = "SELECT tradeskill FROM tradeskill_recipe WHERE id = %s"
                tradeskill_result = self.fetch_data(query, (recipe_id,), fetch_all=False)
                if tradeskill_result:
                    tradeskill_id = tradeskill_result['tradeskill']
                    # Set the dropdown to the correct tradeskill
                    tradeskill_name = self.tradeskill_lookup.get(tradeskill_id, "Unknown Tradeskill")
                    self.tradeskill_var.set(tradeskill_name)
                    # Load recipes for the selected tradeskill
                    self.load_recipes()
                
                # Find and select the recipe in the main window's recipe_tree
                for child in self.recipe_tree.get_children():
                    if self.recipe_tree.item(child, "values")[0] == recipe_id:
                        self.recipe_tree.selection_set(child)
                        self.recipe_tree.focus(child)
                        self.recipe_tree.see(child)
                        # Load the recipe entries for the selected recipe
                        self.load_recipe_entries()
                        break
        
        # Components Results Treeview
        components_header = ttk.Label(content_frame, text="Components", font=("Arial", 12, "bold"), style="Popout.TLabel")
        components_header.grid(row=1, column=0, columnspan=3, sticky="w", padx=5, pady=5)
        
        components_results_tree = ttk.Treeview(content_frame, columns=("Recipe ID", "Recipe Name", "Component Count"), show="headings")
        for col in ("Recipe ID", "Recipe Name", "Component Count"):
            components_results_tree.heading(col, text=col)
            components_results_tree.column(col, width=150, stretch=True)
        components_results_tree.grid(row=2, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
        components_results_tree.bind("<ButtonRelease-1>", link_to_recipe)
        
        # Results Results Treeview
        results_header = ttk.Label(content_frame, text="Results", font=("Arial", 12, "bold"), style="Popout.TLabel")
        results_header.grid(row=3, column=0, columnspan=3, sticky="w", padx=5, pady=5)
        
        results_results_tree = ttk.Treeview(content_frame, columns=("Recipe ID", "Recipe Name", "Success Count"), show="headings")
        for col in ("Recipe ID", "Recipe Name", "Success Count"):
            results_results_tree.heading(col, text=col)
            results_results_tree.column(col, width=150, stretch=True)
        results_results_tree.grid(row=4, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
        results_results_tree.bind("<ButtonRelease-1>", link_to_recipe)

    def open_container_list(self):
        """Open a modal listing common container IDs and names."""
        popout = tk.Toplevel(self.main_frame)
        popout.title("List Containers")
        popout.geometry("360x320")
        popout.configure(bg="#2b2b2b")

        style = ttk.Style(popout)
        style.configure("Popout.TFrame", background="#2b2b2b")
        style.configure("Popout.TLabel", background="#2b2b2b", foreground="white")

        content_frame = ttk.Frame(popout, style="Popout.TFrame")
        content_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        content_frame.grid_columnconfigure(0, weight=1)

        ttk.Label(content_frame, text="Container ID List", style="Popout.TLabel", font=("Arial", 12, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )

        container_lines = [
            "9  - medicine bag",
            "10 - toolbox",
            "11 - research",
            "12 - mortar",
            "14 - mixing bowl",
            "15 - oven",
            "16 - loom",
            "17 - forge",
            "18 - fletching kit",
            "19 - brew barrel",
            "20 - jeweler kit",
            "21 - pottery wheel",
            "22 - kiln",
        ]
        ttk.Label(
            content_frame,
            text="\n".join(container_lines),
            style="Popout.TLabel",
            justify="left",
        ).grid(row=1, column=0, sticky="w")
    
    # Helper function to get current recipe ID
    def get_current_recipe_id(self):
        """Get the current recipe ID from the selected recipe"""
        selected = self.recipe_tree.selection()
        if not selected:
            messagebox.showwarning("No Recipe Selected", "Please select a recipe first.")
            return None
        recipe_id = self.recipe_tree.item(selected[0], "values")[0]
        return recipe_id
    
    # Add functions
    def add_random_comp(self):
        """Add a random component to the database"""
        recipe_id = self.get_current_recipe_id()
        if recipe_id is None:
            return
        
        random_item_result = self.fetch_data("SELECT id FROM items ORDER BY RAND() LIMIT 1", fetch_all=False)
        random_item_id = random_item_result['id']
        
        if self.execute_update(
            "INSERT INTO tradeskill_recipe_entries (recipe_id, item_id, successcount, failcount, componentcount, salvagecount, iscontainer) "
            "VALUES (%s, %s, 0, 0, 1, 0, 0)",
            (recipe_id, random_item_id)
        ):
            self.load_recipe_entries()
    
    def add_stock_container(self):
        """Add a random stock container to the database"""
        recipe_id = self.get_current_recipe_id()
        if recipe_id is None:
            return

        if not self.container_ids:
            messagebox.showwarning("No Containers", "Container lookup data is unavailable.")
            return

        random_container_id = random.choice(self.container_ids)
        
        if self.execute_update(
            "INSERT INTO tradeskill_recipe_entries (recipe_id, item_id, successcount, failcount, componentcount, salvagecount, iscontainer) "
            "VALUES (%s, %s, 0, 0, 1, 0, 1)",
            (recipe_id, random_container_id)
        ):
            self.load_recipe_entries()
    
    def add_random_result(self):
        """Add a random result to the database"""
        recipe_id = self.get_current_recipe_id()
        if recipe_id is None:
            return
        
        random_item_result = self.fetch_data("SELECT id FROM items ORDER BY RAND() LIMIT 1", fetch_all=False)
        random_item_id = random_item_result['id']
        
        if self.execute_update(
            "INSERT INTO tradeskill_recipe_entries (recipe_id, item_id, successcount, failcount, componentcount, salvagecount, iscontainer) "
            "VALUES (%s, %s, 1, 0, 1, 0, 0)",
            (recipe_id, random_item_id)
        ):
            self.load_recipe_entries()
    
    def add_specific_comp(self):
        """Add a specific component based on the item ID entered"""
        recipe_id = self.get_current_recipe_id()
        if recipe_id is None:
            return
        
        item_id = self.comp_itemid_var.get().strip()
        if not item_id or not item_id.isdigit():
            messagebox.showwarning("Invalid Input", "Please enter a valid item ID.")
            return
        
        if self.execute_update(
            "INSERT INTO tradeskill_recipe_entries (recipe_id, item_id, successcount, failcount, componentcount, salvagecount, iscontainer) "
            "VALUES (%s, %s, 0, 0, 1, 0, 0)",
            (recipe_id, int(item_id))
        ):
            self.load_recipe_entries()
    
    def add_specific_container(self):
        """Add a specific container based on the container ID entered"""
        recipe_id = self.get_current_recipe_id()
        if recipe_id is None:
            return
        
        container_id = self.contain_itemid_var.get().strip()
        if not container_id or not container_id.isdigit():
            messagebox.showwarning("Invalid Input", "Please enter a valid container ID.")
            return
        
        if self.execute_update(
            "INSERT INTO tradeskill_recipe_entries (recipe_id, item_id, successcount, failcount, componentcount, salvagecount, iscontainer) "
            "VALUES (%s, %s, 0, 0, 1, 0, 1)",
            (recipe_id, int(container_id))
        ):
            self.load_recipe_entries()
    
    def add_specific_result(self):
        """Add a specific result based on the item ID entered"""
        recipe_id = self.get_current_recipe_id()
        if recipe_id is None:
            return
        
        item_id = self.result_itemid_var.get().strip()
        if not item_id or not item_id.isdigit():
            messagebox.showwarning("Invalid Input", "Please enter a valid item ID.")
            return
        
        if self.execute_update(
            "INSERT INTO tradeskill_recipe_entries (recipe_id, item_id, successcount, failcount, componentcount, salvagecount, iscontainer) "
            "VALUES (%s, %s, 1, 0, 1, 0, 0)",
            (recipe_id, int(item_id))
        ):
            self.load_recipe_entries()
    
    # Delete functions
    def delete_selected_container(self):
        """Delete the selected container from the database"""
        selected_item = self.containers_tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a container to delete.")
            return
        entry_id = self.containers_tree.item(selected_item, "values")[0]
        if self.execute_update("DELETE FROM tradeskill_recipe_entries WHERE id = %s", (entry_id,)):
            self.load_recipe_entries()
    
    def delete_selected_comp(self):
        """Delete the selected component from the database"""
        selected_item = self.components_tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a component to delete.")
            return
        entry_id = self.components_tree.item(selected_item, "values")[0]
        if self.execute_update("DELETE FROM tradeskill_recipe_entries WHERE id = %s", (entry_id,)):
            self.load_recipe_entries()
    
    def delete_selected_result(self):
        """Delete the selected result from the database"""
        selected_item = self.results_tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a result to delete.")
            return
        entry_id = self.results_tree.item(selected_item, "values")[0]
        if self.execute_update("DELETE FROM tradeskill_recipe_entries WHERE id = %s", (entry_id,)):
            self.load_recipe_entries()
    
    def update_database(self, tree, item_id, column_index, new_value):
        """Update database when inline editing occurs"""
        values = tree.item(item_id, "values")
        
        if tree == self.recipe_tree:
            # Recipe tree (tradeskill_recipe table)
            recipe_id = values[0]
            
            column_map = {
                1: "name", 2: "skillneeded", 3: "trivial", 4: "nofail", 5: "replace_container",
                6: "notes", 7: "must_learn", 8: "learned_by_item_id", 9: "quest", 
                10: "enabled", 11: "min_expansion", 12: "max_expansion"
            }
            
            if column_index in column_map:
                column_name = column_map[column_index]
                query = f"UPDATE tradeskill_recipe SET {column_name} = %s WHERE id = %s"
                success = self.execute_update(query, (new_value, recipe_id))
                if success:
                    messagebox.showinfo("Success", f"Recipe {recipe_id} updated successfully.")
                else:
                    messagebox.showerror("Error", f"Failed to update recipe {recipe_id}.")
        
        elif tree in [self.components_tree, self.results_tree, self.containers_tree]:
            # Entry trees (tradeskill_recipe_entries table)
            entry_id = values[0]

            if tree == self.components_tree:
                column_map = {
                    1: "item_id",
                    3: "componentcount",
                    4: "failcount",
                    5: "salvagecount",
                }
            elif tree == self.results_tree:
                column_map = {
                    1: "item_id",
                    3: "successcount",
                }
            else:
                column_map = {
                    1: "item_id",
                }

            if column_index in column_map:
                column_name = column_map[column_index]
                query = f"UPDATE tradeskill_recipe_entries SET {column_name} = %s WHERE id = %s"
                success = self.execute_update(query, (new_value, entry_id))
                if success:
                    messagebox.showinfo("Success", f"Entry {entry_id} updated successfully.")
                else:
                    messagebox.showerror("Error", f"Failed to update entry {entry_id}.")

                if tree == self.containers_tree and column_index == 1 and success:
                    container_name = self.get_container_name(new_value)
                    new_values = list(values)
                    new_values[2] = container_name
                    tree.item(item_id, values=new_values)
