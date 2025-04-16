"""
Script to create and run a Test instance from a JSON file.
"""

import os
import sys
import json
import time
from pynput import mouse, keyboard
from datetime import datetime

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

from src.utils.test import Test
from src.utils.config import Config
from gui.event_window import EventWindow
from src.utils.event_mouse_keyboard import Event
from src.utils.picture_handle import capture_screen, generate_screenshot_filename, get_latest_json_base_filename

config = Config()

class TestRunner:
    def __init__(self, test):
        self.test = test
        self.running = True
        self.quit_key = config.get_keyboard_quit_key()
        self.print_screen_key = config.get_print_screen_key()
        self.keyboard_listener = None
        self.mouse_controller = mouse.Controller()
        self.keyboard_controller = keyboard.Controller()
        self.event_window = None
        self.screenshot_counter = 0
        
    def on_press(self, key):
        try:
            if key.char == self.quit_key:
                print("\nStopping test execution...")
                self.running = False
                if self.keyboard_listener:
                    self.keyboard_listener.stop()
                if self.event_window:
                    self.event_window.after(0, self.event_window.destroy)
                return False
        except AttributeError:
            # Handle special keys
            if key.name in config.get_special_keys() or key.name == self.print_screen_key:
                if key.name == self.print_screen_key:
                    print("\nPrint screen key pressed...")
                    # Add a small delay to allow the window to update
                    time.sleep(0.1)  # 100ms delay
                    screenshot = capture_screen()
                    if screenshot:
                        # Get base filename and generate screenshot filename
                        base_filename = get_latest_json_base_filename()
                        if base_filename:
                            self.screenshot_counter += 1
                            screenshot_filename, screenshot_path = generate_screenshot_filename(
                                base_filename, self.screenshot_counter
                            )
                            
                            if screenshot_filename and screenshot_path:
                                # Create event for the screenshot
                                event = Event(
                                    counter=len(self.test.events) + 1,
                                    time=int(time.time() * 1000),
                                    position=(0, 0),
                                    event_type="keyboard",
                                    action=f"Special key '{self.print_screen_key}' pressed",
                                    priority=config.get_event_priority(),
                                    step_on=f"{config.get_step_prefix()} {len(self.test.events) + 1}",
                                    time_from_last=0,
                                    step_desc="Screen capture",
                                    step_accep="Screenshot saved successfully",
                                    step_resau="none",
                                    screenshot=screenshot
                                )
                                
                                # Save the screenshot and update the event window
                                event.save_screenshot(screenshot_path)
                                self.test.add_event(event)
                                if self.event_window:
                                    self.event_window.update_event(event)
            
    def execute_mouse_event(self, event):
        """Execute a mouse event."""
        # Move mouse to position
        self.mouse_controller.position = event.position
        
        # Handle different mouse button types
        button_map = {
            'mouse_left': mouse.Button.left,
            'mouse_right': mouse.Button.right,
            'mouse_middle': mouse.Button.middle
        }
        
        if event.event_type in button_map:
            button = button_map[event.event_type]
            
            # Check if it's a press or release event
            if "pressed" in event.action:
                self.mouse_controller.press(button)
            elif "released" in event.action:
                self.mouse_controller.release(button)
                
    def execute_keyboard_event(self, event):
        """Execute a keyboard event."""
        # Extract the key from the action text
        key_text = event.action.split("'")[1]  # Get the key between single quotes
        
        # Check if this is the quit key
        if key_text == self.quit_key:
            print("\nStopping test execution...")
            self.running = False
            if self.keyboard_listener:
                self.keyboard_listener.stop()
            if self.event_window:
                self.event_window.after(0, self.event_window.destroy)
            return
            
        # If this is a print screen event, capture the screen
        if key_text == self.print_screen_key:
            print("\nPrint screen key pressed...")
            # Add a small delay to allow the window to update
            time.sleep(0.1)  # 100ms delay
            screenshot = capture_screen()
            if screenshot:
                # Get base filename and generate screenshot filename
                base_filename = get_latest_json_base_filename()
                if base_filename:
                    self.screenshot_counter += 1
                    screenshot_filename, screenshot_path = generate_screenshot_filename(
                        base_filename, self.screenshot_counter
                    )
                    
                    if screenshot_filename and screenshot_path:
                        # Update the event with the screenshot
                        event.screenshot = screenshot
                        event.save_screenshot(screenshot_path)
                        event.step_desc = "Screen capture"
                        event.step_accep = "Screenshot saved successfully"
                        if self.event_window:
                            self.event_window.update_event(event)
            return
        
        # Handle special keys
        special_key_map = {
            'space': keyboard.Key.space,
            'enter': keyboard.Key.enter,
            'tab': keyboard.Key.tab,
            'shift': keyboard.Key.shift,
            'ctrl': keyboard.Key.ctrl,
            'alt': keyboard.Key.alt,
            'esc': keyboard.Key.esc,
            'backspace': keyboard.Key.backspace,
            'delete': keyboard.Key.delete,
            'up': keyboard.Key.up,
            'down': keyboard.Key.down,
            'left': keyboard.Key.left,
            'right': keyboard.Key.right,
            'home': keyboard.Key.home,
            'end': keyboard.Key.end,
            'page_up': keyboard.Key.page_up,
            'page_down': keyboard.Key.page_down,
            'insert': keyboard.Key.insert,
            'menu': keyboard.Key.menu,
            'caps_lock': keyboard.Key.caps_lock,
            'num_lock': keyboard.Key.num_lock,
            'scroll_lock': keyboard.Key.scroll_lock,
            'pause': keyboard.Key.pause,
            'print_screen': keyboard.Key.print_screen,
            'f1': keyboard.Key.f1,
            'f2': keyboard.Key.f2,
            'f3': keyboard.Key.f3,
            'f4': keyboard.Key.f4,
            'f5': keyboard.Key.f5,
            'f6': keyboard.Key.f6,
            'f7': keyboard.Key.f7,
            'f8': keyboard.Key.f8,
            'f9': keyboard.Key.f9,
            'f10': keyboard.Key.f10,
            'f11': keyboard.Key.f11,
            'f12': keyboard.Key.f12,
        }
        
        if key_text in special_key_map:
            self.keyboard_controller.press(special_key_map[key_text])
            self.keyboard_controller.release(special_key_map[key_text])
        else:
            # Handle regular keys
            self.keyboard_controller.press(key_text)
            self.keyboard_controller.release(key_text)
            
    def run_test(self, event_window):
        """Execute all events in the test."""
        self.event_window = event_window  # Store the event window reference
        # Start keyboard listener
        self.keyboard_listener = keyboard.Listener(on_press=self.on_press)
        self.keyboard_listener.start()
        
        try:
            for event in self.test.events:
                if not self.running:
                    break
                    
                # Update the floating window with current event
                event_window.update_event(event)
                
                try:
                    # Execute based on event type
                    if event.event_type.startswith('mouse_'):
                        self.execute_mouse_event(event)
                    elif event.event_type == 'keyboard':
                        self.execute_keyboard_event(event)
                        
                    # Wait for the specified time between events
                    if event.time_from_last > 0:
                        time.sleep(event.time_from_last / 1000)  # Convert ms to seconds
                        
                except Exception as e:
                    print(f"Error executing event {event.counter}: {e}")
                    
        except Exception as e:
            print(f"Error during test execution: {e}")
        finally:
            if self.keyboard_listener:
                self.keyboard_listener.stop()

