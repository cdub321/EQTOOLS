import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sys
import os
import sqlite3

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.theme import set_dark_theme
from dictionaries import CLASS_OPTIONS, RACE_OPTIONS, DEITY_OPTIONS, CATEGORY_OPTIONS, TYPE_OPTIONS, EXPANSION_OPTIONS, SPELL_EFFECTS

class AAManagerTool:
    """AA Manager Tool - modular version for tabbed interface"""
    
    def __init__(self, parent_frame, db_manager):
        self.parent = parent_frame
        self.db_manager = db_manager
        self.conn = db_manager.connect()
        self.cursor = db_manager.get_cursor()
        
        # Connect to notes.db for spell effect details
        try:
            self.notes_db = sqlite3.connect('notes.db')
            self.notes_db.row_factory = sqlite3.Row  # Enable dict-like access
        except Exception as err:
            print(f"Warning: Could not connect to notes.db: {err}")
            self.notes_db = None
        
        # Configure parent frame grid
        self.parent.grid_rowconfigure(0, weight=1)
        self.parent.grid_columnconfigure(0, weight=1)
        
        # Create main container frame
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Initialize UI components
        self.create_ui()
        
        # Load initial data
        self.load_aa_list()
    
    def __del__(self):
        """Clean up SQLite connection"""
        if hasattr(self, 'notes_db') and self.notes_db:
            try:
                self.notes_db.close()
            except:
                pass
    
    def create_ui(self):
        """Create the complete AA Manager UI"""
        
        # Configure main frame grid - same layout as original
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=0)  # Left panel fixed width
        self.main_frame.grid_columnconfigure(1, weight=1)  # Center panel expandable
        self.main_frame.grid_columnconfigure(2, weight=0)  # Right panel fixed width
        
        # Create the three main panels exactly like original
        self.create_left_panel()
        self.create_center_panel() 
        self.create_right_panel()
    
    def create_left_panel(self):
        """Create left panel with AA list - identical to original"""
        left_panel = ttk.Frame(self.main_frame, relief=tk.SUNKEN, borderwidth=1)
        left_panel.grid(row=0, column=0, sticky="ns", padx=5, pady=5)
        left_panel.grid_rowconfigure(1, weight=1)
        left_panel.grid_columnconfigure(0, weight=1)
        
        # Search frame
        search_frame = ttk.Frame(left_panel)
        search_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        ttk.Label(search_frame, text="Search:").grid(row=0, column=0, padx=5)
        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.grid(row=0, column=1, columnspan=4, sticky="ew", padx=5)
        self.search_entry.bind('<KeyRelease>', lambda e: self.filter_aa_list(self.search_entry.get()))
        
        # Buttons in second row
        ttk.Button(search_frame, text="Clear", command=lambda: (self.search_entry.delete(0, 'end'), self.load_aa_list())).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(search_frame, text="Clone", command=self.clone_aa_ability).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(search_frame, text="Delete", command=self.delete_aa_ability).grid(row=1, column=2, padx=5, pady=5)
        
        # Configure grid weights to make search entry expand
        search_frame.grid_columnconfigure(1, weight=1)
        
        # AA tree frame
        aa_tree_frame = ttk.Frame(left_panel, relief=tk.SUNKEN, borderwidth=2)
        aa_tree_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        aa_tree_frame.grid_rowconfigure(0, weight=1)
        aa_tree_frame.grid_columnconfigure(0, weight=1)
        
        ttk.Label(aa_tree_frame, text="AA Abilities List", font=("Arial", 12, "bold")).grid(row=1, column=0, sticky="n")
        
        # AA tree
        self.aa_tree = ttk.Treeview(aa_tree_frame, columns=('id', 'name'), show='headings')
        self.aa_tree.heading('id', text='ID')
        self.aa_tree.heading('name', text='Name')
        self.aa_tree.column('id', width=40)
        self.aa_tree.column('name', width=200)
        self.aa_tree.grid(row=0, column=0, sticky="nsew")
        
        # Bind selection event
        self.aa_tree.bind('<<TreeviewSelect>>', self.on_aa_select)
        
        # Setup sorting
        self.setup_treeview_sorting(self.aa_tree)
    
    def create_center_panel(self):
        """Create center panel with AA details - identical to original"""  
        center_panel = ttk.Frame(self.main_frame, relief=tk.SUNKEN, borderwidth=1)
        center_panel.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        # AA Ability Fields
        ability_frame = ttk.LabelFrame(center_panel, text="AA Ability Information")
        ability_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        # Configure ability_frame to use more columns and center content
        for i in range(12):  # Expand to 12 columns for better spacing
            ability_frame.grid_columnconfigure(i, weight=1)
        
        ttk.Button(ability_frame, text="Save AA Information", command=self.save_aa_ability).grid(row=7, column=0, columnspan=12, pady=5)
        
        # Create entry fields with checkboxes integrated into the same rows
        # Name field keeps default width, others are smaller
        self.name_entry = self.create_label_entry_pair(ability_frame, "Name:", 1, 1)
        
        # Grant Only checkbox between Name and ID
        self.grant_only_var = tk.IntVar()
        grant_only_cb = tk.Checkbutton(ability_frame, text="Grant Only", variable=self.grant_only_var,
                                    fg="#ffffff", bg="#2d2d2d", activeforeground="#ffffff", activebackground="#3c3c3c",
                                    selectcolor="#2d2d2d", font=("Arial", 8))
        grant_only_cb.grid(row=1, column=3, sticky="w", padx=(10,2), pady=2)
        
        self.id_entry = self.create_label_entry_pair(ability_frame, "ID:", 1, 4, width=8)
        
        # Reset On Death checkbox between ID and First Rank ID
        self.reset_var = tk.IntVar()
        reset_cb = tk.Checkbutton(ability_frame, text="Reset On Death", variable=self.reset_var,
                                    fg="#ffffff", bg="#2d2d2d", activeforeground="#ffffff", activebackground="#3c3c3c",
                                    selectcolor="#2d2d2d", font=("Arial", 8))
        reset_cb.grid(row=1, column=6, sticky="w", padx=(10,2), pady=2)
        
        self.first_rank_entry = self.create_label_entry_pair(ability_frame, "First Rank ID:", 1, 7, width=8)
        
        # Category dropdown in last column of row 1
        ttk.Label(ability_frame, text="Category:").grid(row=1, column=9, sticky="e", padx=2, pady=2)
        self.category_var = tk.StringVar()
        self.category_dropdown = ttk.Combobox(ability_frame, textvariable=self.category_var, state="readonly", width=12)
        self.category_dropdown['values'] = [text for (val, text) in CATEGORY_OPTIONS]
        self.category_dropdown.current(0)
        self.category_dropdown.grid(row=1, column=10, sticky="w", padx=3, pady=3)
        
        self.status_entry = self.create_label_entry_pair(ability_frame, "Status:", 2, 1, width=8)
        
        # Enabled checkbox between Status and Charges
        self.enabled_var = tk.IntVar()
        enabled_cb = tk.Checkbutton(ability_frame, text="Enabled", variable=self.enabled_var,
                                    fg="#ffffff", bg="#2d2d2d", activeforeground="#ffffff", activebackground="#3c3c3c",
                                    selectcolor="#2d2d2d", font=("Arial", 8))
        enabled_cb.grid(row=2, column=3, sticky="w", padx=(10,2), pady=2)
        
        self.charges_entry = self.create_label_entry_pair(ability_frame, "Charges:", 2, 4, width=8)
        
        # Auto Grant checkbox between Charges and Drakkin Heritage
        self.auto_grant_var = tk.IntVar()
        auto_grant_cb = tk.Checkbutton(ability_frame, text="Auto Grant", variable=self.auto_grant_var,
                                    fg="#ffffff", bg="#2d2d2d", activeforeground="#ffffff", activebackground="#3c3c3c",
                                    selectcolor="#2d2d2d", font=("Arial", 8))
        auto_grant_cb.grid(row=2, column=6, sticky="w", padx=(10,2), pady=2)
        
        self.drakkin_entry = self.create_label_entry_pair(ability_frame, "Drakkin Heritage:", 2, 7, width=8)
        
        # Type dropdown in last column of row 2
        ttk.Label(ability_frame, text="Type:").grid(row=2, column=9, sticky="e", padx=3, pady=3)
        self.type_var = tk.StringVar()
        self.type_dropdown = ttk.Combobox(ability_frame, textvariable=self.type_var, state="readonly", width=12)
        self.type_dropdown['values'] = [text for (val, text) in TYPE_OPTIONS]
        self.type_dropdown.current(0)
        self.type_dropdown.grid(row=2, column=10, sticky="w", padx=3, pady=3)
        
        # Create bitmask checkbox frames - spread across 12-column layout
        race_frame = ttk.Frame(ability_frame, relief=tk.SUNKEN, borderwidth=1)
        race_frame.grid(row=6, column=0, sticky="ew", padx=5, pady=5, columnspan=4)
        
        class_frame = ttk.Frame(ability_frame, relief=tk.SUNKEN, borderwidth=1)
        class_frame.grid(row=6, column=4, sticky="ew", padx=5, pady=5, columnspan=4)
        
        deity_frame = ttk.Frame(ability_frame, relief=tk.SUNKEN, borderwidth=1)
        deity_frame.grid(row=6, column=8, sticky="ew", padx=5, pady=5, columnspan=4)
        
        # Create bitmask checkboxes with improved spacing - all frames have 6 rows for consistency
        # Race frame: 3 columns with increased horizontal spacing (16 races = 6 rows)
        self.race_checkvars = self.create_bitmask_checkboxes(race_frame, "Races", RACE_OPTIONS, 0, 0, cols=3, padx=10, pady=2)
        # Class frame: 3 columns with increased horizontal spacing (16 classes = 6 rows)  
        self.class_checkvars = self.create_bitmask_checkboxes(class_frame, "Classes", CLASS_OPTIONS, 0, 2, cols=3, padx=15, pady=2)
        # Deity frame: 3 columns with vertical spacing (17 deities = 6 rows)
        self.deity_checkvars = self.create_bitmask_checkboxes(deity_frame, "Deities", DEITY_OPTIONS, 0, 4, cols=3, padx=8, pady=2)
        
        # AA Ranks section - continue in next part...
        self.create_ranks_section(center_panel)
        self.create_effects_section(center_panel)
    
    def create_ranks_section(self, parent):
        """Create AA Ranks section"""
        # AA Ranks Fields
        ranks_frame = ttk.LabelFrame(parent, text="AA Rank Information")
        ranks_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        
        # Configure ranks_frame grid columns for proper spacing
        for i in range(12):  # Expand to 12 columns for better distribution
            ranks_frame.grid_columnconfigure(i, weight=1)
        
        # Add rank dropdown with consistent styling (no custom white styling)
        self.rank_dropdown_var = tk.StringVar()
        self.rank_dropdown_var.set("Select Rank")
        ttk.Label(ranks_frame, text="Select Rank:").grid(row=0, column=0, sticky="e", padx=5, pady=2)
        
        self.rank_dropdown = ttk.Combobox(ranks_frame, textvariable=self.rank_dropdown_var, 
                                         state="readonly", width=15)
        self.rank_dropdown.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        
        # Create inner frame for rank fields with consistent border styling
        rank_fields_frame = ttk.Frame(ranks_frame, relief=tk.SUNKEN, borderwidth=1)
        rank_fields_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5, columnspan=12)
        
        # Configure inner frame grid columns for better spacing
        for i in range(12):  # Expand to 12 columns for better distribution
            rank_fields_frame.grid_columnconfigure(i, weight=1)
        
        # Create reorganized rank entry fields layout with better spacing inside inner frame
        # Row 0: Rank ID, Expansion, Spell ID, Desc SID, Lower Hotkey SID
        self.rank_id_entry = self.create_label_entry_pair(rank_fields_frame, "Rank ID:", 0, 0, width=8)
        
        ttk.Label(rank_fields_frame, text="Expansion:").grid(row=0, column=2, sticky="e", padx=2, pady=2)
        self.expansion_var = tk.StringVar()
        self.expansion_dropdown = ttk.Combobox(rank_fields_frame, textvariable=self.expansion_var, state="readonly", width=12)
        self.expansion_dropdown['values'] = [text for (val, text) in EXPANSION_OPTIONS]
        self.expansion_dropdown.current(0)
        self.expansion_dropdown.grid(row=0, column=3, sticky="w", padx=2, pady=2)
        
        self.spell_entry = self.create_label_entry_pair(rank_fields_frame, "Spell_ID:", 0, 5, width=8)
        self.desc_sid_entry = self.create_label_entry_pair(rank_fields_frame, "Desc SID:", 0, 7, width=8)
        self.lower_hotkey_entry = self.create_label_entry_pair(rank_fields_frame, "Lower Hotkey SID:", 0, 9, width=8)
        
        # Row 1: Prev ID, Level Req, Spell Type, Title SID, Upper Hotkey SID  
        self.prev_id_entry = self.create_label_entry_pair(rank_fields_frame, "Prev ID:", 1, 0, width=8)
        self.level_req_entry = self.create_label_entry_pair(rank_fields_frame, "Level Req:", 1, 2, width=8)
        self.spell_type_entry = self.create_label_entry_pair(rank_fields_frame, "Spell Type:", 1, 5, width=8)
        self.title_sid_entry = self.create_label_entry_pair(rank_fields_frame, "Title SID:", 1, 7, width=8)
        self.upper_hotkey_entry = self.create_label_entry_pair(rank_fields_frame, "Upper Hotkey SID:", 1, 9, width=8)
        
        # Row 2: Next ID, Cost, Recast Time
        self.next_id_entry = self.create_label_entry_pair(rank_fields_frame, "Next ID:", 2, 0, width=8)
        self.cost_entry = self.create_label_entry_pair(rank_fields_frame, "Cost:", 2, 2, width=8)
        self.recast_entry = self.create_label_entry_pair(rank_fields_frame, "Recast Time:", 2, 5, width=8)
        
        # Buttons outside the inner frame
        button_frame = ttk.Frame(ranks_frame)
        button_frame.grid(row=2, column=0, columnspan=12, pady=5)
        
        ttk.Button(button_frame, text="Save AA Rank Info", command=self.save_aa_ranks).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Create Rank", command=self.create_new_rank).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete Rank", command=self.delete_rank).pack(side=tk.LEFT, padx=5)
    
    def create_effects_section(self, parent):
        """Create effects and prerequisites section"""
        effects_andreqs_frame = ttk.LabelFrame(parent, text="AA Rank Effects & Prerequisites")
        effects_andreqs_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        
        # Configure grid weights
        effects_andreqs_frame.grid_columnconfigure(1, weight=0)
        effects_andreqs_frame.grid_columnconfigure(2, weight=1)
        
        # Effects container
        effects_container = ttk.Frame(effects_andreqs_frame)
        effects_container.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        effects_container.grid_columnconfigure(0, weight=1)
        
        effects_frame = ttk.Frame(effects_container, relief=tk.SUNKEN, borderwidth=1)
        effects_frame.grid(row=0, column=0, sticky="nsew")
        
        # Create effects treeview - same columns and styling
        self.effects_treeview = ttk.Treeview(effects_frame, columns=("slot", "effect_id", "effect_name", "base1", "base2"), show="headings", height=6)
        self.effects_treeview.heading("slot", text="Slot")
        self.effects_treeview.heading("effect_id", text="Effect ID")
        self.effects_treeview.heading("effect_name", text="Effect Name")
        self.effects_treeview.heading("base1", text="Base1")
        self.effects_treeview.heading("base2", text="Base2")
        
        self.effects_treeview.column("slot", width=50, stretch=True)
        self.effects_treeview.column("effect_id", width=65, stretch=True)
        self.effects_treeview.column("effect_name", width=165, stretch=True)
        self.effects_treeview.column("base1", width=50, stretch=True)
        self.effects_treeview.column("base2", width=50, stretch=True)
        
        self.effects_treeview.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        
        # Bind click event to show effect details
        self.effects_treeview.bind('<ButtonRelease-1>', self.show_effect_details)
        
        # Effects buttons
        effects_button_frame = ttk.Frame(effects_frame)
        effects_button_frame.grid(row=1, column=0, sticky="e", padx=2, pady=2)
        ttk.Button(effects_button_frame, text="Lookup & Add Effects", command=self.open_spell_effects_lookup).pack(side=tk.RIGHT)
        
        # Center buttons frame
        buttons_frame = ttk.Frame(effects_andreqs_frame)
        buttons_frame.grid(row=1, column=1, sticky="n", padx=(45,5))  # More left padding to push center toward middle
        
        ttk.Button(buttons_frame, text="Add Effect", command=self.add_effect).grid(row=0, column=0, padx=5, pady=3)
        ttk.Button(buttons_frame, text="Delete Effect", command=self.delete_effect).grid(row=1, column=0, padx=5, pady=3)
        ttk.Button(buttons_frame, text="Add Prerequisite", command=self.add_prereq).grid(row=2, column=0, padx=5, pady=3)
        ttk.Button(buttons_frame, text="Delete Prerequisite", command=self.delete_prereq).grid(row=3, column=0, padx=5, pady=3)
        
        # Effects info label (moved to center column under buttons)
        self.effects_info_label = ttk.Label(buttons_frame, text="Select an effect to see\nBase1/Base2 descriptions", 
                                          wraplength=200, justify=tk.CENTER, font=("Arial", 9))
        self.effects_info_label.grid(row=4, column=0, padx=5, pady=(2,5))
        
        # Prerequisites container
        prereqs_container = ttk.Frame(effects_andreqs_frame)
        prereqs_container.grid(row=1, column=2, sticky="nse", padx=(5), pady=5)  # Right-justified (east) with no right padding
        prereqs_container.grid_columnconfigure(0, weight=1)
        
        prereqs_frame = ttk.Frame(prereqs_container, relief=tk.SUNKEN, borderwidth=1)
        prereqs_frame.grid(row=0, column=0, sticky="nsew")
        
        # Create prerequisites treeview
        self.prereq_treeview = ttk.Treeview(prereqs_frame, columns=("rank_id", "aa_id", "aa_name", "points"), show="headings", height=6)
        self.prereq_treeview.heading("rank_id", text="Rank ID")
        self.prereq_treeview.heading("aa_id", text="AA ID")
        self.prereq_treeview.heading("aa_name", text="AA Name")
        self.prereq_treeview.heading("points", text="Points")
        
        self.prereq_treeview.column("rank_id", width=75, stretch=True)
        self.prereq_treeview.column("aa_id", width=60, stretch=True)
        self.prereq_treeview.column("aa_name", width=165, stretch=True)
        self.prereq_treeview.column("points", width=50, stretch=True)
        
        self.prereq_treeview.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        
        # Prerequisites button
        prereq_button_frame = ttk.Frame(prereqs_frame)
        prereq_button_frame.grid(row=1, column=0, sticky="e", padx=2, pady=2)
        ttk.Button(prereq_button_frame, text="Lookup & Add AA", command=self.open_aa_lookup).pack(side=tk.RIGHT)
        
        # Make treeviews editable
        self.make_treeview_editable(
            self.effects_treeview, 
            ["slot", "effect_id", "effect_name", "base1", "base2"],
            "aa_rank_effects",
            "slot",
            self.rank_id_entry
        )
        
        self.make_treeview_editable(
            self.prereq_treeview, 
            ["rank_id", "aa_id", "aa_name", "points"],
            "aa_rank_prereqs",
            "rank_id",
            self.rank_id_entry
        )
    
    def create_right_panel(self):
        """Create right panel with string information - identical to original"""
        right_panel = ttk.Frame(self.main_frame, relief=tk.SUNKEN, borderwidth=1)
        right_panel.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)
        
        # String information frame
        string_frame = ttk.Frame(right_panel, relief=tk.SUNKEN, borderwidth=1)
        string_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Title section
        title_frame = ttk.LabelFrame(string_frame, text="Title")
        title_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5, columnspan=2)
        self.title_text = tk.Text(title_frame, height=3, width=40, wrap=tk.WORD)
        self.title_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Description section
        desc_frame = ttk.LabelFrame(string_frame, text="Description")
        desc_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5, columnspan=2)
        self.desc_text = tk.Text(desc_frame, height=5, width=40, wrap=tk.WORD)
        self.desc_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Hotkeys section
        hotkeys_frame = ttk.LabelFrame(string_frame, text="Hotkeys")
        hotkeys_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5, columnspan=2)
        
        # Lower hotkey
        lower_frame = ttk.Frame(hotkeys_frame)
        lower_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.lower_hotkey_text = tk.Text(lower_frame, height=2, width=40, wrap=tk.WORD)
        self.lower_hotkey_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Upper hotkey
        upper_frame = ttk.Frame(hotkeys_frame)
        upper_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        self.upper_hotkey_text = tk.Text(upper_frame, height=2, width=40, wrap=tk.WORD)
        self.upper_hotkey_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Save button
        ttk.Button(string_frame, text="Save String Information", command=self.save_all_strings).grid(row=3, column=0, columnspan=2, padx=5, pady=5)
        
        # Disclaimer
        disclaimer_frame = ttk.Frame(string_frame, relief=tk.SUNKEN, borderwidth=1)
        disclaimer_frame.grid(row=4, column=0, sticky="ew", padx=5, pady=5, columnspan=2)
        disclaimer_text = "WARNING: Editing db_str requires distributing a new dbstr_us.txt file to players."
        ttk.Label(disclaimer_frame, text=disclaimer_text, foreground="red", wraplength=300).grid(row=0, column=0, padx=5, pady=5)
        
        # Spell information section
        spell_frame = ttk.LabelFrame(string_frame, text="Associated Spell")
        spell_frame.grid(row=5, column=0, sticky="nsew", padx=5, pady=5, columnspan=2)
        
        # Spell name label
        self.spell_name_label = ttk.Label(spell_frame, text="No spell associated", font=("Arial", 10, "bold"))
        self.spell_name_label.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        # Spell effects display (scrollable text widget)
        self.spell_effects_text = tk.Text(spell_frame, height=8, width=40, wrap=tk.WORD, state=tk.DISABLED)
        self.spell_effects_text.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Configure spell frame to expand
        spell_frame.grid_rowconfigure(1, weight=1)
        spell_frame.grid_columnconfigure(0, weight=1)
        
        # Bind rank selection to update string display (overwrites previous bind!)
        self.rank_dropdown.bind("<<ComboboxSelected>>", lambda e: self.update_string_display())
    
    def recreate_rank_dropdown(self, ranks):
        """Recreate the rank dropdown with new values"""
        # Get parent frame and grid info
        parent = self.rank_dropdown.master
        grid_info = self.rank_dropdown.grid_info()
        
        # Destroy old dropdown
        self.rank_dropdown.destroy()
        
        # Create new dropdown
        self.rank_dropdown = ttk.Combobox(parent, textvariable=self.rank_dropdown_var, state="readonly")
        self.rank_dropdown['values'] = ranks
        self.rank_dropdown_var.set(ranks[0])
        
        # Restore grid position
        self.rank_dropdown.grid(**grid_info)
        
        # Rebind events
        self.rank_dropdown.bind("<<ComboboxSelected>>", self.load_rank_details)
        
        print(f"DEBUG: Recreated dropdown with values: {ranks}")

    # Helper methods (same as original functions)
    def create_label_entry_pair(self, frame, label_text, row, column, entry_column=None, width=None):
        if entry_column is None:
            entry_column = column + 1
        
        ttk.Label(frame, text=label_text).grid(row=row, column=column, sticky="e", padx=2, pady=2)
        entry = ttk.Entry(frame, width=width)
        entry.grid(row=row, column=entry_column, sticky="w", padx=2, pady=2, columnspan=1)
        return entry
    
    # I'll continue with the remaining methods in the next part...
    # This includes all the database operations, UI handlers, etc.
    
    # Core functionality methods (converted from original functions)
    def load_aa_list(self):
        """Load AA list into treeview"""
        try:
            aa_list = self.db_manager.execute_query("SELECT id, name FROM aa_ability ORDER BY name")
            self.aa_tree.delete(*self.aa_tree.get_children())
            for aa in aa_list:
                self.aa_tree.insert('', 'end', values=(aa['id'], aa['name']))
        except Exception as err:
            messagebox.showerror("Database Error", f"Failed to load AA list:\n{err}")
    
    def filter_aa_list(self, search_term):
        """Filter AA list based on search term"""
        try:
            query = "SELECT id, name FROM aa_ability WHERE name LIKE %s ORDER BY name"
            aa_list = self.db_manager.execute_query(query, (f"%{search_term}%",))
            self.aa_tree.delete(*self.aa_tree.get_children())
            for aa in aa_list:
                self.aa_tree.insert('', 'end', values=(aa['id'], aa['name']))
        except Exception as err:
            messagebox.showerror("Database Error", f"Failed to filter AA list:\n{err}")
    
    def on_aa_select(self, event):
        """Handle AA selection"""
        selected_item = event.widget.selection()
        if selected_item:
            aa_id = event.widget.item(selected_item)['values'][0]
            self.load_aa_details(aa_id)
            self.load_string_info()
    
    def load_aa_details(self, aa_id):
        """Load AA details for selected AA"""
        try:
            # Clear previous data
            self.clear_all_fields()
            
            # Load basic AA info
            aa_data = self.db_manager.execute_query("SELECT * FROM aa_ability WHERE id = %s", (aa_id,), fetch_all=False)
            
            if not aa_data:
                messagebox.showwarning("Not Found", f"AA ability with ID {aa_id} not found")
                return
            
            # Populate fields
            self.id_entry.insert(0, aa_data.get('id', ''))
            self.name_entry.insert(0, aa_data.get('name', ''))
            self.status_entry.insert(0, aa_data.get('status', '0'))
            self.charges_entry.insert(0, aa_data.get('charges', '0'))
            self.first_rank_entry.insert(0, aa_data.get('first_rank_id', '-1'))
            self.drakkin_entry.insert(0, aa_data.get('drakkin_heritage', '127'))
            
            # Set checkboxes
            self.grant_only_var.set(int(aa_data.get('grant_only', '0')))
            self.enabled_var.set(int(aa_data.get('enabled', '1')))
            self.reset_var.set(int(aa_data.get('reset_on_death', '0')))
            self.auto_grant_var.set(int(aa_data.get('auto_grant_enabled', '1')))
            
            # Set dropdowns
            category_value = str(aa_data.get('category', '-1'))
            for i, (val, text) in enumerate(CATEGORY_OPTIONS):
                if val == category_value:
                    self.category_dropdown.current(i)
                    break
            else:
                self.category_dropdown.current(0)
            
            type_value = str(aa_data.get('type', '1'))
            for i, (val, text) in enumerate(TYPE_OPTIONS):
                if val == type_value:
                    self.type_dropdown.current(i)
                    break
            else:
                self.type_dropdown.current(0)
            
            # Set bitmask checkboxes
            self.set_bitmask_checkboxes(self.race_checkvars, int(aa_data.get('races', '65535')))
            self.set_bitmask_checkboxes(self.class_checkvars, int(aa_data.get('classes', '65535')))
            self.set_bitmask_checkboxes(self.deity_checkvars, int(aa_data.get('deities', '131071')))
            
            # Load ranks
            first_rank_id = aa_data.get('first_rank_id')
            print(f"DEBUG: first_rank_id = {first_rank_id}, type = {type(first_rank_id)}")
            
            if first_rank_id and int(first_rank_id) != -1:
                print(f"DEBUG: Getting rank chain for first_rank_id: {first_rank_id}")
                ranks = self.get_rank_chain(first_rank_id)
                print(f"DEBUG: Found ranks: {ranks}")
                if ranks:
                    print(f"DEBUG: About to set dropdown values to: {ranks}")
                    self.rank_dropdown['values'] = ranks
                    print(f"DEBUG: Dropdown values immediately after setting: {self.rank_dropdown['values']}")
                    self.rank_dropdown_var.set(str(ranks[0]))
                    print(f"DEBUG: Dropdown var after setting: {self.rank_dropdown_var.get()}")
                    
                    # Check again after a brief moment
                    self.rank_dropdown.after(100, lambda: print(f"DEBUG: Dropdown values after 100ms: {self.rank_dropdown['values']}"))
                    self.load_rank_details()
                else:
                    # Clear dropdown if no ranks found
                    self.rank_dropdown['values'] = []
                    self.rank_dropdown_var.set("No Ranks")
                    print("DEBUG: No ranks found")
            else:
                # Clear dropdown if no first rank
                self.rank_dropdown['values'] = []
                self.rank_dropdown_var.set("No First Rank")
                print(f"DEBUG: No first rank (value: {first_rank_id})")
                    
        except Exception as err:
            messagebox.showerror("Database Error", f"Failed to load AA details:\n{err}")
    
    def get_rank_chain(self, first_rank_id):
        """Get all ranks in a chain"""
        ranks = []
        current_rank_id = first_rank_id
        
        print(f"DEBUG: get_rank_chain starting with ID: {current_rank_id}")
        
        while current_rank_id and current_rank_id != -1:
            print(f"DEBUG: Querying for rank ID: {current_rank_id}")
            rank_data = self.db_manager.execute_query("SELECT id, next_id FROM aa_ranks WHERE id = %s", (current_rank_id,), fetch_all=False)
            print(f"DEBUG: Query result: {rank_data}")
            if not rank_data:
                print(f"DEBUG: No rank data found for ID: {current_rank_id}")
                break
            ranks.append(rank_data['id'])
            current_rank_id = rank_data['next_id']
            print(f"DEBUG: Added rank {rank_data['id']}, next_id: {current_rank_id}")
        
        print(f"DEBUG: Final ranks list: {ranks}")
        return ranks
    
    def clear_all_fields(self):
        """Clear all input fields"""
        # Clear entry fields
        for entry in [self.id_entry, self.name_entry, self.drakkin_entry, self.status_entry, 
                     self.charges_entry, self.first_rank_entry]:
            entry.delete(0, 'end')
        
        # Reset dropdowns
        self.category_dropdown.current(0)
        self.type_dropdown.current(0)
        
        # Reset checkboxes
        self.grant_only_var.set(0)
        self.enabled_var.set(1)
        self.reset_var.set(0)
        self.auto_grant_var.set(1)
        
        # Clear rank fields
        self.clear_rank_fields()
        
        # Clear treeviews
        for item in self.effects_treeview.get_children():
            self.effects_treeview.delete(item)
        for item in self.prereq_treeview.get_children():
            self.prereq_treeview.delete(item)
        
        # Clear string texts
        self.title_text.delete(1.0, tk.END)
        self.desc_text.delete(1.0, tk.END)
        self.lower_hotkey_text.delete(1.0, tk.END)
        self.upper_hotkey_text.delete(1.0, tk.END)
    
    def clear_rank_fields(self):
        """Clear rank-specific fields"""
        rank_entries = [self.rank_id_entry, self.upper_hotkey_entry, self.lower_hotkey_entry,
                       self.title_sid_entry, self.desc_sid_entry, self.cost_entry, 
                       self.level_req_entry, self.spell_entry, self.spell_type_entry,
                       self.recast_entry, self.prev_id_entry, self.next_id_entry]
        
        for entry in rank_entries:
            entry.delete(0, 'end')
        
        # Don't clear dropdown values - they should persist
        # Only clear if we're doing a full clear, not a rank detail load
        # self.rank_dropdown['values'] = []
        # self.rank_dropdown_var.set("Select Rank")
    
    def create_bitmask_checkboxes(self, parent, label_text, options, row, column, cols=3, padx=2, pady=0):
        """Create bitmask checkboxes with configurable layout"""
        label = ttk.Label(parent, text=label_text, font=("Arial", 12, "bold"))
        label.grid(row=row, column=column, sticky="n", columnspan=2)

        frame = ttk.Frame(parent)
        frame.grid(row=row+1, column=column, sticky="w", padx=10, columnspan=2)

        checkvars = []
        for i, (option_name, bit_value) in enumerate(options.items()):
            var = tk.IntVar()
            cb = tk.Checkbutton(frame, text=option_name, variable=var,
                                fg="#ffffff", bg="#2d2d2d", activeforeground="#ffffff", activebackground="#3c3c3c",
                                selectcolor="#2d2d2d", font=("Arial", 8))
            cb.grid(row=i//cols, column=i%cols, sticky="w", padx=padx, pady=pady)
            checkvars.append((bit_value, var))

        return checkvars
    
    def set_bitmask_checkboxes(self, checkvars, bitmask):
        """Set bitmask checkbox values"""
        for bit_value, var in checkvars:
            if bitmask & bit_value:
                var.set(1)
            else:
                var.set(0)
    
    def setup_treeview_sorting(self, tree):
        """Setup treeview column sorting - same as original"""
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
    
    # Placeholder implementations for methods we'll implement later
    def load_rank_details(self, event=None):
        """Load rank details for selected rank"""
        selected_rank_id = self.rank_dropdown_var.get()
        if not selected_rank_id or selected_rank_id == "Select Rank":
            return
            
        try:
            self.clear_rank_fields()
            
            # Clear treeviews
            for item in self.effects_treeview.get_children():
                self.effects_treeview.delete(item)
            
            for item in self.prereq_treeview.get_children():
                self.prereq_treeview.delete(item)
            
            # Load rank data
            rank_data = self.db_manager.execute_query("SELECT * FROM aa_ranks WHERE id = %s", (selected_rank_id,), fetch_all=False)
            
            if not rank_data:
                messagebox.showwarning("Not Found", f"AA rank with ID {selected_rank_id} not found")
                return
                
            # Load all rank data into their respective entry widgets
            self.rank_id_entry.insert(0, rank_data.get('id', ''))
            self.upper_hotkey_entry.insert(0, rank_data.get('upper_hotkey_sid', '-1'))
            self.lower_hotkey_entry.insert(0, rank_data.get('lower_hotkey_sid', '-1'))
            self.title_sid_entry.insert(0, rank_data.get('title_sid', '-1'))
            self.desc_sid_entry.insert(0, rank_data.get('desc_sid', '-1'))
            self.cost_entry.insert(0, rank_data.get('cost', '1'))
            self.level_req_entry.insert(0, rank_data.get('level_req', '1'))
            self.spell_entry.insert(0, rank_data.get('spell', '-1'))
            self.spell_type_entry.insert(0, rank_data.get('spell_type', '0'))
            self.recast_entry.insert(0, rank_data.get('recast_time', '0'))
            
            # Set expansion dropdown
            expansion_value = str(rank_data.get('expansion', '-1'))
            for i, (val, text) in enumerate(EXPANSION_OPTIONS):
                if val == expansion_value:
                    self.expansion_dropdown.current(i)
                    break
            else:
                self.expansion_dropdown.current(0)
                
            self.prev_id_entry.insert(0, rank_data.get('prev_id', '-1'))
            self.next_id_entry.insert(0, rank_data.get('next_id', '-1'))
            
            # Load string information for this rank
            self.load_string_info()
            
            # Load rank effects
            effects = self.db_manager.execute_query("SELECT * FROM aa_rank_effects WHERE rank_id = %s ORDER BY slot", (rank_data['id'],))
            
            if effects:
                for effect in effects:
                    effect_id = effect.get('effect_id', '0')
                    effect_name = SPELL_EFFECTS.get(int(effect_id), "Unknown Effect")
                    self.effects_treeview.insert('', 'end', values=(
                        effect.get('slot', ''),
                        effect_id,
                        effect_name,
                        effect.get('base1', ''),
                        effect.get('base2', '')
                    ))
            
            # Load rank prerequisites
            prereqs = self.db_manager.execute_query("SELECT * FROM aa_rank_prereqs WHERE rank_id = %s", (rank_data['id'],))
            
            if prereqs:
                for prereq in prereqs:
                    aa_id = prereq.get('aa_id', '')
                    aa_name = ""
                    if aa_id:
                        aa_data = self.db_manager.execute_query("SELECT name FROM aa_ability WHERE id = %s", (aa_id,), fetch_all=False)
                        if aa_data:
                            aa_name = aa_data['name']
                    
                    self.prereq_treeview.insert('', 'end', values=(
                        prereq.get('rank_id', ''),
                        aa_id,
                        aa_name,
                        prereq.get('points', '')
                    ))
            
            # Update spell display after loading rank details
            self.update_spell_display()
                    
        except Exception as err:
            messagebox.showerror("Database Error", f"Failed to load rank details:\n{err}")
    
    def load_string_info(self):
        """Load string content from db_str table based on the SIDs in the rank information"""
        try:
            # Clear all text widgets first
            self.title_text.delete(1.0, tk.END)
            self.desc_text.delete(1.0, tk.END)
            self.lower_hotkey_text.delete(1.0, tk.END)
            self.upper_hotkey_text.delete(1.0, tk.END)
            
            # Get the SIDs from the rank information entries
            title_sid = self.title_sid_entry.get()
            desc_sid = self.desc_sid_entry.get()
            lower_sid = self.lower_hotkey_entry.get()
            upper_sid = self.upper_hotkey_entry.get()
            
            # Load title string (type 1)
            if title_sid and title_sid != '-1':
                result = self.db_manager.execute_query("SELECT value FROM db_str WHERE id = %s AND type = 1", (title_sid,), fetch_all=False)
                if result:
                    self.title_text.insert(1.0, result['value'])
            
            # Load description string (type 4)
            if desc_sid and desc_sid != '-1':
                result = self.db_manager.execute_query("SELECT value FROM db_str WHERE id = %s AND type = 4", (desc_sid,), fetch_all=False)
                if result:
                    self.desc_text.insert(1.0, result['value'])
            
            # Load lower hotkey string (type 3) - but display in upper window due to historical flip
            if lower_sid and lower_sid != '-1':
                result = self.db_manager.execute_query("SELECT value FROM db_str WHERE id = %s AND type = 3", (lower_sid,), fetch_all=False)
                if result:
                    self.upper_hotkey_text.insert(1.0, result['value'])
            
            # Load upper hotkey string (type 2) - but display in lower window due to historical flip
            if upper_sid and upper_sid != '-1':
                result = self.db_manager.execute_query("SELECT value FROM db_str WHERE id = %s AND type = 2", (upper_sid,), fetch_all=False)
                if result:
                    self.lower_hotkey_text.insert(1.0, result['value'])
                    
        except Exception as err:
            messagebox.showerror("Database Error", f"Failed to load string information:\n{err}")
    
    def get_bitmask_from_checkboxes(self, checkvars):
        """Get bitmask value from checkbox variables"""
        bitmask = 0
        for bit_value, var in checkvars:
            if var.get():
                bitmask |= bit_value
        return bitmask
    
    def get_spell_effect_details(self, effect_id):
        """Get spell effect details from notes.db"""
        if not self.notes_db:
            return None
            
        try:
            cursor = self.notes_db.cursor()
            cursor.execute("""
                SELECT display_name, description, base1_description, base2_description, notes 
                FROM spell_effects_details 
                WHERE id = ?
            """, (effect_id,))
            
            result = cursor.fetchone()
            if result:
                return {
                    'display_name': result['display_name'],
                    'description': result['description'],
                    'base1_description': result['base1_description'],
                    'base2_description': result['base2_description'],
                    'notes': result['notes']
                }
            return None
            
        except Exception as err:
            print(f"Error getting spell effect details: {err}")
            return None
    
    def get_spell_details(self, spell_id):
        """Get spell details from notes.db"""
        if not self.notes_db or spell_id <= 0:
            return None
            
        try:
            cursor = self.notes_db.cursor()
            cursor.execute("""
                SELECT * FROM spells WHERE id = ?
            """, (spell_id,))
            
            result = cursor.fetchone()
            return dict(result) if result else None
            
        except Exception as err:
            print(f"Error getting spell details: {err}")
            return None
    
    def format_spell_effects(self, spell_data):
        """Format spell effects into readable text"""
        if not spell_data:
            return "No spell data available"
            
        effects_text = f"Spell ID: {spell_data['id']}\n"
        effects_text += f"Range: {spell_data.get('range', 0)}\n"
        effects_text += f"Cast Time: {spell_data.get('cast_time', 0)}ms\n\n"
        effects_text += "Effects:\n"
        
        # Process all 12 possible effects, only showing ones that exist
        effect_count = 0
        for i in range(1, 13):
            effect_id = spell_data.get(f'effectid{i}', 0)
            if effect_id is not None and effect_id > 0 and effect_id != 254:
                effect_count += 1
                base_value = spell_data.get(f'effect_base_value{i}', 0)
                limit_value = spell_data.get(f'effect_limit_value{i}', 0)
                max_value = spell_data.get(f'max{i}', 0)
                
                # Get effect details from our spell effects table
                effect_details = self.get_spell_effect_details(effect_id)
                effect_name = effect_details['display_name'] if effect_details else f"Effect {effect_id}"
                
                effects_text += f"{effect_count}. {effect_name}\n"
                
                if effect_details:
                    if effect_details.get('base1_description', 'none') != 'none':
                        effects_text += f"   Base ({base_value}): {effect_details['base1_description']}\n"
                    if effect_details.get('base2_description', 'none') != 'none':
                        effects_text += f"   Limit ({limit_value}): {effect_details['base2_description']}\n"
                    if max_value and effect_details.get('max_description') and effect_details['max_description'] != 'none':
                        effects_text += f"   Max ({max_value}): {effect_details['max_description']}\n"
                else:
                    effects_text += f"   Base: {base_value}, Limit: {limit_value}, Max: {max_value}\n"
                
                effects_text += "\n"
        
        if effect_count == 0:
            effects_text += "No effects found for this spell.\n"
        
        return effects_text
    
    def update_spell_display(self):
        """Update the spell display based on current rank selection"""
        try:
            # Get current rank spell ID
            spell_id = self.spell_entry.get() if hasattr(self, 'spell_entry') and self.spell_entry.get() else None
            
            if not spell_id or spell_id == '-1' or int(spell_id) <= 0:
                # No spell associated
                self.spell_name_label.config(text="No spell associated")
                self.spell_effects_text.config(state=tk.NORMAL)
                self.spell_effects_text.delete(1.0, tk.END)
                self.spell_effects_text.insert(1.0, "This AA rank does not have an associated spell.")
                self.spell_effects_text.config(state=tk.DISABLED)
                return
                
            # Get spell details
            spell_data = self.get_spell_details(int(spell_id))
            
            if not spell_data:
                self.spell_name_label.config(text=f"Spell {spell_id} (Not Found)")
                self.spell_effects_text.config(state=tk.NORMAL)
                self.spell_effects_text.delete(1.0, tk.END)
                self.spell_effects_text.insert(1.0, f"Spell data for ID {spell_id} not found in database.")
                self.spell_effects_text.config(state=tk.DISABLED)
                return
                
            # Update spell display
            spell_name = spell_data.get('name', f'Spell {spell_id}')
            self.spell_name_label.config(text=f"{spell_name} (ID: {spell_id})")
            
            # Format and display spell effects
            effects_text = self.format_spell_effects(spell_data)
            self.spell_effects_text.config(state=tk.NORMAL)
            self.spell_effects_text.delete(1.0, tk.END)
            self.spell_effects_text.insert(1.0, effects_text)
            self.spell_effects_text.config(state=tk.DISABLED)
            
        except Exception as err:
            print(f"Error updating spell display: {err}")
            self.spell_name_label.config(text="Error loading spell")
            self.spell_effects_text.config(state=tk.NORMAL)
            self.spell_effects_text.delete(1.0, tk.END)
            self.spell_effects_text.insert(1.0, f"Error loading spell information: {err}")
            self.spell_effects_text.config(state=tk.DISABLED)
    
    def update_string_display(self):
        """Update string and spell displays when rank changes"""
        # This method is called when rank dropdown selection changes
        # load_rank_details already calls update_spell_display at the end
        self.load_rank_details()
    
    def show_effect_details(self, event):
        """Show detailed effect information when an effect is selected"""
        try:
            selected_item = self.effects_treeview.selection()
            if not selected_item:
                self.effects_info_label.config(text="Select an effect to see Base1/Base2 descriptions")
                return
                
            # Get the effect data
            values = self.effects_treeview.item(selected_item[0])['values']
            if len(values) < 5:
                return
                
            effect_id = values[1]  # effect_id is in column 1
            base1_value = values[3]  # base1 is in column 3
            base2_value = values[4]  # base2 is in column 4
            
            # Get detailed effect information
            effect_details = self.get_spell_effect_details(int(effect_id))
            
            if effect_details:
                info_text = f"Effect {effect_id}: {effect_details['display_name']}\n"
                info_text += f"Base1 ({base1_value}): {effect_details['base1_description']}\n"
                info_text += f"Base2 ({base2_value}): {effect_details['base2_description']}"
                
                if effect_details['notes']:
                    info_text += f"\nNotes: {effect_details['notes']}"
            else:
                info_text = f"Effect {effect_id}: No detailed information available"
                
            self.effects_info_label.config(text=info_text)
            
        except Exception as err:
            print(f"Error showing effect details: {err}")
            self.effects_info_label.config(text="Error loading effect details")
    
    def find_available_id_all_tables(self, start_id=1):
        """Find an ID that's available in aa_ability, aa_ranks, AND db_str tables"""
        try:
            # Find next available ID that doesn't exist in any of the three tables
            result = self.db_manager.execute_query("""
                SELECT MIN(t.id) as available_id
                FROM (
                    SELECT %s as id
                    UNION ALL
                    SELECT aa.id + 1 FROM aa_ability aa
                    UNION ALL  
                    SELECT ar.id + 1 FROM aa_ranks ar
                    UNION ALL
                    SELECT ds.id + 1 FROM db_str ds
                ) t
                WHERE t.id >= %s
                AND t.id NOT IN (SELECT id FROM aa_ability)
                AND t.id NOT IN (SELECT id FROM aa_ranks) 
                AND t.id NOT IN (SELECT id FROM db_str)
                ORDER BY t.id
                LIMIT 1
            """, (start_id, start_id), fetch_all=False)
            
            return result['available_id'] if result and result['available_id'] else start_id
            
        except Exception as err:
            print(f"Error finding available ID: {err}")
            # Fallback: simple increment from start_id
            test_id = start_id
            while True:
                # Check all three tables
                aa_exists = self.db_manager.execute_query("SELECT id FROM aa_ability WHERE id = %s", (test_id,), fetch_all=False)
                rank_exists = self.db_manager.execute_query("SELECT id FROM aa_ranks WHERE id = %s", (test_id,), fetch_all=False) 
                str_exists = self.db_manager.execute_query("SELECT id FROM db_str WHERE id = %s", (test_id,), fetch_all=False)
                
                if not aa_exists and not rank_exists and not str_exists:
                    return test_id
                test_id += 1
                
                # Safety break to avoid infinite loop
                if test_id > start_id + 10000:
                    raise Exception("Could not find available ID within reasonable range")
    
    def find_available_rank_id_only(self, start_id=1):
        """Find an ID that's available only in aa_ranks table (for adding to existing chains)"""
        try:
            result = self.db_manager.execute_query("""
                SELECT MIN(t1.id + 1) as next_id
                FROM aa_ranks t1
                LEFT JOIN aa_ranks t2 ON t1.id + 1 = t2.id
                WHERE t1.id >= %s AND t2.id IS NULL
            """, (start_id,), fetch_all=False)
            
            return result['next_id'] if result and result['next_id'] else start_id
            
        except Exception as err:
            print(f"Error finding available rank ID: {err}")
            return start_id
    
    def create_db_str_entries(self, rank_id, title_text="New AA Title", desc_text="New AA Description"):
        """Create db_str entries for a new AA rank"""
        try:
            # Create title entry (type 1)
            self.db_manager.execute_update("""
                INSERT INTO db_str (id, type, value) 
                VALUES (%s, 1, %s)
                ON DUPLICATE KEY UPDATE value = %s
            """, (rank_id, title_text, title_text))
            
            # Create description entry (type 4) 
            self.db_manager.execute_update("""
                INSERT INTO db_str (id, type, value)
                VALUES (%s, 4, %s) 
                ON DUPLICATE KEY UPDATE value = %s
            """, (rank_id, desc_text, desc_text))
            
            return True
            
        except Exception as err:
            print(f"Error creating db_str entries: {err}")
            return False
    
    def create_rank_with_defaults(self, rank_id, title_sid, desc_sid, prev_id=-1, next_id=-1):
        """Create a new AA rank with default values"""
        try:
            # Use default values as specified in requirements
            rank_data = {
                'id': rank_id,
                'upper_hotkey_sid': -1,
                'lower_hotkey_sid': -1, 
                'title_sid': title_sid,
                'desc_sid': desc_sid,
                'cost': 1,
                'level_req': 51,
                'spell': -1,
                'spell_type': 0,
                'recast_time': 0,
                'expansion': -1,
                'prev_id': prev_id,
                'next_id': next_id
            }
            
            # Insert the new rank
            query = """
                INSERT INTO aa_ranks (
                    id, upper_hotkey_sid, lower_hotkey_sid, title_sid, desc_sid,
                    cost, level_req, spell, spell_type, recast_time, expansion,
                    prev_id, next_id
                ) VALUES (
                    %(id)s, %(upper_hotkey_sid)s, %(lower_hotkey_sid)s, %(title_sid)s, 
                    %(desc_sid)s, %(cost)s, %(level_req)s, %(spell)s, %(spell_type)s,
                    %(recast_time)s, %(expansion)s, %(prev_id)s, %(next_id)s
                )
            """
            
            # Use execute_update to commit INSERTs
            self.db_manager.execute_update(query, rank_data)
            return True
            
        except Exception as err:
            print(f"Error creating rank: {err}")
            return False
    
    def save_aa_ability(self): 
        """Save AA ability data to database"""
        try:
            aa_id = self.id_entry.get()
            if not aa_id:
                messagebox.showwarning("Error", "AA ID is required")
                return

            # Prepare data dictionary
            aa_data = {
                'id': aa_id,
                'name': self.name_entry.get(),
                'category': CATEGORY_OPTIONS[self.category_dropdown.current()][0] or '-1',
                'classes': self.get_bitmask_from_checkboxes(self.class_checkvars) or '65535',
                'races': self.get_bitmask_from_checkboxes(self.race_checkvars) or '65535',
                'drakkin_heritage': self.drakkin_entry.get() or '127',
                'deities': self.get_bitmask_from_checkboxes(self.deity_checkvars) or '131071',
                'status': self.status_entry.get() or '0',
                'type': TYPE_OPTIONS[self.type_dropdown.current()][0] or '1',
                'charges': self.charges_entry.get() or '0',
                'grant_only': self.grant_only_var.get() or '0',
                'first_rank_id': self.first_rank_entry.get() or '-1',
                'enabled': self.enabled_var.get() or '1',
                'reset_on_death': self.reset_var.get() or '0',
                'auto_grant_enabled': self.auto_grant_var.get() or '1'
            }

            # Check if this is an update or insert
            exists = self.db_manager.execute_query("SELECT id FROM aa_ability WHERE id = %s", (aa_id,), fetch_all=False)

            if exists:
                # Update existing record
                query = """
                    UPDATE aa_ability SET 
                        name = %(name)s,
                        category = %(category)s,
                        classes = %(classes)s,
                        races = %(races)s,
                        drakkin_heritage = %(drakkin_heritage)s,
                        deities = %(deities)s,
                        status = %(status)s,
                        type = %(type)s,
                        charges = %(charges)s,
                        grant_only = %(grant_only)s,
                        first_rank_id = %(first_rank_id)s,
                        enabled = %(enabled)s,
                        reset_on_death = %(reset_on_death)s,
                        auto_grant_enabled = %(auto_grant_enabled)s
                    WHERE id = %(id)s
                """
            else:
                # Insert new record
                query = """
                    INSERT INTO aa_ability (
                        id, name, category, classes, races, drakkin_heritage, deities, 
                        status, type, charges, grant_only, first_rank_id, enabled, 
                        reset_on_death, auto_grant_enabled
                    ) VALUES (
                        %(id)s, %(name)s, %(category)s, %(classes)s, %(races)s, %(drakkin_heritage)s, 
                        %(deities)s, %(status)s, %(type)s, %(charges)s, %(grant_only)s, 
                        %(first_rank_id)s, %(enabled)s, %(reset_on_death)s, %(auto_grant_enabled)s
                    )
                """

            # Use execute_update so changes commit
            self.db_manager.execute_update(query, aa_data)
            messagebox.showinfo("Success", "AA Ability saved successfully")
            
        except Exception as err:
            messagebox.showerror("Database Error", f"Failed to save AA Ability:\n{err}")
    
    def save_aa_ranks(self): 
        """Save AA rank data to database"""
        try:
            rank_id = self.rank_id_entry.get()
            if not rank_id:
                messagebox.showwarning("Error", "Rank ID is required")
                return

            # Prepare data dictionary
            rank_data = {
                'id': rank_id,
                'upper_hotkey_sid': self.upper_hotkey_entry.get() or '-1',
                'lower_hotkey_sid': self.lower_hotkey_entry.get() or '-1',
                'title_sid': self.title_sid_entry.get() or '-1',
                'desc_sid': self.desc_sid_entry.get() or '-1',
                'cost': self.cost_entry.get() or '1',
                'level_req': self.level_req_entry.get() or '1',
                'spell': self.spell_entry.get() or '-1',
                'spell_type': self.spell_type_entry.get() or '0',
                'recast_time': self.recast_entry.get() or '0',
                'expansion': EXPANSION_OPTIONS[self.expansion_dropdown.current()][0] or '-1',
                'prev_id': self.prev_id_entry.get() or '-1',
                'next_id': self.next_id_entry.get() or '-1'
            }

            # Check if this is an update or insert
            exists = self.db_manager.execute_query("SELECT id FROM aa_ranks WHERE id = %s", (rank_id,), fetch_all=False)

            if exists:
                # Update existing record
                query = """
                    UPDATE aa_ranks SET 
                        upper_hotkey_sid = %(upper_hotkey_sid)s,
                        lower_hotkey_sid = %(lower_hotkey_sid)s,
                        title_sid = %(title_sid)s,
                        desc_sid = %(desc_sid)s,
                        cost = %(cost)s,
                        level_req = %(level_req)s,
                        spell = %(spell)s,
                        spell_type = %(spell_type)s,
                        recast_time = %(recast_time)s,
                        expansion = %(expansion)s,
                        prev_id = %(prev_id)s,
                        next_id = %(next_id)s
                    WHERE id = %(id)s
                """
            else:
                # Insert new record
                query = """
                    INSERT INTO aa_ranks (
                        id, upper_hotkey_sid, lower_hotkey_sid, title_sid, desc_sid, 
                        cost, level_req, spell, spell_type, recast_time, expansion, 
                        prev_id, next_id
                    ) VALUES (
                        %(id)s, %(upper_hotkey_sid)s, %(lower_hotkey_sid)s, %(title_sid)s, 
                        %(desc_sid)s, %(cost)s, %(level_req)s, %(spell)s, %(spell_type)s, 
                        %(recast_time)s, %(expansion)s, %(prev_id)s, %(next_id)s
                    )
                """
            # Execute and commit
            self.db_manager.execute_update(query, rank_data)

            # If this was an insert and the current AA has no first rank, set it
            if not exists:
                try:
                    current_aa_id = self.id_entry.get()
                    if current_aa_id:
                        aa_row = self.db_manager.execute_query("SELECT first_rank_id FROM aa_ability WHERE id = %s", (current_aa_id,), fetch_all=False)
                        if aa_row and (aa_row['first_rank_id'] is None or int(aa_row['first_rank_id']) == -1):
                            self.db_manager.execute_update(
                                "UPDATE aa_ability SET first_rank_id = %s WHERE id = %s",
                                (rank_id, current_aa_id),
                            )
                            # Refresh rank dropdown for this AA
                            self.rank_dropdown['values'] = [int(rank_id)]
                            self.rank_dropdown_var.set(str(rank_id))
                            self.load_rank_details()
                except Exception:
                    # Non-fatal; proceed even if this linkage fails
                    pass
            messagebox.showinfo("Success", "AA Rank saved successfully")
            
        except Exception as err:
            messagebox.showerror("Database Error", f"Failed to save AA Rank:\n{err}")
    
    def create_new_rank(self):
        """Create a new rank. If the AA has no ranks, create the first; otherwise append to chain."""
        try:
            # First, validate that an AA is selected
            selected = self.aa_tree.focus()
            if not selected:
                messagebox.showwarning("Warning", "Please select an AA ability first")
                return
                
            # Get the AA ID and validate it has ranks
            aa_id = self.aa_tree.item(selected)['values'][0]
            aa_data = self.db_manager.execute_query("SELECT first_rank_id FROM aa_ability WHERE id = %s", (aa_id,), fetch_all=False)
            
            # If no ranks exist, create the first rank
            if not aa_data or aa_data['first_rank_id'] is None or int(aa_data['first_rank_id']) == -1:
                # Determine a new rank ID
                new_rank_id = self.find_available_rank_id_only()

                # Ensure db_str title/desc entries exist using rank_id as SID
                self.create_db_str_entries(new_rank_id, title_text="New AA Title", desc_text="New AA Description")

                # Create the first rank with default values and no links
                if not self.create_rank_with_defaults(
                    rank_id=new_rank_id,
                    title_sid=new_rank_id,
                    desc_sid=new_rank_id,
                    prev_id=-1,
                    next_id=-1,
                ):
                    messagebox.showerror("Error", "Failed to create first rank")
                    return

                # Link AA to this first rank
                self.db_manager.execute_update(
                    "UPDATE aa_ability SET first_rank_id = %s WHERE id = %s",
                    (new_rank_id, aa_id),
                )

                # Refresh UI dropdown to show the new rank
                self.rank_dropdown['values'] = [new_rank_id]
                self.rank_dropdown_var.set(str(new_rank_id))
                self.load_rank_details()

                messagebox.showinfo("Success", f"Created first rank (ID: {new_rank_id}) for AA {aa_id}")
                return
                
            first_rank_id = aa_data['first_rank_id']
            
            # Get all ranks in the chain to find the last one
            ranks = self.get_rank_chain(first_rank_id)
            if not ranks:
                messagebox.showwarning("Warning", "Could not load rank chain for selected AA")
                return
                
            # Find the last rank (where next_id = -1)
            last_rank = None
            for rank_id in ranks:
                rank_data = self.db_manager.execute_query("SELECT * FROM aa_ranks WHERE id = %s", (rank_id,), fetch_all=False)
                if rank_data and (rank_data['next_id'] == -1 or rank_data['next_id'] is None):
                    last_rank = rank_data
                    break
                    
            if not last_rank:
                messagebox.showwarning("Warning", "Could not find last rank in chain")
                return
                
            # Get the SIDs from the first rank in the chain (they should all match)
            first_rank_data = self.db_manager.execute_query("SELECT title_sid, desc_sid FROM aa_ranks WHERE id = %s", (first_rank_id,), fetch_all=False)
            if not first_rank_data:
                messagebox.showwarning("Warning", "Could not load first rank data")
                return
                
            title_sid = first_rank_data['title_sid']
            desc_sid = first_rank_data['desc_sid']
            
            # Find next available rank ID (only check aa_ranks table)
            new_rank_id = self.find_available_rank_id_only()
            
            # Create the new rank
            success = self.create_rank_with_defaults(
                rank_id=new_rank_id,
                title_sid=title_sid, 
                desc_sid=desc_sid,
                prev_id=last_rank['id'],
                next_id=-1
            )
            
            if not success:
                messagebox.showerror("Error", "Failed to create new rank")
                return
                
            # Update the last rank's next_id to point to the new rank
            self.db_manager.execute_update("""
                UPDATE aa_ranks 
                SET next_id = %s 
                WHERE id = %s
            """, (new_rank_id, last_rank['id']))
            
            # Copy effects from the last rank
            self.db_manager.execute_update("""
                INSERT INTO aa_rank_effects (rank_id, slot, effect_id, base1, base2)
                SELECT %s, slot, effect_id, base1, base2
                FROM aa_rank_effects
                WHERE rank_id = %s
            """, (new_rank_id, last_rank['id']))
            
            # Copy prerequisites from the last rank
            self.db_manager.execute_update("""
                INSERT INTO aa_rank_prereqs (rank_id, aa_id, points)
                SELECT %s, aa_id, points
                FROM aa_rank_prereqs
                WHERE rank_id = %s
            """, (new_rank_id, last_rank['id']))
            
            # Refresh the rank dropdown to include the new rank
            new_ranks = self.get_rank_chain(first_rank_id)
            if new_ranks:
                self.rank_dropdown['values'] = new_ranks
                # Auto-select the new rank
                self.rank_dropdown_var.set(str(new_rank_id))
                self.load_rank_details()
                
            messagebox.showinfo("Success", f"Successfully created new rank (ID: {new_rank_id}) with copied effects and prerequisites")
            
        except Exception as err:
            messagebox.showerror("Database Error", f"Failed to create new rank:\n{err}")
    
    def delete_rank(self):
        """Delete the currently selected rank and relink the chain properly"""
        try:
            # Validate that a rank is selected
            selected_rank_id = self.rank_dropdown_var.get()
            if not selected_rank_id or selected_rank_id == "Select Rank":
                messagebox.showwarning("Warning", "Please select a rank to delete")
                return
                
            # Validate that an AA is selected
            selected_aa = self.aa_tree.focus()
            if not selected_aa:
                messagebox.showwarning("Warning", "Please select an AA ability first")
                return
                
            # Get the AA ID and validate it has ranks
            aa_id = self.aa_tree.item(selected_aa)['values'][0]
            aa_data = self.db_manager.execute_query("SELECT first_rank_id FROM aa_ability WHERE id = %s", (aa_id,), fetch_all=False)
            
            if not aa_data or not aa_data['first_rank_id'] or aa_data['first_rank_id'] == -1:
                messagebox.showwarning("Warning", "Selected AA has no ranks")
                return
                
            first_rank_id = aa_data['first_rank_id']
            
            # Get all ranks in chain to check if this is the only rank
            ranks = self.get_rank_chain(first_rank_id)
            if len(ranks) <= 1:
                messagebox.showwarning("Warning", "Cannot delete the only rank in an AA. Use 'Delete AA' instead.")
                return
                
            # Get details of the rank to delete
            rank_to_delete = self.db_manager.execute_query("SELECT * FROM aa_ranks WHERE id = %s", (selected_rank_id,), fetch_all=False)
            if not rank_to_delete:
                messagebox.showwarning("Warning", "Selected rank not found")
                return
                
            # SAFEGUARD: Only allow deleting the last rank in the chain
            if rank_to_delete['next_id'] != -1 and rank_to_delete['next_id'] is not None:
                messagebox.showwarning("Safety Warning", 
                    f"Cannot delete rank {selected_rank_id} - only the last rank in a chain can be deleted.\n\n"
                    "This prevents breaking the chain structure. To delete this rank, you must first "
                    "delete all ranks that come after it in the chain.")
                return
                
            # Confirm deletion
            if not messagebox.askyesno("Confirm Delete", 
                f"Are you sure you want to delete the last rank {selected_rank_id}?\n\n"
                "This will also delete all effects and prerequisites for this rank."):
                return
                
            prev_id = rank_to_delete['prev_id'] if rank_to_delete['prev_id'] != -1 else None
            
            # Delete effects and prerequisites first
            self.db_manager.execute_update("DELETE FROM aa_rank_effects WHERE rank_id = %s", (selected_rank_id,))
            self.db_manager.execute_update("DELETE FROM aa_rank_prereqs WHERE rank_id = %s", (selected_rank_id,))
            
            # Simplified chain relinking - since we only delete last rank, logic is simpler
            if prev_id:
                # This was the last rank with a previous rank - set previous rank's next_id to -1
                self.db_manager.execute_update("UPDATE aa_ranks SET next_id = -1 WHERE id = %s", (prev_id,))
            else:
                # This was the only rank (first and last) - AA will have no ranks after deletion
                # This case should be caught by earlier validation, but handle it safely
                self.db_manager.execute_update("UPDATE aa_ability SET first_rank_id = -1 WHERE id = %s", (aa_id,))
            
            # Delete the rank itself
            self.db_manager.execute_update("DELETE FROM aa_ranks WHERE id = %s", (selected_rank_id,))
            
            # Refresh the rank dropdown - get updated first_rank_id
            updated_aa_data = self.db_manager.execute_query("SELECT first_rank_id FROM aa_ability WHERE id = %s", (aa_id,), fetch_all=False)
            new_first_rank_id = updated_aa_data['first_rank_id'] if updated_aa_data else first_rank_id
            new_ranks = self.get_rank_chain(new_first_rank_id)
            if new_ranks:
                self.rank_dropdown['values'] = new_ranks
                # Select the first available rank
                self.rank_dropdown_var.set(str(new_ranks[0]))
                self.load_rank_details()
            else:
                # Clear dropdown if no ranks left (shouldn't happen due to validation)
                self.rank_dropdown['values'] = []
                self.rank_dropdown_var.set("No Ranks")
                self.clear_rank_fields()
                
            messagebox.showinfo("Success", f"Successfully deleted rank {selected_rank_id}")
            
        except Exception as err:
            messagebox.showerror("Database Error", f"Failed to delete rank:\n{err}")
    
    def clone_aa_ability(self): 
        """Create a clone of the selected AA ability with all its ranks, effects, and prerequisites"""
        try:
            selected = self.aa_tree.focus()
            if not selected:
                messagebox.showwarning("Warning", "Please select an AA ability to clone")
                return
                
            # Get the original AA ID
            original_id = self.aa_tree.item(selected)['values'][0]
            
            # Find the next available AA ID starting from the original ID
            result = self.db_manager.execute_query("""
                SELECT MIN(t1.id + 1) as next_id
                FROM aa_ability t1
                LEFT JOIN aa_ability t2 ON t1.id + 1 = t2.id
                WHERE t1.id >= %s AND t2.id IS NULL
            """, (original_id,), fetch_all=False)
            new_id = result['next_id'] if result and result['next_id'] is not None else original_id + 1
            
            # Clone the AA ability with first_rank_id set to -1 initially
            self.db_manager.execute_update("""
                INSERT INTO aa_ability (
                    id, name, category, classes, races, drakkin_heritage, deities,
                    status, type, charges, grant_only, first_rank_id, enabled,
                    reset_on_death, auto_grant_enabled
                )
                SELECT 
                    %s, CONCAT(name, ' CLONE'), category, classes, races, drakkin_heritage, deities,
                    status, type, charges, grant_only, -1, enabled,
                    reset_on_death, auto_grant_enabled
                FROM aa_ability
                WHERE id = %s
            """, (new_id, original_id))
            
            # Get the original first rank ID
            original_first_rank_data = self.db_manager.execute_query("SELECT first_rank_id FROM aa_ability WHERE id = %s", (original_id,), fetch_all=False)
            original_first_rank = original_first_rank_data['first_rank_id'] if original_first_rank_data else None
            
            if original_first_rank and original_first_rank != -1:
                # Clone all ranks and their relationships without using CTEs
                rank_map = {}  # Map original rank IDs to new rank IDs

                # Build original rank ID chain
                original_ranks = self.get_rank_chain(original_first_rank)

                # First pass: clone each rank row
                for orig_rank_id in original_ranks:
                    rank = self.db_manager.execute_query(
                        "SELECT * FROM aa_ranks WHERE id = %s",
                        (orig_rank_id,),
                        fetch_all=False,
                    )
                    if not rank:
                        continue
                    # Find next available rank ID starting from the original rank ID
                    result = self.db_manager.execute_query(
                        """
                        SELECT MIN(t1.id + 1) as next_id
                        FROM aa_ranks t1
                        LEFT JOIN aa_ranks t2 ON t1.id + 1 = t2.id
                        WHERE t1.id >= %s AND t2.id IS NULL
                        """,
                        (rank['id'],),
                        fetch_all=False,
                    )
                    new_rank_id = result['next_id'] if result and result['next_id'] is not None else rank['id'] + 1
                    rank_map[rank['id']] = new_rank_id

                    # Insert cloned rank with original links; will fix links in second pass
                    self.db_manager.execute_update(
                        """
                        INSERT INTO aa_ranks (
                            id, upper_hotkey_sid, lower_hotkey_sid, title_sid, desc_sid,
                            cost, level_req, spell, spell_type, recast_time, expansion,
                            prev_id, next_id
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            new_rank_id,
                            rank['upper_hotkey_sid'],
                            rank['lower_hotkey_sid'],
                            rank['title_sid'],
                            rank['desc_sid'],
                            rank['cost'],
                            rank['level_req'],
                            rank['spell'],
                            rank['spell_type'],
                            rank['recast_time'],
                            rank['expansion'],
                            rank['prev_id'],
                            rank['next_id'],
                        ),
                    )

                # Second pass: update the prev/next IDs to point to cloned IDs
                for orig_rank_id in original_ranks:
                    new_rank_id = rank_map.get(orig_rank_id)
                    if new_rank_id is None:
                        continue
                    rank = self.db_manager.execute_query(
                        "SELECT prev_id, next_id FROM aa_ranks WHERE id = %s",
                        (orig_rank_id,),
                        fetch_all=False,
                    )
                    if not rank:
                        continue
                    new_prev_id = rank_map.get(rank['prev_id'], -1) if rank['prev_id'] != -1 else -1
                    new_next_id = rank_map.get(rank['next_id'], -1) if rank['next_id'] != -1 else -1
                    self.db_manager.execute_update(
                        "UPDATE aa_ranks SET prev_id = %s, next_id = %s WHERE id = %s",
                        (new_prev_id, new_next_id, new_rank_id),
                    )

                # Update the AA's first_rank_id to the mapped first rank
                if original_first_rank in rank_map:
                    self.db_manager.execute_update(
                        "UPDATE aa_ability SET first_rank_id = %s WHERE id = %s",
                        (rank_map[original_first_rank], new_id),
                    )

                # Clone effects and prerequisites for each rank
                for old_rank_id, new_rank_id in rank_map.items():
                    self.db_manager.execute_update(
                        """
                        INSERT INTO aa_rank_effects (rank_id, slot, effect_id, base1, base2)
                        SELECT %s, slot, effect_id, base1, base2 FROM aa_rank_effects WHERE rank_id = %s
                        """,
                        (new_rank_id, old_rank_id),
                    )
                    self.db_manager.execute_update(
                        """
                        INSERT INTO aa_rank_prereqs (rank_id, aa_id, points)
                        SELECT %s, aa_id, points FROM aa_rank_prereqs WHERE rank_id = %s
                        """,
                        (new_rank_id, old_rank_id),
                    )
            
            messagebox.showinfo("Success", f"Successfully cloned AA ability (ID: {new_id})")
            
            # Refresh the AA list and select the new AA
            self.load_aa_list()
            for item in self.aa_tree.get_children():
                if self.aa_tree.item(item)['values'][0] == new_id:
                    self.aa_tree.selection_set(item)
                    self.aa_tree.focus(item)
                    self.on_aa_select(type('Event', (), {'widget': self.aa_tree})())
                    break
                    
        except Exception as err:
            messagebox.showerror("Database Error", f"Failed to clone AA ability:\n{err}")
    
    def delete_aa_ability(self): 
        """Delete the selected AA ability and all its related data"""
        try:
            selected = self.aa_tree.focus()
            if not selected:
                messagebox.showwarning("Warning", "Please select an AA ability to delete")
                return
                
            # Get the AA ID
            aa_id = self.aa_tree.item(selected)['values'][0]
            aa_name = self.aa_tree.item(selected)['values'][1]
            
            # Confirm deletion
            if not messagebox.askyesno("Confirm Delete", 
                f"Are you sure you want to delete AA '{aa_name}' (ID: {aa_id})?\n\n"
                "This will also delete all ranks, effects, and prerequisites associated with this AA."):
                return
                
            # Get the first rank ID
            first_rank_data = self.db_manager.execute_query("SELECT first_rank_id FROM aa_ability WHERE id = %s", (aa_id,), fetch_all=False)
            first_rank = first_rank_data['first_rank_id'] if first_rank_data else None
            
            if first_rank and first_rank != -1:
                # Get all ranks in the chain
                rank_data = self.db_manager.execute_query("""
                    WITH RECURSIVE rank_chain AS (
                        SELECT id, next_id FROM aa_ranks WHERE id = %s
                        UNION ALL
                        SELECT r.id, r.next_id 
                        FROM aa_ranks r
                        JOIN rank_chain rc ON r.id = rc.next_id
                    )
                    SELECT id FROM rank_chain
                """, (first_rank,))
                
                rank_ids = [row['id'] for row in rank_data]
                
                # Delete effects for all ranks
                if rank_ids:
                    placeholders = ','.join(['%s'] * len(rank_ids))
                    self.db_manager.execute_update(f"""
                        DELETE FROM aa_rank_effects 
                        WHERE rank_id IN ({placeholders})
                    """, tuple(rank_ids))
                
                # Delete prerequisites for all ranks
                if rank_ids:
                    placeholders = ','.join(['%s'] * len(rank_ids))
                    self.db_manager.execute_update(f"""
                        DELETE FROM aa_rank_prereqs 
                        WHERE rank_id IN ({placeholders})
                    """, tuple(rank_ids))
                
                # Delete all ranks
                if rank_ids:
                    placeholders = ','.join(['%s'] * len(rank_ids))
                    self.db_manager.execute_update(f"""
                        DELETE FROM aa_ranks 
                        WHERE id IN ({placeholders})
                    """, tuple(rank_ids))
            
            # Finally, delete the AA ability
            self.db_manager.execute_update("DELETE FROM aa_ability WHERE id = %s", (aa_id,))
            
            messagebox.showinfo("Success", f"Successfully deleted AA ability (ID: {aa_id})")
            
            # Refresh the AA list
            self.load_aa_list()
            
        except Exception as err:
            messagebox.showerror("Database Error", f"Failed to delete AA ability:\n{err}")
    
    def add_effect(self): 
        """Add a new effect to the treeview and database"""
        try:
            rank_id = self.rank_id_entry.get()
            if not rank_id:
                messagebox.showwarning("Warning", "Please select a rank first")
                return
                
            # Find the next available slot number by checking the database
            result = self.db_manager.execute_query("""
                SELECT MAX(slot) as max_slot 
                FROM aa_rank_effects 
                WHERE rank_id = %s
            """, (rank_id,), fetch_all=False)
            next_slot = 1 if result['max_slot'] is None else result['max_slot'] + 1
            
            # Insert into database
            self.db_manager.execute_update("""
                INSERT INTO aa_rank_effects (rank_id, slot, effect_id, base1, base2)
                VALUES (%s, %s, %s, %s, %s)
            """, (rank_id, next_slot, 0, 0, 0))
            
            # Add to treeview with effect name
            effect_name = SPELL_EFFECTS.get(0, "Unknown Effect")
            self.effects_treeview.insert('', 'end', values=(next_slot, '0', effect_name, '0', '0'))
            
        except Exception as err:
            messagebox.showerror("Database Error", f"Failed to add effect:\n{err}")
    
    def delete_effect(self): 
        """Delete the selected effect from treeview and database"""
        try:
            selected = self.effects_treeview.focus()
            if not selected:
                messagebox.showwarning("Warning", "Please select an effect to delete")
                return
                
            rank_id = self.rank_id_entry.get()
            if not rank_id:
                messagebox.showwarning("Warning", "Please select a rank first")
                return
                
            # Get the slot number from the selected item
            slot = self.effects_treeview.item(selected)['values'][0]
            
            # Delete from database
            self.db_manager.execute_update("""
                DELETE FROM aa_rank_effects 
                WHERE rank_id = %s AND slot = %s
            """, (rank_id, slot))
            
            # Delete from treeview
            self.effects_treeview.delete(selected)
            
        except Exception as err:
            messagebox.showerror("Database Error", f"Failed to delete effect:\n{err}")
    
    def add_prereq(self): 
        """Add a new prerequisite to the treeview and database"""
        try:
            rank_id = self.rank_id_entry.get()
            if not rank_id:
                messagebox.showwarning("Warning", "Please select a rank first")
                return
                
            # Find an unused AA ID
            result = self.db_manager.execute_query("""
                SELECT MAX(aa_id) as max_aa_id 
                FROM aa_rank_prereqs 
                WHERE rank_id = %s
            """, (rank_id,), fetch_all=False)
            next_aa_id = 1 if result['max_aa_id'] is None else result['max_aa_id'] + 1
            
            # Insert into database
            self.db_manager.execute_update("""
                INSERT INTO aa_rank_prereqs (rank_id, aa_id, points)
                VALUES (%s, %s, %s)
            """, (rank_id, next_aa_id, 1))
            
            # Get the AA name from the aa_ability table
            aa_result = self.db_manager.execute_query("SELECT name FROM aa_ability WHERE id = %s", (next_aa_id,), fetch_all=False)
            aa_name = aa_result.get('name', 'Unknown AA') if aa_result else 'Unknown AA'
            
            # Add to treeview
            self.prereq_treeview.insert('', 'end', values=(rank_id, next_aa_id, aa_name, '1'))
            
        except Exception as err:
            messagebox.showerror("Database Error", f"Failed to add prerequisite:\n{err}")
    
    def delete_prereq(self): 
        """Delete the selected prerequisite from treeview and database"""
        try:
            selected = self.prereq_treeview.focus()
            if not selected:
                messagebox.showwarning("Warning", "Please select a prerequisite to delete")
                return
                
            rank_id = self.rank_id_entry.get()
            if not rank_id:
                messagebox.showwarning("Warning", "Please select a rank first")
                return
                
            # Get the aa_id from the selected item
            aa_id = self.prereq_treeview.item(selected)['values'][1]
            
            # Delete from database
            self.db_manager.execute_update("""
                DELETE FROM aa_rank_prereqs 
                WHERE rank_id = %s AND aa_id = %s
            """, (rank_id, aa_id))
            
            # Delete from treeview
            self.prereq_treeview.delete(selected)
            
        except Exception as err:
            messagebox.showerror("Database Error", f"Failed to delete prerequisite:\n{err}")
    
    def open_spell_effects_lookup(self): 
        """Open a window to lookup spell effects and apply them to the selected effect row"""
        # Create a new window
        lookup_window = tk.Toplevel(self.parent)
        lookup_window.title("Spell Effects Lookup")
        lookup_window.geometry("600x500")
        lookup_window.transient(self.parent)  # Make it a child of the main window
        lookup_window.grab_set()  # Make it modal
        
        # Create a frame for the search
        search_frame = ttk.Frame(lookup_window)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Create a frame for the listbox with scrollbar
        list_frame = ttk.Frame(lookup_window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create a listbox to display the effects
        effects_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        effects_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=effects_listbox.yview)
        
        # Populate the listbox with all effects
        for effect_id, effect_name in sorted(SPELL_EFFECTS.items()):
            effects_listbox.insert(tk.END, f"{effect_id}: {effect_name}")
        
        # Function to filter the listbox based on search
        def filter_list(*args):
            search_term = search_var.get().lower()
            effects_listbox.delete(0, tk.END)
            for effect_id, effect_name in sorted(SPELL_EFFECTS.items()):
                if search_term in str(effect_id).lower() or search_term in effect_name.lower():
                    effects_listbox.insert(tk.END, f"{effect_id}: {effect_name}")
        
        # Bind the search entry to the filter function
        search_var.trace_add("write", filter_list)
        
        # Function to apply the selected effect
        def apply_effect():
            selected = effects_listbox.curselection()
            if not selected:
                messagebox.showwarning("Warning", "Please select an effect")
                return
            
            # Get the selected effect ID
            effect_text = effects_listbox.get(selected[0])
            effect_id = effect_text.split(":")[0].strip()
            effect_name = effect_text.split(":", 1)[1].strip()
            
            # Get the selected row in the effects treeview
            selected_row = self.effects_treeview.focus()
            if not selected_row:
                messagebox.showwarning("Warning", "Please select a row in the effects table")
                return
            
            # Update the effect_id in the treeview
            values = list(self.effects_treeview.item(selected_row)['values'])
            values[1] = effect_id  # effect_id is the second column
            values[2] = effect_name  # effect_name is the third column
            self.effects_treeview.item(selected_row, values=values)
            
            # Update the database
            try:
                rank_id = self.rank_id_entry.get()
                slot = values[0]
                
                self.db_manager.execute_update("""
                    UPDATE aa_rank_effects 
                    SET effect_id = %s 
                    WHERE rank_id = %s AND slot = %s
                """, (effect_id, rank_id, slot))
                
                lookup_window.destroy()
                
            except Exception as err:
                messagebox.showerror("Database Error", f"Failed to update effect:\n{err}")
        
        # Add a button to apply the selected effect
        button_frame = ttk.Frame(lookup_window)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="Apply Effect", command=apply_effect).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=lookup_window.destroy).pack(side=tk.RIGHT, padx=5)
        
        # Add a double-click binding to apply the effect
        effects_listbox.bind("<Double-1>", lambda e: apply_effect())
        
        # Focus the search entry
        search_entry.focus_set()
    
    def open_aa_lookup(self): 
        """Open a window to lookup AAs and apply them to the selected prerequisite row"""
        # Create a new window
        lookup_window = tk.Toplevel(self.parent)
        lookup_window.title("AA Lookup")
        lookup_window.geometry("600x500")
        lookup_window.transient(self.parent)  # Make it a child of the main window
        lookup_window.grab_set()  # Make it modal
        
        # Create a frame for the search
        search_frame = ttk.Frame(lookup_window)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Create a frame for the listbox with scrollbar
        list_frame = ttk.Frame(lookup_window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create a listbox to display the AAs
        aa_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        aa_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=aa_listbox.yview)
        
        # Populate the listbox with all AAs
        try:
            aa_list = self.db_manager.execute_query("SELECT id, name FROM aa_ability ORDER BY name")
            for aa in aa_list:
                aa_listbox.insert(tk.END, f"{aa['id']}: {aa['name']}")
        except Exception as err:
            messagebox.showerror("Database Error", f"Failed to load AA list:\n{err}")
        
        # Function to filter the listbox based on search
        def filter_list(*args):
            search_term = search_var.get().lower()
            aa_listbox.delete(0, tk.END)
            try:
                aa_list = self.db_manager.execute_query("SELECT id, name FROM aa_ability WHERE name LIKE %s OR id LIKE %s ORDER BY name", 
                                                      (f"%{search_term}%", f"%{search_term}%"))
                for aa in aa_list:
                    aa_listbox.insert(tk.END, f"{aa['id']}: {aa['name']}")
            except Exception as err:
                messagebox.showerror("Database Error", f"Failed to filter AA list:\n{err}")
        
        # Bind the search entry to the filter function
        search_var.trace_add("write", filter_list)
        
        # Function to apply the selected AA
        def apply_aa():
            selected = aa_listbox.curselection()
            if not selected:
                messagebox.showwarning("Warning", "Please select an AA")
                return
            
            # Get the selected AA ID and name
            aa_text = aa_listbox.get(selected[0])
            aa_id = aa_text.split(":")[0].strip()
            aa_name = aa_text.split(":", 1)[1].strip()
            
            # Get the selected row in the prereq treeview
            selected_row = self.prereq_treeview.focus()
            if not selected_row:
                messagebox.showwarning("Warning", "Please select a row in the prerequisites table")
                return
            
            # Update the aa_id in the treeview
            values = list(self.prereq_treeview.item(selected_row)['values'])
            values[1] = aa_id  # aa_id is the second column
            values[2] = aa_name  # aa_name is the third column
            self.prereq_treeview.item(selected_row, values=values)
            
            # Update the database
            try:
                rank_id = self.rank_id_entry.get()
                prereq_rank_id = values[0]
                
                self.db_manager.execute_update("""
                    UPDATE aa_rank_prereqs 
                    SET aa_id = %s 
                    WHERE rank_id = %s AND aa_id = %s
                """, (aa_id, rank_id, values[1]))
                
                lookup_window.destroy()
                
            except Exception as err:
                messagebox.showerror("Database Error", f"Failed to update prerequisite:\n{err}")
        
        # Add a button to apply the selected AA
        button_frame = ttk.Frame(lookup_window)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="Apply AA", command=apply_aa).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=lookup_window.destroy).pack(side=tk.RIGHT, padx=5)
        
        # Add a double-click binding to apply the AA
        aa_listbox.bind("<Double-1>", lambda e: apply_aa())
        
        # Focus the search entry
        search_entry.focus_set()
    
    def save_all_strings(self): 
        """Save all string information to the database"""
        try:
            # Get the SIDs from the rank information entries
            title_sid = self.title_sid_entry.get()
            desc_sid = self.desc_sid_entry.get()
            lower_sid = self.lower_hotkey_entry.get()
            upper_sid = self.upper_hotkey_entry.get()
            
            # Get the string content from the text widgets
            title_value = self.title_text.get(1.0, tk.END).strip()
            desc_value = self.desc_text.get(1.0, tk.END).strip()
            lower_value = self.lower_hotkey_text.get(1.0, tk.END).strip()
            upper_value = self.upper_hotkey_text.get(1.0, tk.END).strip()
            
            # Save title string (type 1)
            if title_sid and title_sid != '-1':
                self.db_manager.execute_update("""
                    INSERT INTO db_str (id, type, value) 
                    VALUES (%s, 1, %s)
                    ON DUPLICATE KEY UPDATE value = %s
                """, (title_sid, title_value, title_value))
            
            # Save description string (type 4)
            if desc_sid and desc_sid != '-1':
                self.db_manager.execute_update("""
                    INSERT INTO db_str (id, type, value) 
                    VALUES (%s, 4, %s)
                    ON DUPLICATE KEY UPDATE value = %s
                """, (desc_sid, desc_value, desc_value))
            
            # Save lower hotkey string (type 3)
            if lower_sid and lower_sid != '-1':
                self.db_manager.execute_update("""
                    INSERT INTO db_str (id, type, value) 
                    VALUES (%s, 3, %s)
                    ON DUPLICATE KEY UPDATE value = %s
                """, (lower_sid, lower_value, lower_value))
            
            # Save upper hotkey string (type 2)
            if upper_sid and upper_sid != '-1':
                self.db_manager.execute_update("""
                    INSERT INTO db_str (id, type, value) 
                    VALUES (%s, 2, %s)
                    ON DUPLICATE KEY UPDATE value = %s
                """, (upper_sid, upper_value, upper_value))
            
            messagebox.showinfo("Success", "String information saved successfully")
            
        except Exception as err:
            messagebox.showerror("Error", f"Failed to save string information:\n{err}")
    
    def make_treeview_editable(self, treeview, columns, table_name, id_column, aa_id=None):
        """Make treeview editable with database saving.
        
        Args:
            treeview: The Treeview widget
            columns: List of column names
            table_name: Database table name
            id_column: Name of the ID column in the table
            aa_id: Optional AA ID if this is a related table
        """
        def edit_cell(event):
            row = treeview.identify_row(event.y)
            column = treeview.identify_column(event.x)
            
            if not row or column == '#0':  # Skip header or tree column
                return
                
            col_index = int(column[1:]) - 1
            
            # Skip the effect_name column as it's not editable
            if treeview == self.effects_treeview and col_index == 2:
                return
                
            # Skip the aa_name column as it's not editable
            if treeview == self.prereq_treeview and col_index == 2:
                return
                
            item = treeview.item(row)
            values = item['values']
            if col_index >= len(values):
                return
                
            # Get the cell's bounding box
            bbox = treeview.bbox(row, column)
            if not bbox:  # If bbox is None, the cell is not visible
                return
                
            x, y, width, height = bbox
            
            # Create and configure the entry widget
            entry = ttk.Entry(treeview)
            entry.place(x=x, y=y, width=width, height=height)
            entry.insert(0, values[col_index])
            entry.select_range(0, tk.END)
            entry.focus()
            
            def save_edit(event=None):
                try:
                    new_values = list(values)
                    new_value = entry.get()
                    new_values[col_index] = new_value
                    
                    # If this is the effect_id column in the effects treeview, update the effect_name
                    if treeview == self.effects_treeview and col_index == 1:
                        try:
                            effect_id = int(new_value)
                            effect_name = SPELL_EFFECTS.get(effect_id, "Unknown Effect")
                            new_values[2] = effect_name
                        except ValueError:
                            pass
                    
                    # If this is the aa_id column in the prereq treeview, update the aa_name
                    if treeview == self.prereq_treeview and col_index == 1:
                        try:
                            aa_id_value = int(new_value)
                            aa_result = self.db_manager.execute_query("SELECT name FROM aa_ability WHERE id = %s", (aa_id_value,), fetch_all=False)
                            aa_name = aa_result.get('name', 'Unknown AA') if aa_result else 'Unknown AA'
                            new_values[2] = aa_name
                        except ValueError:
                            pass
                    
                    treeview.item(row, values=new_values)
                    
                    # Update database
                    column_name = columns[col_index]
                    record_id = values[0]  # Assuming first value is the ID
                    
                    if table_name == "aa_rank_effects":
                        # Get the rank_id from the entry widget if it exists
                        rank_id = aa_id.get() if isinstance(aa_id, tk.Entry) else aa_id
                        if not rank_id:
                            raise ValueError("Rank ID is required for updating effects")
                            
                        # Update effects table
                        self.db_manager.execute_update(f"""
                            UPDATE {table_name} 
                            SET {column_name} = %s 
                            WHERE rank_id = %s AND slot = %s
                        """, (new_value, rank_id, record_id))
                    elif table_name == "aa_rank_prereqs":
                        # Get the rank_id from the entry widget if it exists
                        rank_id = aa_id.get() if isinstance(aa_id, tk.Entry) else aa_id
                        if not rank_id:
                            raise ValueError("Rank ID is required for updating prerequisites")
                            
                        # Update prerequisites table
                        self.db_manager.execute_update(f"""
                            UPDATE {table_name} 
                            SET {column_name} = %s 
                            WHERE rank_id = %s AND aa_id = %s
                        """, (new_value, rank_id, values[1]))  # values[1] is aa_id
                    else:
                        # Update other tables
                        self.db_manager.execute_update(f"""
                            UPDATE {table_name} 
                            SET {column_name} = %s 
                            WHERE {id_column} = %s
                        """, (new_value, record_id))
                    
                    print(f"Updated {table_name} record {record_id}: {column_name} = {new_value}")
                except Exception as err:
                    messagebox.showerror("Database Error", f"Failed to update {table_name}:\n{err}")
                    # Revert the treeview change
                    treeview.item(row, values=values)
                finally:
                    entry.destroy()
                
            def cancel_edit(event=None):
                entry.destroy()
                
            entry.bind('<Return>', save_edit)
            entry.bind('<FocusOut>', save_edit)
            entry.bind('<Escape>', cancel_edit)
        
        treeview.bind('<Double-1>', edit_cell)
        treeview.bind('<Return>', edit_cell)
    
    def update_string_display(self):
        """Update string display when rank selection changes"""
        # This should call load_rank_details like the original logic
        self.load_rank_details()
