import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class SpellsManagerTool:
    """Spell Manager Tool modeled after the AA tool layout."""

    MAX_EFFECT_SLOTS = 12
    MAX_CLASS_SLOTS = 16
    MAX_DEITY_SLOTS = 17  # deities0-16

    def __init__(self, parent_frame, db_manager, notes_db_manager=None):
        self.parent = parent_frame
        self.db_manager = db_manager
        self.notes_db_manager = notes_db_manager
        self.conn = db_manager.connect()
        self.cursor = db_manager.get_cursor()

        # Spell state
        self.current_spell_id = None
        self.current_spell_data = {}
        self.effect_rows = []  # list of dicts for effect slots
        self.spell_effect_lookup = {}  # id -> name
        self.spell_effect_details = {}  # id -> detail dict
        self.class_names = [f"Class {i}" for i in range(1, self.MAX_CLASS_SLOTS + 1)]
        self.deity_names = [f"D{i}" for i in range(self.MAX_DEITY_SLOTS)]
        self.icon_value = 0
        self.memicon_value = 0

        # Prepare UI
        self.parent.grid_rowconfigure(0, weight=1)
        self.parent.grid_columnconfigure(0, weight=1)
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=0)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(2, weight=0, minsize=260)

        self.load_spell_effect_lookup()
        self.load_class_deity_names()
        self.create_left_panel()
        self.create_center_panel()
        self.create_right_panel()

        # Load initial data
        self.load_spell_list()

    # ------------------------------------------------------------------
    # Left panel: search/list/clone/delete
    # ------------------------------------------------------------------
    def create_left_panel(self):
        left = ttk.Frame(self.main_frame, relief=tk.SUNKEN, borderwidth=1)
        left.grid(row=0, column=0, sticky="ns", padx=5, pady=5)
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)

        search_frame = ttk.Frame(left)
        search_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        ttk.Label(search_frame, text="Search:").grid(row=0, column=0, padx=5)
        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.grid(row=0, column=1, columnspan=3, sticky="ew", padx=5)
        self.search_entry.bind("<KeyRelease>", lambda e: self.filter_spell_list(self.search_entry.get()))
        search_frame.grid_columnconfigure(1, weight=1)

        ttk.Button(search_frame, text="Clear",
                   command=lambda: (self.search_entry.delete(0, "end"), self.load_spell_list())
                   ).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(search_frame, text="Clone", command=self.clone_spell).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(search_frame, text="Delete", command=self.delete_spell).grid(row=1, column=2, padx=5, pady=5)
        ttk.Button(search_frame, text="Edit ID/Name", command=self.edit_tree_id_name).grid(row=1, column=3, padx=5, pady=5)

        list_frame = ttk.Frame(left, relief=tk.SUNKEN, borderwidth=2)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        ttk.Label(list_frame, text="Spells", font=("Arial", 12, "bold")).grid(row=1, column=0, sticky="n")

        self.spell_tree = ttk.Treeview(list_frame, columns=("id", "name"), show="headings")
        self.spell_tree.heading("id", text="ID")
        self.spell_tree.heading("name", text="Name")
        self.spell_tree.column("id", width=60, anchor="e")
        self.spell_tree.column("name", width=200, anchor="w")
        self.spell_tree.grid(row=0, column=0, sticky="nsew")
        self.spell_tree.bind("<<TreeviewSelect>>", self.on_spell_select)

        self.setup_treeview_sorting(self.spell_tree)

    # ------------------------------------------------------------------
    # Center panel: top form + bottom effects
    # ------------------------------------------------------------------
    def create_center_panel(self):
        center = ttk.Frame(self.main_frame, relief=tk.SUNKEN, borderwidth=1)
        center.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        center.grid_rowconfigure(3, weight=1)  # effects area grows
        center.grid_columnconfigure(0, weight=5)
        center.grid_columnconfigure(1, weight=0, minsize=240)

        self.create_basics_panel(center)
        self.create_classes_panel(center)
        self.create_buff_formula_panel(center)
        self.create_effects_panel(center)

    def create_basics_panel(self, parent):
        basics = ttk.LabelFrame(parent, text="Basic Spell Info")
        basics.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        for i in range(8):
            basics.grid_columnconfigure(i, weight=1)

        # Row 0 header labels for ID/Name
        self.id_label = ttk.Label(basics, text="ID: -", font=("Arial", 10, "bold"))
        self.id_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=(2, 4))
        self.name_label = ttk.Label(basics, text="Name: -", font=("Arial", 10, "bold"))
        self.name_label.grid(row=0, column=2, columnspan=4, sticky="w", padx=5, pady=(2, 4))

        # Row 1
        self.mana_entry = self._add_entry(basics, "Mana:", 1, 0, width=8)
        self.range_entry = self._add_entry(basics, "Range:", 1, 2, width=8)
        self.aoe_range_entry = self._add_entry(basics, "AOE Range:", 1, 4, width=8)
        self.player1_entry = self._add_entry(basics, "Player 1:", 1, 6, width=12)

        # Row 2
        self.min_range_entry = self._add_entry(basics, "Min Range:", 2, 0, width=8)
        self.cast_time_entry = self._add_entry(basics, "Cast Time:", 2, 2, width=10)
        self.recovery_time_entry = self._add_entry(basics, "Recovery:", 2, 4, width=10)
        self.teleport_zone_entry = self._add_entry(basics, "Teleport Zone:", 2, 6, width=12)

        # Row 3
        self.recast_time_entry = self._add_entry(basics, "Recast:", 3, 0, width=10)
        self.pushback_entry = self._add_entry(basics, "Pushback:", 3, 6, width=8)

        # Row 4
        self.ae_duration_entry = self._add_entry(basics, "AE Duration:", 4, 0, width=10)
        self.resist_type_entry = self._add_entry(basics, "Resist Type:", 4, 2, width=10)
        self.resist_diff_entry = self._add_entry(basics, "Resist Diff:", 4, 4, width=10)
        self.pushup_entry = self._add_entry(basics, "Pushup:", 4, 6, width=8)

        # Row 5
        self.min_resist_entry = self._add_entry(basics, "Min Resist:", 5, 0, width=10)
        self.max_resist_entry = self._add_entry(basics, "Max Resist:", 5, 2, width=10)
        self.target_type_entry = self._add_entry(basics, "Target Type:", 5, 4, width=10)

        # Row 6
        self.zone_type_entry = self._add_entry(basics, "Zone Type:", 6, 0, width=10)
        self.skill_entry = self._add_entry(basics, "Skill:", 6, 2, width=10)
        self.travel_type_entry = self._add_entry(basics, "Travel Type:", 6, 4, width=10)

        # Row 7
        self.spell_affect_index_entry = self._add_entry(basics, "Spell Affect Index:", 7, 0, width=10)

        # Row 8 flags
        self.good_effect_var = tk.IntVar()
        self.activated_var = tk.IntVar()
        self.uninterruptable_var = tk.IntVar()
        ttk.Checkbutton(basics, text="Good Effect", variable=self.good_effect_var).grid(row=8, column=0, sticky="w", padx=4, pady=2)
        ttk.Checkbutton(basics, text="Activated", variable=self.activated_var).grid(row=8, column=2, sticky="w", padx=4, pady=2)
        ttk.Checkbutton(basics, text="Uninterruptable", variable=self.uninterruptable_var).grid(row=8, column=4, sticky="w", padx=4, pady=2)

        # Save button
        ttk.Button(basics, text="Save Spell", command=self.save_spell).grid(row=9, column=0, columnspan=2, pady=5, sticky="w")

    def create_effects_panel(self, parent):
        # Effects frame (left)
        effects_frame = ttk.LabelFrame(parent, text="Effects")
        effects_frame.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)
        effects_frame.grid_rowconfigure(1, weight=1)
        effects_frame.grid_columnconfigure(0, weight=1)

        btn_frame = ttk.Frame(effects_frame)
        btn_frame.grid(row=0, column=0, sticky="ew")
        ttk.Button(btn_frame, text="New Effect Slot", command=self.create_new_effect_slot).grid(row=0, column=0, padx=5, pady=3)
        ttk.Button(btn_frame, text="Remove Effect", command=self.remove_effect).grid(row=0, column=1, padx=5, pady=3)
        ttk.Button(btn_frame, text="Apply Selected SPA", command=self.apply_selected_effect_from_library).grid(row=0, column=2, padx=5, pady=3)

        self.effects_tree = ttk.Treeview(
            effects_frame,
            columns=("slot", "effectid", "effectname", "base", "limit", "max", "formula"),
            show="headings",
        )
        for col, label, width in [
            ("slot", "Slot", 40),
            ("effectid", "Effect ID", 70),
            ("effectname", "Effect Name", 160),
            ("base", "Base", 80),
            ("limit", "Limit", 80),
            ("max", "Max", 80),
            ("formula", "Formula", 90),
        ]:
            self.effects_tree.heading(col, text=label)
            self.effects_tree.column(col, width=width, anchor="center")
        self.effects_tree.grid(row=1, column=0, sticky="nsew", padx=(0, 5))
        self.effects_tree.bind("<Double-1>", self.on_effects_tree_double_click)

        self.setup_treeview_sorting(self.effects_tree)

        # SPA library outside effects frame (right)
        lib_frame = ttk.LabelFrame(parent, text="SPA Library")
        # Place in a narrow column; parent configured with lower weight for column 1
        lib_frame.grid(row=3, column=1, sticky="nsew", padx=(0, 5), pady=5)
        lib_frame.grid_rowconfigure(1, weight=1)
        lib_frame.grid_columnconfigure(0, weight=1)
        lib_frame.grid_propagate(False)
        lib_frame.configure(width=260)

        search_frame = ttk.Frame(lib_frame)
        search_frame.grid(row=0, column=0, sticky="ew")
        ttk.Label(search_frame, text="Search SPA:").grid(row=0, column=0, padx=3, pady=3)
        self.spa_search_entry = ttk.Entry(search_frame)
        self.spa_search_entry.grid(row=0, column=1, sticky="ew", padx=3, pady=3)
        search_frame.grid_columnconfigure(1, weight=1)
        self.spa_search_entry.bind("<KeyRelease>", lambda e: self.load_effect_library(self.spa_search_entry.get()))

        self.spa_tree = ttk.Treeview(lib_frame, columns=("id", "name"), show="headings")
        self.spa_tree.heading("id", text="ID")
        self.spa_tree.heading("name", text="Name")
        self.spa_tree.column("id", width=50, anchor="e")
        self.spa_tree.column("name", width=180, anchor="w")
        self.spa_tree.grid(row=1, column=0, sticky="nsew")
        self.spa_tree.bind("<<TreeviewSelect>>", self.on_spa_select)
        self.setup_treeview_sorting(self.spa_tree)
        self.load_effect_library()

        # Detail view for selected SPA
        self.spa_detail = tk.Text(
            lib_frame,
            height=6,
            wrap="word",
            state=tk.DISABLED,
            bg="#2d2d2d",
            fg="#ffffff",
            insertbackground="#ffffff",
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground="#4c4c4c",
        )
        self.spa_detail.grid(row=2, column=0, sticky="nsew", padx=3, pady=3)

    # ------------------------------------------------------------------
    # Right panel: strings/icons/classes/deities
    # ------------------------------------------------------------------
    def create_right_panel(self):
        right = ttk.Frame(self.main_frame, relief=tk.SUNKEN, borderwidth=1)
        right.grid(row=0, column=2, sticky="ns", padx=5, pady=5)
        right.grid_rowconfigure(3, weight=1)
        right.grid_columnconfigure(0, weight=1)
        right.configure(width=260)
        right.grid_propagate(False)

        self.create_string_panel(right)
        self.create_description_panel(right)
        self.create_icons_panel(right)
        self.create_animations_panel(right)

    def create_string_panel(self, parent):
        strings = ttk.LabelFrame(parent, text="Messages")
        strings.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        for i in range(2):
            strings.grid_columnconfigure(i, weight=1)

        self.you_cast_entry = self._add_entry(strings, "You Cast:", 0, 0, width=24)
        self.other_cast_entry = self._add_entry(strings, "Other Casts:", 1, 0, width=24)
        self.cast_on_you_entry = self._add_entry(strings, "Cast On You:", 2, 0, width=24)
        self.cast_on_other_entry = self._add_entry(strings, "Cast On Other:", 3, 0, width=24)
        self.spell_fades_entry = self._add_entry(strings, "Spell Fades:", 4, 0, width=24)

    def create_description_panel(self, parent):
        desc_frame = ttk.LabelFrame(parent, text="Description")
        desc_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        for i in range(4):
            desc_frame.grid_columnconfigure(i, weight=0)
        desc_frame.grid_columnconfigure(1, weight=1)

        self.descnum_entry = self._add_entry(desc_frame, "Desc ID:", 0, 0, width=10)
        ttk.Button(desc_frame, text="Save Desc", command=self.save_description).grid(row=0, column=2, padx=4, pady=2, sticky="w")
        ttk.Button(desc_frame, text="New Desc", command=self.new_description).grid(row=0, column=3, padx=4, pady=2, sticky="w")
        self.desc_text = tk.Text(
            desc_frame,
            height=3,
            wrap="word",
            state=tk.NORMAL,
            bg="#2d2d2d",
            fg="#ffffff",
            insertbackground="#ffffff",
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground="#4c4c4c",
        )
        self.desc_text.grid(row=1, column=0, sticky="ew", padx=3, pady=3, columnspan=4)

    def create_icons_panel(self, parent):
        panel = ttk.LabelFrame(parent, text="Icons")
        panel.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_columnconfigure(1, weight=1)

        self.new_icon_entry = self._add_entry(panel, "New Icon:", 0, 0, width=8)
        self.new_icon_entry.bind("<KeyRelease>", lambda e: self.update_icon_preview())

        self.icon_preview_label = ttk.Label(panel, text="No icon", relief=tk.SUNKEN, width=16)
        self.icon_preview_label.grid(row=0, column=1, rowspan=2, sticky="e", padx=4, pady=2)
        self.icon_image_ref = None

    def create_animations_panel(self, parent):
        panel = ttk.LabelFrame(parent, text="Animations")
        panel.grid(row=3, column=0, sticky="ew", padx=5, pady=5)
        for i in range(2):
            panel.grid_columnconfigure(i, weight=1)

        self.spellanim_entry = self._add_entry(panel, "Spell Anim:", 0, 0, width=8)
        self.casting_anim_entry = self._add_entry(panel, "Casting Anim:", 0, 1, width=8)
        self.target_anim_entry = self._add_entry(panel, "Target Anim:", 1, 0, width=8)
        self.nimbus_entry = self._add_entry(panel, "Nimbus:", 1, 1, width=8)

    def create_classes_panel(self, parent):
        classes_frame = ttk.LabelFrame(parent, text="Classes (1-255)")
        classes_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        for i in range(6):  # 3 label/entry pairs per row
            classes_frame.grid_columnconfigure(i, weight=1)

        self.class_entries = []
        for idx in range(self.MAX_CLASS_SLOTS):
            row = idx // 3
            col_pair = (idx % 3) * 2
            ttk.Label(classes_frame, text=f"{self.class_names[idx]}:").grid(
                row=row, column=col_pair, sticky="w", padx=3, pady=2
            )
            entry = ttk.Entry(classes_frame, width=6, justify="center")
            entry.grid(row=row, column=col_pair + 1, sticky="w", padx=3, pady=2)
            self.class_entries.append(entry)

        # Deities handled in a compact dialog; place at bottom of last column
        bottom_row = (self.MAX_CLASS_SLOTS - 1) // 3 + 1
        ttk.Button(classes_frame, text="Edit Deities", command=self.open_deities_dialog).grid(
            row=bottom_row, column=5, sticky="e", padx=5, pady=5
        )

    def create_buff_formula_panel(self, parent):
        panel = ttk.LabelFrame(parent, text="Buff Duration Formulas")
        panel.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        panel.grid_rowconfigure(0, weight=1)
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_columnconfigure(1, weight=1)
        panel.grid_propagate(False)
        panel.configure(width=240)

        # Dropdown + entries
        options = [
            (0, "0 - Not a buff"),
            (1, "1 - level/2"),
            (2, "2 - level>3 ? level/2+5 : 6"),
            (3, "3 - 30*level"),
            (4, "4 - 50"),
            (5, "5 - 2"),
            (6, "6 - level/2+2"),
            (7, "7 - level"),
            (8, "8 - level+10"),
            (9, "9 - 2*level+10"),
            (10, "10 - 3*level+10"),
            (11, "11 - 30*(level+3)"),
            (12, "12 - level>7?level/4:1"),
            (13, "13 - 4*level+10"),
            (14, "14 - 5*(level+2)"),
            (15, "15 - 10*(level+10)"),
            (50, "50 - 5 days (fixed)"),
            (51, "51 - Permanent"),
            (200, "Custom (>=200 cap/fixed)"),
            (3600, "3600 - duration if not 0 else 3600"),
        ]
        self.buff_formula_options = options
        ttk.Label(panel, text="Formula:").grid(row=0, column=0, sticky="w", padx=4, pady=2)
        self.buff_formula_var = tk.StringVar()
        self.buff_formula_dropdown = ttk.Combobox(
            panel,
            textvariable=self.buff_formula_var,
            state="readonly",
            width=32,
            values=[label for _, label in options],
        )
        self.buff_formula_dropdown.grid(row=0, column=1, sticky="ew", padx=4, pady=2)
        self.buff_formula_dropdown.bind("<<ComboboxSelected>>", self.on_formula_select)

        ttk.Label(panel, text="Formula ID:").grid(row=1, column=0, sticky="w", padx=4, pady=2)
        self.buff_formula_entry = ttk.Entry(panel, width=10, justify="center")
        self.buff_formula_entry.grid(row=1, column=1, sticky="ew", padx=4, pady=2)
        self.buff_formula_entry.bind("<KeyRelease>", lambda e: self.update_buff_preview())

        ttk.Label(panel, text="Duration (ticks):").grid(row=2, column=0, sticky="w", padx=4, pady=2)
        self.buff_duration_entry = ttk.Entry(panel, width=10, justify="center")
        self.buff_duration_entry.grid(row=2, column=1, sticky="ew", padx=4, pady=2)
        self.buff_duration_entry.bind("<KeyRelease>", lambda e: self.update_buff_preview())

        # Preview area
        self.buff_preview = tk.Text(
            panel,
            height=4,
            wrap="word",
            state=tk.DISABLED,
            bg="#2d2d2d",
            fg="#ffffff",
            insertbackground="#ffffff",
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground="#4c4c4c",
        )
        self.buff_preview.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=4, pady=4)

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------
    def load_spell_list(self):
        self.spell_tree.delete(*self.spell_tree.get_children())
        spells = self.db_manager.execute_query("SELECT id, name FROM spells_new ORDER BY id")
        for row in spells:
            self.spell_tree.insert("", "end", values=(row["id"], row["name"]))
        # Refresh SPA library if needed
        self.load_effect_library()
        # Clear selection and form when refreshing list
        self.spell_tree.selection_remove(self.spell_tree.selection())
        self.current_spell_id = None
        self.current_spell_data = {}
        self.clear_form()

    def filter_spell_list(self, term):
        term = term.strip()
        if not term:
            self.load_spell_list()
            return
        like = f"%{term}%"
        spells = self.db_manager.execute_query(
            "SELECT id, name FROM spells_new WHERE name LIKE %s OR id LIKE %s ORDER BY id",
            (like, like),
        )
        self.spell_tree.delete(*self.spell_tree.get_children())
        for row in spells:
            self.spell_tree.insert("", "end", values=(row["id"], row["name"]))

    def on_spell_select(self, event):
        selected = self.spell_tree.selection()
        if not selected:
            return
        values = self.spell_tree.item(selected[0], "values")
        if not values:
            return
        spell_id = int(values[0])
        self.load_spell(spell_id)

    def load_spell(self, spell_id):
        spell = self.db_manager.execute_query(
            "SELECT * FROM spells_new WHERE id = %s",
            (spell_id,),
            fetch_all=False,
        )
        if not spell:
            messagebox.showerror("Load Spell", f"Spell {spell_id} not found.")
            return
        self.current_spell_id = spell_id
        self.current_spell_data = dict(spell)
        self.populate_form()

    # ------------------------------------------------------------------
    # Populate form widgets from current_spell_data
    # ------------------------------------------------------------------
    def populate_form(self):
        data = self.current_spell_data
        if not data:
            return

        def set_entry(entry, key, default=""):
            val = data.get(key, default)
            # Allow writing into disabled ID field
            prev_state = entry.cget("state")
            if prev_state in ("disabled", "readonly"):
                entry.config(state="normal")
            entry.delete(0, "end")
            entry.insert(0, str(val) if val is not None else "")
            if prev_state in ("disabled", "readonly"):
                entry.config(state=prev_state)

        set_entry(self.mana_entry, "mana")
        set_entry(self.range_entry, "range")
        set_entry(self.aoe_range_entry, "aoerange")
        set_entry(self.min_range_entry, "min_range")
        set_entry(self.cast_time_entry, "cast_time")
        set_entry(self.recovery_time_entry, "recovery_time")
        set_entry(self.recast_time_entry, "recast_time")
        set_entry(self.ae_duration_entry, "AEDuration")
        set_entry(self.player1_entry, "player_1")
        set_entry(self.teleport_zone_entry, "teleport_zone")
        set_entry(self.pushback_entry, "pushback")
        set_entry(self.pushup_entry, "pushup")
        set_entry(self.resist_type_entry, "resisttype")
        set_entry(self.resist_diff_entry, "ResistDiff")
        set_entry(self.min_resist_entry, "MinResist")
        set_entry(self.max_resist_entry, "MaxResist")
        set_entry(self.target_type_entry, "targettype")
        set_entry(self.zone_type_entry, "zonetype")
        set_entry(self.skill_entry, "skill")
        set_entry(self.travel_type_entry, "TravelType")
        set_entry(self.spell_affect_index_entry, "SpellAffectIndex")
        # Buff formula/duration
        formula_val = data.get("buffdurationformula", 0)
        duration_val = data.get("buffduration", 0)
        # Set dropdown to matching formula if exists
        matched_label = None
        for fid, text in self.buff_formula_options:
            if fid == formula_val:
                matched_label = text
                break
        if matched_label:
            self.buff_formula_var.set(matched_label)
        else:
            # Custom
            self.buff_formula_var.set("Custom (>=200 cap/fixed)")
        self.buff_formula_entry.delete(0, "end")
        self.buff_formula_entry.insert(0, str(formula_val))
        self.buff_duration_entry.delete(0, "end")
        self.buff_duration_entry.insert(0, str(duration_val))
        self.update_buff_preview()

        # Description from db_str using descnum
        descnum = data.get("descnum", 0)
        self.descnum_entry.delete(0, "end")
        self.descnum_entry.insert(0, str(descnum or ""))
        self.load_description_text(descnum)

        # Update header labels for ID/Name
        self.id_label.config(text=f"ID: {data.get('id', '-')}")
        self.name_label.config(text=f"Name: {data.get('name', '-')}")

        self.good_effect_var.set(data.get("goodEffect", 0) or 0)
        self.activated_var.set(data.get("Activated", 0) or 0)
        self.uninterruptable_var.set(data.get("uninterruptable", 0) or 0)

        set_entry(self.you_cast_entry, "you_cast")
        set_entry(self.other_cast_entry, "other_casts")
        set_entry(self.cast_on_you_entry, "cast_on_you")
        set_entry(self.cast_on_other_entry, "cast_on_other")
        set_entry(self.spell_fades_entry, "spell_fades")

        # Icons (only new_icon editable; preserve others)
        self.icon_value = data.get("icon", 0) or 0
        self.memicon_value = data.get("memicon", 0) or 0
        set_entry(self.new_icon_entry, "new_icon")
        self.update_icon_preview()
        set_entry(self.spellanim_entry, "spellanim")
        set_entry(self.casting_anim_entry, "CastingAnim")
        set_entry(self.target_anim_entry, "TargetAnim")
        set_entry(self.nimbus_entry, "nimbuseffect")

        # Classes
        for idx in range(self.MAX_CLASS_SLOTS):
            key = f"classes{idx+1}"
            if idx < len(self.class_entries):
                set_entry(self.class_entries[idx], key, default=0)

        # Deities (checkbox -1/0); checked -> -1, unchecked -> 0
        for idx, var in enumerate(self.deity_vars):
            key = f"deities{idx}"
            value = data.get(key, 0)
            var.set(1 if value == -1 else 0)

        # Effects
        self.effect_rows = []
        self.effects_tree.delete(*self.effects_tree.get_children())
        for slot in range(1, self.MAX_EFFECT_SLOTS + 1):
            eff_id = data.get(f"effectid{slot}", 0)
            base = data.get(f"effect_base_value{slot}", 0)
            limit = data.get(f"effect_limit_value{slot}", 0)
            mx = data.get(f"max{slot}", 0)
            formula = data.get(f"formula{slot}", 0)
            if eff_id != 254:
                row = {
                    "slot": slot,
                    "effectid": eff_id,
                    "effectname": self.get_effect_name(eff_id),
                    "base": base,
                    "limit": limit,
                    "max": mx,
                    "formula": formula,
                }
                self.effect_rows.append(row)
                self.effects_tree.insert("", "end", values=(slot, eff_id, row["effectname"], base, limit, mx, formula))

    # ------------------------------------------------------------------
    # Effects editing
    # ------------------------------------------------------------------
    def create_new_effect_slot(self):
        """Find the next available empty slot (effectid 0/254) and seed it with effectid 0."""
        used_slots = {row["slot"] for row in self.effect_rows}
        slot_to_use = None
        for slot in range(1, self.MAX_EFFECT_SLOTS + 1):
            if slot not in used_slots:
                slot_to_use = slot
                break
        if slot_to_use is None:
            messagebox.showerror("Effects", "All 12 effect slots are in use.")
            return
        # Seed with defaults
        self.effect_rows.append({
            "slot": slot_to_use,
            "effectid": 0,
            "effectname": self.get_effect_name(0),
            "base": 0,
            "limit": 0,
            "max": 0,
            "formula": 0
        })
        self.refresh_effects_tree()

    def remove_effect(self):
        selected = self.effects_tree.selection()
        if not selected:
            return
        values = self.effects_tree.item(selected[0], "values")
        if not values:
            return
        slot = int(values[0])
        self.effect_rows = [row for row in self.effect_rows if row["slot"] != slot]
        self.refresh_effects_tree()

    def refresh_effects_tree(self):
        self.effects_tree.delete(*self.effects_tree.get_children())
        for row in sorted(self.effect_rows, key=lambda r: r["slot"]):
            self.effects_tree.insert("", "end", values=(
                row["slot"],
                row["effectid"],
                row.get("effectname", self.get_effect_name(row["effectid"])),
                row["base"],
                row["limit"],
                row["max"],
                row["formula"],
            ))

    # ------------------------------------------------------------------
    # Save / Clone / Delete
    # ------------------------------------------------------------------
    def gather_form_data(self):
        d = dict(self.current_spell_data) if self.current_spell_data else {}

        def get_int(entry, default=0):
            try:
                return int(entry.get())
            except Exception:
                return default

        def get_str(entry):
            return entry.get().strip()

        # ID and name now come from header / tree edits, not the basics form
        d["id"] = self.current_spell_id if self.current_spell_id is not None else 0
        d["name"] = self.current_spell_data.get("name", "") if self.current_spell_data else ""
        d["mana"] = get_int(self.mana_entry)
        d["range"] = get_int(self.range_entry)
        d["aoerange"] = get_int(self.aoe_range_entry)
        d["min_range"] = get_int(self.min_range_entry)
        d["player_1"] = get_str(self.player1_entry)
        d["teleport_zone"] = get_str(self.teleport_zone_entry)
        d["pushback"] = get_int(self.pushback_entry)
        d["pushup"] = get_int(self.pushup_entry)
        d["cast_time"] = get_int(self.cast_time_entry)
        d["recovery_time"] = get_int(self.recovery_time_entry)
        d["recast_time"] = get_int(self.recast_time_entry)
        d["buffdurationformula"] = get_int(self.buff_formula_entry)
        d["buffduration"] = get_int(self.buff_duration_entry)
        d["descnum"] = get_int(self.descnum_entry)
        d["AEDuration"] = get_int(self.ae_duration_entry)
        d["resisttype"] = get_int(self.resist_type_entry)
        d["ResistDiff"] = get_int(self.resist_diff_entry)
        d["MinResist"] = get_int(self.min_resist_entry)
        d["MaxResist"] = get_int(self.max_resist_entry)
        d["targettype"] = get_int(self.target_type_entry)
        d["zonetype"] = get_int(self.zone_type_entry)
        d["skill"] = get_int(self.skill_entry)
        d["TravelType"] = get_int(self.travel_type_entry)
        d["SpellAffectIndex"] = get_int(self.spell_affect_index_entry)
        d["goodEffect"] = self.good_effect_var.get()
        d["Activated"] = self.activated_var.get()
        d["uninterruptable"] = self.uninterruptable_var.get()

        d["you_cast"] = get_str(self.you_cast_entry)
        d["other_casts"] = get_str(self.other_cast_entry)
        d["cast_on_you"] = get_str(self.cast_on_you_entry)
        d["cast_on_other"] = get_str(self.cast_on_other_entry)
        d["spell_fades"] = get_str(self.spell_fades_entry)

        d["icon"] = self.icon_value
        d["memicon"] = self.memicon_value
        d["new_icon"] = get_int(self.new_icon_entry)
        d["spellanim"] = get_int(self.spellanim_entry)
        d["CastingAnim"] = get_int(self.casting_anim_entry)
        d["TargetAnim"] = get_int(self.target_anim_entry)
        d["nimbuseffect"] = get_int(self.nimbus_entry)

        for idx, entry in enumerate(self.class_entries):
            d[f"classes{idx+1}"] = get_int(entry, default=0)

        for idx, var in enumerate(self.deity_vars):
            d[f"deities{idx}"] = -1 if var.get() else 0

        # Reset all effect columns to 0, then apply edited rows
        for slot in range(1, self.MAX_EFFECT_SLOTS + 1):
            d[f"effectid{slot}"] = 254
            d[f"effect_base_value{slot}"] = 0
            d[f"effect_limit_value{slot}"] = 0
            d[f"max{slot}"] = 0
            d[f"formula{slot}"] = 0
        for row in self.effect_rows:
            slot = row["slot"]
            d[f"effectid{slot}"] = row["effectid"]
            d[f"effect_base_value{slot}"] = row["base"]
            d[f"effect_limit_value{slot}"] = row["limit"]
            d[f"max{slot}"] = row["max"]
            d[f"formula{slot}"] = row["formula"]

        return d

    def save_spell(self):
        if not self.current_spell_id:
            messagebox.showerror("Save Spell", "Select a spell first.")
            return
        data = self.gather_form_data()
        target_id = data.get("id", self.current_spell_id)
        columns = list(data.keys())
        # Quote column names to avoid reserved word issues (e.g., range, cast_time)
        placeholders = ", ".join([f"`{k}` = %s" for k in columns])
        params = [data[k] for k in columns]
        params.append(self.current_spell_id)
        query = f"UPDATE spells_new SET {placeholders} WHERE id = %s"
        success = self.db_manager.execute_update(query, tuple(params))
        if success:
            self.current_spell_id = target_id
            messagebox.showinfo("Save Spell", f"Spell {target_id} saved.")
            self.load_spell_list()
            # Refresh display to show any changes to ID or other fields
            self.load_spell(target_id)
        else:
            messagebox.showerror("Save Spell", "Failed to save spell.")

    def clone_spell(self):
        selected = self.spell_tree.selection()
        if not selected:
            messagebox.showerror("Clone Spell", "Select a spell to clone.")
            return
        values = self.spell_tree.item(selected[0], "values")
        if not values:
            return
        parent_id = int(values[0])
        parent = self.db_manager.execute_query(
            "SELECT * FROM spells_new WHERE id = %s",
            (parent_id,),
            fetch_all=False,
        )
        if not parent:
            messagebox.showerror("Clone Spell", f"Spell {parent_id} not found.")
            return
        next_id_row = self.db_manager.execute_query("SELECT MAX(id) AS max_id FROM spells_new", fetch_all=False)
        next_id = (next_id_row["max_id"] or 0) + 1
        parent = dict(parent)
        parent["id"] = next_id
        parent["name"] = f"{parent.get('name', '')} (Clone)"
        # field### left untouched from parent; user requested defaults/parent carry

        columns = ", ".join(parent.keys())
        placeholders = ", ".join(["%s"] * len(parent))
        # Quote columns to avoid reserved words
        query = f"INSERT INTO spells_new ({', '.join([f'`{c}`' for c in parent.keys()])}) VALUES ({placeholders})"
        success = self.db_manager.execute_update(query, tuple(parent.values()))
        if success:
            messagebox.showinfo("Clone Spell", f"Cloned to ID {next_id}.")
            self.load_spell_list()
        else:
            messagebox.showerror("Clone Spell", "Failed to clone spell.")

    def delete_spell(self):
        selected = self.spell_tree.selection()
        if not selected:
            messagebox.showerror("Delete Spell", "Select a spell to delete.")
            return
        values = self.spell_tree.item(selected[0], "values")
        if not values:
            return
        spell_id = int(values[0])
        if not messagebox.askyesno("Delete Spell", f"Delete spell {spell_id}?"):
            return
        success = self.db_manager.execute_update("DELETE FROM spells_new WHERE id = %s", (spell_id,))
        if success:
            self.load_spell_list()
            self.current_spell_id = None
            self.current_spell_data = {}
            self.clear_form()
        else:
            messagebox.showerror("Delete Spell", "Failed to delete spell.")

    def edit_tree_id_name(self):
        selected = self.spell_tree.selection()
        if not selected:
            messagebox.showerror("Edit Spell", "Select a spell to edit ID/Name.")
            return
        values = self.spell_tree.item(selected[0], "values")
        if not values:
            return
        old_id = int(values[0])
        old_name = values[1]

        new_id = simpledialog.askinteger("Edit Spell ID", "Enter new ID:", initialvalue=old_id, parent=self.parent)
        if new_id is None:
            return
        new_name = simpledialog.askstring("Edit Spell Name", "Enter new name:", initialvalue=old_name, parent=self.parent)
        if new_name is None:
            return

        # Prevent duplicate IDs
        if new_id != old_id:
            exists = self.db_manager.execute_query(
                "SELECT id FROM spells_new WHERE id = %s",
                (new_id,),
                fetch_all=False,
            )
            if exists:
                messagebox.showerror("Edit Spell", f"ID {new_id} already exists.")
                return

        success = self.db_manager.execute_update(
            "UPDATE spells_new SET id = %s, name = %s WHERE id = %s",
            (new_id, new_name, old_id),
        )
        if success:
            self.current_spell_id = new_id
            self.load_spell_list()
            self.load_spell(new_id)
        else:
            messagebox.showerror("Edit Spell", "Failed to update spell ID/Name.")

    def clear_form(self):
        self.id_label.config(text="ID: -")
        self.name_label.config(text="Name: -")
        for entry in [
            self.mana_entry, self.range_entry, self.aoe_range_entry,
            self.min_range_entry, self.cast_time_entry, self.recovery_time_entry, self.recast_time_entry,
            self.ae_duration_entry,
            self.resist_type_entry, self.resist_diff_entry, self.min_resist_entry, self.max_resist_entry,
            self.target_type_entry, self.zone_type_entry, self.skill_entry, self.travel_type_entry,
            self.spell_affect_index_entry, self.you_cast_entry, self.other_cast_entry, self.cast_on_you_entry,
            self.cast_on_other_entry, self.spell_fades_entry,
            self.new_icon_entry, self.spellanim_entry, self.casting_anim_entry, self.target_anim_entry,
            self.nimbus_entry, self.player1_entry, self.teleport_zone_entry, self.pushback_entry, self.pushup_entry,
            self.descnum_entry, self.buff_formula_entry, self.buff_duration_entry,
        ]:
            prev_state = entry.cget("state")
            if prev_state in ("disabled", "readonly"):
                entry.config(state="normal")
            entry.delete(0, "end")
            if prev_state in ("disabled", "readonly"):
                entry.config(state=prev_state)
        for entry in self.class_entries:
            entry.delete(0, "end")
            entry.insert(0, "0")
        for var in getattr(self, "deity_vars", []):
            var.set(0)
        self.good_effect_var.set(0)
        self.activated_var.set(0)
        self.uninterruptable_var.set(0)
        self.icon_value = 0
        self.memicon_value = 0
        self.icon_image_ref = None
        if hasattr(self, "icon_preview_label"):
            self.icon_preview_label.config(image="", text="No icon")
        self.buff_formula_var.set("")
        self.buff_formula_entry.delete(0, "end")
        self.buff_duration_entry.delete(0, "end")
        self.desc_text.config(state=tk.NORMAL)
        self.desc_text.delete("1.0", tk.END)
        self.desc_text.config(state=tk.DISABLED)
        self.effect_rows = []
        self.refresh_effects_tree()
        self.update_buff_preview()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def load_spell_effect_lookup(self):
        """Load SPA id->name mapping from notes.db if available."""
        lookup = {}
        details = {}

        # First, try notes.db
        if self.notes_db_manager:
            try:
                rows = self.notes_db_manager.get_all_spell_effects()
                lookup.update({row["id"]: row["name"] for row in rows})
            except Exception:
                pass

        # Next, parse local markdown for richer details
        md_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "spell-effect-ids.md")
        if os.path.exists(md_path):
            try:
                with open(md_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line.startswith("|") or line.startswith("| ID"):
                            continue
                        parts = [p.strip() for p in line.strip("|").split("|")]
                        if len(parts) < 4:
                            continue
                        # Expect columns: ID, SPA, Name, Description, Base, Limit, Max, Notes
                        if len(parts) >= 8:
                            id_str, spa_code, name, desc, base, limit, maxv = parts[:7]
                            notes = "|".join(parts[7:]).strip()
                        else:
                            id_str, spa_code, name = parts[:3]
                            desc = base = limit = maxv = notes = ""
                        try:
                            eff_id = int(id_str)
                        except Exception:
                            continue
                        lookup.setdefault(eff_id, name)
                        details[eff_id] = {
                            "id": eff_id,
                            "spa": spa_code,
                            "name": name,
                            "description": desc,
                            "base": base,
                            "limit": limit,
                            "max": maxv,
                            "notes": notes,
                        }
            except Exception:
                pass

        # fallback for none values
        lookup.setdefault(0, "None")
        lookup.setdefault(254, "None")
        self.spell_effect_lookup = lookup
        self.spell_effect_details = details
        # Initialize deity vars list for dialog
        if not hasattr(self, "deity_vars"):
            self.deity_vars = [tk.IntVar() for _ in range(self.MAX_DEITY_SLOTS)]

    def load_class_deity_names(self):
        """Load human-readable class/deity names if available."""
        # Classes 1-16
        try:
            if self.notes_db_manager:
                classes = self.notes_db_manager.get_class_bitmasks()
                # Sort by id to align with classes1..classes16 ordering
                classes_sorted = sorted(classes, key=lambda r: r.get("id", 0))
                for idx in range(min(len(classes_sorted), self.MAX_CLASS_SLOTS)):
                    self.class_names[idx] = classes_sorted[idx].get("name", self.class_names[idx])
        except Exception:
            pass

        # Deities 0-16
        try:
            if self.notes_db_manager:
                deities = self.notes_db_manager.get_deity_bitmasks()
                # Use provided order; if fewer than 17, fill remaining with defaults
                for idx in range(min(len(deities), self.MAX_DEITY_SLOTS)):
                    self.deity_names[idx] = deities[idx].get("name", self.deity_names[idx])
        except Exception:
            pass

    def get_effect_name(self, effect_id):
        return self.spell_effect_lookup.get(effect_id, f"Effect {effect_id}")

    def load_effect_library(self, term=""):
        """Populate SPA library tree with optional search."""
        self.spa_tree.delete(*self.spa_tree.get_children())
        term = (term or "").strip().lower()
        items = self.spell_effect_lookup.items()
        if term:
            items = [(i, n) for i, n in items if term in n.lower() or term in str(i)]
        for eff_id, name in sorted(items, key=lambda x: x[0]):
            self.spa_tree.insert("", "end", values=(eff_id, name))

    def on_spa_select(self, event=None):
        """Show SPA detail in detail pane."""
        if not hasattr(self, "spa_tree"):
            return
        selection = self.spa_tree.selection()
        if not selection:
            return
        values = self.spa_tree.item(selection[0], "values")
        if not values:
            return
        eff_id = int(values[0])
        detail = self.spell_effect_details.get(eff_id, {})
        desc = detail.get("description", "")
        base = detail.get("base", "")
        limit = detail.get("limit", "")
        maxv = detail.get("max", "")
        notes = detail.get("notes", "")

        text = f"Description: {desc}\nBase: {base}\nLimit: {limit}\nMax: {maxv}\nNotes: {notes}"
        self.spa_detail.config(state=tk.NORMAL)
        self.spa_detail.delete("1.0", tk.END)
        self.spa_detail.insert("1.0", text)
        self.spa_detail.config(state=tk.DISABLED)

    def on_formula_select(self, event=None):
        """Update formula/duration fields based on dropdown selection."""
        label = self.buff_formula_var.get()
        # find formula id from label
        formula_id = None
        for fid, text in self.buff_formula_options:
            if text == label:
                formula_id = fid
                break
        if formula_id is None:
            return
        self.buff_formula_entry.delete(0, "end")
        self.buff_formula_entry.insert(0, str(formula_id))
        # Auto duration for fixed/permanent selections
        if formula_id in (50, 51):
            self.buff_duration_entry.delete(0, "end")
            self.buff_duration_entry.insert(0, "1")
        elif formula_id == 0:
            self.buff_duration_entry.delete(0, "end")
            self.buff_duration_entry.insert(0, "0")
        self.update_buff_preview()

    def compute_formula_ticks(self, formula_id, duration_ticks, level):
        """Return effective ticks based on formula and duration (lower of calc/cap)."""
        if formula_id in (50, 51):
            return 1
        if formula_id == 0:
            return duration_ticks
        if formula_id == 200:
            # custom cap: duration as desired
            return duration_ticks
        if formula_id >= 200 and formula_id != 3600:
            # use formula as cap if duration > formula
            return min(duration_ticks, formula_id)
        if formula_id == 3600:
            return duration_ticks if duration_ticks else 3600

        # Classic formulas
        f = formula_id
        lvl = level
        calc = duration_ticks
        try:
            if f == 1:
                calc = lvl // 2
            elif f == 2:
                calc = lvl // 2 + 5 if lvl > 3 else 6
            elif f == 3:
                calc = 30 * lvl
            elif f == 4:
                calc = 50
            elif f == 5:
                calc = 2
            elif f == 6:
                calc = lvl // 2 + 2
            elif f == 7:
                calc = lvl
            elif f == 8:
                calc = lvl + 10
            elif f == 9:
                calc = 2 * lvl + 10
            elif f == 10:
                calc = 3 * lvl + 10
            elif f == 11:
                calc = 30 * (lvl + 3)
            elif f == 12:
                calc = lvl // 4 if lvl > 7 else 1
            elif f == 13:
                calc = 4 * lvl + 10
            elif f == 14:
                calc = 5 * (lvl + 2)
            elif f == 15:
                calc = 10 * (lvl + 10)
        except Exception:
            calc = duration_ticks

        # For standard formulas, use the lower of duration or calculated
        return min(duration_ticks, calc) if duration_ticks else calc

    def update_buff_preview(self):
        """Show sample durations for a few levels with current formula/duration."""
        try:
            formula_id = int(self.buff_formula_entry.get() or 0)
        except Exception:
            formula_id = 0
        try:
            duration_ticks = int(self.buff_duration_entry.get() or 0)
        except Exception:
            duration_ticks = 0

        sample_levels = [10, 20, 50]
        lines = []
        for lvl in sample_levels:
            ticks = self.compute_formula_ticks(formula_id, duration_ticks, lvl)
            seconds = ticks * 6
            lines.append(f"Lvl {lvl}: {ticks} ticks ({seconds}s)")

        text = "\n".join(lines) if lines else ""
        self.buff_preview.config(state=tk.NORMAL)
        self.buff_preview.delete("1.0", tk.END)
        self.buff_preview.insert("1.0", text)
        self.buff_preview.config(state=tk.DISABLED)

    def update_icon_preview(self):
        """Update icon preview based on new_icon value."""
        try:
            icon_id = int(self.new_icon_entry.get() or 0)
        except Exception:
            icon_id = 0
        icons_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "images", "icons")
        icon_path = os.path.join(icons_dir, f"{icon_id}.gif")
        if os.path.exists(icon_path):
            try:
                img = tk.PhotoImage(file=icon_path)
                self.icon_image_ref = img
                self.icon_preview_label.config(image=img, text="")
            except Exception:
                self.icon_preview_label.config(image="", text="No icon")
                self.icon_image_ref = None
        else:
            self.icon_preview_label.config(image="", text="No icon")
            self.icon_image_ref = None

    def load_description_text(self, descnum):
        """Load description text from db_str using descnum."""
        text = ""
        if descnum and descnum > 0:
            text = self.get_db_str_value(descnum)
        self.desc_text.config(state=tk.NORMAL)
        self.desc_text.delete("1.0", tk.END)
        self.desc_text.insert("1.0", text or "")

    def get_db_str_value(self, sid):
        """Fetch db_str value; for spell descriptions use type 6."""
        try:
            result = self.db_manager.execute_query(
                "SELECT value FROM db_str WHERE id = %s AND type = 6",
                (sid,),
                fetch_all=False,
            )
            if result and result.get("value"):
                return result["value"]
        except Exception:
            pass
        return ""

    def save_description(self):
        """Insert/update db_str type 6 with current descnum and text."""
        try:
            desc_id = int(self.descnum_entry.get())
        except Exception:
            messagebox.showerror("Description", "Desc ID must be a number.")
            return
        text = self.desc_text.get("1.0", tk.END).strip()
        if desc_id <= 0:
            messagebox.showerror("Description", "Desc ID must be greater than 0.")
            return
        # Determine if exists
        existing = self.db_manager.execute_query(
            "SELECT value FROM db_str WHERE id = %s AND type = 6",
            (desc_id,),
            fetch_all=False,
        )
        if existing:
            ok = self.db_manager.execute_update(
                "UPDATE db_str SET value = %s WHERE id = %s AND type = 6",
                (text, desc_id),
            )
        else:
            ok = self.db_manager.execute_update(
                "INSERT INTO db_str (id, type, value) VALUES (%s, 6, %s)",
                (desc_id, text),
            )
        if ok:
            messagebox.showinfo("Description", f"Description saved to db_str id {desc_id}, type 6.")
        else:
            messagebox.showerror("Description", "Failed to save description.")

    def new_description(self):
        """Find next available db_str id for type 6 and prep for new text."""
        next_id_row = self.db_manager.execute_query(
            "SELECT COALESCE(MAX(id),0) + 1 AS next_id FROM db_str WHERE type = 6",
            fetch_all=False,
        )
        next_id = (next_id_row["next_id"] if next_id_row else 0) or 0
        if next_id <= 0:
            messagebox.showerror("Description", "Could not determine next description ID.")
            return
        self.descnum_entry.delete(0, "end")
        self.descnum_entry.insert(0, str(next_id))
        self.desc_text.config(state=tk.NORMAL)
        self.desc_text.delete("1.0", tk.END)
        self.desc_text.focus_set()

    def setup_treeview_sorting(self, treeview):
        def sort_column(tv, col, reverse):
            data = [(tv.set(k, col), k) for k in tv.get_children("")]
            try:
                data.sort(key=lambda t: int(t[0]), reverse=reverse)
            except ValueError:
                data.sort(reverse=reverse)
            for index, (val, k) in enumerate(data):
                tv.move(k, "", index)
            tv.heading(col, command=lambda: sort_column(tv, col, not reverse))

        for col in treeview["columns"]:
            treeview.heading(col, command=lambda _col=col: sort_column(treeview, _col, False))

    def _add_entry(self, parent, label, row, col, width=12, state="normal"):
        ttk.Label(parent, text=label).grid(row=row, column=col, sticky="e", padx=3, pady=2)
        entry = ttk.Entry(parent, width=width, state=state)
        entry.grid(row=row, column=col + 1, sticky="w", padx=3, pady=2)
        return entry

    def on_effects_tree_double_click(self, event):
        """Inline edit effect rows via an Entry overlay."""
        tree = self.effects_tree
        item_id = tree.identify_row(event.y)
        col_id = tree.identify_column(event.x)  # '#1', '#2', ...
        if not item_id or not col_id:
            return

        col_map = {
            "#2": "effectid",
            "#4": "base",
            "#5": "limit",
            "#6": "max",
            "#7": "formula",
        }
        field = col_map.get(col_id)
        if not field:
            return  # non-editable column

        values = list(tree.item(item_id, "values"))
        if not values:
            return
        slot = int(values[0])
        current_val = values[int(col_id[1:]) - 1]

        bbox = tree.bbox(item_id, col_id)
        if not bbox:
            return

        entry = tk.Entry(tree)
        entry.insert(0, current_val)
        entry.select_range(0, tk.END)
        entry.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])
        entry.focus_set()

        def commit(event=None):
            new_val_raw = entry.get()
            entry.destroy()
            try:
                new_val = int(new_val_raw)
            except Exception:
                return

            # Update effect_rows
            for row in self.effect_rows:
                if row["slot"] == slot:
                    row[field] = new_val
                    if field == "effectid":
                        row["effectname"] = self.get_effect_name(new_val)
                    break
            else:
                return

            # Refresh row display
            for row in self.effect_rows:
                if row["slot"] == slot:
                    tree.item(
                        item_id,
                        values=(
                            row["slot"],
                            row["effectid"],
                            row.get("effectname", self.get_effect_name(row["effectid"])),
                            row["base"],
                            row["limit"],
                            row["max"],
                            row["formula"],
                        ),
                    )
                    break
            # Auto-save after edit
            self.save_spell()

        entry.bind("<Return>", commit)
        entry.bind("<FocusOut>", commit)

    def apply_selected_effect_from_library(self):
        """Apply selected SPA from library to next available slot."""
        selection = self.spa_tree.selection()
        if not selection:
            messagebox.showerror("Effects", "Select a SPA to apply.")
            return
        values = self.spa_tree.item(selection[0], "values")
        if not values:
            return
        eff_id = int(values[0])
        # find next available slot
        used_slots = {row["slot"] for row in self.effect_rows}
        slot_to_use = None
        for slot in range(1, self.MAX_EFFECT_SLOTS + 1):
            if slot not in used_slots:
                slot_to_use = slot
                break
        if slot_to_use is None:
            messagebox.showerror("Effects", "All 12 effect slots are in use.")
            return
        self.effect_rows.append({
            "slot": slot_to_use,
            "effectid": eff_id,
            "effectname": self.get_effect_name(eff_id),
            "base": 0,
            "limit": 0,
            "max": 0,
            "formula": 0
        })
        self.refresh_effects_tree()

    def open_deities_dialog(self):
        """Open a compact dialog to edit deity flags."""
        dlg = tk.Toplevel(self.parent)
        dlg.title("Deities")
        dlg.configure(bg="#2d2d2d")
        dlg.resizable(False, False)
        grid = ttk.Frame(dlg)
        grid.grid(row=0, column=0, padx=8, pady=8)
        for idx in range(self.MAX_DEITY_SLOTS):
            # Ensure var list exists
            if idx >= len(self.deity_vars):
                self.deity_vars.append(tk.IntVar())
            cb = tk.Checkbutton(
                grid,
                text=self.deity_names[idx],
                variable=self.deity_vars[idx],
                fg="#ffffff",
                bg="#2d2d2d",
                activeforeground="#ffffff",
                activebackground="#3c3c3c",
                selectcolor="#2d2d2d",
                highlightthickness=0,
                borderwidth=0,
            )
            cb.grid(row=idx // 4, column=idx % 4, sticky="w", padx=4, pady=4)
        ttk.Button(dlg, text="Close", command=dlg.destroy).grid(row=1, column=0, pady=(0, 8))
