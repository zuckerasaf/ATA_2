"""
Control Panel UI for test recording and execution.

This module provides the main GUI for managing test cases, running tests, updating images, and viewing results.
It includes functionality for:
- Recording new test cases with metadata (name, purpose, accuracy level, precondition)
- Running single or multiple test cases
- Updating test images
- Viewing test results and logs
- Creating test documentation
- Managing test and result lists
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import shutil
import subprocess
import json

# Add project root to Python path for module imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

from src.tests.recordTest import main as start_recording
from src.tests.runTest import main as start_runing
from src.utils.general_func import  display_test_data, update_images_to_test
from src.utils.config import Config
from src.gui.test_name_dialog import TestNameDialog
from src.utils.starting_points import go_to_starting_point
from src.utils.run_log import RunLog


run_log = RunLog()
class ControlPanel:
    """
    Main class for the ATA Control Panel GUI.

    This class implements a singleton pattern to ensure only one instance of the control panel
    is open at a time. It provides a comprehensive interface for test management with the following features:

    - Test Recording:
        * Create new tests with metadata (name, purpose, accuracy level, precondition)
        * Select starting points for tests
        * Record test steps with mouse and keyboard actions

    - Test Execution:
        * Run single or multiple tests
        * View real-time test execution status
        * Handle test failures and errors

    - Test Management:
        * View and organize test cases
        * Update test images
        * Create test documentation
        * Navigate to test folders

    - Result Management:
        * View test results
        * Access test logs
        * Clear logs
        * View detailed execution status

    The GUI is divided into three main sections:
    1. Left panel: List of available tests
    2. Center panel: Control buttons for test operations
    3. Right panel: List of test results
    4. Bottom panel: Status bar showing execution details

    Attributes
    ----------
    _instance : ControlPanel
        Class variable implementing the singleton pattern
    root : tk.Tk
        The root Tkinter window
    config : Config
        Configuration object for loading settings
    test_listbox : tk.Listbox
        Listbox showing available tests
    result_listbox : tk.Listbox
        Listbox showing test results
    status_text : tk.Text
        Text widget showing execution status
    """

    _instance = None  # Class variable to track the open instance

    def __init__(self, root):
        """
        Initialize the ControlPanel.

        Args:
            root (tk.Tk): The root Tkinter window.
        """
        # Singleton pattern: store the instance
        ControlPanel._instance = self

        self.root = root
        self.config = Config()
        
        # Get control panel configuration from config file
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
        
        # Create main frames for test list, control buttons, result list, and status bar
        self.create_list_frame(self.root, "List of Tests", 0, "test_listbox")
        self.create_control_buttons_frame()
        self.create_list_frame(self.root, "List of Results", 2, "result_listbox")
        self.create_status_bar()
        
        # Initialize data in the lists and run log status
        self.refresh_test_list()
        self.refresh_result_list()
        self.refresh_run_log_status()
        
        # Bind window close event to custom handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def killOldListener(self):
        """
        Kill any existing mouse listener process and clean up its lock file.

        This method ensures that only one mouse listener is running at a time by:
        1. Checking for the existence of a lock file
        2. Reading the process ID from the lock file
        3. Terminating the process using taskkill
        4. Removing the lock file

        This is called during application shutdown to prevent orphaned listener processes.
        """
        try:
            lock_file = "cursor_listener.lock"
            if os.path.exists(lock_file):
                try:
                    with open(lock_file, 'r') as f:
                        pid = int(f.read().strip())
                    os.system(f'taskkill /F /PID {pid}')
                except:
                    pass
                try:
                    os.remove(lock_file)
                except:
                    pass
            self.root.update()
        except Exception as e:
            print(f"Error during shutdown: {e}")

    def on_closing(self):
        """
        Handle the window close event.

        This method is called when the user attempts to close the control panel window.
        It ensures a clean shutdown by:
        1. Killing any active mouse listeners
        2. Clearing the singleton instance
        3. Destroying the root window
        """
        self.killOldListener()
        # Clear the singleton instance on close
        ControlPanel._instance = None
        
        self.root.destroy()

    def create_list_frame(self, parent, title, column, listbox_var_name):
        """
        Create a generic list frame with scrollbars.

        This method creates a labeled frame containing a listbox with both vertical
        and horizontal scrollbars. The listbox is stored as an instance variable
        using the provided name.

        Args:
            parent (tk.Widget): The parent widget to contain the frame
            title (str): The title for the LabelFrame
            column (int): The column number for grid placement
            listbox_var_name (str): The name of the instance variable to store the listbox

        Returns:
            ttk.LabelFrame: The created frame containing the listbox and scrollbars
        """
        frame = ttk.LabelFrame(parent, text=title)
        frame.grid(row=0, column=column, padx=5, pady=5, sticky="nsew")
        inner_frame = ttk.Frame(frame)
        inner_frame.pack(fill="both", expand=True)
        listbox = tk.Listbox(inner_frame, selectmode=tk.EXTENDED)
        v_scrollbar = ttk.Scrollbar(inner_frame, orient="vertical", command=listbox.yview)
        listbox.configure(yscrollcommand=v_scrollbar.set)
        h_scrollbar = ttk.Scrollbar(inner_frame, orient="horizontal", command=listbox.xview)
        listbox.configure(xscrollcommand=h_scrollbar.set)
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        listbox.pack(side="left", fill="both", expand=True)
        setattr(self, listbox_var_name, listbox)
        return frame

    def create_control_buttons_frame(self):
        """
        Create the center frame containing control buttons for test operations.

        This method creates a frame with buttons for:
        - Recording new tests
        - Running tests
        - Navigating to test folders
        - Updating test images
        - Creating test documentation
        - Closing the application
        - Clearing logs

        The buttons are arranged vertically with separators for visual grouping.
        """
        frame = ttk.Frame(self.root)
        frame.grid(row=0, column=1, padx=5, pady=5, sticky="ns")
        ttk.Button(frame, text="Record", command=self.start_recording).pack(pady=5)
        ttk.Button(frame, text="Run", command=self.run_test).pack(pady=5)
        
        # Add separator frame for gap
        separator = ttk.Frame(frame, height=50)
        separator.pack(pady=5)
        
        ttk.Button(frame, text="Go to", command=self.go_to_folder).pack(pady=5)
        ttk.Button(frame, text="Update Images", command=self.update_images).pack(pady=5)
        ttk.Button(frame, text="Edit Test", command=self.edit_test).pack(pady=5)
        ttk.Button(frame, text="Create Doc", command=self.create_document).pack(pady=5)
        # Add separator frame for gap
        separator = ttk.Frame(frame, height=50)
        separator.pack(pady=5)

        ttk.Button(frame, text="Close", command=self.on_closing).pack(pady=5)

        ttk.Button(frame, text="Clear Log", command=self.clear_log).pack(pady=5, side="bottom")

    def create_status_bar(self):
        """
        Create the status bar at the bottom of the window.

        This method creates a status bar that shows the execution status of tests.
        Features include:
        - A text widget for displaying status messages
        - Vertical and horizontal scrollbars
        - Line selection on click
        - Read-only text to prevent modification
        - Disabled right-click menu

        The status bar is used to display:
        - Test execution progress
        - Error messages
        - Success/failure status
        - Other important notifications
        """
        frame = ttk.LabelFrame(self.root, text="Status of the Last Run")
        frame.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="ew")

        # Inner frame for text and vertical scrollbar
        inner_frame = ttk.Frame(frame)
        inner_frame.pack(fill="both", expand=True)

        # Text widget - make it selectable but read-only
        self.status_text = tk.Text(inner_frame, height=20, wrap="none")
        self.status_text.pack(side="left", fill="both", expand=True)
        
        # Bind click event to select entire line
        self.status_text.bind("<Button-1>", self.select_line)
        # Prevent text editing but allow selection
        self.status_text.bind("<Key>", lambda e: "break")
        self.status_text.bind("<Button-3>", lambda e: "break")  # Disable right-click menu

        # Vertical scrollbar
        v_scrollbar = ttk.Scrollbar(inner_frame, orient="vertical", command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=v_scrollbar.set)
        v_scrollbar.pack(side="right", fill="y")

        # Horizontal scrollbar (pack it to the bottom of the outer frame)
        h_scrollbar = ttk.Scrollbar(frame, orient="horizontal", command=self.status_text.xview)
        self.status_text.configure(xscrollcommand=h_scrollbar.set)
        h_scrollbar.pack(side="bottom", fill="x")

        # Add a button to open selected image
        ttk.Button(frame, text="Open Selected Image", command=self.open_image).pack(pady=5)

    def select_line(self, event):
        """Select the entire line when clicked."""
        try:
            # Get the line number where the click occurred
            index = self.status_text.index(f"@{event.x},{event.y}")
            line_start = f"{index} linestart"
            line_end = f"{index} lineend"
            
            # Select the entire line
            self.status_text.tag_remove("sel", "1.0", "end")
            self.status_text.tag_add("sel", line_start, line_end)
            
            # Make sure the selection is visible
            self.status_text.see(line_start)
        except Exception as e:
            print(f"Error in select_line: {e}")

    def set_status(self, message):
        """
        Update the status text widget with a new message.

        This method:
        1. Clears the current status text
        2. Inserts the new message
        3. Ensures the new message is visible
        4. Updates the display

        Args:
            message (str): The message to display in the status bar
        """
        self.status_text.config(state="normal")  # Enable editing temporarily
        self.status_text.delete("1.0", tk.END)
        self.status_text.insert("1.0", message)
        self.status_text.config(state="normal")  # Keep it editable for selection

    def _populate_list(self, listbox, directory_path, file_pattern, state):
        """
        Populate a listbox with files from a directory.

        This method:
        1. Clears the current listbox contents
        2. Gets a list of files matching the pattern
        3. Sorts the files by modification time
        4. Inserts the files into the listbox with timestamps
        5. Updates the listbox state

        Args:
            listbox (tk.Listbox): The listbox to populate
            directory_path (str): Path to the directory containing the files
            file_pattern (str): Pattern to match files (e.g., "*.json")
            state (str): The state to set for the listbox ("normal" or "disabled")
        """
        listbox.delete(0, tk.END)
        
        if state == "result":
            self.result_display_to_folder = {}  # Reset mapping for results
        
        if os.path.exists(directory_path):
            # Create a list to store file info (name, creation time, and display name)
            file_info = []
            for name in os.listdir(directory_path):
                if state == "test":
                    file_path = file_pattern(name)
                    test_summary = display_test_data(file_path)
                    display_name = name + " - " + str(test_summary)
                else: #state == "result"    
                    # Extract just the test name from the timestamped filename
                    display_name = "Result_"+self._extract_test_name_from_timestamp(name)
                    file_path = os.path.join(directory_path, name, f"{display_name}.json")

                    test_summary = display_test_data(file_path)
                    display_name = display_name + " - " + str(test_summary)
                    
                if os.path.exists(file_path):
                    # Get file creation time
                    creation_time = os.path.getctime(file_path)
                    
                    # Store file info
                    if state == "test":
                        # Format the creation time
                        creation_date = datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        parts = name.split("_")[0:2]  # ['20250605', '085117']
                        dt = datetime.strptime(parts[0] + parts[1], "%Y%m%d%H%M%S")
                        creation_date = dt.strftime("%Y-%m-%d %H:%M:%S")

                    #creation_time = creation_time.timestamp()
                    file_info.append({
                        'name': name,
                        'creation_time': creation_time,
                        'display_name': f"{display_name} - {creation_date}",
                        'has_failed': 'failed' in str(test_summary).lower()
                    })
                    if state == "result":
                        # Store mapping from display string to actual folder name
                        self.result_display_to_folder[f"{display_name} - {creation_date}"] = name
            
            # Sort by creation time (newest first)
            file_info.sort(key=lambda x: x['creation_time'], reverse=True)
            
            # Add sorted items to listbox with colors
            for item in file_info:
                listbox.insert(tk.END, item['display_name'])
                if item['has_failed']:
                    listbox.itemconfig(listbox.size()-1, {'fg': 'red'})
                else:
                    listbox.itemconfig(listbox.size()-1, {'fg': 'green'})
                
    def refresh_test_list(self):
        """Refresh the list of test .

        This method:
        1. Gets the test directory path from config
        2. Populates the test listbox with JSON files
        3. Enables the listbox for interaction
        """
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
        """Refresh the list of test results.

        This method:
        1. Gets the result directory path from config
        2. Populates the result listbox with JSON files
        3. Enables the listbox for interaction
        """
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
        Extract the test name from a display text string.

        Args:
            display_text (str): The display text in format "timestamp - filename"

        Returns:
            str: The extracted test name
        """
        return display_text.split(" - ")[0]
        
    def _extract_test_name_from_timestamp(self, filename):
        """
        Extract the test name from a timestamped filename.

        Args:
            filename (str): The filename in format "timestamp_filename.json"
            timestamp (str): The timestamp in format "YYYYMMDD_HHMMSS"

        Returns:
            str: The extracted test name
        """
        # Split by underscore and take the last part before .json
        parts = filename.split('_')
        if len(parts) >= 3:  # Ensure we have timestamp parts and test name
            test_name = filename[16:]
            #test_name = parts[2:]
            return test_name
        return filename  # Return original if format doesn't match
        
    def start_recording(self):
        """
        Start recording a new test.

        This method:
        1. Shows a dialog to get test metadata (name, purpose, accuracy, precondition)
        2. Creates a new test directory
        3. Saves the test metadata
        4. Starts the recording process
        5. Updates the test list when recording is complete

        The recording process captures:
        - Mouse movements and clicks
        - Keyboard input
        - Screenshots at each step
        """
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
            precondition = test_data['precondition']

            print(f"Starting recording with test name: {test_name}")  # Debug print
            
            self.set_status(f"Recording new test: {test_name}")
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

            # Hide the control panel window in case of multiWindow is false
            if self.config.get("multiWindow") == False:
                self.root.withdraw()

            try:
                go_to_starting_point(starting_point)
                # Now close the Control Panel window
                self.root.destroy()
                #run_log.clear()
                # Start recording with the specified test name and starting point
                start_recording(test_name, starting_point, precondition)
            except Exception as e:
                print(f"Error during recording: {e}")
                raise e
            finally:
                # show the control panel window again in case of multiWindow is false
                if self.config.get("multiWindow") == False:
                    self.root.deiconify()
            
            # # Refresh test list after recording
            # self.refresh_test_list()

            try:
                root = tk.Tk()
                app = ControlPanel(root)
                root.mainloop()
            except Exception as e:
                print(f"Fatal error creating control panel: {e}")
            
        except Exception as e:
            self.set_status(f"Error during recording: {str(e)}")
            messagebox.showerror("Recording Error", str(e))
            # Show the control panel window in case of error
            self.root.deiconify()
            
    def run_test(self):
        """
        Run selected test(s).

        This method:
        1. Gets the selected test(s) from the listbox
        2. Creates a result directory for each test
        3. Runs each test in sequence
        4. Updates the result list when complete

        The test execution:
        - Follows the recorded steps
        - Takes screenshots for comparison
        - Logs the execution results
        - Handles any errors that occur
        """
        self.killOldListener()

        selections = self.test_listbox.curselection()
        if not selections:
            messagebox.showwarning("No Test Selected", "Please select at least one test to run.")
            return
            
        # Get all selected test names
        test_names = []
        for selection in selections:
            display_text = self.test_listbox.get(selection)
            test_name = self._extract_name_from_display(display_text)
            test_names.append(test_name)
        
        try:
            print(f"Running {len(test_names)} tests... {test_names}")
            #self.status_var.set(f"Running {len(test_names)} tests...")
            self.root.update()
            
            # Get paths from config
            paths_config = self.config.get('paths', {})
            db_path = paths_config.get('db_path', os.path.join(project_root, "DB"))
            test_path = paths_config.get('test_path', "Test")
            
            # Create a queue for test completion
            import queue
            test_completion_queue = queue.Queue()
            
            def run_next_test(test_index=0):
                if test_index >= len(test_names):
                    self.refresh_run_log_status()
                    # All tests are done
                    if len(test_names) > 1:
                        messagebox.showinfo("Test Sequence Complete", f"All {len(test_names)} tests have been completed.")
                    return
                
                test_name = test_names[test_index]
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
                
                # Hide the control panel window in case of multiWindow is false
                if self.config.get("multiWindow") == False:
                    self.root.withdraw()
                
                def test_completed_callback():
                    # Show the control panel window again
                    self.root.deiconify()
                    # Update status
                    #self.status_var.set(f"Test completed: {test_name} (Result saved in: {result_dir_name})")
                    print(f"Test completed: {test_name} (Result saved in: {result_dir_name})")
                    self.root.update()
                    # Refresh the result list
                    self.refresh_result_list()
                    # Signal completion and run next test
                    test_completion_queue.put(True)
                    self.root.after(100, lambda: run_next_test(test_index + 1))
                
                # Use the copied test file path for running the test with callback
                success = start_runing(result_test_file, callback=test_completed_callback, run_number=test_index+1, run_total=len(test_names))
                if not success:
                    # If test failed to start, show control panel and continue with next test
                    if self.config.get("multiWindow") == False:
                        self.root.deiconify()
                    self.set_status(f"Test failed to start: {test_name}")
                    self.root.after(100, lambda: run_next_test(test_index + 1))
            
            # Start the first test
            run_next_test(0)
            
        except Exception as e:
            self.set_status(f"Error running test: {str(e)}")
            messagebox.showerror("Test Error", str(e))
            # Show the control panel window in case of error
            self.root.deiconify()

    def _convert_display_to_timestamp(self, display_text, is_result=False):
        """
        Convert a display text to a timestamped filename.

        Args:
            display_text (str): The display text in format "timestamp - filename"
            is_result (bool): Whether this is a result file

        Returns:
            str: The timestamped filename
        """
        try:
            # Split the display text into name and date parts
            name_part, stepResult, date_part = display_text.split(" - ")
            
            # For test list, just return the name part
            if is_result:                
                # For result list, process the timestamp
                # Extract the test number from the name part (remove "Result_" prefix)
                test_name = name_part.replace("Result_", "")
                
                # Parse the date string
                date_obj = datetime.strptime(date_part, '%Y-%m-%d %H:%M:%S')
                
                # Format the date into the timestamp format
                timestamp = date_obj.strftime('%Y%m%d_%H%M%S')
                
                # Combine into the final format
                return f"{timestamp}_{test_name}"
            else :

                return f"{name_part}"

            
        except Exception as e:
            print(f"Error converting display format: {e}")
            return display_text  # Return original if conversion fails

    def go_to_folder(self):
        """
        Open the folder of the selected test or result.

        This method:
        1. Gets the selected item from either listbox
        2. Determines if it's a test or result
        3. Opens
        """
        try:
            test_selections = self.test_listbox.curselection()
            result_selections = self.result_listbox.curselection()
            
            # Check for multiple selections
            if len(test_selections) > 1:
                messagebox.showwarning("Multiple Selections", "Please select only one test to open its folder.")
                return
            if len(result_selections) > 1:
                messagebox.showwarning("Multiple Selections", "Please select only one result to open its folder.")
                return
            
            if test_selections:
                selected_item = self.test_listbox.get(test_selections[0])
                folder_name = self._convert_display_to_timestamp(selected_item, is_result=False)
                test_path = self.config.get('paths', {}).get('test_path', "Test")
                folder_path = os.path.join(test_path, folder_name)
            elif result_selections:
                selected_item = self.result_listbox.get(result_selections[0])
                # Use the mapping to get the real folder name
                folder_name = self.result_display_to_folder.get(selected_item, None)
                if not folder_name:
                    messagebox.showerror("Error", "Could not find the folder for the selected result.")
                    return
                result_path = self.config.get('paths', {}).get('result_path', "Result")
                folder_path = os.path.join(result_path, folder_name)
            else:
                messagebox.showwarning("Warning", "Please select a test or result from the list")
                return
            if os.path.exists(folder_path):
                if sys.platform == 'win32':
                    os.startfile(folder_path)
                elif sys.platform == 'darwin':  # macOS
                    subprocess.run(['open', folder_path])
                else:  # linux
                    subprocess.run(['xdg-open', folder_path])
            else:
                messagebox.showerror("Error", f"Folder not found: {folder_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open folder: {str(e)}")

    def update_images(self):
        """
        Update images for the selected test.

        This method:
        1. Gets the selected test from the listbox
        2. Updates the test images with current screen state
        3. Refreshes the test list
        """
        
        selections = self.result_listbox.curselection()
        if not selections:
            messagebox.showwarning("No Result Selected", "Please select a result folder to update images from.")
            return
            
        # Get the selected result folder name
        selected_item = self.result_listbox.get(selections[0])
        folder_name = self.result_display_to_folder.get(selected_item, None)
        if not folder_name:
            messagebox.showerror("Error", "Could not find the folder for the selected result.")
            return
            
        # Get paths from config
        paths_config = self.config.get('paths', {})
        db_path = paths_config.get('db_path', os.path.join(project_root, "DB"))
        result_path = paths_config.get('result_path', "Result")
        
        # Construct full path to result folder
        result_folder_path = os.path.join(db_path, result_path, folder_name)
        
        # Extract test name from folder name
        parts = folder_name.split('_')
        if len(parts) >= 3:
            test_name = '_'.join(parts[2:])  # Join remaining parts in case test name contains underscores
        else:
            test_name = folder_name
            
        # Show confirmation dialog
        if not messagebox.askyesno(
            "Confirm Image Update",
            f"This will copy all _Result.jpg files from the result folder to the test folder '{test_name}'.\n"
            "Existing images in the test folder will be overwritten.\n\n"
            "Do you want to continue?"
        ):
            return
        
        # Call the update function
        if update_images_to_test(result_folder_path):
            messagebox.showinfo("Success", "Images updated successfully!")
        else:
            messagebox.showerror("Error", "Failed to update images.")

    def refresh_run_log_status(self):
        """
        Refresh the run log status display.

        This method:
        1. Gets the current run log content
        2. Updates the status text widget
        3. Ensures the latest content is visible
        """
        log_file_path = self.config.get_run_log_path()
        try:
            if os.path.exists(log_file_path):
                with open(log_file_path, "r", encoding="utf-8") as f:
                    log_content = f.read().strip()
                if log_content:
                    self.set_status(log_content)
                else:
                    self.set_status("Run log is empty.")
            else:
                self.set_status("Run log file not found.")
        except Exception as e:
            self.set_status(f"Error reading run log: {e}")

    def clear_log(self):
        """
        Clear the run log.

        This method:
        1. Clears the run log file
        2. Updates the status display
        3. Shows a confirmation message
        """
        log_file_path = self.config.get_run_log_path()
        
        if not messagebox.askyesno("Clear Log", "Are you sure you want to clear the run log?"):
            return
        try:
            # Erase the log file
            with open(log_file_path, "w", encoding="utf-8") as f:
                pass  # Opening in 'w' mode truncates the file
            # Clear the status bar
            self.refresh_run_log_status()
        except Exception as e:
            self.set_status(f"Error clearing run log: {e}")

    @classmethod
    def bring_to_front_and_refresh(cls):
        """
        Bring the control panel window to front and refresh its contents.

        This class method:
        1. Checks if an instance exists
        2. Brings the window to front
        3. Refreshes the test and result lists
        4. Refreshes the run log status

        Returns:
            bool: True if the window was brought to front, False if no instance exists
        """
        if cls._instance is not None:
            try:
                cls._instance.root.deiconify()
                cls._instance.root.lift()
                cls._instance.root.focus_force()
                cls._instance.refresh_test_list()
                cls._instance.refresh_result_list()
                cls._instance.refresh_run_log_status()
            except Exception as e:
                print(f"Error bringing ControlPanel to front: {e}")
    
    def open_image(self):
        """
        Open the image in the image viewer.

        This method:
        1. Checks if there's any text selected
        2. Extracts the image path from the selected line
        3. Opens the image in the image viewer
        """
        try:
            # Check if there's any text selected
            try:
                selected_line = self.status_text.get("sel.first", "sel.last")
            except tk.TclError:
                messagebox.showwarning("No Selection", "Please click on a line containing [IMAGE] to select it.")
                return

            # Check if the line contains [IMAGE]
            if "[IMAGE]" in selected_line:
                # Extract the image path (everything after the timestamp)
                parts = selected_line.split(": ", 1)  # Split on first ": " to separate timestamp from path
                if len(parts) > 1:
                    image_path = parts[1].strip()
                    if os.path.exists(image_path):
                        if sys.platform == 'win32':
                            # Open the result image
                            os.startfile(image_path)
                            # Try to open the corresponding diff image
                            diff_path = image_path.replace("_Result.jpg", "_gray.jpg")
                            if os.path.exists(diff_path):
                                os.startfile(diff_path)
                            diff_path = image_path.replace("_Result.jpg", "_Result_diff.jpg")
                            if os.path.exists(diff_path):
                                os.startfile(diff_path)
                        else:
                            messagebox.showerror("Error", "Image opening is only supported on Windows.")
                    else:
                        messagebox.showerror("Error", f"Image file not found: {image_path}")
                else:
                    messagebox.showerror("Error", "Invalid image path format in log.")
            else:
                messagebox.showwarning("No Image Selected", "Please select a line containing [IMAGE].")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open image: {str(e)}")
    def edit_test(self):
        """
        Edit the selected test.
        messagebox.showinfo("Edit Test", "Edit the selected test.")
        """
        messagebox.showinfo("Edit Test", "Edit the selected test future feature.")


    def create_document(self):
        """
        Create a Word document from selected tests or results.

        This method:
        1. Gets the selected tests or results
        2. Creates a list of JSON paths
        """
        try:
            # Get selections from both lists
            test_selections = self.test_listbox.curselection()
            result_selections = self.result_listbox.curselection()
            
            if not test_selections and not result_selections:
                messagebox.showwarning("No Selection", "Please select at least one test or result from the lists.")
                return

            # Get paths from config
            paths_config = self.config.get('paths', {})
            db_path = paths_config.get('db_path', os.path.join(project_root, "DB"))
            test_path = paths_config.get('test_path', "Test")
            result_path = paths_config.get('result_path', "Result")

            # Create list to store JSON paths
            json_paths = []

            # Process test selections
            for selection in test_selections:
                display_text = self.test_listbox.get(selection)
                test_name = self._extract_name_from_display(display_text)
                test_dir = os.path.join(db_path, test_path, test_name)
                json_file = os.path.join(test_dir, f"{test_name}.json")
                
                if os.path.exists(json_file):
                    json_paths.append(json_file)

                TYPE="ATP"

            # Process result selections
            for selection in result_selections:
                display_text = self.result_listbox.get(selection)
                folder_name = self.result_display_to_folder.get(display_text, None)
                if folder_name:
                    result_dir = os.path.join(db_path, result_path, folder_name)
                    # Look for JSON files in the result directory
                    for file in os.listdir(result_dir):
                        if file.endswith('.json') and file.startswith('Result'):
                            json_file = os.path.join(result_dir, file)
                            if os.path.exists(json_file):
                                json_paths.append(json_file)
                    
                TYPE="ATR"

            if not json_paths:
                messagebox.showwarning("No Files", "No valid JSON files found in selected items.")
                return

            # Import the document creation function
            from src.Doc.create_Doc import create_doc_from_json

            # Create the document
            success = create_doc_from_json(json_paths, pictures=True, Type=TYPE, Regular_doc_path=False)
            
            if success:
                messagebox.showinfo("Success", "Document created successfully!")
            else:
                messagebox.showerror("Error", "Failed to create document.")
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")



def main():
    # If already open, just bring to front and refresh
    if ControlPanel._instance is not None:
        ControlPanel.bring_to_front_and_refresh()
    else:
        root = tk.Tk()
        app = ControlPanel(root)
        root.mainloop()

if __name__ == "__main__":
    main() 