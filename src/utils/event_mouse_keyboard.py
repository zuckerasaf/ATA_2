"""
Event class for storing mouse and keyboard events.
"""

class Event:
    # Priority levels
    PRIORITY_HIGH = "high"
    PRIORITY_MEDIUM = "medium"
    PRIORITY_LOW = "low"
    
    def __init__(self, counter: int, time: int, position: tuple, event_type: str, 
                 action: str, priority: str = PRIORITY_MEDIUM, step_on: str = "",
                 time_from_last: int = 0, step_desc: str = "none", 
                 step_accep: str = "none", step_resau: str = "none", 
                 pic: str = "none"):
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
            pic (str): Path to associated picture
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
        self.pic = pic
    
    def __str__(self) -> str:
        """String representation of the Event."""
        return f"Event(counter={self.counter}, time={self.time}, position={self.position}, " \
               f"type='{self.event_type}', action='{self.action}', priority={self.priority}, " \
               f"step_on='{self.step_on}', time_from_last={self.time_from_last}, " \
               f"step_desc='{self.step_desc}', step_accep='{self.step_accep}', " \
               f"step_resau='{self.step_resau}', pic='{self.pic}')"
    
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
            'pic': self.pic
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
            step_resau=data['step_resau'],
            pic=data['pic']
        )
    
    def get_priority_text(self) -> str:
        """Get the text representation of the priority level."""
        priority_map = {
            self.PRIORITY_HIGH: "High",
            self.PRIORITY_MEDIUM: "Medium",
            self.PRIORITY_LOW: "Low"
        }
        return priority_map.get(self.priority, "Unknown") 