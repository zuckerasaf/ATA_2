"""
Test class for storing test-related data including events, configuration, and comments.
"""

import os
import json
from datetime import datetime
from typing import List
from src.utils.event_mouse_keyboard import Event
from src.utils.config import Config

class CompactJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles base64 image data in a compact way."""
    def default(self, obj):
        return super().default(obj)
    
    def encode(self, obj):
        if isinstance(obj, dict):
            # For dictionaries, handle image_data specially
            if 'image_data' in obj:
                # Replace long base64 string with a placeholder
                obj['image_data'] = f"[BASE64_IMAGE_DATA_LENGTH={len(obj['image_data'])}]"
            # Recursively encode all values
            return '{' + ','.join(f'{self.encode(k)}:{self.encode(v)}' for k, v in obj.items()) + '}'
        elif isinstance(obj, list):
            # For lists, recursively encode all items
            return '[' + ','.join(self.encode(item) for item in obj) + ']'
        else:
            return super().encode(obj)

class Test:
    def __init__(self, config: str = "", comment1: str = "", comment2: str = "", accuracy_level: int = 5, starting_point: str = "none", numOfSteps: int = 0, stepResult: list = None, total_time_in_screenshot_dialog: int = 0):
        """
        Initialize a new Test instance.
        
        Args:
            config (str): Configuration string for the test
            comment1 (str): First comment for the test
            comment2 (str): Second comment for the test
            accuracy_level (int): Accuracy level between 1-10 (default: 5)
            starting_point (str): Starting point for the test (default: "none")
            numOfSteps (int): Number of steps in the test (default: 0)
            stepResult (list): List to store step results (default: empty list)
        """
        self.events: List[Event] = []
        self.config = config
        self.comment1 = comment1
        self.comment2 = comment2
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.numOfSteps = numOfSteps
        self.stepResult = stepResult if stepResult is not None else []
        self.total_time_in_screenshot_dialog = total_time_in_screenshot_dialog
        
        # Validate and set accuracy level
        if not isinstance(accuracy_level, int) or accuracy_level < 1 or accuracy_level > 10:
            raise ValueError("Accuracy level must be an integer between 1 and 10")
        self.accuracy_level = accuracy_level
        
        # Read valid starting points from config.json
        config = Config()
        valid_starting_points = config.get('startingPoint', ["none", "desktop", "point_A", "point_B", "point_C"])
        if starting_point not in valid_starting_points:
            raise ValueError(f"Starting point must be one of: {valid_starting_points}")
        self.starting_point = starting_point
    
    def add_event(self, event: Event) -> None:
        """
        Add an event to the test's event list.
        
        Args:
            event (Event): The event to add
        """
        self.events.append(event)
    
    def get_events(self) -> List[Event]:
        """
        Get all events in the test.
        
        Returns:
            List[Event]: List of all events
        """
        return self.events
    
    def clear_events(self) -> None:
        """Clear all events from the test."""
        self.events.clear()
    
    def set_test_config(self, config: str) -> None:
        """
        Set the configuration string.
        
        Args:
            config (str): The configuration string to set
        """
        self.config = config
    
    def get_test_config(self) -> str:
        """
        Get the configuration string.
        
        Returns:
            str: The current configuration string
        """
        return self.config
    
    def set_test_comments(self, comment1: str, comment2: str) -> None:
        """
        Set both comments.
        
        Args:
            comment1 (str): First comment
            comment2 (str): Second comment
        """
        self.comment1 = comment1
        self.comment2 = comment2
    
    def get_test_comments(self) -> tuple:
        """
        Get both comments.
        
        Returns:
            tuple: (comment1, comment2)
        """
        return (self.comment1, self.comment2)
        
    def set_accuracy_level(self, level: int) -> None:
        """
        Set the accuracy level.
        
        Args:
            level (int): Accuracy level between 1-10
            
        Raises:
            ValueError: If level is not between 1 and 10
        """
        if not isinstance(level, int) or level < 1 or level > 10:
            raise ValueError("Accuracy level must be an integer between 1 and 10")
        self.accuracy_level = level
        
    def get_accuracy_level(self) -> int:
        """
        Get the accuracy level.
        
        Returns:
            int: Current accuracy level (1-10)
        """
        return self.accuracy_level
        
    def set_starting_point(self, point: str) -> None:
        """
        Set the starting point.
        
        Args:
            point (str): Starting point for the test
            
        Raises:
            ValueError: If point is not a valid starting point
        """
        # Read valid starting points from config.json
        config = Config()
        valid_starting_points = config.get('startingPoint', ["none", "desktop", "point_A", "point_B", "point_C"])
        if point not in valid_starting_points:
            raise ValueError(f"Starting point must be one of: {valid_starting_points}")
        self.starting_point = point
        
    def get_starting_point(self) -> str:
        """
        Get the starting point.
        
        Returns:
            str: Current starting point
        """
        return self.starting_point
    
    def to_dict(self) -> dict:
        """
        Convert the test to a dictionary format.
        
        Returns:
            dict: Dictionary representation of the test
        """
        return {
            'events': [event.to_dict() for event in self.events],
            'config': self.config,
            'comment1': self.comment1,
            'comment2': self.comment2,
            'timestamp': self.timestamp,
            'accuracy_level': self.accuracy_level,
            'starting_point': self.starting_point,
            'numOfSteps': self.numOfSteps,
            'stepResult': self.stepResult,
            'total_time_in_screenshot_dialog': self.total_time_in_screenshot_dialog
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Test':
        """
        Create a Test instance from a dictionary.
        
        Args:
            data (dict): Dictionary containing test data
            
        Returns:
            Test: New Test instance
        """
        test = cls(
            config=data.get('config', ''),
            comment1=data.get('comment1', ''),
            comment2=data.get('comment2', ''),
            accuracy_level=data.get('accuracy_level', 5),
            starting_point=data.get('starting_point', 'none'),
            numOfSteps=data.get('numOfSteps', 0),
            stepResult=data.get('stepResult', []),
            total_time_in_screenshot_dialog=data.get('total_time_in_screenshot_dialog', 0)
        )
        
        # Reconstruct events from dictionary data
        for event_data in data.get('events', []):
            event = Event(
                counter=event_data.get('counter', 0),
                time=event_data.get('time', 0),
                position=event_data.get('position', (0, 0)),
                event_type=event_data.get('event_type', ''),
                action=event_data.get('action', ''),
                priority=event_data.get('priority', 'medium'),
                step_on=event_data.get('step_on', '')
            )
            test.add_event(event)
        
        return test
    
    def save_to_file(self, db_path: str = "C:\\projectPython\\ATA_V2\\DB") -> str:
        """
        Save the test data to a JSON file in the specified directory.
        
        Args:
            db_path (str): Path to the database directory
            
        Returns:
            str: Path to the saved file
        """
        # Create DB directory if it doesn't exist
        os.makedirs(db_path, exist_ok=True)
        
        # Create filename with timestamp
        filename = f"test_{self.timestamp}.json"
        filepath = os.path.join(db_path, filename)
        
        # Convert test to dictionary and save to file using custom encoder
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=4, cls=CompactJSONEncoder)
            
        return filepath 