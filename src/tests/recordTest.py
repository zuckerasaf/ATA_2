"""
Mouse click listener for creating Event objects.
"""

import os
import sys
import time
import threading
from pynput import mouse, keyboard
from datetime import datetime
import atexit
from PIL import ImageGrab
import json

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

from src.utils.event_mouse_keyboard import Event
from src.utils.event_window import EventWindow
from src.utils.config import Config
from src.utils.test import Test

LOCK_FILE = "cursor_listener.lock"
config = Config()

def cleanup():
    """Clean up function to remove lock file on exit."""
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except:
        pass

def is_already_running():
    """Check if another instance is already running."""
    if os.path.exists(LOCK_FILE):
        print("Another instance is already running!")
        print("If this is an error, manually delete the cursor_listener.lock file.")
        return True
    
    # Create lock file
    try:
        with open(LOCK_FILE, 'w') as f:
            f.write(str(os.getpid()))
        return False
    except:
        return True

def close_existing_mouse_threads():
    """Close any existing mouse listener threads."""
    try:
        for thread in threading.enumerate():
            if isinstance(thread, mouse.Listener):
                thread.stop()
    except Exception as e:
        print(f"Warning: Could not close existing threads: {e}")

class EventListener:
    def __init__(self, event_window):
        self.counter = 0
        self.screenshot_counter = 0
        self.start_time = int(time.time() * 1000)
        self.last_event_time = self.start_time
        self.running = True
        self.event_window = event_window
        self.quit_key = config.get_keyboard_quit_key()
        self.print_screen_key = config.get_print_screen_key()
        
        # Create a new test instance
        self.current_test = Test(
            config="nothing for now",
            comment1="Test started",
            comment2=f"Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
    def capture_screen(self):
        """Capture the screen and save it as a JPG file."""
        try:
            # Get the DB directory path
            db_dir = os.path.join(project_root, "DB")
            
            # Get the most recent JSON file name (without extension)
            json_files = [f for f in os.listdir(db_dir) if f.endswith('.json')]
            if not json_files:
                print("No JSON files found in the DB directory.")
                return
                
            base_filename = os.path.splitext(json_files[0])[0]
            
            # Create screenshot filename with counter
            self.screenshot_counter += 1
            screenshot_filename = f"{base_filename}_{self.screenshot_counter}.jpg"
            screenshot_path = os.path.join(db_dir, screenshot_filename)
            
            # Get Print Screen window configuration
            width, height = config.get_Print_Screen_window_size()
            x, y = config.get_Print_Screen_window_position()
            
            # Capture the screen with configured dimensions and position
            screenshot = ImageGrab.grab(bbox=(x, y, x + width, y + height))
            
            # Save the screenshot
            screenshot.save(screenshot_path, 'JPEG')
            print(f"Screenshot saved: {screenshot_filename}")
            
            return screenshot_filename
        except Exception as e:
            print(f"Error capturing screenshot: {e}")
            return None
        
    def on_click(self, x, y, button, pressed):
        if not self.running:
            return False
            
        # Check if we should track this type of event
        if pressed and not config.should_track_mouse_press():
            return True
        if not pressed and not config.should_track_mouse_release():
            return True
            
        self.counter += 1
        current_time = int(time.time() * 1000)
        time_diff = current_time - self.last_event_time
        time_total = current_time - self.start_time
        
        # Different action text for press and release
        action_text = f"Mouse {button.name} pressed" if pressed else f"Mouse {button.name} released"
        
        event = Event(
            counter=self.counter,
            time=time_total,  # Total time since start
            position=(x, y),
            event_type=f"mouse_{button.name}",
            action=action_text,
            priority=config.get_event_priority(),
            step_on=f"{config.get_step_prefix()} {self.counter}",
            time_from_last=time_diff,
            step_desc="none",
            step_accep="none",
            step_resau="none",
            pic="none"
        )
        
        # Add event to current test
        self.current_test.add_event(event)
        
        # Update the floating window
        self.event_window.update_event(event)
        self.last_event_time = current_time

    def on_press(self, key):
        try:
            # Create common event data
            self.counter += 1
            current_time = int(time.time() * 1000)
            time_diff = current_time - self.last_event_time
            time_total = current_time - self.start_time
            
            # Create base event
            event = Event(
                counter=self.counter,
                time=time_total,
                position=(0, 0),
                event_type="keyboard",
                action=f"Key '{key.char}' pressed",
                priority=config.get_event_priority(),
                step_on=f"{config.get_step_prefix()} {self.counter}",
                time_from_last=time_diff,
                step_desc="none",
                step_accep="none",
                step_resau="none",
                pic="none"
            )
            
            # Update the floating window
            self.event_window.update_event(event)
            if key.char == self.quit_key:
                print("\nStopping event listener...")
                self.running = False
                
                # Save the test data
                try:
                    filepath = self.current_test.save_to_file()
                    print(f"Test data saved to: {filepath}")
                except Exception as e:
                    print(f"Error saving test data: {e}")
                
                # Schedule window destruction in the main thread
                self.event_window.after(0, self.event_window.destroy)
                return False
                
        except AttributeError:
            # Handle special keys
            if key.name in config.get_special_keys() or key.name == self.print_screen_key:
                # Create base event for special keys
                event = Event(
                    counter=self.counter,
                    time=time_total,
                    position=(0, 0),
                    event_type="keyboard",
                    action=f"Special key '{key.name}' pressed",
                    priority=config.get_event_priority(),
                    step_on=f"{config.get_step_prefix()} {self.counter}",
                    time_from_last=time_diff,
                    step_desc="none",
                    step_accep="none",
                    step_resau="none",
                    pic="none"
                )
                # Update the floating window
                self.event_window.update_event(event)
                
                if key.name == self.print_screen_key:
                    print("\nPrint screen key pressed...")
                    screenshot_filename = self.capture_screen()
                    if screenshot_filename:
                        event.step_desc = "Screen capture"
                        event.step_accep = "Screenshot saved successfully"
                        event.pic = screenshot_filename
                    else:
                        return True
            else:
                return True
                
        # Add event to current test  
        self.current_test.add_event(event)
        self.last_event_time = current_time

def main():
    # Register cleanup function
    atexit.register(cleanup)
    
    # Check if already running
    if is_already_running():
        return
        
    # Create and show the event window
    event_window = EventWindow()
    
    # Create event listener
    listener = EventListener(event_window)
    
    # Create and start mouse and keyboard listeners
    mouse_listener = mouse.Listener(on_click=listener.on_click)
    keyboard_listener = keyboard.Listener(on_press=listener.on_press)
    
    mouse_listener.start()
    keyboard_listener.start()
    
    print(f"Event listeners are active. Click anywhere, press keys, or press '{config.get_keyboard_quit_key()}' to quit...")
    print(f"Press '{config.get_print_screen_key()}' to capture a screenshot")
    
    try:
        # Run tkinter main loop
        event_window.mainloop()
    except KeyboardInterrupt:
        print("\nStopping event listener...")
        listener.running = False
    finally:
        # Stop all listeners
        mouse_listener.stop()
        keyboard_listener.stop()
        try:
            event_window.destroy()
        except:
            pass
        print("Event listeners stopped.")
        cleanup()

if __name__ == "__main__":
    main() 