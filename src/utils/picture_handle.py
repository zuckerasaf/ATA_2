"""
Utility module for handling pictures and screenshots in the ATA testing framework.

This module provides functionality for:
- Capturing screenshots of specific screen regions
- Generating and managing screenshot filenames
- Comparing images with tolerance and position matching
- Finding image offsets and matches
- Saving screenshots to disk

The module uses OpenCV for image processing and PIL for screenshot capture.
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

def capture_screen(x, y, width, height):
    """
    Capture a screenshot of a specific region of the screen.
    
    This function captures a rectangular region of the screen based on the provided
    coordinates and dimensions. It uses PIL's ImageGrab for the actual capture.
    
    Args:
        x (int): X-coordinate of the top-left corner
        y (int): Y-coordinate of the top-left corner
        width (int): Width of the capture region
        height (int): Height of the capture region
    
    Returns:
        PIL.Image: The captured screenshot, or None if capture fails
    """
    try:
        # Capture the screen with configured dimensions and position
        screenshot = ImageGrab.grab(bbox=(x, y, x + width, y + height))
        
        return screenshot
    except Exception as e:
        print(f"Error capturing screenshot: {e}")
        return None

def generate_screenshot_filename(test_name, counter, image_name, state, result_folder_path):
    """
    Generate a filename for a screenshot based on test context and state.
    
    This function creates appropriate filenames for screenshots based on whether
    they are being taken during test recording or result comparison. It handles
    both test and result directory structures.
    
    Args:
        test_name (str): Name of the test
        counter (int): Screenshot counter number
        image_name (str): Name to use for the image
        state (str): Current state ("Recording" or "Result")
        result_folder_path (str): Path to the result folder when in result state
        
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
            screenshot_filename = f"{test_name}_{image_name}.jpg"
        else:
            # Generate screenshot filename and path in result folder
            test_dir = result_folder_path
            screenshot_filename = f"{image_name.split('.')[0]}_Result.jpg"   

        screenshot_path = os.path.join(test_dir, screenshot_filename)
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
        
        return screenshot_filename, screenshot_path
    except Exception as e:
        print(f"Error generating screenshot filename: {e}")
        return None, None

