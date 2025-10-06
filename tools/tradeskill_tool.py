import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import random

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.theme import set_dark_theme
from dictionaries import TRADESKILL_IDS, CONTAINER_IDS

class TreeviewEdit:
    """Cell editing functionality for Treeview widgets"""
    def __init__(self, tree, editable_columns=None, update_callback=None):
        self.tree = tree
        self.editable_columns = editable_columns or []  # List of column indices that can be edited
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
            # For numeric columns, try to convert to int or float
            if column_index in [0, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12]:  # Numeric columns in recipe tree
                new_value = int(new_value)
            elif column_index in [0, 1, 3, 4, 5] and 'components' in str(self.tree):  # Numeric columns in components tree
                new_value = int(new_value)
            elif column_index in [0, 1] and 'containers' in str(self.tree):  # Numeric columns in containers tree
                new_value = int(new_value)
            elif column_index in [0, 1, 3] and 'results' in str(self.tree):  # Numeric columns in results tree
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
    
    def __init__(self, parent_frame, db_manager):
        self.parent = parent_frame
        self.db_manager = db_manager
        
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
        
        # Initialize UI components
        self.create_ui()
        
        # Load initial data
        self.clear_all_entries()
    
    def create_ui(self):
        """Create the complete Tradeskill Manager UI"""
        
        # Configure main frame grid
        self.main_frame.grid_rowconfigure(0, weight=0)  # Top frame - fixed height
        self.main_frame.grid_rowconfigure(1, weight=1)  # Middle frame - expandable
        self.main_frame.grid_rowconfigure(2, weight=1)  # Bottom frame - expandable
        self.main_frame.grid_rowconfigure(3, weight=0)  # Instructions - fixed height
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Create the three main sections
        self.create_top_frame()
        self.create_middle_frame()
        self.create_bottom_frame()
        self.create_instructions()
    
    def create_top_frame(self):
        """Create top frame with search controls"""
        self.top_frame = ttk.Frame(self.main_frame, relief=tk.SUNKEN, borderwidth=1)
        self.top_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        # Search Frame
        search_frame = ttk.Frame(self.top_frame, relief=tk.SUNKEN, borderwidth=2)
        search_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        # Tradeskill dropdown
        ttk.Label(search_frame, text="List Recipes By\n   Tradeskill").grid(row=0, column=0)
        self.tradeskill_dropdown = ttk.Combobox(search_frame, textvariable=self.tradeskill_var, state="readonly")
        self.tradeskill_dropdown["values"] = ["Select a Tradeskill"] + list(TRADESKILL_IDS.values())
        self.tradeskill_dropdown.current(0)
        self.tradeskill_dropdown.grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.tradeskill_dropdown.bind("<<ComboboxSelected>>", self.load_recipes)
        
        # Item search frame
        find_byitem_frame = ttk.Frame(self.top_frame, relief=tk.SUNKEN, borderwidth=2)
        find_byitem_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        
        ttk.Label(find_byitem_frame, text="Search Recipe\n    by Item:").grid(row=0, column=0)
        ttk.Button(find_byitem_frame, text="Search by Item ID", command=self.open_item_search).grid(row=2, column=0, padx=5, pady=5)
        
        # Recipe lookup frame
        lookup_frame = ttk.Frame(self.top_frame, relief=tk.SUNKEN, borderwidth=2)
        lookup_frame.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        
        ttk.Label(lookup_frame, text=" Search Recipe by\nName or Recipe ID:").grid(row=0, column=0)
        search_entry = ttk.Entry(lookup_frame, textvariable=self.search_var)
        search_entry.grid(row=1, column=0, sticky="w")
        search_button = ttk.Button(lookup_frame, text="Search", command=self.search_recipes)
        search_button.grid(row=2, column=0, padx=5, pady=5)
        
        # Create new recipe frame
        create_recipe_frame = ttk.Frame(self.top_frame, relief=tk.SUNKEN, borderwidth=2)
        create_recipe_frame.grid(row=0, column=3, padx=5, pady=5, sticky="nsew")
        
        ttk.Label(create_recipe_frame, text="New Recipe").grid(row=0, column=0)
        ttk.Button(create_recipe_frame, text="Create", command=self.create_new_recipe).grid(row=1, column=0, padx=5, pady=18)
    
    def create_middle_frame(self):
        """Create middle frame with recipe treeview"""
        self.middle_frame = ttk.Frame(self.main_frame, relief=tk.SUNKEN, borderwidth=1)
        self.middle_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        
        # Configure grid
        self.middle_frame.grid_rowconfigure(0, weight=1)
        self.middle_frame.grid_columnconfigure(0, weight=1)
        
        # Recipe view frame
        recipe_view_frame = ttk.Frame(self.middle_frame, relief=tk.SUNKEN, borderwidth=2)
        recipe_view_frame.grid(row=0, column=0, sticky="nsew", pady=5, padx=5)
        
        # Recipe treeview
        self.recipe_tree = ttk.Treeview(recipe_view_frame, columns=(
            "\nID", "\nName", "  Skill\nNeeded", "\nTrivial", " No\nFail", " Replace\nContainer", 
            "\nNotes", "Must\nLearn", "Learned by\n  Item ID", "\nQuest", "\nEnabled?", "Min\nXpac", "Max\nXpac"
        ), show="headings")
        
        # Configure columns
        column_configs = [
            ("\nID", 45, False),
            ("\nName", 150, True),
            ("  Skill\nNeeded", 55, False),
            ("\nTrivial", 45, False),
            (" No\nFail", 35, False),
            (" Replace\nContainer", 60, False),
            ("\nNotes", 120, False),
            ("Must\nLearn", 50, False),
            ("Learned by\n  Item ID", 70, False),
            ("\nQuest", 40, False),
            ("\nEnabled?", 60, False),
            ("Min\nXpac", 40, False),
            ("Max\nXpac", 40, False)
        ]
        
        for col, width, stretch in column_configs:
            self.recipe_tree.heading(col, text=col)
            self.recipe_tree.column(col, width=width, stretch=stretch, anchor="center")
        
        self.recipe_tree.grid(row=1, column=0, columnspan=3, sticky="nsew")
        self.recipe_tree.bind("<<TreeviewSelect>>", self.load_recipe_entries)
        
        # Add scrollbars
        recipe_scrollbar_y = ttk.Scrollbar(recipe_view_frame, orient="vertical", command=self.recipe_tree.yview)
        recipe_scrollbar_y.grid(row=1, column=3, sticky="ns")
        self.recipe_tree.configure(yscrollcommand=recipe_scrollbar_y.set)
        
        recipe_scrollbar_x = ttk.Scrollbar(recipe_view_frame, orient="horizontal", command=self.recipe_tree.xview)
        recipe_scrollbar_x.grid(row=2, column=0, columnspan=3, sticky="ew")
        self.recipe_tree.configure(xscrollcommand=recipe_scrollbar_x.set)
        
        # Configure recipe view frame grid
        recipe_view_frame.grid_rowconfigure(1, weight=1)
        recipe_view_frame.grid_columnconfigure(0, weight=1)
    
    def create_bottom_frame(self):
        """Create bottom frame with entry management"""
        self.bottom_frame = ttk.Frame(self.main_frame, relief=tk.SUNKEN, borderwidth=1)
        self.bottom_frame.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")
        
        # Configure grid for three columns
        self.bottom_frame.grid_rowconfigure(0, weight=1)
        self.bottom_frame.grid_columnconfigure(0, weight=1)
        self.bottom_frame.grid_columnconfigure(1, weight=1)
        self.bottom_frame.grid_columnconfigure(2, weight=1)
        
        # Components frame
        self.create_components_frame()
        
        # Containers frame
        self.create_containers_frame()
        
        # Results frame
        self.create_results_frame()
    
    def create_components_frame(self):
        """Create components management frame"""
        components_frame = ttk.Frame(self.bottom_frame, relief=tk.SUNKEN, borderwidth=2)
        components_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Components header and controls
        ttk.Button(components_frame, text="Delete Selected", command=self.delete_selected_comp).grid(row=0, column=1, padx=2, pady=2)
        ttk.Button(components_frame, text="Add Random", command=self.add_random_comp).grid(row=1, column=1, padx=2, pady=2)
        ttk.Button(components_frame, text="Add Item by ID:", command=self.add_specific_comp).grid(row=0, column=2, padx=2, pady=1)
        ttk.Entry(components_frame, textvariable=self.comp_itemid_var).grid(row=1, column=2)
        ttk.Label(components_frame, text="Components", font=("Arial", 12, "bold")).grid(row=3, column=0, pady=3, columnspan=4)
        
        # Components treeview
        self.components_tree = ttk.Treeview(components_frame, columns=(
            "Entry\n  ID", "Item\n ID", "\nItem Name", "Component\n   Count", "  Fail\nCount", "Salvage\n Count"
        ), show="headings")
        
        component_columns = [
            ("Entry\n  ID", 50, False),
            ("Item\n ID", 55, False),
            ("\nItem Name", 150, False),
            ("Component\n   Count", 70, False),
            ("  Fail\nCount", 55, False),
            ("Salvage\n Count", 60, False)
        ]
        
        for col, width, stretch in component_columns:
            self.components_tree.heading(col, text=col)
            self.components_tree.column(col, width=width, stretch=stretch, anchor="center")
        
        self.components_tree.grid(row=2, column=0, sticky="nsew", padx=5, pady=5, columnspan=4)
        
        # Configure components frame grid
        components_frame.grid_rowconfigure(2, weight=1)
        components_frame.grid_columnconfigure(0, weight=1)
    
    def create_containers_frame(self):
        """Create containers management frame"""
        containers_frame = ttk.Frame(self.bottom_frame, relief=tk.SUNKEN, borderwidth=2)
        containers_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        # Containers header and controls
        ttk.Button(containers_frame, text="Delete Selected", command=self.delete_selected_container).grid(row=0, column=1, padx=2, pady=2)
        ttk.Button(containers_frame, text="Add Random", command=self.add_stock_container).grid(row=1, column=1, padx=2, pady=2)
        ttk.Button(containers_frame, text="Add Container by ID:", command=self.add_specific_container).grid(row=0, column=2, padx=2, pady=1)
        ttk.Entry(containers_frame, textvariable=self.contain_itemid_var).grid(row=1, column=2)
        ttk.Label(containers_frame, text="Containers", font=("Arial", 12, "bold")).grid(row=3, column=0, pady=3, columnspan=4)
        
        # Containers treeview
        self.containers_tree = ttk.Treeview(containers_frame, columns=(
            "Entry\n  ID", "Container\n     ID", "Container\n  Name"
        ), show="headings")
        
        container_columns = [
            ("Entry\n  ID", 50, False),
            ("Container\n     ID", 60, False),
            ("Container\n  Name", 150, False)
        ]
        
        for col, width, stretch in container_columns:
            self.containers_tree.heading(col, text=col)
            self.containers_tree.column(col, width=width, stretch=stretch, anchor="center")
        
        self.containers_tree.grid(row=2, column=0, sticky="nsew", padx=5, pady=5, columnspan=3)
        
        # Configure containers frame grid
        containers_frame.grid_rowconfigure(2, weight=1)
        containers_frame.grid_columnconfigure(0, weight=1)
    
    def create_results_frame(self):
        """Create results management frame"""
        results_frame = ttk.Frame(self.bottom_frame, relief=tk.SUNKEN, borderwidth=2)
        results_frame.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)
        
        # Results header and controls
        ttk.Button(results_frame, text="Delete Selected", command=self.delete_selected_result).grid(row=0, column=1, padx=2, pady=2)
        ttk.Button(results_frame, text="Add Random", command=self.add_random_result).grid(row=1, column=1, padx=2, pady=2)
        ttk.Button(results_frame, text="Add Item by ID:", command=self.add_specific_result).grid(row=0, column=2, padx=2, pady=1)
        ttk.Entry(results_frame, textvariable=self.result_itemid_var).grid(row=1, column=2)
        ttk.Label(results_frame, text="Results", font=("Arial", 12, "bold")).grid(row=3, column=0, pady=3, columnspan=4)
        
        # Results treeview
        self.results_tree = ttk.Treeview(results_frame, columns=(
            "Entry\n  ID", "Item\n ID", " Item\nName", "Success\n  Count"
        ), show="headings")
        
        result_columns = [
            ("Entry\n  ID", 50, False),
            ("Item\n ID", 50, False),
            (" Item\nName", 150, False),
            ("Success\n  Count", 60, False)
        ]
        
        for col, width, stretch in result_columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=width, stretch=stretch, anchor="center")
        
        self.results_tree.grid(row=2, column=0, sticky="nsew", padx=5, pady=5, columnspan=3)
        
        # Configure results frame grid
        results_frame.grid_rowconfigure(2, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)
    
    def create_instructions(self):
        """Create instructions label"""
        edit_label = ttk.Label(self.main_frame, text="Double-click most cells to edit. Press Enter to save.", 
                              font=("Arial", 10, "italic"))
        edit_label.grid(row=3, column=0, columnspan=3, padx=5, pady=5)
        
        # Initialize editing functionality
        self.setup_editing()
    
    def setup_editing(self):
        """Setup inline editing for all treeviews"""
        # Recipe editor
        self.recipe_editor = TreeviewEdit(
            self.recipe_tree, 
            editable_columns=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            update_callback=self.update_database
        )
        
        # Components editor
        self.components_editor = TreeviewEdit(
            self.components_tree, 
            editable_columns=[0, 1, 3, 4, 5],
            update_callback=self.update_database
        )
        
        # Containers editor
        self.containers_editor = TreeviewEdit(
            self.containers_tree, 
            editable_columns=[0, 1],
            update_callback=self.update_database
        )
        
        # Results editor
        self.results_editor = TreeviewEdit(
            self.results_tree, 
            editable_columns=[0, 1, 3],
            update_callback=self.update_database
        )
    
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
        tradeskill_id = next((id for id, name in TRADESKILL_IDS.items() if name == tradeskill_name), None)
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
    
    def clear_all_entries(self):
        """Clear all trees"""
        for subtree in [self.recipe_tree, self.components_tree, self.containers_tree, self.results_tree]:
            subtree.delete(*subtree.get_children())
    
    def load_recipe_entries(self, event=None):
        """Load recipe entries for the selected recipe"""
        self.clear_recipe_entries()
        selected = self.recipe_tree.selection()
        if selected:
            recipe_id = self.recipe_tree.item(selected[0], "values")[0]
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
        if container_id in CONTAINER_IDS:
            return CONTAINER_IDS[container_id]
        item_name = self.fetch_data("SELECT name FROM items WHERE id = %s", (container_id,), fetch_all=False)
        return item_name['name'] if item_name else f"Unknown Container (ID: {container_id})"
    
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
        """Create new recipe - not implemented yet"""
        messagebox.showinfo("Not Implemented", "Recipe creation feature will be added in a future update.")
    
    def open_item_search(self):
        """Open item search popup window"""
        popout = tk.Toplevel(self.main_frame)
        popout.title("Search Item by ID")
        popout.geometry("600x400")
        
        item_id_var = tk.StringVar()
        ttk.Label(popout, text="Item ID:").grid(row=0, column=0, padx=5, pady=5)
        item_id_entry = ttk.Entry(popout, textvariable=item_id_var)
        item_id_entry.grid(row=0, column=1, padx=5, pady=5)
        
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
        
        ttk.Button(popout, text="Search", command=search_item).grid(row=0, column=2, padx=5, pady=5)
        
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
                    tradeskill_name = TRADESKILL_IDS.get(tradeskill_id, "Unknown Tradeskill")
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
        components_header = ttk.Label(popout, text="Components", font=("Arial", 12, "bold"))
        components_header.grid(row=1, column=0, columnspan=3, sticky="w", padx=5, pady=5)
        
        components_results_tree = ttk.Treeview(popout, columns=("Recipe ID", "Recipe Name", "Component Count"), show="headings")
        for col in ("Recipe ID", "Recipe Name", "Component Count"):
            components_results_tree.heading(col, text=col)
            components_results_tree.column(col, width=150, stretch=True)
        components_results_tree.grid(row=2, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
        components_results_tree.bind("<ButtonRelease-1>", link_to_recipe)
        
        # Results Results Treeview
        results_header = ttk.Label(popout, text="Results", font=("Arial", 12, "bold"))
        results_header.grid(row=3, column=0, columnspan=3, sticky="w", padx=5, pady=5)
        
        results_results_tree = ttk.Treeview(popout, columns=("Recipe ID", "Recipe Name", "Success Count"), show="headings")
        for col in ("Recipe ID", "Recipe Name", "Success Count"):
            results_results_tree.heading(col, text=col)
            results_results_tree.column(col, width=150, stretch=True)
        results_results_tree.grid(row=4, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
        results_results_tree.bind("<ButtonRelease-1>", link_to_recipe)
    
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
        
        random_container_id = random.choice(list(CONTAINER_IDS.keys()))
        
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
            
            column_map = {
                0: "id", 1: "item_id", 3: "componentcount", 4: "failcount", 5: "salvagecount"
            }
            
            if column_index in column_map:
                column_name = column_map[column_index]
                query = f"UPDATE tradeskill_recipe_entries SET {column_name} = %s WHERE id = %s"
                success = self.execute_update(query, (new_value, entry_id))
                if success:
                    messagebox.showinfo("Success", f"Entry {entry_id} updated successfully.")
                else:
                    messagebox.showerror("Error", f"Failed to update entry {entry_id}.")
            
            # Special handling for specific trees
            if tree == self.results_tree and column_index == 3:  # Success count
                query = "UPDATE tradeskill_recipe_entries SET successcount = %s WHERE id = %s"
                success = self.execute_update(query, (new_value, entry_id))
                if success:
                    messagebox.showinfo("Success", f"Success count for entry {entry_id} updated successfully.")
                else:
                    messagebox.showerror("Error", f"Failed to update success count for entry {entry_id}.")
            
            if tree == self.containers_tree and column_index == 1:  # Container ID
                query = "UPDATE tradeskill_recipe_entries SET item_id = %s WHERE id = %s"
                success = self.execute_update(query, (new_value, entry_id))
                if success:
                    messagebox.showinfo("Success", f"Container for entry {entry_id} updated successfully.")
                    # Update the container name in the tree
                    container_name = self.get_container_name(new_value)
                    new_values = list(values)
                    new_values[2] = container_name
                    tree.item(item_id, values=new_values)
                else:
                    messagebox.showerror("Error", f"Failed to update container for entry {entry_id}.")