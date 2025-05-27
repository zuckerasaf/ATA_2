"""
Utility functions for process management.

This module provides utility functions for managing processes, including checking if an instance is already running,
terminating running instances, cleaning up resources, and saving test data.

Functions
---------
cleanup(lock_file)
    Remove the lock file upon program exit.
terminate_running_instance(lock_file)
    Terminate the running instance of the program.
is_already_running(lock_file)
    Check if another instance of the program is already running.
register_cleanup(lock_file)
    Register the cleanup function to run on exit.
cleanup_and_restart(event_window, lock_file="cursor_listener.lock")
    Clean up resources and restart the control panel.
save_test(test, test_name=None, state="running", result_folder_path=None)
    Save the test data to a file.
close_existing_mouse_threads()
    Close any existing mouse listener threads.
"""

import os
import atexit
import time
import json
import psutil
import threading
from src.utils.app_lifecycle import restart_control_panel
from tkinter import messagebox
from src.Doc.create_Doc import create_doc_from_json


def cleanup(lock_file):
    """
    Remove the lock file upon program exit.

    This function is registered to run on program exit to ensure the lock file is removed,
    preventing issues with subsequent program starts.

    Parameters
    ----------
    lock_file : str
        Path to the lock file to remove.

    Raises
    ------
    Exception
        If an error occurs while removing the lock file.
    """
    try:
        if os.path.exists(lock_file):
            os.remove(lock_file)
            print(f"Lock file {lock_file} removed successfully")
    except Exception as e:
        print(f"Error removing lock file: {e}")


def terminate_running_instance(lock_file):
    """
    Terminate the running instance of the program.

    This function reads the PID from the lock file and attempts to terminate the process.
    It first tries a graceful termination and waits for the process to end.

    Parameters
    ----------
    lock_file : str
        Path to the lock file containing the PID.

    Returns
    -------
    bool
        True if the process was successfully terminated, False otherwise.

    Raises
    ------
    Exception
        If an error occurs while terminating the process.
    """
    try:
        if os.path.exists(lock_file):
            # Read the PID from the lock file
            with open(lock_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Try to terminate the process
            try:
                process = psutil.Process(pid)

                messagebox.showinfo(
                    "Application Stopped",
                    "The application has been stopped.\nAll running processes have been terminated."
                )
                # Try graceful termination first
                process.terminate()
                # Wait for the process to terminate
                process.wait(timeout=3)
                print(f"Terminated process with PID {pid}")
                return True
            except psutil.NoSuchProcess:
                print(f"Process {pid} no longer exists")
                return True
            except psutil.TimeoutExpired:
                print(f"Process {pid} did not terminate in time")
                return False
    except Exception as e:
        print(f"Error terminating process: {e}")
        return False


def is_already_running(lock_file):
    """
    Check if another instance of the program is already running.

    If another instance is found, this function attempts to terminate it.
    If the lock file still exists after termination, it indicates a failure to terminate the instance.

    Parameters
    ----------
    lock_file : str
        Path to the lock file to check.

    Returns
    -------
    bool
        True if another instance is running and couldn't be terminated, False otherwise.

    Raises
    ------
    Exception
        If an error occurs while checking if the program is running.
    """
    try:
        if os.path.exists(lock_file):
            print("Another instance is already running!")
            # Try to terminate the running instance
            if terminate_running_instance(lock_file):
                # Wait a moment for cleanup
                time.sleep(0.5)
                # If lock file still exists, return True
                if os.path.exists(lock_file):
                    print("Failed to terminate running instance")
                    return True
                # If lock file is gone, create new one and return False
                with open(lock_file, 'w') as f:
                    f.write(str(os.getpid()))
                return False
            return True
        else:
            # Create the lock file
            with open(lock_file, 'w') as f:
                f.write(str(os.getpid()))
            return False
    except Exception as e:
        print(f"Error checking if program is running: {e}")
        return False


def register_cleanup(lock_file):
    """
    Register the cleanup function to run on exit.

    This function registers the cleanup function to be called when the program exits,
    ensuring the lock file is removed.

    Parameters
    ----------
    lock_file : str
        Path to the lock file to remove on exit.
    """
    atexit.register(cleanup, lock_file)


def cleanup_and_restart(event_window, lock_file="cursor_listener.lock"):
    """
    Clean up resources and restart the control panel.

    This function deletes the lock file, destroys the event window, and restarts the control panel.

    Parameters
    ----------
    event_window : tk.Toplevel
        The event window to destroy.
    lock_file : str, optional
        Path to the lock file to remove.
    """
    # Delete the lock file to ensure clean restart
    try:
        if os.path.exists(lock_file):
            os.remove(lock_file)
            print(f"Lock file {lock_file} deleted successfully")
    except Exception as e:
        print(f"Error deleting lock file: {e}")
        
    # Destroy the event window
    event_window.destroy()
    time.sleep(0.2)
    
    # Restart the control panel
    restart_control_panel()


def save_test(test, test_name=None, state="running", result_folder_path=None):
    """
    Save the test data to a file.

    This function saves the test data to a JSON file, either in the result directory or the test directory,
    depending on the state of the test.

    Parameters
    ----------
    test : Test
        The Test object to save.
    test_name : str, optional
        Name of the test.
    state : str, optional
        State of the test ("running" or "recording").
    result_folder_path : str, optional
        Path to the result folder.

    Returns
    -------
    str
        Path to the saved file, or None if an error occurs.

    Raises
    ------
    Exception
        If an error occurs while saving the test data.
    """
    Doctype = "ATP"
    DocPictures=True
    try:
        # Get paths from config
        from src.utils.config import Config
        config = Config()
        paths_config = config.get('paths', {})
        
        if state == "running":
            result_dir = result_folder_path
            test_name = "Result_" + test_name  
            # Set the result filename
            result_file = os.path.join(result_dir, f"{test_name}.json")
            # Ensure the directory exists
            os.makedirs(os.path.dirname(result_file), exist_ok=True)
            Doctype = "ATR"
        else:
            # For recording tests, save to the test directory
            test_path = paths_config.get('test_path', "Test")
            db_path = paths_config.get('db_path', os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "DB"))
            
            # Create the test directory structure
            test_dir = os.path.join(db_path, test_path, test_name)
            os.makedirs(test_dir, exist_ok=True)
            Doctype = "ATP"
            # Set the test filename
            result_file = os.path.join(test_dir, f"{test_name}.json")
        
        # Save the test data
        with open(result_file, 'w') as f:
            json.dump(test.to_dict(), f, indent=4)
           
        
        print(f"Test data saved to: {result_file}")
        create_doc_from_json(result_file, DocPictures, Doctype)
        return result_file
        
    except Exception as e:
        print(f"Error saving test data: {e}")
        return None


def close_existing_mouse_threads():
    """
    Close any existing mouse listener threads.

    This function iterates through all threads and stops any thread named "MouseListener",
    ensuring no lingering threads remain active.
    """
    for thread in threading.enumerate():
        if thread.name == "MouseListener":
            thread._stop()
            thread.join()