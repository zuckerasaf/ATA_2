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
import json
import subprocess

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

from src.utils.event_mouse_keyboard import Event
from src.utils.event_window import EventWindow
from src.utils.config import Config
from src.utils.test import Test
from src.utils.picture_handle import capture_screen, generate_screenshot_filename
from src.utils.starting_points import go_to_starting_point

LOCK_FILE = "cursor_listener.lock"
config = Config()

def restart_control_panel():
    """Start the control panel in a new process."""
    try:
        control_panel_path = os.path.join(project_root, "src", "gui", "control_panel.py")
        subprocess.Popen([sys.executable, control_panel_path])
    except Exception as e:
        print(f"Error starting control panel: {e}")

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
    def __init__(self, event_window, test_name=None):
        self.counter = 0
        self.screenshot_counter = 0
        self.start_time = int(time.time() * 1000)
        self.last_event_time = self.start_time
        self.running = True
        self.event_window = event_window
        self.quit_key = config.get_keyboard_quit_key()
        self.print_screen_key = config.get_print_screen_key()
        self.test_name = test_name
        
        # Create a new test instance
        self.current_test = Test(
            config="nothing for now",
            comment1=f"Test: {test_name}" if test_name else "Test started",
            comment2=f"Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
    def save_test(self):
        """Save the test data with custom filename if provided."""
        try:
            if self.test_name:
                # Create DB/Test directory structure if it doesn't exist
                db_path = os.path.join(project_root, "DB", "Test", self.test_name)
                os.makedirs(db_path, exist_ok=True)
                
                # Set custom filename
                filename = f"{self.test_name}.json"
                filepath = os.path.join(db_path, filename)
                
                # Save with custom filename
                with open(filepath, 'w') as f:
                    json.dump(self.current_test.to_dict(), f, indent=4)
                print(f"Test data saved to: {filepath}")
                return filepath
            else:
                # Use default save method
                return self.current_test.save_to_file()
        except Exception as e:
            print(f"Error saving test data: {e}")
            raise

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
                
                # Add the final event to test before saving
                self.current_test.add_event(event)
                
                # Save any pending screenshots and convert to base64
                for event in self.current_test.events:
                    if event.screenshot:
                        # Generate filename for unsaved screenshot if needed
                        if not event.pic:
                            self.screenshot_counter += 1
                            screenshot_filename, screenshot_path = generate_screenshot_filename(
                                self.test_name, self.screenshot_counter
                            )
                            if screenshot_filename and screenshot_path:
                                event.save_screenshot(screenshot_path)
                        
                        # Convert screenshot to base64 if not already done
                        if not event.image_data:
                            event._convert_screenshot_to_base64()
                
                # Save the test data
                try:
                    filepath = self.save_test()
                except Exception as e:
                    print(f"Error saving test data: {e}")
                
                # Schedule window destruction and control panel restart in the main thread
                def cleanup_and_restart():
                    self.event_window.destroy()
                    restart_control_panel()
                
                self.event_window.after(0, cleanup_and_restart)
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
                    # Add a small delay to allow the window to update
                    time.sleep(0.1)  # 100ms delay
                    screenshot = capture_screen()
                    if screenshot:
                        # Generate screenshot filename with test name
                        self.screenshot_counter += 1
                        screenshot_filename, screenshot_path = generate_screenshot_filename(
                            self.test_name, self.screenshot_counter
                        )
                        
                        if screenshot_filename and screenshot_path:
                            # Store screenshot in event and save it
                            event.screenshot = screenshot
                            event.save_screenshot(screenshot_path)
                            event.step_desc = "Screen capture"
                            event.step_accep = "Screenshot saved successfully"
                            # Update window with final event data
                            self.event_window.update_event(event)
                    else:
                        return True
            else:
                return True
                
        # Add event to current test  
        self.current_test.add_event(event)
        self.last_event_time = current_time

def main(test_name=None, starting_point="none"):
    """
    Main function to start recording a test.
    
    Args:
        test_name (str, optional): Name of the test to record
        starting_point (str, optional): Starting point for the test ("desktop", "point_A", etc.)
    """
    # Register cleanup function
    atexit.register(cleanup)
    
    # Check if already running
    if is_already_running():
        return
        
    # Navigate to starting point if specified
    if starting_point.lower() != "none":
        print(f"Navigating to starting point: {starting_point}")
        if not go_to_starting_point(starting_point):
            print("Failed to navigate to starting point. Recording cancelled.")
            cleanup()
            return
        
    # Create and show the event window
    event_window = EventWindow()
    
    # Create event listener with test name
    listener = EventListener(event_window, test_name)
    
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