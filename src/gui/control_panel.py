"""
Control Panel UI for test recording and execution.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import shutil

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

from src.tests.recordTest import main as start_recording
from src.tests.runTest import main as start_runing
from src.utils.test import Test
from src.utils.config import Config
from src.gui.test_name_dialog import TestNameDialog
from src.utils.starting_points import go_to_starting_point


class ControlPanel:
    def __init__(self, root):
        self.root = root
        self.config = Config()
        
        # Get control panel configuration
        panel_config = self.config.get_Control_Panel_config()
        
        # Set window title and size
        self.root.title(panel_config["title"])
        self.root.geometry(f"{panel_config['width']}x{panel_config['height']}+{panel_config['position']['x']}+{panel_config['position']['y']}")
        
        # Configure grid weights for resizing
        self.root.grid_rowconfigure(0, weight=1)  # Main content row
        self.root.grid_rowconfigure(1, weight=0)  # Status bar row
        self.root.grid_columnconfigure(0, weight=1)  # Left list
        self.root.grid_columnconfigure(1, weight=0)  # Center buttons
        self.root.grid_columnconfigure(2, weight=1)  # Right list
        
        # Create main frames
        self.create_test_list_frame()
        self.create_control_buttons_frame()
        self.create_result_list_frame()
        self.create_status_bar()
        
        # Initialize data
        self.refresh_test_list()
        self.refresh_result_list()
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def killOldListener(self):
        """Handle window closing event."""
        try:
            # Check for cursor_listener.lock file
            lock_file = "cursor_listener.lock"
            if os.path.exists(lock_file):
                # Try to read the PID from the lock file
                try:
                    with open(lock_file, 'r') as f:
                        pid = int(f.read().strip())
                    # On Windows, we can use taskkill to force terminate the process
                    os.system(f'taskkill /F /PID {pid}')
                    messagebox.showinfo(
                        "Process Cleanup", 
                        "The system detected that it didn't close properly last time. It will be closed properly now."
                    )
                except:
                    pass
                # Remove the lock file
                try:
                    os.remove(lock_file)
                except:
                    pass
            
            # Update status
            self.status_var.set("Terminating all listeners and closing application...")
            self.root.update()
            
            # Give a small delay to ensure status is updated
            self.root.after(500)
            
        except Exception as e:
            print(f"Error during shutdown: {e}")
            # Don't re-raise the exception, just log it
            # This allows the application to continue even if there's an error
            
    def on_closing(self):
        self.killOldListener()
        # Quit the application
        self.root.quit()
            
    def create_test_list_frame(self):
        """Create the left frame containing the list of tests."""
        frame = ttk.LabelFrame(self.root, text="List of Tests")
        frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        # Create listbox with scrollbar
        self.test_listbox = tk.Listbox(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.test_listbox.yview)
        self.test_listbox.configure(yscrollcommand=scrollbar.set)
        
        # Pack listbox and scrollbar
        self.test_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def create_control_buttons_frame(self):
        """Create the center frame containing control buttons."""
        frame = ttk.Frame(self.root)
        frame.grid(row=0, column=1, padx=5, pady=5, sticky="ns")
        
        # Add buttons
        ttk.Button(frame, text="Record", command=self.start_recording).pack(pady=5)
        ttk.Button(frame, text="Run", command=self.run_test).pack(pady=5)
        ttk.Button(frame, text="Close", command=self.on_closing).pack(pady=5)
        
    def create_result_list_frame(self):
        """Create the right frame containing the list of results."""
        frame = ttk.LabelFrame(self.root, text="List of Results")
        frame.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        
        # Create listbox with scrollbar
        self.result_listbox = tk.Listbox(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.result_listbox.yview)
        self.result_listbox.configure(yscrollcommand=scrollbar.set)
        
        # Pack listbox and scrollbar
        self.result_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def create_status_bar(self):
        """Create the status bar at the bottom."""
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        
        frame = ttk.LabelFrame(self.root, text="Status of the Last Run")
        frame.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        
        ttk.Label(frame, textvariable=self.status_var).pack(pady=5)
        
    def _populate_list(self, listbox, directory_path, file_pattern,state):
        """
        Generic function to populate a listbox with files from a directory.
        
        Args:
            listbox: The listbox widget to populate
            directory_path: Path to the directory containing the files
            file_pattern: Lambda function that takes a filename and returns the path to the actual file
                        (e.g., lambda name: os.path.join(directory, name, f"{name}.json"))
        """
        # Clear the listbox
        listbox.delete(0, tk.END)
        
        if os.path.exists(directory_path):
            # Create a list to store file info (name, creation time, and display name)
            file_info = []
            for name in os.listdir(directory_path):
                if state == "test":
                    file_path = file_pattern(name)
                    display_name = name
                else: #state == "result"    
                    # Extract just the test name from the timestamped filename
                    display_name = "Result_"+self._extract_test_name_from_timestamp(name)
                    file_path = os.path.join(directory_path, name, f"{display_name}.json")

                if os.path.exists(file_path):
                    # Get file creation time
                    creation_time = os.path.getctime(file_path)
                    # Format the creation time
                    creation_date = datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d %H:%M:%S')
                    # Store file info
                    file_info.append({
                        'name': name,
                        'creation_time': creation_time,
                        'display_name': f"{display_name} - {creation_date}"
                    })
            
            # Sort by creation time (newest first)
            file_info.sort(key=lambda x: x['creation_time'], reverse=True)
            
            # Add sorted items to listbox
            for item in file_info:
                listbox.insert(tk.END, item['display_name'])
                
    def refresh_test_list(self):
        """Refresh the list of available tests."""
        # Get paths from config
        paths_config = self.config.get('paths', {})
        db_path = paths_config.get('db_path', os.path.join(project_root, "DB"))
        test_path = paths_config.get('test_path', "Test")
        
        # Get list of test files from DB directory
        test_dir = os.path.join(db_path, test_path)
        self._populate_list(
            self.test_listbox,
            test_dir,
            lambda name: os.path.join(test_dir, name, f"{name}.json"),
            "test"
        )
        
    def refresh_result_list(self):
        """Refresh the list of available results."""
        # Get paths from config
        paths_config = self.config.get('paths', {})
        db_path = paths_config.get('db_path', os.path.join(project_root, "DB"))
        result_path = paths_config.get('result_path', "Result")
        
        # Get list of result files from DB directory
        result_dir = os.path.join(db_path, result_path)
        self._populate_list(
            self.result_listbox,
            result_dir,
            lambda name: os.path.join(result_dir, name, f"{name}.json"),
            "result"
        )
        
    def _extract_name_from_display(self, display_text):
        """
        Extract the original name from the display text.
        
        Args:
            display_text: The text shown in the listbox (format: "name - date")
            
        Returns:
            The original name without the date suffix
        """
        return display_text.split(" - ")[0]
        
    def _extract_test_name_from_timestamp(self, filename):
        """
        Extract the test name from a timestamped filename.
        Example: '20250418_162642_test1.json' -> 'test1'
        
        Args:
            filename: The timestamped filename
            
        Returns:
            The test name without the timestamp prefix
        """
        # Split by underscore and take the last part before .json
        parts = filename.split('_')
        if len(parts) >= 3:  # Ensure we have timestamp parts and test name
            test_name = parts[-1].replace('.json', '')
            return test_name
        return filename  # Return original if format doesn't match
        
    def start_recording(self):
        """Start recording a new test."""
        try:
            # First, try to kill any existing listener
            self.killOldListener()
            
            # Show the test name dialog
            dialog = TestNameDialog()
            dialog.dialog.wait_window()  # Wait for the dialog window itself
            
            print(f"Dialog result after closing: {dialog.result}")  # Debug print
            
            # If user cancelled, return
            if dialog.result is None:
                print("Dialog was cancelled")  # Debug print
                return
                
            test_data = dialog.result
            test_name = test_data['name']
            starting_point = test_data['starting_point']
            
            print(f"Starting recording with test name: {test_name}")  # Debug print
            
            self.status_var.set(f"Recording new test: {test_name}")
            self.root.update()
            
            # Get paths from config
            paths_config = self.config.get('paths', {})
            db_path = paths_config.get('db_path', os.path.join(project_root, "DB"))
            test_path = paths_config.get('test_path', "Test")
            
            # Create the test directory structure
            test_dir = os.path.join(db_path, test_path, test_name)
            os.makedirs(test_dir, exist_ok=True)
            
            # Set the test filename
            test_file = os.path.join(test_dir, f"{test_name}.json")
            
            # Check if file already exists
            if os.path.exists(test_file):
                if not messagebox.askyesno(
                    "File Exists",
                    f"A test named '{test_name}' already exists. Do you want to overwrite it?"
                ):
                    return
            
            # # Create a new test with the specified parameters
            # test = Test(
            #     config="",
            #     comment1=test_data['purpose'],
            #     comment2="",
            #     accuracy_level=test_data['accuracy_level'],
            #     starting_point=starting_point
            # )
            
            # Hide the control panel window
            self.root.withdraw()

            go_to_starting_point(starting_point)
            
            # Start recording with the specified test name and starting point
            start_recording(test_name, starting_point)
            
            # Show the control panel window again (in case the recording was cancelled)
            self.root.deiconify()
            
            # Refresh test list after recording
            self.refresh_test_list()
            # self.refresh_result_list()
            # self.status_var.set(f"Recording completed successfully: {test_name}")
            
        except Exception as e:
            self.status_var.set(f"Error during recording: {str(e)}")
            messagebox.showerror("Recording Error", str(e))
            # Show the control panel window in case of error
            self.root.deiconify()
            
    def run_test(self):
        """Run the selected test."""
        self.killOldListener()

        selection = self.test_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Test Selected", "Please select a test to run.")
            return
            
        # Get the full display text and extract just the test name
        display_text = self.test_listbox.get(selection[0])
        test_name = self._extract_name_from_display(display_text)
        

        
        try:
            self.status_var.set(f"Running test: {test_name}")
            self.root.update()
            
            # Get paths from config
            paths_config = self.config.get('paths', {})
            db_path = paths_config.get('db_path', os.path.join(project_root, "DB"))
            test_path = paths_config.get('test_path', "Test")
            
            # Construct full path to test file
            test_file_path = os.path.join(db_path, test_path, test_name, f"{test_name}.json")
            
            # Create timestamp for result directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            result_dir_name = f"{timestamp}_{test_name}"
            
            # Create the result directory structure with timestamp prefix
            resu_path = paths_config.get('result_path', "Result")
            resu_dir = os.path.join(db_path, resu_path, result_dir_name)
            os.makedirs(resu_dir, exist_ok=True)
            
            # Copy the test file to the result directory
            result_test_file = os.path.join(resu_dir, f"{test_name}.json")
            shutil.copy2(test_file_path, result_test_file)
            
            # Hide the control panel window
            self.root.withdraw()
            
            # Use the copied test file path for running the test
            start_runing(result_test_file)   
                    
            # Show the control panel window again
            self.root.deiconify()
            self.status_var.set(f"Test completed: {test_name} (Result saved in: {result_dir_name})")
            # Refresh the result list to show the new test result
            self.refresh_result_list()
            
        except Exception as e:
            self.status_var.set(f"Error running test: {str(e)}")
            messagebox.showerror("Test Error", str(e))
            # Show the control panel window in case of error
            self.root.deiconify()

def main():
    root = tk.Tk()
    app = ControlPanel(root)
    root.mainloop()

if __name__ == "__main__":
    main() 