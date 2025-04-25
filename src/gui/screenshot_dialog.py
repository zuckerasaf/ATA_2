"""
Dialog for configuring screenshot event data.
"""

import tkinter as tk
from tkinter import ttk, StringVar, Text
from src.utils.config import Config

class ScreenshotDialog ():
    def __init__(self):
        self.result = None
        self.config = Config()
        
        # Get dialog configuration
        dialog_config = self.config.get('Screenshot_Dialog', {})
        
        # Create the dialog window
        self.dialog = tk.Toplevel()
        self.dialog.title(dialog_config.get("title", "Screenshot Configuration"))
        self.dialog.transient()
        self.dialog.grab_set()  # Make the dialog modal
        
        # Set window size and position from config
        width = dialog_config.get('width', 400)
        height = dialog_config.get('height', 400)  # Increased height for multi-line text
        x = dialog_config.get('position', {}).get('x', 200)
        y = dialog_config.get('position', {}).get('y', 200)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Make dialog modal
        self.dialog.focus_force()
        self.dialog.grab_set()
        
        # Create main frame with padding
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Priority Section
        ttk.Label(main_frame, text="Priority:").pack(anchor="w", pady=(0, 5))
        self.priority_var = StringVar(value=self.config.get('event', {}).get('priority', 'medium'))
        priority_frame = ttk.Frame(main_frame)
        priority_frame.pack(fill="x", pady=(0, 10))
        
        priorities = ["low", "medium", "high"]
        for priority in priorities:
            ttk.Radiobutton(
                priority_frame,
                text=priority.capitalize(),
                variable=self.priority_var,
                value=priority
            ).pack(side="left", padx=5)
        
        # Image Name Section
        ttk.Label(main_frame, text="Enter name to the saved image ...:").pack(anchor="w", pady=(0, 5))
        self.imagName_text = Text(main_frame, height=1, width=40)
        self.imagName_text.pack(fill="x", pady=(0, 10))
        
        # Step Description Section
        ttk.Label(main_frame, text="Step Description - Enter what this step does...:").pack(anchor="w", pady=(0, 5))
        # Create a frame to hold the text widget and scrollbar
        desc_frame = ttk.Frame(main_frame)
        desc_frame.pack(fill="x", pady=(0, 10))
        
        # Create scrollbar for description
        desc_scrollbar = ttk.Scrollbar(desc_frame)
        desc_scrollbar.pack(side="right", fill="y")
        
        # Create text widget with scrollbar
        self.desc_text = Text(desc_frame, height=4, width=40, yscrollcommand=desc_scrollbar.set)
        self.desc_text.pack(side="left", fill="x", expand=True)
        
        # Configure scrollbar to work with text widget
        desc_scrollbar.config(command=self.desc_text.yview)
        
        # Step Acceptance Section
        ttk.Label(main_frame, text="Step Acceptance - Enter expected outcome...:").pack(anchor="w", pady=(0, 5))
        # Create a frame to hold the text widget and scrollbar
        accep_frame = ttk.Frame(main_frame)
        accep_frame.pack(fill="x", pady=(0, 10))
        
        # Create scrollbar for acceptance
        accep_scrollbar = ttk.Scrollbar(accep_frame)
        accep_scrollbar.pack(side="right", fill="y")
        
        # Create text widget with scrollbar
        self.accep_text = Text(accep_frame, height=4, width=40, yscrollcommand=accep_scrollbar.set)
        self.accep_text.pack(side="left", fill="x", expand=True)
        
        # Configure scrollbar to work with text widget
        accep_scrollbar.config(command=self.accep_text.yview)
        
        # Button Frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(button_frame, text="OK", command=self._on_ok).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Cancel", command=self._on_cancel).pack(side="right", padx=5)
        
        # Set focus to the dialog window itself instead of any entry
        self.dialog.focus_set()
        
        # Prevent closing the window with the X button
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
        # Bind keyboard shortcuts
        #self.dialog.bind('<Return>', lambda e: self._on_ok())
        #self.dialog.bind('<Escape>', lambda e: self._on_cancel())
            
    def _on_ok(self):
        """Handle OK button click."""
        # Get text content
        image_name = self.imagName_text.get("1.0", "end-1c")
        step_desc = self.desc_text.get("1.0", "end-1c")
        step_accep = self.accep_text.get("1.0", "end-1c")
        
        self.result = {
            'image_name': image_name,
            'step_desc': step_desc,
            'step_accep': step_accep,
            'priority': self.priority_var.get()
        }
        print("\nDialog data being saved:")
        print(f"Priority: {self.result['priority']}")
        print(f"Description: {self.result['step_desc']}")
        print(f"Acceptance: {self.result['step_accep']}")
        
        # Release grab and destroy window
        self.dialog.grab_release()
        self.dialog.destroy()
        
    def _on_cancel(self):
        """Handle Cancel button click."""
        print("\nDialog cancelled")
        self.result = None
        # Release grab and destroy window
        self.dialog.grab_release()
        self.dialog.destroy() 