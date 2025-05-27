"""
Floating window for displaying event data.

This module provides a floating window to display event data during test execution.
It includes an EventWindow class that updates the displayed event information and handles window dragging.

Classes
-------
EventWindow
    A class that creates a floating window to display event data.
"""

import tkinter as tk
from tkinter import ttk
from src.utils.config import Config
from src.utils.process_utils import terminate_running_instance, close_existing_mouse_threads


class EventWindow(tk.Tk):
    """
    A class that creates a floating window to display event data.

    This class initializes a Tkinter window that displays event data and allows for window dragging.
    It updates the displayed event information and handles window closing.

    Attributes
    ----------
    frame : ttk.Frame
        The main frame of the window.
    event_label : ttk.Label
        The label that displays the event data.
    x : int
        The initial x-coordinate for window dragging.
    y : int
        The initial y-coordinate for window dragging.

    Methods
    -------
    start_move(event)
        Start window dragging.
    on_move(event)
        Handle window dragging.
    update_event(event)
        Update the displayed event data.
    on_closing()
        Handle window closing.
    """

    def __init__(self, test_name=None):
        """
        Initialize the EventWindow with the given test name.

        Parameters
        ----------
        test_name : str, optional
            The name of the test being executed.
        """
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
        
        # Set up window close handler
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def start_move(self, event):
        """
        Start window dragging.

        Parameters
        ----------
        event : tk.Event
            The event that triggered the start of dragging.
        """
        self.x = event.x
        self.y = event.y
        
    def on_move(self, event):
        """
        Handle window dragging.

        Parameters
        ----------
        event : tk.Event
            The event that triggered the dragging.
        """
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry(f"+{x}+{y}")
        
    def update_event(self, event):
        """
        Update the displayed event data.

        Parameters
        ----------
        event : Event
            The event data to display.
        """
        text = f"Event #{event.counter} | Position: {event.position} | Type: {event.event_type} | Action: {event.action} | Time: {event.time}ms"
        self.event_label.config(text=text)
        
    def on_closing(self):
        """
        Handle window closing.

        This function closes any existing mouse listener threads, terminates the running instance,
        and destroys the window.
        """
        try:
            # Close any existing mouse listener threads
            close_existing_mouse_threads()
            
            # Terminate running instance using process_utils
            terminate_running_instance("cursor_listener.lock")
            
            # Destroy the window
            self.quit()  # Stop the mainloop
            self.destroy()  # Destroy the window
            
        except Exception as e:
            print(f"Error during window closing: {e}")
            self.quit()
            self.destroy() 