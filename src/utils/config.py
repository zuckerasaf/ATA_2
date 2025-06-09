"""
Configuration utility for managing application settings.
"""

import json
import os
from typing import Dict, Any
import sys

class Config:
    _instance = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._config:
            self._load_config()
    
    def _load_config(self):
        """
        Load the document configuration from config.json.
        
        This function reads the configuration file that contains application settings.
        
       
                dict: The configuration data containing:
                    - keyboard: Keyboard settings
                    - mouse: Mouse settings
                    - event: Event settings
                    - paths: Path settings
                    - Image_compare: Image compare settings
                    - Control_Panel: Control Panel settings
                    - startingPoint: Starting point for tests
                    - Test_Name_Dialog: Test Name Dialog settings
                    - track_mouse_scroll: Mouse scroll tracking settings
                    - Test_Name_Dialog: Test Name Dialog settings
                    - track_mouse_scroll: Mouse scroll tracking settings
                    - Test_Name_Dialog: Test Name Dialog settings

        """
        if getattr(sys, 'frozen', False):
            # Running as a PyInstaller bundle
            base_path = os.path.dirname(sys.executable)
            #base_path = sys._MEIPASS
            config_path = os.path.join(base_path, 'config.json')
        else:
            base_path = os.path.dirname(__file__)
            config_path = os.path.join(base_path, 'config.json')
        try:
            with open(config_path, 'r') as f:
                self._config = json.load(f)
        except FileNotFoundError:
            print(f"Warning: Config file not found at {config_path}")
            self._config = {}
        except json.JSONDecodeError:
            print(f"Warning: Invalid JSON in config file at {config_path}")
            self._config = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation."""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
                
        return value
    
    def get_keyboard_quit_key(self) -> str:
        """Get the configured quit key."""
        return self.get('keyboard.quit_key', 'q')
    
    def get_special_keys(self) -> list:
        """Get the list of special keys to track."""
        return self.get('keyboard.special_keys', [])
    
    def get_print_screen_key(self) -> str:
        """Get the configured print screen key."""
        return self.get('keyboard.print_screen_key', 'print_screen')
    
    def get_Event_Monitor_window_title(self) -> str:
        """Get the window title."""
        return self.get('Event_Monitor_window.title', 'Event Monitor')
    
    def get_Event_Monitor_window_size(self) -> tuple:
        """Get the window size as (width, height)."""
        width = self.get('Event_Monitor_window.width', 800)
        height = self.get('Event_Monitor_window.height', 50)
        return (width, height)
    
    def get_Event_Monitor_window_opacity(self) -> float:
        """Get the window opacity."""
        return self.get('Event_Monitor_window.opacity', 0.8)
    
    def get_Event_Monitor_window_position(self) -> tuple:
        """Get the window position as (x, y)."""
        pos = self.get('Event_Monitor_window.position', {'x': 10, 'y': 10})
        return (pos.get('x', 10), pos.get('y', 10))
    
    def get_event_priority(self) -> str:
        """Get the event priority level."""
        return self.get('event.priority', 'medium')
    
    def get_step_prefix(self) -> str:
        """Get the step prefix for event steps."""
        return self.get('event.step_prefix', 'Step')
    
    def should_track_mouse_press(self) -> bool:
        """Check if mouse press events should be tracked."""
        return self.get('mouse.track_press', True)
    
    def should_track_mouse_release(self) -> bool:
        """Check if mouse release events should be tracked."""
        return self.get('mouse.track_release', True)
        
    def get_Print_Screen_window_size(self) -> tuple:
        """Get the Print Screen window size as (width, height)."""
        width = self.get('Print_Screen_window.PSW_width', 600)
        height = self.get('Print_Screen_window.PSW_height', 600)
        return (width, height)
    
    def get_Print_Screen_window_position(self) -> tuple:
        """Get the Print Screen window position as (x, y)."""
        pos = self.get('Print_Screen_window.PSW_position', {'PSW_x': 10, 'PSW_y': 10})
        return (pos.get('PSW_x', 10), pos.get('PSW_y', 10))
        
    def get_Control_Panel_config(self) -> dict:
        """Get the Control Panel configuration."""
        return self.get('Control_Panel', {
            'title': 'Test Control Panel',
            'width': 1000,
            'height': 600,
            'position': {
                'x': 100,
                'y': 100
            }
        })
        
    def get_starting_point(self) -> str:
        """Get the configured starting point for tests."""
        return self.get('startingPoint', 'none')
        
    def get_Test_Name_Dialog_config(self) -> dict:
        """Get the Test Name Dialog configuration."""
        return self.get('Test_Name_Dialog', {
            'title': 'New Test Configuration',
            'width': 400,
            'height': 500,
            'position': {
                'x': 200,
                'y': 200
            }
        }) 
    
    def get_track_drag_threshold(self) -> int:
        """Get the track drag threshold."""
        return self.get('mouse.track_drag_threshold', 5)
    
    def should_track_mouse_scroll(self):
        """Check if mouse scroll events should be tracked."""
        return self.get('track_mouse_scroll', True)  # Default to True if not specified
    
    def get_scroll_sensitivity(self) -> float:
        """Get the mouse scroll sensitivity factor."""
        return self.get('mouse.scroll_sensitivity', 0.1)  # Default to 0.1 if not specified
    
    def get_run_log_path(self) -> str:
        """Get the run log path."""
        return self.get('paths.run_log_path', 'run_log.txt')
    
    def get_Image_compare_config(self) -> dict:
        """Get the Image compare configuration."""
        return self.get('Image_compare', {
            'position_tolerance': 0,
            'tolerance': 0,
            'debug': True,
            'threshold': 0.8,
            'frame_threshold': 20
        })
    
    def get_invalid_chars(self) -> str:
        """Get the invalid characters."""
        return self.get('keyboard.invalid_chars', '<>:\"/\\|?*')
    
    def get_comment_screen_key(self) -> str:
        """Get the comment screen key."""
        return self.get('keyboard.comment_screen_key', 'f3')
    
    def get_Comment_Panel_config(self) -> dict:
        """Get the Comment Panel configuration."""
        width = self.get('Comment_Panel.CSW_width', 600)
        height = self.get('Comment_Panel.CSW_height', 200)
        position = self.get('Comment_Panel.CSW_position', {'x': 20, 'y': 20})
        return (width, height, position)

    
