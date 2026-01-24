import tkinter as tk
from tkinter import ttk

def set_dark_theme(root):
    style = ttk.Style(root)
    
    # Configure colors
    bg_color = "#2d2d2d"  # Dark background
    fg_color = "#ffffff"  # White foreground
    accent_color = "#3c3c3c"  # Slightly lighter background for buttons, etc.
    text_bg_color = "#3c3c3c"  # Background for text widgets
    text_fg_color = "#ffffff"  # Text color for text widgets
    insert_color = "#ffffff"  # Cursor color for text widgets
    label_frame_bg = "#2d2d2d"  # Background for LabelFrames
    label_frame_fg = "#ffffff"  # Foreground for LabelFrames
    
    # Apply the dark theme to root
    root.configure(bg='black')
    
    # Create the dark theme
    style.theme_create("dark", parent="alt", settings={
        "TFrame": {"configure": {"background": bg_color}},
        "TLabel": {"configure": {"background": bg_color, "foreground": fg_color}},
        "TButton": {
            "configure": {
                "background": accent_color,
                "foreground": fg_color,
                "borderwidth": 1,
                "relief": "raised",
            },
            "map": {
                "background": [("active", "#4c4c4c")],
                "foreground": [("active", fg_color)],
            },
        },
        "TEntry": {
            "configure": {
                "fieldbackground": accent_color,
                "foreground": fg_color,
                "insertcolor": fg_color,
            },
        },
        "TCombobox": {
            "configure": {
                "fieldbackground": accent_color,
                "foreground": fg_color,
                "background": bg_color,
            },
        },
        "TNotebook": {
            "configure": {
                "background": bg_color,
                "foreground": fg_color,
            },
        },
        "TNotebook.Tab": {
            "configure": {
                "background": accent_color,
                "foreground": fg_color,
                "padding": [10, 5],
            },
            "map": {
                "background": [("selected", bg_color)],
                "foreground": [("selected", fg_color)],
            },
        },
        "TLabelframe": {
            "configure": {
                "background": label_frame_bg,
                "foreground": label_frame_fg,
                "borderwidth": 1,
                "relief": "sunken",
            },
        },
        "TLabelframe.Label": {
            "configure": {
                "background": label_frame_bg,
                "foreground": label_frame_fg,
                "font": ("Arial", 10, "bold"),
            },
        },
    })
    
    # Set the custom dark theme
    style.theme_use("dark")
    
    # Configure Treeview
    style.configure("Treeview", 
                   background="#d3d3d3", 
                   fieldbackground="#d3d3d3", 
                   foreground="black")
    
    # Make the column separators more visible
    style.configure("Treeview.Heading",
                   background="#808080",
                   foreground="white",
                   font=("Arial", 10),
                   borderwidth=1,
                   relief="raised",
                   padding=(2, 2, 2, 2))
    
    # Configure heading separator
    style.configure("Treeview.Heading.Separator", background="black")
    
    # Change selected row color
    style.map("Treeview", background=[("selected", "#a6a6a6")])
    
    # Add specific style for when the user is resizing columns
    style.map("Treeview.Heading",
             relief=[("active", "sunken")])
    
    # Fix for empty Treeview background
    style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])
    
    # Configure Text widget appearance
    def configure_text_widget(text_widget):
        text_widget.configure(
            background=text_bg_color,
            foreground=text_fg_color,
            insertbackground=insert_color,
            selectbackground="#4c4c4c",
            selectforeground=text_fg_color,
            font=("Arial", 10),
            relief="sunken",
            borderwidth=1
        )
    
    # Add method to style to configure text widgets
    style.configure_text_widget = configure_text_widget
    
    return style
