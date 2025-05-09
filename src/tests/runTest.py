"""
Script to create and run a Test instance from a JSON file.
"""

import os
import sys
import json
import time
from pynput import mouse, keyboard
from datetime import datetime
import threading
import base64
from PIL import Image
import io


# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

from src.utils.test import Test
from src.utils.config import Config
from src.gui.event_window import EventWindow
from src.utils.event_mouse_keyboard import Event
from src.utils.process_utils import is_already_running, register_cleanup, cleanup_and_restart, save_test
from src.utils.picture_handle import capture_screen, generate_screenshot_filename, compare_images
from src.utils.starting_points import go_to_starting_point
from src.utils.general_func import create_test_from_json

# Global lock file
lock_file = "cursor_listener.lock"
config = Config()

def close_existing_mouse_threads():
    """Close any existing mouse listener threads."""
    for thread in threading.enumerate():
        if thread.name == "MouseListener":
            thread._stop()
            thread.join()

class TestRunner:
    def __init__(self, test,result_folder_path):
        self.counter = 0
        self.screenshot_counter = 0
        self.start_time = int(time.time() * 1000)
        self.last_event_time = self.start_time
        self.save = True  # Global save flag with default True
        self.test = test
        self.running = True
        self.quit_key = config.get_keyboard_quit_key()
        self.print_screen_key = config.get_print_screen_key()
        self.keyboard_listener = None
        self.mouse_controller = mouse.Controller()
        self.keyboard_controller = keyboard.Controller()
        self.event_window = None
        self.screenshot_counter = 0
        self.result_folder_path = result_folder_path

        # Create a new test instance for the running one 
        self.current_test = Test(
            config="nothing for now",
            comment1=f"Test: {test.comment1}",
            comment2=f"Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            starting_point=test.starting_point,
            numOfSteps=0,
            stepResult=[]

        )

    def on_press(self, key):
        try:
            if key.char == self.quit_key:
                print("\nStopping test execution in the middle of the running ...")
                self.running = False
                if self.keyboard_listener:
                    self.keyboard_listener.stop()
                if self.event_window:
                    self.event_window.after(0, self.event_window.destroy)
                
                # Use the imported cleanup_and_restart function
                self.event_window.after(0, lambda: cleanup_and_restart(self.event_window))
                return False
        except AttributeError:
            if key.name == self.quit_key:
                print("\nStopping test execution in the middle of the running ...")
                self.running = False
                if self.keyboard_listener:
                    self.keyboard_listener.stop()
                if self.event_window:
                    self.event_window.after(0, self.event_window.destroy)
                
                # Use the imported cleanup_and_restart function
                self.event_window.after(0, lambda: cleanup_and_restart(self.event_window))
                return False
            else:
                pass
            
    def peek_next_event(self, current_index):
        """Look at the next event without consuming it."""
        if current_index + 1 < len(self.test.events):
            return self.test.events[current_index + 1]
        return None

    def execute_mouse_event(self, event):
        """Execute a mouse event."""
        try:
            self.counter += 1
            current_time = int(time.time() * 1000)
            time_diff = current_time - self.last_event_time
            time_total = current_time - self.start_time
            
            resevent = Event(
                counter=self.counter,
                time=time_total,  # Total time since start
                position=(event.position[0], event.position[1]),
                event_type=event.event_type,
                action=event.action,
                priority=event.priority,
                step_on=event.step_on,
                time_from_last=time_diff,
                step_desc=event.step_desc,
                step_accep=event.step_accep,
                step_resau=event.step_resau,
                pic_path=event.pic_path,
                step_resau_num=event.step_resau_num,
                image_name=event.image_name
            )

            # Handle different mouse button types
            button_map = {
                'mouse_left': mouse.Button.left,
                'mouse_right': mouse.Button.right,
                'mouse_middle': mouse.Button.middle
            }
            
            if event.event_type in button_map:
                button = button_map[resevent.event_type]
                
                # Check if it's a press or release event
                if "pressed" in event.action:
                    # Move mouse to position first
                    self.mouse_controller.position = event.position
                    # Add a small delay to ensure the mouse has moved
                    time.sleep(0.1)  # Increased delay for more stability
                    self.mouse_controller.press(button)
                    
                    # Look at the next event
                    next_event = self.peek_next_event(self.counter - 1)
                    # If this is a drag operation, look at the next event
                    if next_event and "drag" in next_event.action.lower():
                        # Store the start position and time
                        drag_start_pos = event.position
                        drag_start_time = current_time
                        
                        if next_event.event_type == event.event_type and "released" in next_event.action:
                            try:
                                # Try to get recorded movement data
                                movement_data = json.loads(next_event.step_resau)
                                positions = movement_data['positions']
                                times = movement_data['times']
                                
                                # Keep the button pressed while moving
                                self.mouse_controller.press(button)
                                
                                # Replay the exact movement
                                for i in range(1, len(positions)):
                                    # Calculate time to wait based on recorded timing
                                    wait_time = (times[i] - times[i-1]) / 1000.0  # Convert to seconds
                                    time.sleep(wait_time)
                                    
                                    # Move to the recorded position while keeping button pressed
                                    self.mouse_controller.position = positions[i]
                                
                            except (json.JSONDecodeError, KeyError, TypeError):
                                # Fallback to simple movement if no recorded data
                                self.mouse_controller.position = next_event.position
                                time.sleep(0.1)
                            
                            # Release the button at the end
                            self.mouse_controller.release(button)
                            
                            # Update the event with drag information
                            resevent.step_desc = f"Drag from {drag_start_pos} to {next_event.position}"
                            resevent.step_resau = f"Drag duration: {next_event.time - event.time}ms"
                            
                elif "released" in event.action:
                    # For non-drag releases, just move and release
                    self.mouse_controller.position = event.position
                    time.sleep(0.1)  # Increased delay for more stability
                    self.mouse_controller.release(button)
            
            if self.save == True:
                # Add event to current test
                self.current_test.add_event(resevent)
                
                # Update the floating window
                if hasattr(self, 'event_window') and self.event_window and self.event_window.winfo_exists():
                    self.event_window.update_event(resevent)
                self.last_event_time = current_time
                
        except Exception as e:
            print(f"Error executing mouse event: {e}")

    def execute_keyboard_event(self, event):
        """Execute a keyboard event."""

        self.counter += 1
        current_time = int(time.time() * 1000)
        time_diff = current_time - self.last_event_time
        time_total = current_time - self.start_time
        # duplicatethe 
        resevent = Event(
            counter=self.counter,
            time=time_total,  # Total time since start
            position=(event.position[0], event.position[1]),
            event_type=event.event_type,
            action=event.action,
            priority=event.priority,
            step_on=event.step_on,
            time_from_last=time_diff,
            step_desc=event.step_desc,
            step_accep=event.step_accep,
            step_resau=event.step_resau,
            pic_path=event.pic_path,
            step_resau_num=event.step_resau_num,
            image_name=event.image_name
        )

        # Extract the key from the action text
        key_text = resevent.action.split("'")[1]  # Get the key between single quotes
        
        # Check if this is the quit key
        if key_text == self.quit_key:
            print("\nStopping test execution...")
            self.running = False
            self.current_test.add_event(resevent)  # Add event to current test
            self.event_window.update_event(resevent) # Update the floating window

            # for resevent in self.current_test.events:
            #     if resevent.screenshot and not resevent.image_data:
            #         resevent._convert_screenshot_to_base64()  

            # Save the test data using the imported save_test function
            filepath = save_test(self.current_test, self.test.comment1.split(": ")[1], "running",self.result_folder_path)
            if not filepath:
                print("Error saving test data")

            # Schedule window destruction and control panel restart in the main thread
            self.event_window.after(0, lambda: cleanup_and_restart(self.event_window))
            return False
            
            
        # If this is a print screen event, capture the screen
        if key_text == self.print_screen_key:
            print("\nPrint screen key pressed...")
            self.save = False # stop the saving of the listener data while deal with the snapshot 
            # Add a small delay to allow the window to update
            time.sleep(0.1)  # 100ms delay
            screenshot = capture_screen()
            if screenshot:
                self.screenshot_counter += 1
                self.test
                
                screenshot_filename, screenshot_path = generate_screenshot_filename(
                        self.test.comment1.split(": ")[1], self.screenshot_counter,os.path.basename(resevent.pic_path),"running",self.result_folder_path)
                
                if screenshot_filename and screenshot_path:
                    # Update the event with the screenshot and save it first
                    resevent.screenshot = screenshot
                    resevent.save_screenshot(screenshot_path)
                    
                    # Now compare the images using the saved file paths
                    match_percentage, result_path = compare_images(event.pic_path, screenshot_path, self.result_folder_path)
                    resevent.step_resau = "match percentage is "+str(match_percentage)
                    self.current_test.numOfSteps += 1
                    self.current_test.stepResult.append([str(resevent.image_name),str(match_percentage)])  
                    self.current_test.comment2 = match_percentage
                    self.save = True # Resume saving events    
                    if self.event_window:
                        self.event_window.update_event(resevent)
            
        
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

        if self.save == True:
            # Add event to current test
            self.current_test.add_event(resevent)
            
            # Update the floating window
            self.event_window.update_event(resevent)
            self.last_event_time = current_time

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
                    

                
                try:
                    # Wait for the specified time between events
                    if event.time_from_last > 0:
                        time.sleep(event.time_from_last / 1000)  # Convert ms to seconds
                    # Execute based on event type
                    current_time = int(time.time() * 1000)
                    if event.event_type.startswith('mouse_'):
                        # print("execute mouse command time is {current_time}")
                        self.execute_mouse_event(event)
                        # Update the floating window with current event
                        event_window.update_event(event)
                    elif event.event_type == 'keyboard':
                        # print("execute keyboard command time is {current_time}")
                        self.execute_keyboard_event(event)
                        # Update the floating window with current event
                        event_window.update_event(event)
                    
                        
                except Exception as e:
                    print(f"Error executing event {event.counter}: {e}")
                    
        except Exception as e:
            print(f"Error during test execution: {e}")
        finally:
            if self.keyboard_listener:
                self.keyboard_listener.stop()



def main(test_full_name=None):

    # Check if another instance is already running
    if is_already_running(lock_file):
        sys.exit(1)

    # Register cleanup function
    register_cleanup(lock_file)
    
    # Close any existing mouse listener threads
    close_existing_mouse_threads()
    
    filename = test_full_name
    result_folder_path = os.path.dirname(test_full_name) #get_folder_path(test_full_name)

    print(f"the test to be run is {test_full_name}")
    print(f"test folder path is {result_folder_path}")
    
    # Create the test
    test = create_test_from_json(filename)
    
    if test:
        print(f"Test starting_point is: {test.starting_point}")
        print(f"Test configuration: {test.config}")
        print(f"Comment 1: {test.comment1}")
        print(f"Comment 2: {test.comment2}")
        print(f"Number of events: {len(test.events)}")
        
        # Create and show the event window
        event_window = EventWindow()

        go_to_starting_point(test.starting_point)
        
        # Create and run the test
        runner = TestRunner(test,result_folder_path)
        
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