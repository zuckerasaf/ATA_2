"""
Floating window for displaying event data.
"""

import tkinter as tk
from tkinter import ttk
from src.utils.config import Config

class EventWindow(tk.Tk):
    def __init__(self, test_name=None):
        super().__init__()
        
        # Get configuration
        config = Config()
        
        # Configure window
        base_title = config.get_Event_Monitor_window_title()
        self.title(f"{base_title} - {test_name}" if test_name else base_title)
        self.attributes('-alpha', config.get_Event_Monitor_window_opacity())  # Set transparency
        self.attributes('-topmost', True)  # Always on top
        
        # Set window size and position
        width, height = config.get_Event_Monitor_window_size()
        x, y = config.get_Event_Monitor_window_position()
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        # Create frame
        self.frame = ttk.Frame(self)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # Create label for event data
        self.event_label = ttk.Label(
            self.frame,
            text="Waiting for events...",
            font=('Arial', 10)
        )
        self.event_label.pack(fill=tk.BOTH, expand=True)
        
        # Make window draggable
        self.bind('<Button-1>', self.start_move)
        self.bind('<B1-Motion>', self.on_move)
        
        # Store initial position for dragging
        self.x = 0
        self.y = 0
        
    def start_move(self, event):
        """Start window dragging."""
        self.x = event.x
        self.y = event.y
        
    def on_move(self, event):
        """Handle window dragging."""
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry(f"+{x}+{y}")
        
    def update_event(self, event):
        """Update the displayed event data."""
        text = f"Event #{event.counter} | Position: {event.position} | Type: {event.event_type} | Action: {event.action} | Time: {event.time}ms"
        self.event_label.config(text=text) 