"""
Application lifecycle management functions.
"""

import tkinter as tk

def restart_control_panel():
    """Restart (or bring to front) the control panel application."""
    from src.gui.control_panel import ControlPanel  # Import here to avoid circular dependency
    if ControlPanel._instance is not None:
        ControlPanel.bring_to_front_and_refresh()
    else:
        root = tk.Tk()
        app = ControlPanel(root)
        root.mainloop() 