def create_test_from_json(filepath):
    """Create a Test instance from a JSON file."""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        # Create Test instance with data from JSON
        test = Test(
            config=data.get('config', ''),
            comment1=data.get('comment1', ''),
            comment2=data.get('comment2', '')
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

def main():
    # Get the DB directory path
    db_dir = os.path.join(project_root, "DB")
    
    # Get the first JSON file in the DB directory
    json_files = [f for f in os.listdir(db_dir) if f.endswith('.json')]
    
    if not json_files:
        print("No JSON files found in the DB directory.")
        return
        
    # Use the first JSON file found
    filepath = os.path.join(db_dir, json_files[0])
    
    # Create the test
    test = create_test_from_json(filepath)
    
    if test:
        print(f"Successfully created test from {json_files[0]}")
        print(f"Test configuration: {test.config}")
        print(f"Comment 1: {test.comment1}")
        print(f"Comment 2: {test.comment2}")
        print(f"Number of events: {len(test.events)}")
        
        # Create and show the event window
        event_window = EventWindow()
        
        # Create and run the test
        runner = TestRunner(test)
        
        print(f"\nStarting test execution...")
        print(f"Press '{config.get_keyboard_quit_key()}' to stop at any time")
        
        # Start test execution in a separate thread
        import threading
        test_thread = threading.Thread(target=runner.run_test, args=(event_window,))
        test_thread.start()
        
        try:
            # Run tkinter main loop
            event_window.mainloop()
        except KeyboardInterrupt:
            print("\nStopping test execution...")
            runner.running = False
        finally:
            try:
                event_window.destroy()
            except:
                pass
            print("Test execution completed.")
    else:
        print("Failed to create test.")

if __name__ == "__main__":
    main() 