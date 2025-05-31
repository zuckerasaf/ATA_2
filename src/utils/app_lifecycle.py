"""
Application lifecycle management functions.
"""

import tkinter as tk

def restart_control_panel():
    """
    Restart (or bring to front) the control panel application.
    
    This function either brings an existing control panel to front or creates a new one
    if none exists. It includes error handling for window management operations.
    """
    from src.gui.control_panel import ControlPanel  # Import here to avoid circular dependency
    
    try:
        if ControlPanel._instance is not None:
            try:
                ControlPanel.bring_to_front_and_refresh()
            except Exception as e:
                print(f"Error bringing control panel to front: {e}")
                # If bringing to front fails, create a new instance
                root = tk.Tk()
                app = ControlPanel(root)
                root.mainloop()
        else:
            root = tk.Tk()
            app = ControlPanel(root)
            root.mainloop()
    except Exception as e:
        print(f"Error restarting control panel: {e}")
        # Last resort: try to create a new instance
        try:
            root = tk.Tk()
            app = ControlPanel(root)
            root.mainloop()
        except Exception as e:
            print(f"Fatal error creating control panel: {e}") 