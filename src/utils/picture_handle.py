"""
Utility module for handling pictures and screenshots.
"""

import os
from PIL import ImageGrab, Image
import cv2
import numpy as np
from src.utils.config import Config
from datetime import datetime

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
            #screenshot_filename = f"{test_name}_{image_name}_screenshot_{counter:03d}.jpg"
            screenshot_filename = f"{test_name}_{image_name}_{counter:03d}.jpg"
        else:
             # Generate screenshot filename and path in result folder
            test_dir = result_folder_path
            #screenshot_filename=f"Result_{test_name}_screenshot_{counter:03d}.jpg"   
            screenshot_filename=f"{test_name}_{image_name}_Result_{counter:03d}.jpg"   

        screenshot_path = os.path.join(test_dir, screenshot_filename)
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
        
        return screenshot_filename, screenshot_path
    except Exception as e:
        print(f"Error generating screenshot filename: {e}")
        return None, None

def compare_images(source, target, result_folder):
    
    """
    Compare two images and highlight differences based on tolerance.
    
    Args:
        source (str): Path to the source image
        target (str): Path to the target image
        result_folder (str): Folder to save the result image
        
    Returns:
        tuple: (match_percentage, result_image_path)
    """
    config = Config()
    image_compare_config = config.get('Image_compare', {})
    tolerance = image_compare_config.get('tolerance', 0.95)
    position_tolerance = image_compare_config.get('position_tolerance', 10)
    debug = image_compare_config.get('debug', True)
    source_name = os.path.basename(source).split(".")[0]
    target_name = os.path.basename(target).split(".")[0]


   
    try:
        # Read images
        source_img = cv2.imread(source)
        target_img = cv2.imread(target)
        
        if source_img is None or target_img is None:
            print("Error: Could not read one or both images")
            return 0, None
        
        
            
        # Ensure both images are the same size
        if source_img.shape != target_img.shape:
            target_img = cv2.resize(target_img, (source_img.shape[1], source_img.shape[0]))
        
        # Convert images to grayscale
        source_gray = cv2.cvtColor(source_img, cv2.COLOR_BGR2GRAY)
        target_gray = cv2.cvtColor(target_img, cv2.COLOR_BGR2GRAY)

        found, offset_x, offset_y, match_confidence = find_image_offset(source_gray, target_gray, result_folder)
        
        # Save grayscale images for debugging if requested
        if debug:
            # Save source grayscale image
            source_gray_path = os.path.join(result_folder, source_name+"_gray.jpg")
            cv2.imwrite(source_gray_path, source_gray)
            print(f"Saved source grayscale image to: {source_gray_path}")
            
            # Save target grayscale image
            target_gray_path = os.path.join(result_folder, target_name+"_gray.jpg")
            cv2.imwrite(target_gray_path, target_gray)
            print(f"Saved target grayscale image to: {target_gray_path}")
        
        # Calculate absolute difference
        diff = cv2.absdiff(source_gray, target_gray)
        

        
        # Save difference image for debugging if requested
        if debug:
            # Calculate and print pixel statistics
            total_pixels = diff.shape[0] * diff.shape[1]
            non_zero_pixels = cv2.countNonZero(diff)
            print(f"Total pixels in image: {total_pixels}")
            print(f"Number of non-zero pixels (differences): {non_zero_pixels}")
            print(f"Percentage of different pixels: {(non_zero_pixels/total_pixels)*100:.2f}%")
            diff_path = os.path.join(result_folder,target_name+"_diff.jpg")
            cv2.imwrite(diff_path, diff)
            print(f"Saved difference image to: {diff_path}")
        
        # # Apply position tolerance if specified
        # if position_tolerance > 0:
        #     # Create a copy of the difference image
        #     diff_with_tolerance = diff.copy()
            
        #     # Get image dimensions
        #     height, width = diff.shape
            
        #     # For each pixel in the difference image
        #     for y in range(height):
        #         for x in range(width):
        #             # If this pixel has a difference
        #             if diff[y, x] > tolerance:
        #                 # Check surrounding pixels within the tolerance radius
        #                 match_found = False
                        
        #                 # Define search boundaries
        #                 y_start = max(0, y - position_tolerance)
        #                 y_end = min(height, y + position_tolerance + 1)
        #                 x_start = max(0, x - position_tolerance)
        #                 x_end = min(width, x + position_tolerance + 1)
                        
        #                 # Search for a matching pixel in the neighborhood
        #                 for ny in range(y_start, y_end):
        #                     for nx in range(x_start, x_end):
        #                         # Skip the original pixel
        #                         if ny == y and nx == x:
        #                             continue
                                    
        #                         # Calculate the difference at this position
        #                         pixel_diff = abs(int(source_gray[y, x]) - int(target_gray[ny, nx]))
                                
        #                         # If we found a match within tolerance
        #                         if pixel_diff <= tolerance:
        #                             match_found = True
        #                             break
                            
        #                     if match_found:
        #                         break
                        
        #                 # If a match was found, set the difference to 0
        #                 if match_found:
        #                     diff_with_tolerance[y, x] = 0
            
        #     # Use the new difference image with position tolerance
        #     diff = diff_with_tolerance
            
            
            
        #     # Save difference with tolerance image for debugging if requested
        #     if debug:
        #         # Calculate and print pixel statistics after position tolerance
        #         non_zero_pixels_after_tolerance = cv2.countNonZero(diff)
        #         print(f"Number of non-zero pixels after position tolerance: {non_zero_pixels_after_tolerance}")
        #         print(f"Percentage of different pixels after tolerance: {(non_zero_pixels_after_tolerance/total_pixels)*100:.2f}%")
        #         diff_tolerance_path = os.path.join(result_folder, "debug_diff_with_tolerance.jpg")
        #         cv2.imwrite(diff_tolerance_path, diff)
        #         print(f"Saved difference with tolerance image to: {diff_tolerance_path}")
        
        # Apply threshold based on tolerance
        _, thresh = cv2.threshold(diff, tolerance, 255, cv2.THRESH_BINARY)
        
        # Save threshold image for debugging if requested
        if debug:
            thresh_path = os.path.join(result_folder, target_name+"_thresh.jpg")
            non_zero_pixels = cv2.countNonZero(thresh)
            print(f"Number of non-zero pixels (differences) with {tolerance}: {non_zero_pixels}")
            print(f"Percentage of different pixels: {(non_zero_pixels/total_pixels)*100:.2f}%")
            cv2.imwrite(thresh_path, thresh)
            print(f"Saved threshold image to: {thresh_path}")
        
        # Find contours of differences
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Create a mask for differences
        mask = np.zeros_like(source_img)
        cv2.drawContours(mask, contours, -1, (0, 0, 255), -1)  # Red color for differences
        
        # Create result image (only showing differences)
        result = cv2.bitwise_and(source_img, mask)
        
        # Calculate match percentage
        total_pixels = source_img.shape[0] * source_img.shape[1]
        diff_pixels = cv2.countNonZero(thresh)
        match_percentage = ((total_pixels - diff_pixels) / total_pixels) * 100
        print(f"Match percentage: {match_percentage}")
        
        # Generate result filename
        #result_dif_filename = "diff_"+ os.path.basename(target).split(".")[0]+"_"+os.path.basename(source).split(".")[0]+".jpg"
        result_dif_filename = target_name+"diff_.jpg"
        result_dif_path = os.path.join(result_folder, result_dif_filename)
        
        # Save result image
        cv2.imwrite(result_dif_path, result)
        
        return match_percentage, result_dif_path
        
    except Exception as e:
        print(f"Error comparing images: {e}")
        return 0, None

