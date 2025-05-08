"""
Event class for storing mouse and keyboard events.
"""

import base64
from io import BytesIO

class Event:
    # Priority levels
    PRIORITY_HIGH = "high"
    PRIORITY_MEDIUM = "medium"
    PRIORITY_LOW = "low"
    
    def __init__(self, counter: int, time: int, position: tuple, event_type: str, 
                 action: str, priority: str = PRIORITY_MEDIUM, step_on: str = "",
                 time_from_last: int = 0, step_desc: str = "none", 
                 step_accep: str = "none", step_resau: str = "none", step_resau_num: int = 0,
                 pic_path: str = "none", screenshot_counter: int = 0, image_name: str = "none"):
        """
        Initialize a new Event instance.
        
        Args:
            counter (int): Event counter
            time (int): Time since last event in milliseconds
            position (tuple): Mouse position (x, y)
            event_type (str): Type of event (e.g., "mouse_left", "keyboard")
            action (str): Description of the action
            priority (str): Event priority level
            step_on (str): Step number or identifier
            time_from_last (int): Time from last event in milliseconds
            step_desc (str): Description of what this step does
            step_accep (str): Expected outcome of the step
            step_resau (str): Actual result of the step
            step_resau_num (int): Numeric result value
            pic_path (str): Path to associated picture
            screenshot_counter (int): Counter for screenshots
            image_name (str): Name of the image
        """
        self.counter = counter
        self.time = time
        self.position = position
        self.event_type = event_type
        self.action = action
        self.priority = priority
        self.step_on = step_on
        self.time_from_last = time_from_last
        self.step_desc = step_desc
        self.step_accep = step_accep
        self.step_resau = step_resau
        self.step_resau_num = step_resau_num
        self.pic_path = pic_path
        self.screenshot_counter = screenshot_counter
        self.image_name = image_name


        
    #     # If we have a screenshot but no image_data, convert it
    #     if screenshot and not image_data:
    #         self._convert_screenshot_to_base64()
    
    # def _convert_screenshot_to_base64(self):
    #     """Convert PIL Image screenshot to base64 string."""
    #     if self.screenshot:
    #         # Convert PIL Image to bytes
    #         buffered = BytesIO()
    #         self.screenshot.save(buffered, format="JPEG")
    #         # Convert bytes to base64 string
    #         self.image_data = base64.b64encode(buffered.getvalue()).decode()
    
    def save_screenshot(self, filepath: str) -> None:
        """Save the screenshot to a file if it exists."""
        if self.screenshot:
            self.screenshot.save(filepath, 'JPEG')
            self.pic = filepath  # Update the pic field with the saved file path
            # Also store the image data
            # self._convert_screenshot_to_base64()
    
    def get_image_from_data(self):
        """Convert base64 image data back to PIL Image."""
        if self.image_data:
            from PIL import Image
            image_bytes = base64.b64decode(self.image_data)
            return Image.open(BytesIO(image_bytes))
        return None
    
    def __str__(self) -> str:
        """String representation of the Event."""
        return f"Event(counter={self.counter}, time={self.time}, position={self.position}, " \
               f"type='{self.event_type}', action='{self.action}', priority={self.priority}, " \
               f"step_on='{self.step_on}', time_from_last={self.time_from_last}, " \
               f"step_desc='{self.step_desc}', step_accep='{self.step_accep}', " \
               f"step_resau='{self.step_resau}', pic_path='{self.pic_path}', " \
               f"screenshot_counter={self.screenshot_counter}, image_name='{self.image_name}')"
    
    def __repr__(self) -> str:
        """Detailed string representation of the Event."""
        return self.__str__()
    
    def to_dict(self) -> dict:
        """Convert event to dictionary format."""
        return {
            'counter': self.counter,
            'time': self.time,
            'position': self.position,
            'type': self.event_type,
            'action': self.action,
            'priority': self.priority,
            'step_on': self.step_on,
            'time_from_last': self.time_from_last,
            'step_desc': self.step_desc,
            'step_accep': self.step_accep,
            'step_resau': self.step_resau,
            'step_resau_num': self.step_resau_num,
            'pic_path': self.pic_path,
            'screenshot_counter': self.screenshot_counter,
            'image_name': self.image_name
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Event':
        """Create an Event instance from a dictionary."""
        return cls(
            counter=data['counter'],
            time=data['time'],
            position=data['position'],
            event_type=data['type'],
            action=data['action'],
            priority=data['priority'],
            step_on=data['step_on'],
            time_from_last=data['time_from_last'],
            step_desc=data['step_desc'],
            step_accep=data['step_accep'],
            step_resau=data.get('step_resau', 'none'),
            step_resau_num=data.get('step_resau_num', 0),
            pic_path=data.get('pic_path', 'none'),
            screenshot_counter=data.get('screenshot_counter', 0),
            image_name=data.get('image_name', 'none')
        )