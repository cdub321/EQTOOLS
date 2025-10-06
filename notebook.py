import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
from datetime import datetime

class NotebookWindow:
    """Pop-out notebook window for user notes"""
    
    def __init__(self, parent):
        self.parent = parent
        self.window = None
        self.db_path = os.path.join(os.path.dirname(__file__), "notes.db")
        
        # Initialize database
        self.init_database()
    
    def init_database(self):
        """Initialize the notes database with proper schema"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if notes table exists and what columns it has
            cursor.execute("PRAGMA table_info(notes)")
            columns = cursor.fetchall()
            
            if not columns:
                # Table doesn't exist, create new one
                cursor.execute('''
                    CREATE TABLE notes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        topic TEXT NOT NULL,
                        title TEXT NOT NULL,
                        content TEXT NOT NULL,
                        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        modified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
            else:
                # Table exists, check if it has old schema
                column_names = [col[1] for col in columns]
                
                if 'name' in column_names and 'type' in column_names and 'topic' not in column_names:
                    # Old schema detected - migrate data
                    print("Migrating notes database to new schema...")
                    
                    # Backup existing data
                    cursor.execute("SELECT id, name, type, content FROM notes")
                    old_data = cursor.fetchall()
                    
                    # Drop old table
                    cursor.execute("DROP TABLE notes")
                    
                    # Create new table
                    cursor.execute('''
                        CREATE TABLE notes (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            topic TEXT NOT NULL,
                            title TEXT NOT NULL,
                            content TEXT NOT NULL,
                            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            modified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                    
                    # Migrate old data
                    for row in old_data:
                        old_id, name, old_type, content = row
                        # Map old 'type' to new 'topic' and 'name' to 'title'
                        topic = old_type if old_type else 'Misc'
                        title = name if name else 'Untitled'
                        cursor.execute('''
                            INSERT INTO notes (topic, title, content)
                            VALUES (?, ?, ?)
                        ''', (topic, title, content))
                    
                    print(f"Migrated {len(old_data)} notes to new schema")
                
                elif 'topic' not in column_names:
                    # Table exists but missing new columns - add them
                    cursor.execute('ALTER TABLE notes ADD COLUMN topic TEXT DEFAULT "Misc"')
                    cursor.execute('ALTER TABLE notes ADD COLUMN title TEXT DEFAULT "Untitled"')
                    cursor.execute('ALTER TABLE notes ADD COLUMN created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
                    cursor.execute('ALTER TABLE notes ADD COLUMN modified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
            
            # Create index for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_notes_topic ON notes(topic)')
            
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"Database initialization error: {e}")
    
    def show(self):
        """Show the notebook window"""
        if self.window is not None and self.window.winfo_exists():
            # Window already exists, just bring it to front
            self.window.lift()
            self.window.focus_force()
            return
        
        # Create new window
        self.window = tk.Toplevel(self.parent)
        self.window.title("Developer Notebook")
        self.window.geometry("800x600")
        self.window.resizable(True, True)
        
        # Set window icon (if available)
        try:
            self.window.iconbitmap(self.parent.winfo_toplevel().iconbitmap())
        except:
            pass
        
        # Configure grid
        self.window.grid_rowconfigure(1, weight=1)
        self.window.grid_columnconfigure(0, weight=1)
        
        # Create UI
        self.create_ui()
        
        # Load notes
        self.load_notes()
        
        # Bind close event
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def create_ui(self):
        """Create the notebook UI"""
        
        # Top frame for controls
        top_frame = ttk.Frame(self.window, padding="5")
        top_frame.grid(row=0, column=0, sticky="ew")
        top_frame.grid_columnconfigure(1, weight=1)
        
        # Topic dropdown
        ttk.Label(top_frame, text="Topic:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        
        self.topic_var = tk.StringVar()
        self.topic_combo = ttk.Combobox(top_frame, textvariable=self.topic_var, width=20)
        self.topic_combo['values'] = (
            'AA Manager',
            'Inventory',
            'Tradeskill',
            'Loot Tables',
            'Factions',
            'Guilds',
            'Database',
            'Development',
            'Misc'
        )
        self.topic_combo.grid(row=0, column=1, sticky="w", padx=(0, 20))
        
        # Title field
        ttk.Label(top_frame, text="Title:").grid(row=0, column=2, sticky="w", padx=(0, 5))
        
        self.title_var = tk.StringVar()
        self.title_entry = ttk.Entry(top_frame, textvariable=self.title_var, width=30)
        self.title_entry.grid(row=0, column=3, sticky="ew", padx=(0, 20))
        
        # Buttons
        button_frame = ttk.Frame(top_frame)
        button_frame.grid(row=0, column=4, sticky="e")
        
        ttk.Button(button_frame, text="Save Note", command=self.save_note).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(button_frame, text="New Note", command=self.new_note).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(button_frame, text="Delete Note", command=self.delete_note).grid(row=0, column=2)
        
        # Main content area with notebook and notes list
        main_frame = ttk.Frame(self.window)
        main_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        
        # Left panel - Notes list
        left_frame = ttk.LabelFrame(main_frame, text="Notes", padding="5")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        left_frame.grid_rowconfigure(1, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)
        
        # Search frame
        search_frame = ttk.Frame(left_frame)
        search_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        search_frame.grid_columnconfigure(0, weight=1)
        
        ttk.Label(search_frame, text="Search:").grid(row=0, column=0, sticky="w")
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.grid(row=1, column=0, sticky="ew")
        self.search_var.trace("w", self.filter_notes)
        
        # Notes listbox
        listbox_frame = ttk.Frame(left_frame)
        listbox_frame.grid(row=1, column=0, sticky="nsew")
        listbox_frame.grid_rowconfigure(0, weight=1)
        listbox_frame.grid_columnconfigure(0, weight=1)
        
        self.notes_listbox = tk.Listbox(listbox_frame, width=30)
        self.notes_listbox.grid(row=0, column=0, sticky="nsew")
        self.notes_listbox.bind('<<ListboxSelect>>', self.on_note_select)
        
        # Scrollbar for listbox
        notes_scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.notes_listbox.yview)
        notes_scrollbar.grid(row=0, column=1, sticky="ns")
        self.notes_listbox.config(yscrollcommand=notes_scrollbar.set)
        
        # Right panel - Note editor
        right_frame = ttk.LabelFrame(main_frame, text="Note Editor", padding="5")
        right_frame.grid(row=0, column=1, sticky="nsew")
        right_frame.grid_rowconfigure(0, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)
        
        # Text editor with scrollbar
        text_frame = ttk.Frame(right_frame)
        text_frame.grid(row=0, column=0, sticky="nsew")
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)
        
        self.text_editor = tk.Text(text_frame, wrap=tk.WORD, undo=True, maxundo=20)
        self.text_editor.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbar for text editor
        text_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.text_editor.yview)
        text_scrollbar.grid(row=0, column=1, sticky="ns")
        self.text_editor.config(yscrollcommand=text_scrollbar.set)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(self.window, textvariable=self.status_var, relief="sunken", anchor="w")
        self.status_bar.grid(row=2, column=0, sticky="ew")
        
        # Initialize variables
        self.current_note_id = None
        self.notes_data = {}
        
        # Bind text editor changes
        self.text_editor.bind('<KeyRelease>', self.on_text_change)
        self.text_editor.bind('<Button-1>', self.on_text_change)
        
        # Set default topic
        self.topic_var.set('Misc')
    
    def load_notes(self):
        """Load all notes from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, topic, title, content, created_date, modified_date
                FROM notes
                ORDER BY modified_date DESC
            ''')
            
            notes = cursor.fetchall()
            conn.close()
            
            # Clear existing data
            self.notes_listbox.delete(0, tk.END)
            self.notes_data = {}
            
            # Load notes
            for note in notes:
                note_id, topic, title, content, created, modified = note
                display_text = f"[{topic}] {title}"
                self.notes_listbox.insert(tk.END, display_text)
                
                index = self.notes_listbox.size() - 1
                self.notes_data[index] = {
                    'id': note_id,
                    'topic': topic,
                    'title': title,
                    'content': content,
                    'created_date': created,
                    'modified_date': modified
                }
            
            self.status_var.set(f"Loaded {len(notes)} notes")
            
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to load notes: {e}")
    
    def filter_notes(self, *args):
        """Filter notes based on search term"""
        search_term = self.search_var.get().lower()
        
        if not search_term:
            self.load_notes()
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, topic, title, content, created_date, modified_date
                FROM notes
                WHERE LOWER(title) LIKE ? OR LOWER(content) LIKE ? OR LOWER(topic) LIKE ?
                ORDER BY modified_date DESC
            ''', (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
            
            notes = cursor.fetchall()
            conn.close()
            
            # Clear existing data
            self.notes_listbox.delete(0, tk.END)
            self.notes_data = {}
            
            # Load filtered notes
            for note in notes:
                note_id, topic, title, content, created, modified = note
                display_text = f"[{topic}] {title}"
                self.notes_listbox.insert(tk.END, display_text)
                
                index = self.notes_listbox.size() - 1
                self.notes_data[index] = {
                    'id': note_id,
                    'topic': topic,
                    'title': title,
                    'content': content,
                    'created_date': created,
                    'modified_date': modified
                }
            
            self.status_var.set(f"Found {len(notes)} matching notes")
            
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to search notes: {e}")
    
    def on_note_select(self, event):
        """Handle note selection"""
        selection = self.notes_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        if index in self.notes_data:
            note = self.notes_data[index]
            
            # Load note into editor
            self.current_note_id = note['id']
            self.topic_var.set(note['topic'])
            self.title_var.set(note['title'])
            
            # Load content
            self.text_editor.delete(1.0, tk.END)
            self.text_editor.insert(1.0, note['content'])
            
            # Update status
            created = note['created_date']
            modified = note['modified_date']
            self.status_var.set(f"Note: {note['title']} | Created: {created} | Modified: {modified}")
    
    def on_text_change(self, event=None):
        """Handle text editor changes"""
        if self.current_note_id:
            self.status_var.set(f"Note modified (not saved)")
    
    def save_note(self):
        """Save current note to database"""
        topic = self.topic_var.get().strip()
        title = self.title_var.get().strip()
        content = self.text_editor.get(1.0, tk.END).strip()
        
        if not topic or not title:
            messagebox.showwarning("Missing Information", "Please provide both a topic and title for the note.")
            return
        
        if not content:
            messagebox.showwarning("Empty Note", "Please add some content to the note.")
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if self.current_note_id:
                # Update existing note
                cursor.execute('''
                    UPDATE notes 
                    SET topic = ?, title = ?, content = ?, modified_date = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (topic, title, content, self.current_note_id))
                action = "updated"
            else:
                # Create new note
                cursor.execute('''
                    INSERT INTO notes (topic, title, content)
                    VALUES (?, ?, ?)
                ''', (topic, title, content))
                self.current_note_id = cursor.lastrowid
                action = "saved"
            
            conn.commit()
            conn.close()
            
            # Refresh notes list
            self.load_notes()
            
            self.status_var.set(f"Note '{title}' {action} successfully")
            
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to save note: {e}")
    
    def new_note(self):
        """Create a new note"""
        # Clear current note
        self.current_note_id = None
        self.topic_var.set('Misc')
        self.title_var.set('')
        self.text_editor.delete(1.0, tk.END)
        
        # Focus on title entry
        self.title_entry.focus_set()
        
        self.status_var.set("New note - ready to edit")
    
    def delete_note(self):
        """Delete the current note"""
        if not self.current_note_id:
            messagebox.showwarning("No Note Selected", "Please select a note to delete.")
            return
        
        title = self.title_var.get()
        
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the note '{title}'?"):
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM notes WHERE id = ?', (self.current_note_id,))
                conn.commit()
                conn.close()
                
                # Clear editor and refresh list
                self.new_note()
                self.load_notes()
                
                self.status_var.set(f"Note '{title}' deleted successfully")
                
            except sqlite3.Error as e:
                messagebox.showerror("Database Error", f"Failed to delete note: {e}")
    
    def on_close(self):
        """Handle window closing"""
        # Check if there are unsaved changes
        if self.current_note_id and "not saved" in self.status_var.get():
            if messagebox.askyesno("Unsaved Changes", "You have unsaved changes. Do you want to save before closing?"):
                self.save_note()
        
        self.window.destroy()
        self.window = None

class NotebookManager:
    """Manager class for the notebook functionality"""
    
    def __init__(self):
        self.notebook_window = None
    
    def show_notebook(self, parent):
        """Show the notebook window"""
        if self.notebook_window is None:
            self.notebook_window = NotebookWindow(parent)
        
        self.notebook_window.show()
