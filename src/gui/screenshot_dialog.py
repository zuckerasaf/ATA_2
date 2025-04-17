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
        self.imagName_entry.insert(0, "Enter name to the saved image ...")
        self.imagName_entry.bind('<FocusIn>', lambda e: self._on_entry_focus_in(e, "Enter name to the saved image ..."))
        self.imagName_entry.bind('<FocusOut>', lambda e: self._on_entry_focus_out(e, "Enter name to the saved image..."))
        
        # Step Description Section
        ttk.Label(main_frame, text="Step Description:").pack(anchor="w", pady=(0, 5))
        self.desc_var = StringVar()
        self.desc_entry = ttk.Entry(main_frame, textvariable=self.desc_var, width=40)
        self.desc_entry.pack(fill="x", pady=(0, 10))
        self.desc_entry.insert(0, "Enter what this step does...")
        self.desc_entry.bind('<FocusIn>', lambda e: self._on_entry_focus_in(e, "Enter what this step does..."))
        self.desc_entry.bind('<FocusOut>', lambda e: self._on_entry_focus_out(e, "Enter what this step does..."))
        
        # Step Acceptance Section
        ttk.Label(main_frame, text="Step Acceptance:").pack(anchor="w", pady=(0, 5))
        self.accep_var = StringVar()
        self.accep_entry = ttk.Entry(main_frame, textvariable=self.accep_var, width=40)
        self.accep_entry.pack(fill="x", pady=(0, 10))
        self.accep_entry.insert(0, "Enter expected outcome...")
        self.accep_entry.bind('<FocusIn>', lambda e: self._on_entry_focus_in(e, "Enter expected outcome..."))
        self.accep_entry.bind('<FocusOut>', lambda e: self._on_entry_focus_out(e, "Enter expected outcome..."))
        
        # Button Frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(button_frame, text="OK", command=self._on_ok).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Cancel", command=self._on_cancel).pack(side="right", padx=5)
        
        # Set focus to the dialog window itself instead of any entry
        self.dialog.focus_set()
        
        # Configure entry widgets to show placeholder text in gray
        self.imagName_entry.config(foreground='gray')
        self.desc_entry.config(foreground='gray')
        self.accep_entry.config(foreground='gray')
        
        # Prevent closing the window with the X button
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
        # Bind keyboard shortcuts
        self.dialog.bind('<Return>', lambda e: self._on_ok())
        self.dialog.bind('<Escape>', lambda e: self._on_cancel())
        
    def _on_entry_focus_in(self, event, placeholder):
        """Handle focus in event for entry widgets."""
        if event.widget.get() == placeholder:
            event.widget.delete(0, tk.END)
            event.widget.config(foreground='black')  # Change text color to black
            
    def _on_entry_focus_out(self, event, placeholder):
        """Handle focus out event for entry widgets."""
        if not event.widget.get():
            event.widget.insert(0, placeholder)
            event.widget.config(foreground='gray')  # Change text color to gray
            
    def _on_ok(self):
        """Handle OK button click."""
        # Store all parameters in result
        image_name = self.desc_var.get() if self.accep_var.get() != "Enter name to the saved image ..." else "" 
        step_desc = self.desc_var.get() if self.desc_var.get() != "Enter what this step does..." else ""
        step_accep = self.accep_var.get() if self.accep_var.get() != "Enter expected outcome..." else ""
        
        self.result = {
            'image_name':image_name,
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