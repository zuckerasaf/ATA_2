"""
Utility module for handling pictures and screenshots.
"""

import os
from PIL import ImageGrab
from src.utils.config import Config

config = Config()

# Define project root path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

def capture_screen():
    """
    Capture the screen based on Print Screen window configuration.
    
    Returns:
        PIL.Image: The captured screenshot, or None if capture fails
    """
    try:
        # Get Print Screen window configuration
        width, height = config.get_Print_Screen_window_size()
        x, y = config.get_Print_Screen_window_position()
        
        # Capture the screen with configured dimensions and position
        screenshot = ImageGrab.grab(bbox=(x, y, x + width, y + height))
        
        return screenshot
    except Exception as e:
        print(f"Error capturing screenshot: {e}")
        return None

def generate_screenshot_filename(test_name, counter, image_name,state,result_folder_path):
    """
    Generate a filename for a screenshot using the test name and counter.
    
    Args:
        test_name (str): Name of the test
        counter (int): Screenshot counter number
        
    Returns:
        tuple: (filename, full_path) or (None, None) if generation fails
    """
    try:
        if not test_name:
            print("No test name provided to generate screenshot filename")
            return None, None
            
        # Get paths from config
        paths_config = config.get('paths', {})
        db_path = paths_config.get('db_path', os.path.join(project_root, "DB")) 
        if state == "Recording":
            test_path = paths_config.get('test_path', "Test")
            # Create full path in test directory
            test_dir = os.path.join(db_path, test_path, test_name)
             # Generate screenshot filename
            screenshot_filename = f"{test_name}_{image_name}_screenshot_{counter:03d}.jpg"
        else:
             # Generate screenshot filename and path in result folder
            test_dir = result_folder_path
            screenshot_filename=f"Result_{test_name}_screenshot_{counter:03d}.jpg"   

        screenshot_path = os.path.join(test_dir, screenshot_filename)
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
        
        return screenshot_filename, screenshot_path
    except Exception as e:
        print(f"Error generating screenshot filename: {e}")
        return None, None

