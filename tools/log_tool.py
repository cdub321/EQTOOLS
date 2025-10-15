import tkinter as tk
from tkinter import ttk, messagebox
import os
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

# Add parent directory to path for imports if needed
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


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


@dataclass
class LogEntry:
    timestamp: str
    channel: str
    speaker: str
    message: str
    raw_line: str
    coordinates: Optional[Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]]


class LogManagerTool(_TreeviewScrollMixin):
    """Log Manager Tool - load EQ client logs and group messages by keyword."""

    LOG_LINE_RE = re.compile(r"^\[(?P<timestamp>.*?)\]\s+(?P<content>.*)$")
    QUOTED_MESSAGE_RE = re.compile(r"^(?P<prefix>[^']*)'(?P<message>.*)'$")
    LOCATION_RE = re.compile(
        r"Your Location is\s+(-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)(?:,\s*(-?\d+(?:\.\d+)?))?",
        re.IGNORECASE,
    )
    LOCATION_FOR_RE = re.compile(
        r"Location for .*?\|\s*XYZ:\s*(-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)(?:\s*Heading:\s*(-?\d+(?:\.\d+)?))?",
        re.IGNORECASE,
    )

    def __init__(self, parent_frame, db_manager=None):
        self.parent = parent_frame
        self.db_manager = db_manager

        self.parent.grid_rowconfigure(0, weight=1)
        self.parent.grid_columnconfigure(0, weight=1)

        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.grid(row=0, column=0, sticky="nsew")

        # State
        self.keyword_entries: Dict[str, List[LogEntry]] = defaultdict(list)
        self.log_directory: str = ""
        self.logs_path: str = ""
        self.log_files: List[str] = []
        self.log_file_var = tk.StringVar()
        self.loaded_file_var = tk.StringVar()
        self.keyword_filter_var = tk.StringVar()
        self.entry_filter_var = tk.StringVar()
        self.current_keyword: Optional[str] = None
        self.selected_keyword: Optional[str] = None
        self.keyword_tree_ids: Dict[str, str] = {}
        self.entry_item_map: Dict[str, LogEntry] = {}

        # Build UI
        self.create_ui()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------
    def create_ui(self):
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.create_controls()
        self.create_content_area()

    def create_controls(self):
        control_frame = ttk.LabelFrame(self.main_frame, text="Log File", padding="5")
        control_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 2))
        control_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(control_frame, text="Log File:").grid(row=0, column=0, padx=(0, 5), sticky="w")
        self.log_file_combo = ttk.Combobox(
            control_frame,
            textvariable=self.log_file_var,
            state="readonly",
            values=[]
        )
        self.log_file_combo.grid(row=0, column=1, sticky="ew")
        self.log_file_combo.bind("<<ComboboxSelected>>", self.on_log_selected)

        ttk.Button(control_frame, text="Reload", command=self.reload_log_list, width=10).grid(
            row=0, column=2, padx=(5, 0)
        )
        self.load_button = ttk.Button(control_frame, text="Load", command=self.load_selected_file, width=8)
        self.load_button.grid(row=0, column=3, padx=(5, 0))

        ttk.Label(control_frame, text="Selected Path:").grid(row=1, column=0, sticky="w", pady=(5, 0))
        file_entry = ttk.Entry(control_frame, textvariable=self.loaded_file_var, state="readonly")
        file_entry.grid(row=1, column=1, sticky="ew", pady=(5, 0))

        ttk.Label(control_frame, text="Keyword Filter:").grid(row=2, column=0, sticky="w", pady=(5, 0))
        keyword_filter_entry = ttk.Entry(control_frame, textvariable=self.keyword_filter_var)
        keyword_filter_entry.grid(row=2, column=1, sticky="ew", pady=(5, 0))
        self.keyword_filter_var.trace_add("write", lambda *args: self.refresh_keyword_tree())

    def create_content_area(self):
        content_frame = ttk.Frame(self.main_frame)
        content_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=0)
        content_frame.grid_columnconfigure(1, weight=1)

        # Left: keyword list
        keyword_frame = ttk.LabelFrame(content_frame, text="Keywords", padding="5")
        keyword_frame.grid(row=0, column=0, sticky="ns", padx=(0, 5))
        keyword_frame.grid_rowconfigure(0, weight=1)
        keyword_frame.grid_columnconfigure(0, weight=1)

        self.keyword_tree = ttk.Treeview(
            keyword_frame,
            columns=("keyword", "count"),
            show="headings",
            selectmode="browse",
            height=18,
        )
        self._make_treeview_invisible_scroll(self.keyword_tree)
        self.keyword_tree.heading("keyword", text="Keyword")
        self.keyword_tree.heading("count", text="Count")
        self.keyword_tree.column("keyword", width=150, anchor="w")
        self.keyword_tree.column("count", width=60, anchor="center")
        self.keyword_tree.grid(row=0, column=0, sticky="nsew")

        self.keyword_tree.bind("<<TreeviewSelect>>", self.on_keyword_selected)

        # Right: entries for selected keyword
        entries_frame = ttk.LabelFrame(content_frame, text="Entries", padding="5")
        entries_frame.grid(row=0, column=1, sticky="nsew")
        entries_frame.grid_rowconfigure(2, weight=1)
        entries_frame.grid_columnconfigure(0, weight=1)

        filter_row = ttk.Frame(entries_frame)
        filter_row.grid(row=0, column=0, sticky="ew")
        filter_row.grid_columnconfigure(1, weight=1)

        ttk.Label(filter_row, text="Entry Filter:").grid(row=0, column=0, sticky="w")
        entry_filter_entry = ttk.Entry(filter_row, textvariable=self.entry_filter_var)
        entry_filter_entry.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        self.entry_filter_var.trace_add("write", lambda *args: self.refresh_entry_tree())

        button_row = ttk.Frame(entries_frame)
        button_row.grid(row=1, column=0, sticky="ew", pady=(5, 5))

        ttk.Button(button_row, text="Copy Message", command=self.copy_message, width=14).grid(
            row=0, column=0, padx=(0, 5)
        )
        self.copy_coords_btn = ttk.Button(
            button_row, text="Copy X Y Z H", command=self.copy_coordinates, width=16, state="disabled"
        )
        self.copy_coords_btn.grid(row=0, column=1, padx=(0, 5))
        self.copy_coords_commas_btn = ttk.Button(
            button_row,
            text="Copy X, Y, Z, H",
            command=self.copy_coordinates_with_commas,
            width=18,
            state="disabled",
        )
        self.copy_coords_commas_btn.grid(row=0, column=2, padx=(0, 5))
        ttk.Button(button_row, text="Refresh", command=self.load_selected_file, width=10).grid(row=0, column=3)

        self.entry_tree = ttk.Treeview(
            entries_frame,
            columns=("timestamp", "channel", "speaker", "message"),
            show="headings",
            selectmode="browse",
        )
        self._make_treeview_invisible_scroll(self.entry_tree)
        self.entry_tree.heading("timestamp", text="Timestamp")
        self.entry_tree.heading("channel", text="Channel")
        self.entry_tree.heading("speaker", text="Speaker")
        self.entry_tree.heading("message", text="Message")
        self.entry_tree.column("timestamp", width=155, anchor="w")
        self.entry_tree.column("channel", width=150, anchor="w")
        self.entry_tree.column("speaker", width=150, anchor="w")
        self.entry_tree.column("message", width=600, anchor="w")
        self.entry_tree.grid(row=2, column=0, sticky="nsew")

        self.entry_tree.bind("<<TreeviewSelect>>", self.on_entry_selected)

    # ------------------------------------------------------------------
    # File handling
    # ------------------------------------------------------------------
    def set_client_directory(self, directory: str):
        self.log_directory = directory.strip() if directory else ""
        self.reload_log_list()

    def reload_log_list(self):
        self.logs_path = self._resolve_logs_path()

        if self.logs_path and os.path.isdir(self.logs_path):
            files = [
                f for f in os.listdir(self.logs_path)
                if os.path.isfile(os.path.join(self.logs_path, f))
                and f.lower().startswith("eqlog_")
                and f.lower().endswith(".txt")
            ]
            files.sort(key=lambda name: name.lower())
            self.log_files = files
            self.log_file_combo.configure(values=self.log_files)
            if files:
                if self.log_file_var.get() not in self.log_files:
                    self.log_file_var.set(self.log_files[0])
                    self.on_log_selected()
            else:
                self.log_file_var.set("")
                self.loaded_file_var.set("")
        else:
            self.log_files = []
            self.log_file_combo.configure(values=[])
            self.log_file_var.set("")
            self.loaded_file_var.set("")

        self.update_load_state()

    def on_log_selected(self, event=None):
        selected = self.log_file_var.get()
        if self.logs_path and selected:
            self.loaded_file_var.set(os.path.join(self.logs_path, selected))
        else:
            self.loaded_file_var.set("")
        self.update_load_state()

    def update_load_state(self):
        if self.load_button:
            state = "normal" if self.loaded_file_var.get() else "disabled"
            self.load_button.configure(state=state)

    def load_selected_file(self):
        filepath = self.loaded_file_var.get()
        if not filepath:
            messagebox.showinfo("No File", "Please select a log file to load.", parent=self.main_frame)
            return
        if not os.path.exists(filepath):
            messagebox.showerror("File Missing", "The selected log file no longer exists.", parent=self.main_frame)
            return

        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as log_file:
                lines = log_file.readlines()
        except OSError as err:
            messagebox.showerror("Read Error", f"Could not read log file:\n{err}", parent=self.main_frame)
            return

        self.parse_log_lines(lines)
        self.refresh_keyword_tree()
        self.entry_tree.delete(*self.entry_tree.get_children())
        self.selected_keyword = None
        self.set_coordinate_buttons_state(False)

    # ------------------------------------------------------------------
    # Parsing and data preparation
    # ------------------------------------------------------------------
    def parse_log_lines(self, lines: List[str]):
        self.keyword_entries.clear()
        self.entry_item_map.clear()
        self.current_keyword = None

        last_keyword_for_loc: Optional[str] = None

        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue

            log_match = self.LOG_LINE_RE.match(line)
            if not log_match:
                continue

            timestamp = log_match.group("timestamp")
            content = log_match.group("content")

            message_match = self.QUOTED_MESSAGE_RE.match(content)
            if message_match:
                prefix = message_match.group("prefix").strip()
                prefix = prefix[:-1].strip() if prefix.endswith(",") else prefix
                message = message_match.group("message").strip()
                if not message:
                    continue

                keyword = message.split()[0].lower()
                last_keyword_for_loc = keyword

                channel, speaker = self.parse_prefix(prefix)
                coordinates = self.extract_coordinates(raw_line)
                entry = LogEntry(
                    timestamp=timestamp,
                    channel=channel,
                    speaker=speaker,
                    message=message,
                    raw_line=line,
                    coordinates=coordinates,
                )
                self.keyword_entries[keyword].append(entry)
                continue

            # Handle /loc style output if we have a last keyword to attach it to
            system_message = content.lower()
            if last_keyword_for_loc:
                loc_match = self.LOCATION_RE.search(content)
                loc_for_match = self.LOCATION_FOR_RE.search(content)
                if loc_match:
                    x_val, y_val, z_val, heading_val = loc_match.groups()
                    coordinates = (x_val, y_val, z_val, heading_val)
                elif loc_for_match:
                    x_val, y_val, z_val, heading_val = loc_for_match.groups()
                    coordinates = (x_val, y_val, z_val, heading_val)
                else:
                    coordinates = None

                if not coordinates:
                    if "location" in system_message or "heading" in system_message or "xyz" in system_message:
                        coordinates = self.extract_coordinates(content)

                if coordinates:
                    entry = LogEntry(
                        timestamp=timestamp,
                        channel="System",
                        speaker="",
                        message=content,
                        raw_line=line,
                        coordinates=coordinates,
                    )
                self.keyword_entries[last_keyword_for_loc].append(entry)

    def _resolve_logs_path(self) -> str:
        if not self.log_directory:
            return ""

        client_dir = self.log_directory
        if os.path.isdir(client_dir) and self._contains_log_files(client_dir):
            return client_dir

        # Common variations of logs directory
        candidate_names = ["logs", "Logs", "LOGS"]
        for name in candidate_names:
            candidate = os.path.join(client_dir, name)
            if os.path.isdir(candidate) and self._contains_log_files(candidate):
                return candidate

        # Search subdirectories case-insensitively
        try:
            for entry in os.listdir(client_dir):
                full_path = os.path.join(client_dir, entry)
                if os.path.isdir(full_path) and entry.lower() == "logs" and self._contains_log_files(full_path):
                    return full_path
        except OSError:
            return ""

        return ""

    def _contains_log_files(self, directory: str) -> bool:
        try:
            for name in os.listdir(directory):
                if not os.path.isfile(os.path.join(directory, name)):
                    continue
                lower_name = name.lower()
                if lower_name.startswith("eqlog_") and lower_name.endswith(".txt"):
                    return True
            return False
        except OSError:
            return False

    def parse_prefix(self, prefix: str) -> Tuple[str, str]:
        if not prefix:
            return "", ""

        parts = prefix.split(None, 1)
        speaker = parts[0] if parts else ""
        channel = prefix
        return channel, speaker

    def extract_coordinates(
        self, text: str
    ) -> Optional[Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]]:
        numbers = re.findall(r"-?\d+(?:\.\d+)?", text)
        if len(numbers) >= 3:
            x_val = numbers[0]
            y_val = numbers[1]
            z_val = numbers[2]
            h_val = numbers[3] if len(numbers) >= 4 else None
            return (x_val, y_val, z_val, h_val)
        return None

    # ------------------------------------------------------------------
    # Tree refresh helpers
    # ------------------------------------------------------------------
    def refresh_keyword_tree(self):
        self.keyword_tree.delete(*self.keyword_tree.get_children())
        self.keyword_tree_ids.clear()

        filter_text = self.keyword_filter_var.get().strip().lower()
        for keyword in sorted(self.keyword_entries.keys()):
            if filter_text and filter_text not in keyword:
                continue
            count = len(self.keyword_entries[keyword])
            tree_id = self.keyword_tree.insert("", "end", values=(keyword, count))
            self.keyword_tree_ids[keyword] = tree_id

    def refresh_entry_tree(self):
        self.entry_tree.delete(*self.entry_tree.get_children())
        self.entry_item_map.clear()
        self.set_coordinate_buttons_state(False)

        if not self.selected_keyword:
            return

        entries = self.keyword_entries.get(self.selected_keyword, [])
        filter_text = self.entry_filter_var.get().strip().lower()

        for entry in entries:
            combined_text = " ".join(
                [
                    entry.timestamp.lower(),
                    entry.channel.lower(),
                    entry.speaker.lower(),
                    entry.message.lower(),
                ]
            )
            if filter_text and filter_text not in combined_text:
                continue

            tree_id = self.entry_tree.insert(
                "",
                "end",
                values=(entry.timestamp, entry.channel, entry.speaker, entry.message),
            )
            self.entry_item_map[tree_id] = entry

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------
    def on_keyword_selected(self, event=None):
        selected = self.keyword_tree.selection()
        if not selected:
            self.selected_keyword = None
            self.refresh_entry_tree()
            return

        tree_id = selected[0]
        values = self.keyword_tree.item(tree_id, "values")
        self.selected_keyword = values[0]
        self.refresh_entry_tree()

    def on_entry_selected(self, event=None):
        selected = self.entry_tree.selection()
        if not selected:
            self.set_coordinate_buttons_state(False)
            return

        entry = self.entry_item_map.get(selected[0])
        if entry and entry.coordinates:
            self.set_coordinate_buttons_state(True)
        else:
            self.set_coordinate_buttons_state(False)

    def set_coordinate_buttons_state(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        for button in (getattr(self, "copy_coords_btn", None), getattr(self, "copy_coords_commas_btn", None)):
            if button is not None:
                button.configure(state=state)

    # ------------------------------------------------------------------
    # Clipboard helpers
    # ------------------------------------------------------------------
    def copy_message(self):
        selected = self.entry_tree.selection()
        if not selected:
            messagebox.showinfo("No Entry", "Select an entry to copy its text.", parent=self.main_frame)
            return

        entry = self.entry_item_map.get(selected[0])
        if not entry:
            return

        toplevel = self.main_frame.winfo_toplevel()
        toplevel.clipboard_clear()
        toplevel.clipboard_append(entry.message)
        toplevel.update_idletasks()

    def copy_coordinates(self):
        selected = self.entry_tree.selection()
        if not selected:
            return

        entry = self.entry_item_map.get(selected[0])
        if not entry or not entry.coordinates:
            messagebox.showinfo("No Coordinates", "The selected entry does not contain coordinates.", parent=self.main_frame)
            return

        x_val, y_val, z_val, h_val = entry.coordinates
        values = [val for val in (x_val, y_val, z_val, h_val) if val is not None]
        coord_string = " ".join(values)

        toplevel = self.main_frame.winfo_toplevel()
        toplevel.clipboard_clear()
        toplevel.clipboard_append(coord_string)
        toplevel.update_idletasks()

    def copy_coordinates_with_commas(self):
        selected = self.entry_tree.selection()
        if not selected:
            return

        entry = self.entry_item_map.get(selected[0])
        if not entry or not entry.coordinates:
            messagebox.showinfo("No Coordinates", "The selected entry does not contain coordinates.", parent=self.main_frame)
            return

        x_val, y_val, z_val, h_val = entry.coordinates
        values = [val for val in (x_val, y_val, z_val, h_val) if val is not None]
        coord_string = ", ".join(values)

        toplevel = self.main_frame.winfo_toplevel()
        toplevel.clipboard_clear()
        toplevel.clipboard_append(coord_string)
        toplevel.update_idletasks()
