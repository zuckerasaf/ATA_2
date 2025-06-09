import tkinter as tk
from tkinter import ttk
from src.utils.config import Config

class CommentDialog:
    """
    A simple dialog for entering or editing a comment (step_desc).
    Shows a text widget with a scrollbar and OK/Cancel buttons.
    Usage:
        dialog = CommentDialog(parent, initial_text="optional")
        dialog.dialog.wait_window()  # Wait for user
        result = dialog.result  # The entered text, or None if cancelled
    """
    def __init__(self, parent=None, initial_text=""):

        self.config = Config()

        # Get comment panel configuration from config file
        panel_config = self.config.get_Comment_Panel_config()
        # Get Print Screen window configuration
        cs_config = self.config.get('Comment_Screen_window', {})
        self.default_cs_width = cs_config.get('CSW_width', 600)
        self.default_cs_height = cs_config.get('CSW_height', 800)
        self.default_cs_x = cs_config.get('CSW_position', {}).get('CSW_x', 10)
        self.default_cs_y = cs_config.get('CSW_position', {}).get('CSW_y', 10)

        




        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(" Comment")
        self.dialog.geometry(f"{self.default_cs_width}x{self.default_cs_height}+{self.default_cs_x}+{self.default_cs_y}")#self.dialog.geometry(f"{panel_config['width']}x{panel_config['height']}+{panel_config['position']['x']}+{panel_config['position']['y']}")
        self.dialog.transient(parent)
        self.dialog.grab_set()


        ttk.Label(self.dialog, text="Enter Comment:").pack(anchor="w", pady=(0, 5))

        # Text widget with scrollbar
        frame = ttk.Frame(self.dialog)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.text = tk.Text(frame, wrap="word", height=6)
        self.text.pack(side="left", fill="both", expand=True)
        self.text.insert("1.0", initial_text)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # OK and Cancel buttons
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(fill="x", pady=(5, 0))
        ok_btn = ttk.Button(btn_frame, text="OK", command=self.on_ok)
        ok_btn.pack(side="left", expand=True, padx=5)
        cancel_btn = ttk.Button(btn_frame, text="Cancel", command=self.on_cancel)
        cancel_btn.pack(side="right", expand=True, padx=5)

        self.dialog.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.text.focus_set()

    def on_ok(self):
        self.result = self.text.get("1.0", "end").strip()
        self.dialog.destroy()

    def on_cancel(self):
        self.result = None
        self.dialog.destroy()
