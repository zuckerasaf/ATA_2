"""
Utility functions for process management.
"""

import os
import atexit
import time
import json
import psutil
from src.utils.app_lifecycle import restart_control_panel


def cleanup(lock_file):
    """
    Remove the lock file upon program exit.
    
    Args:
        lock_file: Path to the lock file to remove
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
    
    Args:
        lock_file: Path to the lock file containing the PID
    """
    try:
        if os.path.exists(lock_file):
            # Read the PID from the lock file
            with open(lock_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Try to terminate the process
            try:
                process = psutil.Process(pid)
                # Check if this is our own process
                if process.pid == os.getpid():
                    print("This is our own process, not terminating")
                    return False
                    
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
    If found, attempt to terminate it.
    
    Args:
        lock_file: Path to the lock file to check
        
    Returns:
        bool: True if another instance is running and couldn't be terminated, False otherwise
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
    
    Args:
        lock_file: Path to the lock file to remove on exit
    """
    atexit.register(cleanup, lock_file)

def cleanup_and_restart(event_window, lock_file="cursor_listener.lock"):
    """
    Clean up resources and restart the control panel.
    
    Args:
        event_window: The event window to destroy
        lock_file: Path to the lock file to remove
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

def save_test(test, test_name=None, state="running",result_folder_path=None):
    """
    Save the test data to a file.
    
    Args:
        test: The Test object to save
        test_name: Name of the test (optional)
        state: State of the test ("running" or "recording")
        
    Returns:
        str: Path to the saved file
    """
    try:
        # Get paths from config
        from src.utils.config import Config
        config = Config()
        paths_config = config.get('paths', {})
        
        if state == "running":

            result_dir = result_folder_path
            test_name="Result_"+test_name  
            # Set the result filename
            result_file = os.path.join(result_dir, f"{test_name}.json")
            # Ensure the directory exists
            os.makedirs(os.path.dirname(result_file), exist_ok=True)
        else:
            # For recording tests, save to the test directory
            test_path = paths_config.get('test_path', "Test")
            db_path = paths_config.get('db_path', os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "DB"))
            
            # Create the test directory structure
            test_dir = os.path.join(db_path, test_path, test_name)
            os.makedirs(test_dir, exist_ok=True)
            
            # Set the test filename
            result_file = os.path.join(test_dir, f"{test_name}.json")
        
        # Save the test data
        with open(result_file, 'w') as f:
            json.dump(test.to_dict(), f, indent=4)
        
        print(f"Test data saved to: {result_file}")
        return result_file
        
    except Exception as e:
        print(f"Error saving test data: {e}")
        return None 



