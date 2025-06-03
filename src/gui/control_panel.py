"""
Control Panel UI for test recording and execution.

This module provides the main GUI for managing test cases, running tests, updating images, and viewing results.
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
from src.utils.general_func import create_test_from_json, display_test_data, update_images_to_test
from src.utils.config import Config
from src.gui.test_name_dialog import TestNameDialog
from src.utils.starting_points import go_to_starting_point
from src.utils.run_log import RunLog


run_log = RunLog()
class ControlPanel:
    """
    Main class for the ATA Control Panel GUI.

    Handles the creation and management of the test and result lists, control buttons, status bar,
    and all user interactions for recording and running tests.

    This class now supports a singleton pattern: if an instance is already open, you can call
    ControlPanel.bring_to_front_and_refresh() to bring the window to the front and refresh the lists.
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
        Kill any old mouse listener process and remove the lock file if it exists.
        This prevents multiple listeners from running at the same time.
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
            #self.status_var.set("Terminating all listeners and closing application...")
            self.root.update()
        except Exception as e:
            print(f"Error during shutdown: {e}")

    def on_closing(self):
        """
        Handle the window close event.
        Ensures all listeners are killed and the application exits cleanly.
        """
        self.killOldListener()
        # Clear the singleton instance on close
        ControlPanel._instance = None
        
        self.root.destroy()

    def create_list_frame(self, parent, title, column, listbox_var_name):
        """
        Create a generic list frame with scrollbars.

        Args:
            parent: The parent widget
            title: The title for the LabelFrame
            column: The column number for grid placement
            listbox_var_name: The name of the instance variable to store the listbox

        Returns:
            The created frame.
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
        Create the center frame containing control buttons for recording, running, updating, and closing.
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
        ttk.Button(frame, text="Create Doc", command=self.create_document).pack(pady=5)
        # Add separator frame for gap
        separator = ttk.Frame(frame, height=50)
        separator.pack(pady=5)

        ttk.Button(frame, text="Close", command=self.on_closing).pack(pady=5)

        ttk.Button(frame, text="Clear Log", command=self.clear_log).pack(pady=5, side="bottom")

    def create_status_bar(self):
        """
        Create the status bar at the bottom of the window to show the status of the last run,
        with vertical and horizontal scrollbars.
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
        Set the status message in the status bar.
        """
        self.status_text.config(state="normal")  # Enable editing temporarily
        self.status_text.delete("1.0", tk.END)
        self.status_text.insert("1.0", message)
        self.status_text.config(state="normal")  # Keep it editable for selection

    def _populate_list(self, listbox, directory_path, file_pattern, state):
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
                    # Format the creation time
                    creation_date = datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d %H:%M:%S')
                    # Store file info
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
                start_recording(test_name, starting_point)
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
        """Run the selected tests."""
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
        Convert display format back to timestamp format.
        For results: 'Result_9 - 2025-04-26 09:29:02' -> '20250426_092902_9'
        For tests: 'test1 - 2025-04-26 09:29:02' -> 'test1'
        
        Args:
            display_text: The text shown in the listbox (format: "name - date")
            is_result: Boolean indicating if this is from the result list
            
        Returns:
            The timestamped filename format for results, or original name for tests
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
        """Open the selected test or result folder in file explorer."""
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
        """Copy images from selected result folder to corresponding test folder."""
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
        Read the contents of run_log.txt and display it in the status bar.
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
        Clear the run log file and the status bar display.
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
        If the ControlPanel is already open, bring its window to the front and refresh the lists.
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
        """Open the image in the image viewer."""
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

    def create_document(self):
        """Create a Word document from selected tests or results."""
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
                        if file.endswith('.json'):
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