"""
Dialog for configuring screenshot event data.
"""

import tkinter as tk
from tkinter import ttk, StringVar, Text, messagebox
from src.utils.config import Config
from PIL import ImageGrab, Image, ImageTk
from pynput import mouse

class ScreenshotDialog ():
    def __init__(self, screenshot_counter):
        self.result = None
        self.config = Config()
        self.screenshot_counter = screenshot_counter
        self.selection_state = "waiting_first_click"
        self.start_x = None
        self.start_y = None
        self.current_rect = None
        self.selection_canvas = None
        self.mouse_listener = None
        
        # Get dialog configuration
        dialog_config = self.config.get('Screenshot_Dialog', {})
        
        # Get Print Screen window configuration
        ps_config = self.config.get('Print_Screen_window', {})
        self.default_ps_width = ps_config.get('PSW_width', 600)
        self.default_ps_height = ps_config.get('PSW_height', 800)
        self.default_ps_x = ps_config.get('PSW_position', {}).get('PSW_x', 10)
        self.default_ps_y = ps_config.get('PSW_position', {}).get('PSW_y', 10)
        
        # Create the dialog window
        self.dialog = tk.Toplevel()
        self.dialog.title(dialog_config.get("title", "Screenshot Configuration"))
        self.dialog.transient()
        self.dialog.grab_set()  # Make the dialog modal
        
        # Set window size and position from config
        width = dialog_config.get('width', 400)
        height = dialog_config.get('height', 500)  # Increased height for new section
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
        self.imagName_text.insert("1.0", f"Pic_{self.screenshot_counter:03d}")
        self.imagName_text.pack(fill="x", pady=(0, 10))
        
        # Print Screen Window Section
        ttk.Label(main_frame, text="Print Screen Window Configuration:").pack(anchor="w", pady=(0, 5))
        ps_frame = ttk.Frame(main_frame)
        ps_frame.pack(fill="x", pady=(0, 10))
        
        # Width
        ttk.Label(ps_frame, text="Width:").grid(row=0, column=0, padx=5, pady=2)
        self.ps_width_var = StringVar(value=str(self.default_ps_width))
        ttk.Entry(ps_frame, textvariable=self.ps_width_var, width=10).grid(row=0, column=1, padx=5, pady=2)
        
        # Height
        ttk.Label(ps_frame, text="Height:").grid(row=0, column=2, padx=5, pady=2)
        self.ps_height_var = StringVar(value=str(self.default_ps_height))
        ttk.Entry(ps_frame, textvariable=self.ps_height_var, width=10).grid(row=0, column=3, padx=5, pady=2)
        
        # X Position
        ttk.Label(ps_frame, text="X Position:").grid(row=1, column=0, padx=5, pady=2)
        self.ps_x_var = StringVar(value=str(self.default_ps_x))
        ttk.Entry(ps_frame, textvariable=self.ps_x_var, width=10).grid(row=1, column=1, padx=5, pady=2)
        
        # Y Position
        ttk.Label(ps_frame, text="Y Position:").grid(row=1, column=2, padx=5, pady=2)
        self.ps_y_var = StringVar(value=str(self.default_ps_y))
        ttk.Entry(ps_frame, textvariable=self.ps_y_var, width=10).grid(row=1, column=3, padx=5, pady=2)
        
        # Buttons frame
        button_frame = ttk.Frame(ps_frame)
        button_frame.grid(row=2, column=0, columnspan=4, pady=5)
        
        # Reset button
        ttk.Button(button_frame, text="Reset to Default", command=self._reset_ps_values).pack(side="left", padx=5)
        
        # Select Area button
        self.select_area_button = ttk.Button(button_frame, text="Select Area", command=self._start_area_selection)
        self.select_area_button.pack(side="left", padx=5)
        
        # Add instruction label
        self.instruction_label = ttk.Label(ps_frame, text="", foreground="blue")
        self.instruction_label.grid(row=3, column=0, columnspan=4, pady=5)
        
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
        self.desc_text.insert("1.0", f"Step {self.screenshot_counter:03d} - do something")
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
        self.accep_text.insert("1.0", f"Step {self.screenshot_counter:03d} - result is good")
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

    def _start_area_selection(self):
        """Start the area selection process."""
        # Initialize selection state
        self.selection_state = "waiting_first_click"
        self.start_x = None
        self.start_y = None
        
        # Update button state and instruction label
        self.select_area_button.configure(style='Accent.TButton')  # Make button appear pressed
        self.instruction_label.config(text="Click once for top-left corner (X,Y)")
        
        # Start mouse listener
        self.mouse_listener = mouse.Listener(on_click=self._on_click)
        self.mouse_listener.start()

    def _on_click(self, x, y, button, pressed):
        """Handle mouse click event."""
        if not pressed:  # Only handle button release
            return
            
        if self.selection_state == "waiting_first_click":
            # First click - set X,Y position
            self.start_x = x
            self.start_y = y
            
            # Update X,Y position fields
            self.ps_x_var.set(str(self.start_x))
            self.ps_y_var.set(str(self.start_y))
            
            # Update instruction label and button state
            self.instruction_label.config(text="Now click for bottom-right corner to set Width and Height")
            self.select_area_button.configure(style='Accent.TButton')  # Keep button pressed
            
            self.selection_state = "waiting_second_click"
            
        elif self.selection_state == "waiting_second_click":
            # Second click - set width and height
            end_x = x
            end_y = y
            
            # Calculate width and height
            width = abs(end_x - self.start_x)
            height = abs(end_y - self.start_y)
            
            # Update width and height fields
            self.ps_width_var.set(str(width))
            self.ps_height_var.set(str(height))
            
            # Clear instruction label and reset button state
            self.instruction_label.config(text="")
            self.select_area_button.configure(style='TButton')  # Return button to normal state
            
            # Stop mouse listener and reset state
            if self.mouse_listener:
                self.mouse_listener.stop()
                self.mouse_listener = None
            self.selection_state = "waiting_first_click"
            self.start_x = None
            self.start_y = None

    def _reset_ps_values(self):
        """Reset Print Screen window values to defaults"""
        self.ps_width_var.set(str(self.default_ps_width))
        self.ps_height_var.set(str(self.default_ps_height))
        self.ps_x_var.set(str(self.default_ps_x))
        self.ps_y_var.set(str(self.default_ps_y))
            
    def _on_ok(self):
        """Handle OK button click."""
        # Get text content
        image_name = self.imagName_text.get("1.0", "end-1c")
        step_desc = self.desc_text.get("1.0", "end-1c")
        step_accep = self.accep_text.get("1.0", "end-1c")
        
        # Get Print Screen window values
        try:
            ps_width = int(self.ps_width_var.get())
            ps_height = int(self.ps_height_var.get())
            ps_x = int(self.ps_x_var.get())
            ps_y = int(self.ps_y_var.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers for Print Screen window dimensions and position.")
            return
        
        self.result = {
            'image_name': image_name,
            'step_desc': step_desc,
            'step_accep': step_accep,
            'priority': self.priority_var.get(),
            'ps_width': ps_width,
            'ps_height': ps_height,
            'ps_x': ps_x,
            'ps_y': ps_y
        }
        print("\nDialog data being saved:")
        print(f"Priority: {self.result['priority']}")
        print(f"Description: {self.result['step_desc']}")
        print(f"Acceptance: {self.result['step_accep']}")
        print(f"Print Screen Window: {ps_width}x{ps_height} at ({ps_x},{ps_y})")
        
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