def compare_images(source, target, result_folder):
    """
    Compare two images and generate a visual difference map.
    
    This function performs a detailed comparison between source and target images,
    including:
    - Position matching with tolerance
    - Pixel-by-pixel difference analysis
    - Generation of difference visualization
    - Debug output if enabled
    
    The comparison uses configurable tolerances for both position and pixel matching.
    
    Args:
        source (str): Path to the source (reference) image
        target (str): Path to the target (test) image
        result_folder (str): Folder to save comparison results and debug images
        
    Returns:
        tuple: (match_percentage, result_image_path)
            - match_percentage (int): Percentage of matching pixels (0-100)
            - result_image_path (str): Path to the generated difference image
    """
    config = Config()
    image_compare_config = config.get('Image_compare', {})
    tolerance = image_compare_config.get('tolerance', 0.95)
    position_tolerance = image_compare_config.get('position_tolerance', 10)
    debug = image_compare_config.get('debug', True)
    source_name = os.path.basename(source).split(".")[0]
    target_name = os.path.basename(target).split(".")[0]

    # Create debug log file if in debug mode
    debug_log = None
    if debug:
        debug_log_path = os.path.join(result_folder, f"{target_name}_debug_log.txt")
        debug_log = open(debug_log_path, 'w', encoding='utf-8')
        # Write header with timestamp
        debug_log.write(f"\n Debug Log for {target_name}\n")
        debug_log.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        debug_log.write("="*50 + "\n\n")

    def debug_print(*args, **kwargs):
        """Helper function to print to both console and debug log"""
        print(*args, **kwargs)
        if debug and debug_log:
            debug_log.write(" ".join(str(arg) for arg in args) + "\n")

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

        
        found, offset_x, offset_y, w, h, match_confidence, matched_region = find_image_offset(source_gray, target_gray, result_folder, debug, target_name)
        
        if found:
            #cut the source image to the size of the matched region 
            source_gray = source_gray[offset_y:offset_y+h, offset_x:offset_x+w]
            #cut the target image to the size of config.get_Image_compare_config().get('frame_threshold')
            cut_threshold = config.get_Image_compare_config().get('frame_threshold')
            target_gray = target_gray[cut_threshold:cut_threshold+h, cut_threshold:cut_threshold+w]
            
        if debug:
            # present the trimed source and trimed  grayscale image
            source_trimed_path = os.path.join(result_folder, target_name +"_trimmed_source.jpg")
            cv2.imwrite(source_trimed_path, source_gray)
            print(f"Saved matched region to: {source_trimed_path}")
                
            target_trimmed_path = os.path.join(result_folder, target_name +"_trimmed_target.jpg")
            cv2.imwrite(target_trimmed_path, target_gray)
            print(f"Saved trimmed target to: {target_trimmed_path}")
        
        # Calculate absolute difference
        diff = cv2.absdiff(source_gray, target_gray)
        
        # Save difference image for debugging if requested
        if debug:
            # Calculate and print pixel statistics
            total_pixels = diff.shape[0] * diff.shape[1]
            non_zero_pixels = cv2.countNonZero(diff)
            debug_print(f"Total pixels in image: {total_pixels} in {target_name}")
            debug_print(f"According to Diff Number of non-zero pixels (differences) between {target_name} and {source_name}: {non_zero_pixels}")
            debug_print(f"Percentage of different pixels: {(non_zero_pixels/total_pixels)*100:.2f}%")
            print(f"Total pixels in image: {total_pixels} in {target_name}")
            print(f" According to Diff Number of non-zero pixels (differences) between {target_name} and {source_name}: {non_zero_pixels}")
            print(f"Thresh Percentage of different pixels: {(non_zero_pixels/total_pixels)*100:.2f}%")
            diff_path = os.path.join(result_folder,target_name+"_diff.jpg")
            cv2.imwrite(diff_path, diff)
            print(f"Saved difference image to: {diff_path}")
        
        tolerance = config.get('Image_compare', {}).get('tolerance', 10)
        _, thresh = cv2.threshold(diff, tolerance, 255, cv2.THRESH_BINARY)
        
        # Save threshold image for debugging if requested
        if debug:
            thresh_path = os.path.join(result_folder, target_name+"_thresh.jpg")
            non_zero_pixels = cv2.countNonZero(thresh)
            debug_print(f"according to Thresh Number of non-zero pixels (differences) with {tolerance}: {non_zero_pixels}")
            debug_print(f"Thresh Percentage of different pixels: {(non_zero_pixels/total_pixels)*100:.2f}% ")
            print(f"according to Thresh Number of non-zero pixels (differences) with {tolerance}: {non_zero_pixels}")
            print(f"Percentage of different pixels: {(non_zero_pixels/total_pixels)*100:.2f}%")
            cv2.imwrite(thresh_path, thresh)
            print(f"Saved threshold image to: {thresh_path}")
        
        # # Find contours of differences
        # contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # # Create a mask for differences
        # mask = np.zeros_like(source_gray)
        # cv2.drawContours(mask, contours, -1, (0, 0, 255), -1)  # Red color for differences
        
        # # Create result image (only showing differences)
        # result = cv2.bitwise_and(source_gray, mask)
        
        # Calculate match percentage
        total_pixels = source_gray.size
        diff_pixels = cv2.countNonZero(thresh)
        match_percentage = ((total_pixels - diff_pixels) / total_pixels) * 100
        debug_print(f"Match percentage: {match_percentage}")
        
        # Generate result filename
        result_dif_filename = target_name+"_diffrence.jpg"
        result_dif_path = os.path.join(result_folder, result_dif_filename)
        
        # Save result image
        cv2.imwrite(result_dif_path, thresh)
        
        return int(match_percentage), result_dif_path
        
    except Exception as e:
        print(f"Error comparing images: {e}")
        return 0, None
    finally:
        # Close debug log file if it was opened
        if debug_log:
            debug_log.close()

