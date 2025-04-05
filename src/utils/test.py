"""
Test class for storing test-related data including events, configuration, and comments.
"""

import os
import json
from datetime import datetime
from typing import List
from src.utils.event_mouse_keyboard import Event

class Test:
    def __init__(self, config: str = "", comment1: str = "", comment2: str = ""):
        """
        Initialize a new Test instance.
        
        Args:
            config (str): Configuration string for the test
            comment1 (str): First comment for the test
            comment2 (str): Second comment for the test
        """
        self.events: List[Event] = []
        self.config = config
        self.comment1 = comment1
        self.comment2 = comment2
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
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
    
    def to_dict(self) -> dict:
        """
        Convert the test to a dictionary format.
        
        Returns:
            dict: Dictionary representation of the test
        """
        return {
            'events': [event.__dict__ for event in self.events],
            'config': self.config,
            'comment1': self.comment1,
            'comment2': self.comment2,
            'timestamp': self.timestamp
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
            comment2=data.get('comment2', '')
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
        
        # Convert test to dictionary and save to file
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=4)
            
        return filepath 