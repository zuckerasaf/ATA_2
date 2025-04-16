"""
Utility functions for process management.
"""

import os

def cleanup(lock_file):
    """Remove the lock file when the program exits."""
    try:
        if os.path.exists(lock_file):
            os.remove(lock_file)
    except Exception as e:
        print(f"Error cleaning up lock file: {e}")

def is_already_running(lock_file):
    """Check if another instance is already running using a lock file."""
    try:
        if os.path.exists(lock_file):
            # Try to read the PID from the lock file
            with open(lock_file, 'r') as f:
                pid = int(f.read().strip())
                
            # Check if the process is still running
            if os.path.exists(f"/proc/{pid}"):
                print("Another instance is already running!")
                return True
            else:
                # Process is not running, clean up the lock file
                cleanup(lock_file)
                
        # Create new lock file with current PID
        with open(lock_file, 'w') as f:
            f.write(str(os.getpid()))
            
        return False
        
    except Exception as e:
        print(f"Error checking lock file: {e}")
        return False

def register_cleanup(lock_file):
    """Register the cleanup function to run on exit."""
    import atexit
    atexit.register(lambda: cleanup(lock_file)) 