def find_image_offset(source_gray, target_gray, result_folder=None, debug=False, target_name=None):
    """
    Find if target image exists within source image and calculate its offset.
    
    This function uses template matching to find if the target image exists within
    the source image, accounting for potential position differences. It includes:
    - Edge trimming to improve matching
    - Confidence scoring
    - Debug visualization
    - Position offset calculation
    - Extraction of matching region from source image
    
    Args:
        source_gray (numpy.ndarray): Grayscale source image
        target_gray (numpy.ndarray): Grayscale target image to find
        result_folder (str, optional): Folder to save debug visualization
        debug (bool): If True, saves visualization of the match
        target_name (str, optional): Name of the target image for debug files
        
    Returns:
        tuple: (found, offset_x, offset_y, match_confidence, matched_region)
            - found (bool): True if target was found in source
            - offset_x (int): X coordinate of the match
            - offset_y (int): Y coordinate of the match
            - match_confidence (float): Confidence of the match (0-1)
            - matched_region (numpy.ndarray): The region from source image that matches the trimmed target
    """
    try:
        # Trim 10 pixels from each edge of the target image
        h, w = target_gray.shape
        frame_threshold = config.get_Image_compare_config().get('frame_threshold')
        if h > frame_threshold *2 and w > frame_threshold *2:  # Only trim if image is large enough
            target_gray = target_gray[frame_threshold:h-frame_threshold, frame_threshold:w-frame_threshold]
            print(f"Trimmed target image to shape: {target_gray.shape}")
        
        # Perform template matching
        result = cv2.matchTemplate(source_gray, target_gray, cv2.TM_CCOEFF_NORMED)
        
        # Get the best match location
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        # Print detailed matching information
        print("\nTemplate Matching Results:")
        print(f"Max Value (Best Match Confidence): {max_val:.4f}")
        print(f"Max Location (Best Match Position): {max_loc}")
        print(f"Min Value (Worst Match): {min_val:.4f}")
        print(f"Min Location (Worst Match Position): {min_loc}")
        print(f"Result Matrix Shape: {result.shape}")
        print(f"Result Matrix Type: {result.dtype}")
        print(f"Result Matrix Range: [{result.min():.4f}, {result.max():.4f}]")
        
        # Get dimensions of trimmed target
        h, w = target_gray.shape
        
        # Calculate match confidence
        match_confidence = max_val
        
        # Define threshold for considering it a match (adjust as needed)
        threshold = config.get('Image_compare', {}).get('threshold', 0.8)
        debug = config.get('Image_compare', {}).get('debug', True)
        
        if match_confidence >= threshold:
            # Get the offset coordinates (add 10 to account for the trimming)
            offset_x, offset_y = max_loc[0] , max_loc[1] 
            
            # Extract the matching region from source image
            matched_region = source_gray[max_loc[1]:max_loc[1] + h, max_loc[0]:max_loc[0] + w]
            
            print("\nMatch Found!")
            print(f"Offset X: {offset_x}")
            print(f"Offset Y: {offset_y}")
            print(f"Match Confidence: {match_confidence:.4f}")
            print(f"Threshold: {threshold}")
            print(f"Matched Region Shape: {matched_region.shape}")
            
            if debug and result_folder:
                # Create a visualization
                debug_img = source_gray.copy()
                # Draw rectangle around the match (add 10 to account for the trimming)
                cv2.rectangle(debug_img, 
                            (max_loc[0] , max_loc[1]), 
                            (max_loc[0] + w , max_loc[1] + h ), 
                            (0, 255, 0), 2)
                # Add text showing offset and confidence
                text = f"Offset: ({offset_x}, {offset_y}), Confidence: {match_confidence:.2f}"
                cv2.putText(debug_img, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                # Save debug visualization
                offset_debug_path = os.path.join(result_folder, target_name +"_offest_in_source.jpg")
                cv2.imwrite(offset_debug_path, debug_img)
                print(f"Saved match visualization to: {offset_debug_path}")
                
                # # Save the matched region
                # source_triimed_path = os.path.join(result_folder, target_name +"_trimmed_source.jpg")
                # cv2.imwrite(source_triimed_path, matched_region)
                # print(f"Saved matched region to: {source_triimed_path}")
                
                # # Save the trimmed target for comparison
                # target_trimmed_path = os.path.join(result_folder, target_name +"_trimmed_target.jpg")
                # cv2.imwrite(target_trimmed_path, target_gray)
                # print(f"Saved trimmed target to: {target_trimmed_path}")
            
            return True, offset_x, offset_y, w, h, match_confidence, matched_region
            
        else:
            print("\nNo Match Found!")
            print(f"Best Match Confidence: {match_confidence:.4f}")
            print(f"Required Threshold: {threshold}")
            return False, 0, 0, 0, 0, match_confidence, None
            
    except Exception as e:
        print(f"Error finding image offset: {e}")
        return False, 0, 0, 0, 0, 0.0, None

def save_screenshot(screenshot, filepath: str) -> None:
    """
    Save a screenshot to disk.
    
    This function saves a PIL Image object to the specified filepath in JPEG format.
    
    Args:
        screenshot (PIL.Image): The screenshot to save
        filepath (str): The path where the screenshot should be saved
        
    Returns:
        str: The filepath where the screenshot was saved, or None if save fails
    """
    if screenshot:
        screenshot.save(filepath, 'JPEG')
        return filepath  # Update the pic_path field with the saved file path