def find_image_offset(source_gray, target_gray, result_folder=None, debug=False):
    """
    Find if target image exists within source image and calculate its offset.
    
    Args:
        source_gray (numpy.ndarray): Grayscale source image
        target_gray (numpy.ndarray): Grayscale target image to find
        result_folder (str, optional): Folder to save debug visualization
        debug (bool): If True, saves visualization of the match
        
    Returns:
        tuple: (found, offset_x, offset_y, match_confidence)
            - found (bool): True if target was found in source
            - offset_x (int): X coordinate of the match
            - offset_y (int): Y coordinate of the match
            - match_confidence (float): Confidence of the match (0-1)
    """
    try:
        # Trim 10 pixels from each edge of the target image
        h, w = target_gray.shape
        if h > 20 and w > 20:  # Only trim if image is large enough
            target_gray = target_gray[10:h-10, 10:w-10]
            print(f"Trimmed target image to shape: {target_gray.shape}")
        
        # Perform template matching
        result = cv2.matchTemplate(source_gray, target_gray, cv2.TM_CCOEFF_NORMED)
        
        # Get the best match location
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        # Get dimensions of trimmed target
        h, w = target_gray.shape
        
        # Calculate match confidence
        match_confidence = max_val
        
        # Define threshold for considering it a match (adjust as needed)
        threshold = config.get('Image_compare', {}).get('threshold', 0.8)
        debug = config.get('Image_compare', {}).get('debug', True)
        
        if match_confidence >= threshold:
            # Get the offset coordinates (add 10 to account for the trimming)
            offset_x, offset_y = max_loc[0] + 10, max_loc[1] + 10
            
            if debug and result_folder:
                # Create a visualization
                debug_img = source_gray.copy()
                # Draw rectangle around the match (add 10 to account for the trimming)
                cv2.rectangle(debug_img, 
                            (max_loc[0] + 10, max_loc[1] + 10), 
                            (max_loc[0] + w + 10, max_loc[1] + h + 10), 
                            (0, 255, 0), 2)
                # Add text showing offset and confidence
                text = f"Offset: ({offset_x}, {offset_y}), Confidence: {match_confidence:.2f}"
                cv2.putText(debug_img, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                # Save debug visualization
                debug_path = os.path.join(result_folder, "debug_match.jpg")
                cv2.imwrite(debug_path, debug_img)
                print(f"Saved match visualization to: {debug_path}")
            
            print(f"Target image found in source image!")
            print(f"Offset: ({offset_x}, {offset_y})")
            print(f"Match confidence: {match_confidence:.2f}")
            return True, offset_x, offset_y, match_confidence
            
        else:
            print("Target image not found in source image")
            print(f"Best match confidence: {match_confidence:.2f}")
            return False, 0, 0, match_confidence
            
    except Exception as e:
        print(f"Error finding image offset: {e}")
        return False, 0, 0, 0.0

