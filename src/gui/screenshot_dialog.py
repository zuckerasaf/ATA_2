"""
Dialog for configuring screenshot event data.
"""

import tkinter as tk
from tkinter import ttk, StringVar
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
        height = dialog_config.get('height', 300)
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
        
                # Step Description Section
        ttk.Label(main_frame, text="image name:").pack(anchor="w", pady=(0, 5))
        self.imagName_var = StringVar()
        self.imagName_entry = ttk.Entry(main_frame, textvariable=self.imagName_var, width=40)
        self.imagName_entry.pack(fill="x", pady=(0, 10))
        
        # Step Description Section
        ttk.Label(main_frame, text="Step Description:").pack(anchor="w", pady=(0, 5))
        self.desc_var = StringVar()
        self.desc_entry = ttk.Entry(main_frame, textvariable=self.desc_var, width=40)
        self.desc_entry.pack(fill="x", pady=(0, 10))
        
        # Step Acceptance Section
        ttk.Label(main_frame, text="Step Acceptance:").pack(anchor="w", pady=(0, 5))
        self.accep_var = StringVar()
        self.accep_entry = ttk.Entry(main_frame, textvariable=self.accep_var, width=40)
        self.accep_entry.pack(fill="x", pady=(0, 10))
        
        # Button Frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel_clicked).pack(side="right", padx=5)
        
        # Set focus on the description entry
        self.desc_entry.focus_set()
        
        # Prevent closing the window with the X button
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel_clicked)
        
        # Bind Enter key to OK button
        self.dialog.bind('<Return>', lambda e: self.ok_clicked())
        # Bind Escape key to Cancel button
        self.dialog.bind('<Escape>', lambda e: self.cancel_clicked())
        
    def ok_clicked(self):
        """Handle OK button click."""
        # Store all parameters in result
        self.result = {
            'image_name':self.imagName_var.get().strip(),
            'priority': self.priority_var.get(),
            'step_desc': self.desc_entry.get().strip(),  # Get directly from entry widget
            'step_accep': self.accep_entry.get().strip()  # Get directly from entry widget
        }
        print("\nDialog data being saved:")
        print(f"Priority: {self.result['priority']}")
        print(f"Description: {self.result['step_desc']}")
        print(f"Acceptance: {self.result['step_accep']}")
        
        # Release grab and destroy window
        self.dialog.grab_release()
        self.dialog.destroy()
        
    def cancel_clicked(self):
        """Handle Cancel button click."""
        print("\nDialog cancelled")
        self.result = None
        # Release grab and destroy window
        self.dialog.grab_release()
        self.dialog.destroy() 