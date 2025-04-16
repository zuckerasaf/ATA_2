"""
Application lifecycle management functions.
"""

import tkinter as tk

def restart_control_panel():
    """Restart the control panel application."""
    from src.gui.control_panel import ControlPanel  # Import here to avoid circular dependency
    root = tk.Tk()
    app = ControlPanel(root)
    root.mainloop() 