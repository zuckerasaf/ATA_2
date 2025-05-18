import json
import os
import sys
import random
import string
import whisper
import sounddevice as sd
import numpy as np
import wave
import tempfile
import shutil


# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

from src.utils.test import Test
from src.utils.event_mouse_keyboard import Event
from src.utils.config import Config

def speech_to_text(duration=5, sample_rate=16000, model_size="base"):
    """
    Record from microphone and convert speech to text using Whisper.
    
    Args:
        duration (int): Recording duration in seconds
        sample_rate (int): Audio sample rate
        model_size (str): Size of the model to use (tiny, base, small, medium, large)
        
    Returns:
        str: Transcribed text
    """
    try:
        print(f"Recording for {duration} seconds...")
        # Record audio
        recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1)
        sd.wait()  # Wait until recording is finished
        
        # Create a temporary WAV file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            with wave.open(temp_file.name, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 2 bytes per sample
                wf.setframerate(sample_rate)
                wf.writeframes((recording * 32767).astype(np.int16).tobytes())
            
            # Load the model
            model = whisper.load_model(model_size)
            
            # Transcribe the audio
            result = model.transcribe(temp_file.name)
            
            # Clean up the temporary file
            os.unlink(temp_file.name)
            
            return result["text"]
    except Exception as e:
        print(f"Error in speech to text conversion: {e}")
        return None

def generate_random_word():
    """Generate a random 5-letter word."""
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(5))

def display_test_data(file_path):
    test_summary = []
    test = create_test_from_json(file_path)
    
    if test is None:
        return [["Name1", ""]]
        
    try:
        num_of_events = len(test.stepResult)
        if num_of_events == 0:
            test_summary.append(["Name1", ""])
        else:
            for i in range(num_of_events):
                test_summary.append([test.stepResult[i][0], test.stepResult[i][1]])
    except:
        test_summary.append(["Name1", ""])
    return test_summary


def create_test_from_json(filepath):
    """Create a Test instance from a JSON file."""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        # Create Test instance with data from JSON
        test = Test(
            config=data.get('config', ''),
            comment1=data.get('comment1', ''),
            comment2=data.get('comment2', ''),
            accuracy_level=data.get('accuracy_level', '5'),
            starting_point=data.get('starting_point', ''),
            numOfSteps=data.get('numOfSteps', 0),
            stepResult=data.get('stepResult', [])   
        )
        
        # Add events from JSON
        for event_data in data.get('events', []):
            # Convert dictionary to Event object using from_dict
            event = Event.from_dict(event_data)
            test.add_event(event)
            
        return test
        
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {filepath}")
        return None
    except Exception as e:
        print(f"Error loading test data: {e}")
        return None
    
def update_images_to_test(result_folder_path):
    """
    Copy all image files from a result folder to the corresponding test folder.
    Only copies files ending with _Result.jpg and renames them by removing _Result.
    
    Args:
        result_folder_path: Path to the result folder (e.g., 'DB/Result/20250517_224058_paint')
    """
    try:
        # Get the result folder name
        result_folder_name = os.path.basename(result_folder_path)
        
        # Extract test name by removing timestamp (format: YYYYMMDD_HHMMSS_testname)
        parts = result_folder_name.split('_')
        if len(parts) >= 3:
            test_name = '_'.join(parts[2:])  # Join remaining parts in case test name contains underscores
        else:
            print(f"Invalid result folder name format: {result_folder_name}")
            return False
            
        # Get paths from config
        config = Config()
        paths_config = config.get('paths', {})
        db_path = paths_config.get('db_path', os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "DB"))
        test_path = paths_config.get('test_path', "Test")
        
        # Construct test folder path
        test_folder_path = os.path.join(db_path, test_path, test_name)
        
        # # Create test folder if it doesn't exist
        # os.makedirs(test_folder_path, exist_ok=True)
        
        # Find all _Result.jpg files
        result_files = [f for f in os.listdir(result_folder_path) if f.endswith('_Result.jpg')]
        
        if not result_files:
            print(f"No _Result.jpg files found in {result_folder_path}")
            return False
            
        # Copy and rename files
        copied_files = []
        for file in result_files:
            # Create new filename by removing _Result
            new_filename = file.replace('_Result.jpg', '.jpg')
            src_file = os.path.join(result_folder_path, file)
            dst_file = os.path.join(test_folder_path, new_filename)
            shutil.copy2(src_file, dst_file)
            copied_files.append(new_filename)
                
        if copied_files:
            print(f"Successfully copied {len(copied_files)} images to {test_folder_path}")
            print("Copied files:", copied_files)
            return True
        else:
            print(f"No _Result.jpg files found in {result_folder_path}")
            return False
            
    except Exception as e:
        print(f"Error copying images: {e}")
        return False
    
    
