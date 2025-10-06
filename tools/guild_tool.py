import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.theme import set_dark_theme
from dictionaries import RACE_BITMASK_DISPLAY, CLASS_BITMASK_DISPLAY

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
            if column_index in [2, 3, 4, 5, 6, 7]:  # Numeric columns (rank, tribute settings, etc.)
                new_value = int(new_value)
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

class GuildManagerTool:
    """Guild Manager Tool - modular version for tabbed interface"""
    
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
        
        # Current selections
        self.current_guild_id = None
        self.current_guild_data = None
        
        # Initialize UI components
        self.create_ui()
        
        # Load initial data
        try:
            self.load_guilds()
            print("Guild tool initialized successfully")
        except Exception as e:
            print(f"Warning: Could not initialize guild tool data: {e}")
    
    def create_ui(self):
        """Create the complete Guild Manager UI"""
        # Configure main frame grid - 3 columns, 2 rows
        self.main_frame.grid_rowconfigure(0, weight=0)  # Top area 
        self.main_frame.grid_rowconfigure(1, weight=1)  # Bottom area (members/bank)
        self.main_frame.grid_columnconfigure(0, weight=0)  # Left column (guild list)
        self.main_frame.grid_columnconfigure(1, weight=1)  # Center column (guild details)
        self.main_frame.grid_columnconfigure(2, weight=0)  # Right column (ranks/relations)
        
        # Create the main sections
        self.create_left_column()     # Guild list spanning full height
        self.create_center_top()      # Guild details
        self.create_right_column()    # Ranks, relations, permissions
        self.create_bottom_area()     # Member roster and guild bank
    
    def create_left_column(self):
        """Create left column with guild list spanning full height"""
        # Guild list frame spanning both rows
        guild_list_frame = ttk.LabelFrame(self.main_frame, text="Guild List", padding="5")
        guild_list_frame.grid(row=0, column=0, rowspan=2, padx=5, pady=5, sticky="nsew")
        guild_list_frame.grid_rowconfigure(2, weight=1)
        guild_list_frame.grid_columnconfigure(0, weight=1)
        
        # Search controls
        search_frame = ttk.Frame(guild_list_frame)
        search_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        search_frame.grid_columnconfigure(0, weight=1)
        
        ttk.Label(search_frame, text="Search Guilds:").grid(row=0, column=0, sticky="w")
        self.guild_search_var = tk.StringVar()
        self.guild_search_entry = ttk.Entry(search_frame, textvariable=self.guild_search_var, width=25)
        self.guild_search_entry.grid(row=1, column=0, sticky="ew", pady=(2, 0))
        self.guild_search_var.trace("w", self.filter_guilds)
        
        # Filter controls
        filter_frame = ttk.Frame(guild_list_frame)
        filter_frame.grid(row=1, column=0, sticky="ew", pady=(0, 5))
        
        ttk.Button(filter_frame, text="Show All", command=self.show_all_guilds).grid(row=0, column=0, padx=(0, 2))
        ttk.Button(filter_frame, text="Clear", command=self.clear_search).grid(row=0, column=1)
        ttk.Button(filter_frame, text="Refresh", command=self.load_guilds).grid(row=0, column=2, padx=(2, 0))
        
        # Guild listbox
        self.guild_listbox = tk.Listbox(guild_list_frame, width=35)
        self.guild_listbox.grid(row=2, column=0, sticky="nsew")
        self.guild_listbox.bind('<<ListboxSelect>>', self.on_guild_select)
        
        # Scrollbar for listbox
        guild_scrollbar = ttk.Scrollbar(guild_list_frame, orient="vertical", command=self.guild_listbox.yview)
        guild_scrollbar.grid(row=2, column=1, sticky="ns")
        self.guild_listbox.config(yscrollcommand=guild_scrollbar.set)
    
    def create_center_top(self):
        """Create center area with guild details"""
        # Guild details frame
        details_frame = ttk.LabelFrame(self.main_frame, text="Guild Information", padding="5")
        details_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        details_frame.grid_columnconfigure(1, weight=1)
        details_frame.grid_columnconfigure(3, weight=1)
        
        # Basic guild info in 2 columns
        ttk.Label(details_frame, text="Guild ID:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.guild_id_var = tk.StringVar()
        self.guild_id_entry = ttk.Entry(details_frame, textvariable=self.guild_id_var, state="readonly", width=15)
        self.guild_id_entry.grid(row=0, column=1, sticky="ew", padx=(0, 20))
        
        ttk.Label(details_frame, text="Guild Name:").grid(row=0, column=2, sticky="w", padx=(0, 5))
        self.guild_name_var = tk.StringVar()
        self.guild_name_entry = ttk.Entry(details_frame, textvariable=self.guild_name_var)
        self.guild_name_entry.grid(row=0, column=3, sticky="ew")
        
        ttk.Label(details_frame, text="Leader:").grid(row=1, column=0, sticky="w", padx=(0, 5), pady=(5, 0))
        self.guild_leader_var = tk.StringVar()
        self.guild_leader_entry = ttk.Entry(details_frame, textvariable=self.guild_leader_var, width=15)
        self.guild_leader_entry.grid(row=1, column=1, sticky="ew", pady=(5, 0), padx=(0, 20))
        
        ttk.Label(details_frame, text="Min Status:").grid(row=1, column=2, sticky="w", padx=(0, 5), pady=(5, 0))
        self.guild_minstatus_var = tk.StringVar()
        self.guild_minstatus_entry = ttk.Entry(details_frame, textvariable=self.guild_minstatus_var)
        self.guild_minstatus_entry.grid(row=1, column=3, sticky="ew", pady=(5, 0))
        
        ttk.Label(details_frame, text="Tribute:").grid(row=2, column=0, sticky="w", padx=(0, 5), pady=(5, 0))
        self.guild_tribute_var = tk.StringVar()
        self.guild_tribute_entry = ttk.Entry(details_frame, textvariable=self.guild_tribute_var, width=15)
        self.guild_tribute_entry.grid(row=2, column=1, sticky="ew", pady=(5, 0), padx=(0, 20))
        
        ttk.Label(details_frame, text="Favor:").grid(row=2, column=2, sticky="w", padx=(0, 5), pady=(5, 0))
        self.guild_favor_var = tk.StringVar()
        self.guild_favor_entry = ttk.Entry(details_frame, textvariable=self.guild_favor_var)
        self.guild_favor_entry.grid(row=2, column=3, sticky="ew", pady=(5, 0))
        
        # MOTD section
        ttk.Label(details_frame, text="Message of the Day:").grid(row=3, column=0, columnspan=4, sticky="w", pady=(10, 2))
        
        motd_frame = ttk.Frame(details_frame)
        motd_frame.grid(row=4, column=0, columnspan=4, sticky="ew", pady=(0, 5))
        motd_frame.grid_columnconfigure(0, weight=1)
        
        self.guild_motd_text = tk.Text(motd_frame, height=4, wrap=tk.WORD)
        self.guild_motd_text.grid(row=0, column=0, sticky="ew")
        
        motd_scrollbar = ttk.Scrollbar(motd_frame, orient="vertical", command=self.guild_motd_text.yview)
        motd_scrollbar.grid(row=0, column=1, sticky="ns")
        self.guild_motd_text.config(yscrollcommand=motd_scrollbar.set)
        
        ttk.Label(details_frame, text="MOTD Setter:").grid(row=5, column=0, sticky="w", padx=(0, 5), pady=(5, 0))
        self.guild_motd_setter_var = tk.StringVar()
        self.guild_motd_setter_entry = ttk.Entry(details_frame, textvariable=self.guild_motd_setter_var)
        self.guild_motd_setter_entry.grid(row=5, column=1, sticky="ew", pady=(5, 0), padx=(0, 20))
        
        ttk.Label(details_frame, text="Channel:").grid(row=5, column=2, sticky="w", padx=(0, 5), pady=(5, 0))
        self.guild_channel_var = tk.StringVar()
        self.guild_channel_entry = ttk.Entry(details_frame, textvariable=self.guild_channel_var)
        self.guild_channel_entry.grid(row=5, column=3, sticky="ew", pady=(5, 0))
        
        ttk.Label(details_frame, text="URL:").grid(row=6, column=0, sticky="w", padx=(0, 5), pady=(5, 0))
        self.guild_url_var = tk.StringVar()
        self.guild_url_entry = ttk.Entry(details_frame, textvariable=self.guild_url_var)
        self.guild_url_entry.grid(row=6, column=1, columnspan=3, sticky="ew", pady=(5, 0))
        
        # Buttons
        button_frame = ttk.Frame(details_frame)
        button_frame.grid(row=7, column=0, columnspan=4, sticky="ew", pady=(10, 0))
        
        ttk.Button(button_frame, text="Save Guild", command=self.save_guild).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(button_frame, text="New Guild", command=self.new_guild).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(button_frame, text="Delete Guild", command=self.delete_guild).grid(row=0, column=2)
    
    def create_right_column(self):
        """Create right column with ranks, relations, and permissions"""
        right_frame = ttk.Frame(self.main_frame)
        right_frame.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        right_frame.grid_rowconfigure(0, weight=1)
        right_frame.grid_rowconfigure(1, weight=1)
        right_frame.grid_rowconfigure(2, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)
        
        # Guild Ranks
        ranks_frame = ttk.LabelFrame(right_frame, text="Guild Ranks", padding="5")
        ranks_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 3))
        ranks_frame.grid_rowconfigure(0, weight=1)
        ranks_frame.grid_columnconfigure(0, weight=1)
        
        self.ranks_tree = ttk.Treeview(ranks_frame, columns=("rank", "title"), show="headings", height=6)
        self.ranks_tree.heading("#1", text="Rank")
        self.ranks_tree.heading("#2", text="Title")
        self.ranks_tree.column("#1", width=50)
        self.ranks_tree.column("#2", width=120)
        self.ranks_tree.grid(row=0, column=0, sticky="nsew")
        
        ranks_scrollbar = ttk.Scrollbar(ranks_frame, orient="vertical", command=self.ranks_tree.yview)
        ranks_scrollbar.grid(row=0, column=1, sticky="ns")
        self.ranks_tree.config(yscrollcommand=ranks_scrollbar.set)
        
        # Rank editing - allow editing of title column (index 1)
        self.ranks_editor = TreeviewEdit(self.ranks_tree, [1], self.update_rank)
        
        # Guild Relations
        relations_frame = ttk.LabelFrame(right_frame, text="Guild Relations", padding="5")
        relations_frame.grid(row=1, column=0, sticky="nsew", pady=3)
        relations_frame.grid_rowconfigure(0, weight=1)
        relations_frame.grid_columnconfigure(0, weight=1)
        
        self.relations_tree = ttk.Treeview(relations_frame, columns=("guild2", "guild_name", "relation"), show="headings", height=6)
        self.relations_tree.heading("#1", text="Guild ID")
        self.relations_tree.heading("#2", text="Guild Name")
        self.relations_tree.heading("#3", text="Relation")
        self.relations_tree.column("#1", width=60)
        self.relations_tree.column("#2", width=100)
        self.relations_tree.column("#3", width=60)
        self.relations_tree.grid(row=0, column=0, sticky="nsew")
        
        relations_scrollbar = ttk.Scrollbar(relations_frame, orient="vertical", command=self.relations_tree.yview)
        relations_scrollbar.grid(row=0, column=1, sticky="ns")
        self.relations_tree.config(yscrollcommand=relations_scrollbar.set)
        
        # Relations editing - allow editing of relation column (index 2)
        self.relations_editor = TreeviewEdit(self.relations_tree, [2], self.update_relation)
        
        # Guild Permissions
        permissions_frame = ttk.LabelFrame(right_frame, text="Guild Permissions", padding="5")
        permissions_frame.grid(row=2, column=0, sticky="nsew", pady=(3, 0))
        permissions_frame.grid_rowconfigure(0, weight=1)
        permissions_frame.grid_columnconfigure(0, weight=1)
        
        self.permissions_tree = ttk.Treeview(permissions_frame, columns=("perm_id", "permission"), show="headings", height=6)
        self.permissions_tree.heading("#1", text="Perm ID")
        self.permissions_tree.heading("#2", text="Permission")
        self.permissions_tree.column("#1", width=60)
        self.permissions_tree.column("#2", width=100)
        self.permissions_tree.grid(row=0, column=0, sticky="nsew")
        
        permissions_scrollbar = ttk.Scrollbar(permissions_frame, orient="vertical", command=self.permissions_tree.yview)
        permissions_scrollbar.grid(row=0, column=1, sticky="ns")
        self.permissions_tree.config(yscrollcommand=permissions_scrollbar.set)
        
        # Permissions editing - allow editing of permission column (index 1)
        self.permissions_editor = TreeviewEdit(self.permissions_tree, [1], self.update_permission)
    
    def create_bottom_area(self):
        """Create bottom area with member roster and guild bank"""
        # Notebook for tabs
        notebook = ttk.Notebook(self.main_frame)
        notebook.grid(row=1, column=1, columnspan=2, padx=5, pady=(0, 5), sticky="nsew")
        
        # Member roster tab
        members_frame = ttk.Frame(notebook)
        notebook.add(members_frame, text="Guild Members")
        
        members_frame.grid_rowconfigure(1, weight=1)
        members_frame.grid_columnconfigure(0, weight=1)
        
        # Member search
        member_search_frame = ttk.Frame(members_frame)
        member_search_frame.grid(row=0, column=0, sticky="ew", pady=(5, 5))
        member_search_frame.grid_columnconfigure(0, weight=1)
        
        ttk.Label(member_search_frame, text="Search Members:").grid(row=0, column=0, sticky="w")
        self.member_search_var = tk.StringVar()
        self.member_search_entry = ttk.Entry(member_search_frame, textvariable=self.member_search_var)
        self.member_search_entry.grid(row=1, column=0, sticky="ew")
        self.member_search_var.trace("w", self.filter_members)
        
        # Members treeview
        member_columns = ("char_id", "name", "rank", "rank_title", "level", "class", "race", 
                         "tribute_enable", "total_tribute", "last_tribute", "banker", "alt", "online", "last_login")
        
        self.members_tree = ttk.Treeview(members_frame, columns=member_columns, show="headings", height=12)
        
        # Set up member columns
        column_widths = {
            "char_id": 60, "name": 120, "rank": 40, "rank_title": 100, "level": 40, "class": 60, "race": 60,
            "tribute_enable": 70, "total_tribute": 80, "last_tribute": 80, "banker": 50, "alt": 30, "online": 50, "last_login": 100
        }
        
        for col in member_columns:
            self.members_tree.heading(col, text=col.replace("_", " ").title())
            self.members_tree.column(col, width=column_widths.get(col, 80))
        
        self.members_tree.grid(row=1, column=0, sticky="nsew")
        
        members_scrollbar = ttk.Scrollbar(members_frame, orient="vertical", command=self.members_tree.yview)
        members_scrollbar.grid(row=1, column=1, sticky="ns")
        self.members_tree.config(yscrollcommand=members_scrollbar.set)
        
        # Member editing - allow editing of rank, tribute settings, banker, alt status
        self.members_editor = TreeviewEdit(self.members_tree, [2, 7, 10, 11], self.update_member)
        
        # Guild Bank tab
        bank_frame = ttk.Frame(notebook)
        notebook.add(bank_frame, text="Guild Bank")
        
        bank_frame.grid_rowconfigure(0, weight=1)
        bank_frame.grid_columnconfigure(0, weight=1)
        
        # Bank treeview
        bank_columns = ("area", "slot", "item_id", "item_name", "quantity", "donator", "permissions", "who_for")
        
        self.bank_tree = ttk.Treeview(bank_frame, columns=bank_columns, show="headings", height=15)
        
        # Set up bank columns
        bank_column_widths = {
            "area": 50, "slot": 50, "item_id": 70, "item_name": 200, "quantity": 70, 
            "donator": 100, "permissions": 80, "who_for": 100
        }
        
        for col in bank_columns:
            self.bank_tree.heading(col, text=col.replace("_", " ").title())
            self.bank_tree.column(col, width=bank_column_widths.get(col, 80))
        
        self.bank_tree.grid(row=0, column=0, sticky="nsew")
        
        bank_scrollbar = ttk.Scrollbar(bank_frame, orient="vertical", command=self.bank_tree.yview)
        bank_scrollbar.grid(row=0, column=1, sticky="ns")
        self.bank_tree.config(yscrollcommand=bank_scrollbar.set)
    
    # Event handlers and data loading methods will be added next
    def load_guilds(self):
        """Load all guilds from database"""
        try:
            query = """
            SELECT g.id, g.name, g.leader, cd.name as leader_name, 
                   COUNT(gm.char_id) as member_count
            FROM guilds g
            LEFT JOIN character_data cd ON g.leader = cd.id
            LEFT JOIN guild_members gm ON g.id = gm.guild_id
            GROUP BY g.id, g.name, g.leader, cd.name
            ORDER BY g.name
            """
            
            guilds = self.db_manager.execute_query(query)
            
            self.guild_listbox.delete(0, tk.END)
            self.guild_data = {}
            
            for guild in guilds:
                guild_id = guild['id']
                guild_name = guild['name']
                leader_name = guild['leader_name'] or f"ID:{guild['leader']}"
                member_count = guild['member_count'] or 0
                
                display_text = f"{guild_name} ({member_count} members) - Leader: {leader_name}"
                self.guild_listbox.insert(tk.END, display_text)
                self.guild_data[self.guild_listbox.size() - 1] = guild
                
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to load guilds: {e}")
    
    def on_guild_select(self, event):
        """Handle guild selection"""
        selection = self.guild_listbox.curselection()
        if not selection:
            return
            
        index = selection[0]
        if index in self.guild_data:
            guild = self.guild_data[index]
            self.current_guild_id = guild['id']
            self.load_guild_details(guild['id'])
    
    def load_guild_details(self, guild_id):
        """Load detailed information for selected guild"""
        try:
            # Load main guild info
            query = "SELECT * FROM guilds WHERE id = %s"
            guild = self.db_manager.execute_query(query, (guild_id,), fetch_all=False)
            
            if guild:
                self.guild_id_var.set(str(guild['id']))
                self.guild_name_var.set(guild['name'])
                self.guild_leader_var.set(str(guild['leader']))
                self.guild_minstatus_var.set(str(guild['minstatus']))
                self.guild_tribute_var.set(str(guild['tribute']))
                self.guild_favor_var.set(str(guild['favor']))
                
                # Set MOTD
                self.guild_motd_text.delete(1.0, tk.END)
                self.guild_motd_text.insert(1.0, guild['motd'])
                
                self.guild_motd_setter_var.set(guild['motd_setter'])
                self.guild_channel_var.set(guild['channel'])
                self.guild_url_var.set(guild['url'])
                
                # Load related data
                self.load_guild_ranks(guild_id)
                self.load_guild_relations(guild_id)
                self.load_guild_permissions(guild_id)
                self.load_guild_members(guild_id)
                self.load_guild_bank(guild_id)
                
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to load guild details: {e}")
    
    def load_guild_ranks(self, guild_id):
        """Load guild ranks"""
        try:
            query = "SELECT rank, title FROM guild_ranks WHERE guild_id = %s ORDER BY rank"
            ranks = self.db_manager.execute_query(query, (guild_id,))
            
            # Clear existing ranks
            for item in self.ranks_tree.get_children():
                self.ranks_tree.delete(item)
            
            # Add ranks
            for rank in ranks:
                self.ranks_tree.insert("", tk.END, values=(rank['rank'], rank['title']))
                
        except Exception as e:
            print(f"Error loading guild ranks: {e}")
    
    def load_guild_relations(self, guild_id):
        """Load guild relations"""
        try:
            query = """
            SELECT gr.guild2, g.name as guild_name, gr.relation
            FROM guild_relations gr
            LEFT JOIN guilds g ON gr.guild2 = g.id
            WHERE gr.guild1 = %s
            """
            relations = self.db_manager.execute_query(query, (guild_id,))
            
            # Clear existing relations
            for item in self.relations_tree.get_children():
                self.relations_tree.delete(item)
            
            # Add relations
            for relation in relations:
                relation_text = {0: "Neutral", 1: "Allied", -1: "Enemy"}.get(relation['relation'], str(relation['relation']))
                self.relations_tree.insert("", tk.END, values=(
                    relation['guild2'], 
                    relation['guild_name'] or "Unknown", 
                    relation_text
                ))
                
        except Exception as e:
            print(f"Error loading guild relations: {e}")
    
    def load_guild_permissions(self, guild_id):
        """Load guild permissions"""
        try:
            query = "SELECT perm_id, permission FROM guild_permissions WHERE guild_id = %s"
            permissions = self.db_manager.execute_query(query, (guild_id,))
            
            # Clear existing permissions
            for item in self.permissions_tree.get_children():
                self.permissions_tree.delete(item)
            
            # Add permissions
            for perm in permissions:
                self.permissions_tree.insert("", tk.END, values=(perm['perm_id'], perm['permission']))
                
        except Exception as e:
            print(f"Error loading guild permissions: {e}")
    
    def load_guild_members(self, guild_id):
        """Load guild members"""
        try:
            query = """
            SELECT gm.char_id, cd.name, gm.rank, gr.title as rank_title, 
                   cd.level, cd.class, cd.race, gm.tribute_enable, gm.total_tribute, 
                   gm.last_tribute, gm.banker, gm.alt, gm.online,
                   FROM_UNIXTIME(cd.last_login) as last_login
            FROM guild_members gm
            JOIN character_data cd ON gm.char_id = cd.id
            LEFT JOIN guild_ranks gr ON gm.guild_id = gr.guild_id AND gm.rank = gr.rank
            WHERE gm.guild_id = %s
            ORDER BY gm.rank, cd.name
            """
            members = self.db_manager.execute_query(query, (guild_id,))
            
            # Clear existing members
            for item in self.members_tree.get_children():
                self.members_tree.delete(item)
            
            # Add members
            for member in members:
                # Get class and race names from dictionaries if available
                class_name = CLASS_BITMASK_DISPLAY.get(member['class'], str(member['class']))
                race_name = RACE_BITMASK_DISPLAY.get(member['race'], str(member['race']))
                
                self.members_tree.insert("", tk.END, values=(
                    member['char_id'], member['name'], member['rank'], 
                    member['rank_title'] or f"Rank {member['rank']}", member['level'],
                    class_name, race_name, member['tribute_enable'], member['total_tribute'],
                    member['last_tribute'], member['banker'], member['alt'], 
                    "Yes" if member['online'] else "No", member['last_login']
                ))
                
        except Exception as e:
            print(f"Error loading guild members: {e}")
    
    def load_guild_bank(self, guild_id):
        """Load guild bank contents"""
        try:
            query = """
            SELECT gb.area, gb.slot, gb.item_id, i.name as item_name, gb.quantity, 
                   gb.donator, gb.permissions, gb.who_for
            FROM guild_bank gb
            LEFT JOIN items i ON gb.item_id = i.id
            WHERE gb.guild_id = %s
            ORDER BY gb.area, gb.slot
            """
            bank_items = self.db_manager.execute_query(query, (guild_id,))
            
            # Clear existing items
            for item in self.bank_tree.get_children():
                self.bank_tree.delete(item)
            
            # Add bank items
            for item in bank_items:
                self.bank_tree.insert("", tk.END, values=(
                    item['area'], item['slot'], item['item_id'], 
                    item['item_name'] or f"Item {item['item_id']}", 
                    item['quantity'], item['donator'], item['permissions'], item['who_for']
                ))
                
        except Exception as e:
            print(f"Error loading guild bank: {e}")
    
    # Filter and search methods
    def filter_guilds(self, *args):
        """Filter guilds based on search term"""
        search_term = self.guild_search_var.get().lower()
        if not search_term:
            self.show_all_guilds()
            return
            
        self.guild_listbox.delete(0, tk.END)
        filtered_data = {}
        
        for index, guild in self.guild_data.items():
            guild_name = guild['name'].lower()
            leader_name = (guild['leader_name'] or '').lower()
            
            if search_term in guild_name or search_term in leader_name:
                leader_name = guild['leader_name'] or f"ID:{guild['leader']}"
                member_count = guild['member_count'] or 0
                display_text = f"{guild['name']} ({member_count} members) - Leader: {leader_name}"
                
                self.guild_listbox.insert(tk.END, display_text)
                filtered_data[self.guild_listbox.size() - 1] = guild
        
        self.guild_data = filtered_data
    
    def filter_members(self, *args):
        """Filter members based on search term"""
        if not self.current_guild_id:
            return
        self.load_guild_members(self.current_guild_id)
    
    def show_all_guilds(self):
        """Show all guilds"""
        self.load_guilds()
    
    def clear_search(self):
        """Clear search field"""
        self.guild_search_var.set("")
    
    # Update methods for treeview editing
    def update_rank(self, tree, item_id, column_index, new_value):
        """Update guild rank in database"""
        if not self.current_guild_id:
            return
            
        values = tree.item(item_id, "values")
        rank_id = values[0]  # rank number
        
        try:
            query = "UPDATE guild_ranks SET title = %s WHERE guild_id = %s AND rank = %s"
            if self.db_manager.execute_update(query, (new_value, self.current_guild_id, rank_id)):
                messagebox.showinfo("Success", "Rank title updated successfully")
            else:
                messagebox.showerror("Error", "Failed to update rank title")
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to update rank: {e}")
    
    def update_relation(self, tree, item_id, column_index, new_value):
        """Update guild relation in database"""
        if not self.current_guild_id:
            return
            
        values = tree.item(item_id, "values")
        guild2_id = values[0]  # target guild ID
        
        try:
            # Convert text back to numeric value
            relation_value = {"Neutral": 0, "Allied": 1, "Enemy": -1}.get(new_value, int(new_value))
            
            query = "UPDATE guild_relations SET relation = %s WHERE guild1 = %s AND guild2 = %s"
            if self.db_manager.execute_update(query, (relation_value, self.current_guild_id, guild2_id)):
                messagebox.showinfo("Success", "Guild relation updated successfully")
            else:
                messagebox.showerror("Error", "Failed to update guild relation")
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to update relation: {e}")
    
    def update_permission(self, tree, item_id, column_index, new_value):
        """Update guild permission in database"""
        if not self.current_guild_id:
            return
            
        values = tree.item(item_id, "values")
        perm_id = values[0]
        
        try:
            query = "UPDATE guild_permissions SET permission = %s WHERE guild_id = %s AND perm_id = %s"
            if self.db_manager.execute_update(query, (new_value, self.current_guild_id, perm_id)):
                messagebox.showinfo("Success", "Guild permission updated successfully")
            else:
                messagebox.showerror("Error", "Failed to update guild permission")
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to update permission: {e}")
    
    def update_member(self, tree, item_id, column_index, new_value):
        """Update guild member in database"""
        if not self.current_guild_id:
            return
            
        values = tree.item(item_id, "values")
        char_id = values[0]
        
        # Map column indices to database fields
        field_map = {2: "rank", 7: "tribute_enable", 10: "banker", 11: "alt"}
        field = field_map.get(column_index)
        
        if not field:
            return
            
        try:
            query = f"UPDATE guild_members SET {field} = %s WHERE char_id = %s AND guild_id = %s"
            if self.db_manager.execute_update(query, (new_value, char_id, self.current_guild_id)):
                messagebox.showinfo("Success", f"Member {field} updated successfully")
                # Reload member data to refresh rank titles if rank was changed
                if field == "rank":
                    self.load_guild_members(self.current_guild_id)
            else:
                messagebox.showerror("Error", f"Failed to update member {field}")
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to update member: {e}")
    
    # Guild management methods
    def save_guild(self):
        """Save guild changes to database"""
        if not self.current_guild_id:
            messagebox.showwarning("No Selection", "Please select a guild to save")
            return
            
        try:
            motd_text = self.guild_motd_text.get(1.0, tk.END).strip()
            
            query = """
            UPDATE guilds SET name = %s, leader = %s, minstatus = %s, motd = %s, 
                   tribute = %s, motd_setter = %s, channel = %s, url = %s, favor = %s
            WHERE id = %s
            """
            
            params = (
                self.guild_name_var.get(),
                int(self.guild_leader_var.get()) if self.guild_leader_var.get().isdigit() else 0,
                int(self.guild_minstatus_var.get()) if self.guild_minstatus_var.get().isdigit() else 0,
                motd_text,
                int(self.guild_tribute_var.get()) if self.guild_tribute_var.get().isdigit() else 0,
                self.guild_motd_setter_var.get(),
                self.guild_channel_var.get(),
                self.guild_url_var.get(),
                int(self.guild_favor_var.get()) if self.guild_favor_var.get().isdigit() else 0,
                self.current_guild_id
            )
            
            if self.db_manager.execute_update(query, params):
                messagebox.showinfo("Success", "Guild saved successfully")
                self.load_guilds()  # Refresh guild list
            else:
                messagebox.showerror("Error", "Failed to save guild")
                
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to save guild: {e}")
    
    def new_guild(self):
        """Create a new guild"""
        # Implementation for creating new guild
        messagebox.showinfo("Feature", "New guild creation feature will be implemented")
    
    def delete_guild(self):
        """Delete selected guild"""
        if not self.current_guild_id:
            messagebox.showwarning("No Selection", "Please select a guild to delete")
            return
            
        guild_name = self.guild_name_var.get()
        
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete guild '{guild_name}'?\n\nThis will also delete all member associations, ranks, relations, and bank items."):
            try:
                # Delete related records first
                self.db_manager.execute_update("DELETE FROM guild_members WHERE guild_id = %s", (self.current_guild_id,))
                self.db_manager.execute_update("DELETE FROM guild_ranks WHERE guild_id = %s", (self.current_guild_id,))
                self.db_manager.execute_update("DELETE FROM guild_relations WHERE guild1 = %s OR guild2 = %s", (self.current_guild_id, self.current_guild_id))
                self.db_manager.execute_update("DELETE FROM guild_permissions WHERE guild_id = %s", (self.current_guild_id,))
                self.db_manager.execute_update("DELETE FROM guild_bank WHERE guild_id = %s", (self.current_guild_id,))
                self.db_manager.execute_update("DELETE FROM guild_tributes WHERE guild_id = %s", (self.current_guild_id,))
                
                # Delete main guild record
                if self.db_manager.execute_update("DELETE FROM guilds WHERE id = %s", (self.current_guild_id,)):
                    messagebox.showinfo("Success", "Guild deleted successfully")
                    self.current_guild_id = None
                    self.load_guilds()
                    self.clear_guild_form()
                else:
                    messagebox.showerror("Error", "Failed to delete guild")
                    
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to delete guild: {e}")
    
    def clear_guild_form(self):
        """Clear the guild form"""
        self.guild_id_var.set("")
        self.guild_name_var.set("")
        self.guild_leader_var.set("")
        self.guild_minstatus_var.set("")
        self.guild_tribute_var.set("")
        self.guild_favor_var.set("")
        self.guild_motd_text.delete(1.0, tk.END)
        self.guild_motd_setter_var.set("")
        self.guild_channel_var.set("")
        self.guild_url_var.set("")
        
        # Clear all treeviews
        for tree in [self.ranks_tree, self.relations_tree, self.permissions_tree, self.members_tree, self.bank_tree]:
            for item in tree.get_children():
                tree.delete(item)
