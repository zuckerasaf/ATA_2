"""
Dialog for entering test name and starting point.
"""

import tkinter as tk
from tkinter import ttk, StringVar, messagebox
from src.utils.config import Config
from src.utils.general_func import generate_random_word

class TestNameDialog:
    def __init__(self):
        self.result = None
        self.config = Config()
        
        # Get dialog configuration
        dialog_config = self.config.get_Test_Name_Dialog_config()
        
        # Create the dialog window
        self.dialog = tk.Toplevel()
        self.dialog.title(dialog_config["title"])
        self.dialog.grab_set()  # Make the dialog modal
        
        # Set window size and position from config
        self.dialog.geometry(f"{dialog_config['width']}x{dialog_config['height']}+{dialog_config['position']['x']}+{dialog_config['position']['y']}")
        
        # Create main frame with padding
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Test Name Section
        ttk.Label(main_frame, text="Test Name:").pack(anchor="w", pady=(0, 5))
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(main_frame, textvariable=self.name_var, width=40)
        self.name_entry.insert(0, generate_random_word())
        self.name_entry.pack(fill="x", pady=(0, 10))
        
        # Test Purpose Section
        ttk.Label(main_frame, text="Test Purpose:").pack(anchor="w", pady=(0, 5))
        self.purpose_var = tk.StringVar()
        self.purpose_entry = ttk.Entry(main_frame, textvariable=self.purpose_var, width=40)
        self.purpose_entry.insert(0, "the test purpose is " + generate_random_word())
        self.purpose_entry.pack(fill="x", pady=(0, 10))
        
        # Accuracy Level Section
        ttk.Label(main_frame, text="Accuracy Level:").pack(anchor="w", pady=(0, 5))
        self.accuracy_var = tk.IntVar(value=5)
        accuracy_frame = ttk.Frame(main_frame)
        accuracy_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(accuracy_frame, text="Low").pack(side="left")
        accuracy_scale = ttk.Scale(
            accuracy_frame,
            from_=1,
            to=10,
            orient="horizontal",
            variable=self.accuracy_var,
            command=self.update_accuracy_label
        )
        accuracy_scale.pack(side="left", fill="x", expand=True, padx=5)
        ttk.Label(accuracy_frame, text="High").pack(side="left")
        
        self.accuracy_label = ttk.Label(accuracy_frame, text="5")
        self.accuracy_label.pack(side="left", padx=5)
        
        # Starting Point Section
        ttk.Label(main_frame, text="Starting Point:").pack(anchor="w", pady=(0, 5))
        self.starting_point_var = tk.StringVar(value="none")
        starting_points = self.config.get('startingPoint', ["none", "desktop", "point_A", "point_B", "point_C"])
        starting_point_combo = ttk.Combobox(
            main_frame,
            textvariable=self.starting_point_var,
            values=starting_points,
            state="readonly"
        )
        starting_point_combo.pack(fill="x", pady=(0, 10))
        
        # Button Frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(button_frame, text="OK", command=self._on_ok).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Cancel", command=self._on_cancel).pack(side="right", padx=5)
        
        # Set focus on the name entry
        self.name_entry.focus_set()
        
        # Bind keyboard shortcuts
        self.dialog.bind('<Return>', lambda e: self._on_ok())
        self.dialog.bind('<Escape>', lambda e: self._on_cancel())
        
        # Prevent closing the window with the X button
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
    def update_accuracy_label(self, *args):
        """Update the accuracy level label when the slider changes."""
        self.accuracy_label.config(text=str(self.accuracy_var.get()))
    
    def _on_ok(self):
        """Handle OK button click."""
        name = self.name_var.get().strip()
        print(f"Test name entered: '{name}'")  # Debug print
        
        if not name:
            messagebox.showwarning(
                "Invalid Name",
                "Please enter a test name.",
                parent=self.dialog
            )
            return
        
        # Check for invalid characters
        invalid_chars = '<>:"/\\|?*'
        if any(char in name for char in invalid_chars):
            messagebox.showwarning(
                "Invalid Name",
                f"Test name cannot contain any of these characters: {invalid_chars}",
                parent=self.dialog
            )
            return
            
        # Store all parameters in result
        self.result = {
            'name': name,
            'purpose': self.purpose_var.get().strip(),
            'accuracy_level': self.accuracy_var.get(),
            'starting_point': self.starting_point_var.get()
        }
        print(f"Dialog result: {self.result}")  # Debug print
        self.dialog.destroy()
    
    def _on_cancel(self):
        """Handle Cancel button click."""
        self.dialog.destroy()
