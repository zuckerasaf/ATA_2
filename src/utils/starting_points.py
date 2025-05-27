"""
Module for handling different starting points for test recording.

This module provides utility functions to navigate to various starting points before beginning test recording. 
It supports minimizing all windows to show the desktop, opening Google Maps, and placeholders for other points.

Functions
---------
minimize_all_windows()
    Minimize all windows to show the desktop.
go_to_starting_point(point_name)
    Navigate to the specified starting point before beginning test recording.
"""

import os
import sys
import time
import pyautogui
import webbrowser
from src.utils.config import Config


def minimize_all_windows():
    """
    Minimize all windows to show the desktop.

    This function simulates the Windows + D hotkey to minimize all open windows and display the desktop.
    It is useful for setting a clean starting point before running or recording a test.

    Raises
    ------
    Exception
        If the hotkey press fails or pyautogui encounters an error.
    """
    try:
        # Send Windows + D to show desktop
        pyautogui.hotkey('win', 'd')
        time.sleep(0.5)  # Give time for windows to minimize
    except Exception as e:
        print(f"Error minimizing windows: {e}")


def go_to_starting_point(point_name):
    """
    Navigate to the specified starting point before beginning test recording.

    This function handles navigation to various predefined starting points, such as minimizing all windows to show the desktop
    or opening Google Maps in a browser. It uses configuration values for URLs and supports extension for additional points.

    Parameters
    ----------
    point_name : str
        Name of the starting point (e.g., "desktop", "google_map", "point_B", "point_C", "none").

    Returns
    -------
    bool
        True if successfully navigated to the starting point, False otherwise.
    """
    try:
        if point_name.lower() == "desktop":
            # Minimize all windows to show the desktop
            minimize_all_windows()
            return True
        elif point_name.lower() == "google_map":
            # Minimize all windows, then open Google Maps in Chrome or default browser
            minimize_all_windows()
            config = Config()
            url = config.get('google_map:', None)
            if url:
                # Try to open with Chrome specifically
                chrome_path = None
                # Try common Chrome paths (Windows example)
                import shutil
                chrome_path = shutil.which("chrome") or shutil.which("chrome.exe")
                if chrome_path:
                    # Open with Chrome if available
                    webbrowser.get(f'"{chrome_path}" %s').open(url)
                else:
                    # Fallback: open with default browser
                    webbrowser.open(url)
                return True
            else:
                print("Google Maps URL not found in config.")
                return False
        elif point_name.lower() == "point_b":
            # TODO: Implement point B navigation
            print("Point B navigation not yet implemented")
            return False
        elif point_name.lower() == "point_c":
            # TODO: Implement point C navigation
            print("Point C navigation not yet implemented")
            return False
        elif point_name.lower() == "none":
            # No starting point needed
            return True
        else:
            print(f"Unknown starting point: {point_name}")
            return False
    except Exception as e:
        print(f"Error navigating to starting point {point_name}: {e}")
        return False 