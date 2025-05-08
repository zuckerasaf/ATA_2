import json
import os
import sys
import random
import string


# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

from src.utils.test import Test
from src.utils.event_mouse_keyboard import Event

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
