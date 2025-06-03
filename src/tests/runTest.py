"""
Script to create and run a Test instance from a JSON file.

This module provides functionality to load a test from a JSON file and execute its recorded events,
including mouse, keyboard, and screenshot actions. It includes a TestRunner class for event execution
and a main() function as the entry point for running a test.

Classes
-------
TestRunner
    Class for executing test events loaded from a JSON file.

Functions
---------
main(test_full_name=None, callback=None)
    Main entry point for running a test from a JSON file.
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
import queue  # Add queue import


# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

from src.utils.test import Test
from src.utils.config import Config
from src.gui.event_window import EventWindow
from src.utils.event_mouse_keyboard import Event
from src.utils.process_utils import is_already_running, register_cleanup, cleanup_and_restart, save_test, close_existing_mouse_threads
from src.utils.picture_handle import capture_screen, generate_screenshot_filename, compare_images, save_screenshot
from src.utils.starting_points import go_to_starting_point
from src.utils.general_func import create_test_from_json
from src.utils.run_log import RunLog

# Global lock file
lock_file = "cursor_listener.lock"
config = Config()
run_log = RunLog()


# def close_existing_mouse_threads():
#     """Close any existing mouse listener threads."""
#     for thread in threading.enumerate():
#         if thread.name == "MouseListener":
#             thread._stop()
#             thread.join()

class TestRunner:
    """
    Class for executing test events loaded from a JSON file.

    This class handles the execution of mouse, keyboard, and screenshot events as recorded in a test JSON file.
    It manages event timing, window updates, and test completion signaling.

    Attributes
    ----------
    counter : int
        Counter for the number of events executed.
    screenshot_counter : int
        Counter for the number of screenshots taken.
    start_time : int
        The start time of the test execution in milliseconds.
    last_event_time : int
        The time of the last executed event in milliseconds.
    save : bool
        Flag indicating whether to save the executed events.
    test : Test
        The Test object containing the events to execute.
    running : bool
        Flag indicating whether the test is running.
    quit_key : str
        The key used to quit the test execution.
    print_screen_key : str
        The key used to take a screenshot.
    keyboard_listener : keyboard.Listener or None
        The keyboard listener for quit key detection.
    mouse_controller : mouse.Controller
        The mouse controller for simulating mouse events.
    keyboard_controller : keyboard.Controller
        The keyboard controller for simulating keyboard events.
    event_window : EventWindow or None
        The floating window that displays the executed events.
    result_folder_path : str
        Path to the result folder for saving test data.
    test_completed : bool
        Flag indicating whether the test has completed.
    completion_queue : queue.Queue
        Queue for signaling test completion.
    current_test : Test
        The Test object for the current execution session.

    Methods
    -------
    on_press(key)
        Handle keyboard press events during test execution.
    peek_next_event(current_index)
        Look at the next event without consuming it.
    _create_event(event, time_total, time_diff)
        Helper function to create an Event object for execution.
    execute_mouse_event(event)
        Execute a mouse event.
    execute_keyboard_event(event)
        Execute a keyboard event.
    execute_mouse_scroll(event)
        Execute a mouse scroll event.
    run_test(event_window)
        Execute all events in the test.
    """
    def __init__(self, test, result_folder_path):
        """
        Initialize the TestRunner with the given test and result folder path.

        Parameters
        ----------
        test : Test
            The Test object containing the events to execute.
        result_folder_path : str
            Path to the result folder for saving test data.
        """
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
        self.test_completed = False  # Add flag for test completion
        self.completion_queue = queue.Queue()  # Add queue for completion signal

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
        """
        Handle keyboard press events during test execution.

        Parameters
        ----------
        key : Key
            The key that was pressed.

        Returns
        -------
        bool or None
            False if the quit key is pressed, otherwise None.
        """
        try:
            if key.char == self.quit_key:
                print("\nStopping test execution in the middle of the running ...")
                self.running = False
                if self.keyboard_listener:
                    self.keyboard_listener.stop()
                if self.event_window:
                    self.event_window.after(0, self.event_window.destroy)
                # Signal completion through queue
                run_log.add("the stop button was pressed in the middle of the test " + self.test.comment1.split(": ")[1], level="INFO")
                run_log.save_to_file()
                self.completion_queue.put(True)
                return False
        except AttributeError:
            if key.name == self.quit_key:
                print("\nStopping test execution in the middle of the running ...")
                self.running = False
                if self.keyboard_listener:
                    self.keyboard_listener.stop()
                if self.event_window:
                    self.event_window.after(0, self.event_window.destroy)
                # Signal completion through queue
                run_log.add("the stop button was pressed in the middle of the test " + self.test.comment1.split(": ")[1], level="INFO")
                run_log.save_to_file()
                self.completion_queue.put(True)
                return False
            else:
                pass
            
    def peek_next_event(self, current_index):
        """
        Look at the next event without consuming it.

        Parameters
        ----------
        current_index : int
            The current index in the event list.

        Returns
        -------
        Event or None
            The next event if available, otherwise None.
        """
        if current_index + 1 < len(self.test.events):
            return self.test.events[current_index + 1]
        return None

    def _create_event(self, event, time_total, time_diff):
        """
        Helper function to create an Event object for execution.

        Parameters
        ----------
        event : Event
            The event to base the new Event object on.
        time_total : int
            Total time since the start of execution.
        time_diff : int
            Time since the last event.

        Returns
        -------
        Event
            The created Event object.
        """
        return Event(
            counter=self.counter,
            time=time_total,  # Total time since start
            position=(event.position[0], event.position[1]),
            event_type=event.type if hasattr(event, 'type') else event.event_type,
            action=event.action,
            priority=event.priority,
            step_on=event.step_on,
            time_from_last=time_diff,
            step_desc=event.step_desc,
            step_accep=event.step_accep,
            step_resau=event.step_resau,
            pic_path=event.pic_path,
            step_resau_num=event.step_resau_num,
            image_name=event.image_name,
            pic_width=event.pic_width if hasattr(event, 'pic_width') else 0,
            pic_height=event.pic_height if hasattr(event, 'pic_height') else 0,
            pic_x=event.pic_x if hasattr(event, 'pic_x') else 0,
            pic_y=event.pic_y if hasattr(event, 'pic_y') else 0
        )

    def execute_mouse_event(self, event):
        """
        Execute a mouse event.

        Parameters
        ----------
        event : Event
            The mouse event to execute.
        """
        try:
            self.counter += 1
            current_time = int(time.time() * 1000)
            time_diff = current_time - self.last_event_time
            time_total = current_time - self.start_time
            
            resevent = self._create_event(event, time_total, time_diff)

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
        """
        Execute a keyboard event.

        Parameters
        ----------
        event : Event
            The keyboard event to execute.
        """
        self.counter += 1
        current_time = int(time.time() * 1000)
        time_diff = current_time - self.last_event_time
        time_total = current_time - self.start_time
        
        resevent = self._create_event(event, time_total, time_diff)

        # Extract the key from the action text
        key_text = resevent.action.split("'")[1]  # Get the key between single quotes
        
        # Check if this is the quit key
        if key_text == self.quit_key:
            print("\n Stopping test execution as quit key reached ...")
            self.running = False
            self.current_test.add_event(resevent)  # Add event to current test
            self.event_window.update_event(resevent) # Update the floating window

            # Save the test data using the imported save_test function
            filepath = save_test(self.current_test, self.test.comment1.split(": ")[1], "running",self.result_folder_path)
            if not filepath:
                print("Error saving test data")

            run_log.add("stop test " + self.test.comment1.split(": ")[1], level="INFO")
             
            # Signal completion through queue
            self.completion_queue.put(True)
            return False

        # If this is a print screen event, capture the screen
        if key_text == self.print_screen_key:
            print("\nPrint screen key pressed...")
            self.save = False # stop the saving of the listener data while deal with the snapshot 
            # Add a small delay to allow the window to update
            time.sleep(0.1)  # 100ms delay
            screenshot = capture_screen(resevent.pic_x,resevent.pic_y,resevent.pic_width,resevent.pic_height)
            if screenshot:
                self.screenshot_counter += 1
                resevent.screenshot_counter = self.screenshot_counter
                self.test
                
                screenshot_filename, screenshot_path = generate_screenshot_filename(
                        self.test.comment1.split(": ")[1], self.screenshot_counter,os.path.basename(resevent.pic_path),"running",self.result_folder_path)
                
                if screenshot_filename and screenshot_path:
                    # Update the event with the screenshot and save it first
                    #resevent.screenshot = screenshot
                    
                    resevent.pic_path = save_screenshot(screenshot, screenshot_path)
                    
                    # Now compare the images using the saved file paths
                    match_percentage, result_path = compare_images(event.pic_path, screenshot_path, self.result_folder_path)
                    #resevent.step_resau = "match percentage is "+str(match_percentage)

                    if resevent.priority == "high":
                        match_percentage_ref = config.get("minmumMatchPresent_high")
                    elif resevent.priority == "medium":
                        match_percentage_ref = config.get("minmumMatchPresent_medium")
                    else:
                        match_percentage_ref = config.get("minmumMatchPresent_low")


                    pass_criteria = 100-self.current_test.accuracy_level*5
                    if match_percentage < pass_criteria:
                        resevent.step_resau = " failed, grade is " + str(match_percentage) + " < " + str(pass_criteria)
                        status="failed"
                    else:
                        resevent.step_resau = " passed, grade is " + str(match_percentage) + " > " + str(pass_criteria)   
                        status="passed"

                    self.current_test.numOfSteps += 1
                    self.current_test.stepResult.append(["step -" + str(event.screenshot_counter),status])  
                    self.current_test.comment2 = match_percentage
                    self.save = True # Resume saving events    
                    if self.event_window:
                        self.event_window.update_event(resevent)


                    run_log.add(event.step_desc + " - " + resevent.step_resau, level="INFO")
                    run_log.add(str(resevent.pic_path), level="IMAGE")

                    if match_percentage < match_percentage_ref:
                        print(f"Match percentage is less than {config.get('match_percentage_ref')}, ending test...")
                        # Save the test data using the imported save_test function
                        filepath = save_test(self.current_test, self.test.comment1.split(": ")[1] , "running",self.result_folder_path)
                        if not filepath:
                            print("Error saving test data")

                        # Signal completion through queue
                        self.completion_queue.put(True)
                        self.running = False
                        self.current_test.add_event(resevent)  # Add event to current test
                        self.event_window.update_event(resevent) # Update the floating window
                        run_log.add("the "  + os.path.basename(resevent.pic_path)+   " gain match precentage of bellow the continue cretira -> " + str(match_percentage_ref) + "<- Test Stopped -> " , level="WARNING")
        
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

    def execute_mouse_scroll(self, event):
        """
        Execute a mouse scroll event.

        Parameters
        ----------
        event : Event
            The mouse scroll event to execute.
        """
        try:
            self.counter += 1
            current_time = int(time.time() * 1000)
            time_diff = current_time - self.last_event_time
            time_total = current_time - self.start_time
            
            resevent = self._create_event(event, time_total, time_diff)

            # Extract scroll direction and amount from the event
            scroll_info = event.step_resau.split(": ")[1] if event.step_resau else "0"
            scroll_amount = int(scroll_info)
            
            # Determine scroll direction
            direction = -1 if "down" in event.action.lower() else 1
            
            # Get scroll sensitivity from config
            sensitivity = config.get_scroll_sensitivity()
            
            # Apply sensitivity to scroll amount
            scaled_amount = scroll_amount * sensitivity
            
            # Perform the scroll with scaled amount
            self.mouse_controller.scroll(0, direction * scaled_amount)
            
            if self.save == True:
                # Add event to current test
                self.current_test.add_event(resevent)
                
                # Update the floating window
                if hasattr(self, 'event_window') and self.event_window and self.event_window.winfo_exists():
                    self.event_window.update_event(resevent)
                self.last_event_time = current_time
                
        except Exception as e:
            print(f"Error executing mouse scroll event: {e}")

    def run_test(self, event_window):
        """
        Execute all events in the test.

        Parameters
        ----------
        event_window : EventWindow
            The floating window to display event updates.
        """
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
                    if event.event_type == 'mouse_scroll':
                        self.execute_mouse_scroll(event)
                        
                        event_window.update_event(event)
                    elif event.event_type.startswith('mouse_'):
                        self.execute_mouse_event(event)
                        # Update the floating window with current event
                        event_window.update_event(event)
                    elif event.event_type == 'keyboard':
                        # Update the floating window with current event
                        event_window.update_event(event)
                        self.execute_keyboard_event(event)

                        
                except Exception as e:
                    print(f"Error executing event {event.counter}: {e}")
                    
        except Exception as e:
            print(f"Error during test execution: {e}")
        finally:
            if self.keyboard_listener:
                self.keyboard_listener.stop()
            # Put completion signal in queue
            self.completion_queue.put(True)
             
            print("Test execution completed, sent completion signal")

def main(test_full_name=None, callback=None, run_number=1, run_total=1):
    """
    Main entry point for running a test from a JSON file.

    This function loads a test from a JSON file, creates the event window, and executes the test events.
    It supports an optional callback to be called upon test completion.

    Parameters
    ----------
    test_full_name : str, optional
        The full path to the test JSON file to run.
    callback : callable, optional
        A function to call when the test completes.

    Returns
    -------
    bool
        True if the test ran successfully, False otherwise.
    """

    
    # Register cleanup function
    register_cleanup(lock_file)
    
    # Close any existing mouse listener threads
    close_existing_mouse_threads()
    
    filename = test_full_name
    result_folder_path = os.path.dirname(test_full_name)

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
        
        # Extract test name from the full path
        test_name = os.path.basename(os.path.dirname(filename))
        
        # Create and show the event window with test name
        event_window = EventWindow(test_name=test_name, run_number=run_number, run_total=run_total)
        run_log.clear()
        run_log.add(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", level="INFO")
        run_log.add("start test " + test_name, level="INFO")

        go_to_starting_point(test.starting_point)
        run_log.add("go to starting point " + test.starting_point, level="INFO")

        print(f"\nStarting test execution...")
        print(f"Press '{config.get_keyboard_quit_key()}' to stop at any time")
        
        # Create and run the test
        runner = TestRunner(test, result_folder_path)
        
        def on_test_complete():
            print("Test completed, calling callback...")
            run_log.add("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<", level="INFO")
            run_log.add("", level="INFO")
            run_log.save_to_file()
            if callback:
                callback()
            # Schedule window destruction in the main thread
            event_window.after(100, event_window.destroy)
        
        # Start test execution in a separate thread
        import threading
        test_thread = threading.Thread(target=runner.run_test, args=(event_window,))
        test_thread.start()
        
        # Set up a periodic check for test completion
        def check_test_completion():
            #print("Checking test completion...")
            try:
                # Check if there's a completion signal in the queue
                if not runner.completion_queue.empty():
                    #print("Test is completed, calling callback...")
                    on_test_complete()
                else:
                  #  print("Test still running, will check again...")
                    event_window.after(100, check_test_completion)  # Check again in 100ms
            except Exception as e:
                print(f"Error checking completion: {e}")
                # Don't schedule another check if there was an error
                on_test_complete()
        
        # Start checking for test completion immediately
        check_test_completion()
        
        try:
            # Run tkinter main loop
            event_window.mainloop()
            return True
        except KeyboardInterrupt:
            print("\nStopping test execution...")
            runner.running = False
            print(f"except KeyboardInterrupt runner.running is {runner.running}")
            on_test_complete()
            return False
    else:
        print("Failed to create test.")
        return False

if __name__ == "__main__":
    main() 