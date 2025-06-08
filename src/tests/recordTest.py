"""
Test recording module for capturing mouse and keyboard events.

This module provides functionality to record mouse and keyboard events during test execution.
It includes an EventListener class that captures mouse movements, clicks, keyboard presses, and scroll events,
and updates a floating event window with the recorded events.

Classes
-------
EventListener
    A class that listens for mouse and keyboard events and records them for test execution.

Functions
---------
main(test_name=None, starting_point="none")
    Main function to start the test recording process.
"""

import os
import sys
import time
import json
import atexit
import threading
import tkinter as tk
from datetime import datetime
from pynput import mouse, keyboard
from src.utils.config import Config
from src.utils.test import Test
from src.utils.picture_handle import capture_screen, generate_screenshot_filename, save_screenshot
from src.utils.event_mouse_keyboard import Event
from src.utils.process_utils import is_already_running, register_cleanup, cleanup_and_restart, save_test, close_existing_mouse_threads
from src.utils.app_lifecycle import restart_control_panel
from src.gui.event_window import EventWindow
from src.gui.screenshot_dialog import ScreenshotDialog
from src.utils.starting_points import go_to_starting_point
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


class EventListener:
    """
    A class that listens for mouse and keyboard events and records them for test execution.

    This class captures mouse movements, clicks, keyboard presses, and scroll events,
    and updates a floating event window with the recorded events.

    Attributes
    ----------
    counter : int
        Counter for the number of events recorded.
    screenshot_counter : int
        Counter for the number of screenshots taken.
    start_time : int
        The start time of the recording in milliseconds.
    last_event_time : int
        The time of the last recorded event in milliseconds.
    neto_time : int
        The net time elapsed since the start of the recording, excluding time spent in the screenshot dialog.
    running : bool
        Flag indicating whether the event listener is running.
    save : bool
        Flag indicating whether to save the recorded events.
    event_window : EventWindow
        The floating window that displays the recorded events.
    quit_key : str
        The key used to quit the recording.
    print_screen_key : str
        The key used to take a screenshot.
    test_name : str, optional
        The name of the test being recorded.
    dialog_open : bool
        Flag indicating whether a dialog is open.
    last_press_position : tuple, optional
        The last position where a mouse button was pressed.
    last_press_time : int, optional
        The time when the last mouse button was pressed.
    drag_positions : list
        List of positions recorded during a drag operation.
    drag_times : list
        List of times recorded during a drag operation.
    current_test : Test
        The current test instance being recorded.

    Methods
    -------
    on_move(x, y)
        Track mouse movement during drag operations.
    on_click(x, y, button, pressed)
        Handle mouse click events, including drag operations.
    on_press(key)
        Handle keyboard press events.
    on_scroll(x, y, dx, dy)
        Handle mouse scroll events.
    """

    def __init__(self, event_window, test_name=None, starting_point="none", precondition="nothing for now"):
        """
        Initialize the EventListener with the given event window and test name.

        Parameters
        ----------
        event_window : EventWindow
            The floating window that displays the recorded events.
        test_name : str, optional
            The name of the test being recorded.
        starting_point : str, optional
            The starting point for the test recording.
        precondition : str, optional
            The precondition for the test recording.
        """
        self.counter = 0
        self.screenshot_counter = 0
        self.start_time = int(time.time() * 1000)
        self.last_event_time = 0
        self.neto_time = 0
        self.running = True
        self.save = True  # Global save flag with default True
        self.event_window = event_window
        self.quit_key = config.get_keyboard_quit_key()
        self.print_screen_key = config.get_print_screen_key()
        self.test_name = test_name
        self.dialog_open = False  # Flag to track if dialog is open
        self.last_press_position = None  # Track last press position
        self.last_press_time = None  # Track last press time
        self.drag_positions = []  # Track positions during drag
        self.drag_times = []  # Track times during drag
        
        # Create a new test instance
        self.current_test = Test(
            config= precondition,
            comment1=f"Test: {test_name}" if test_name else "Test started",
            comment2=f"Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            starting_point=starting_point,
            total_time_in_screenshot_dialog=0
        )
        
    def on_move(self, x, y):
        """
        Track mouse movement during drag operations.

        Parameters
        ----------
        x : int
            The x-coordinate of the mouse.
        y : int
            The y-coordinate of the mouse.
        """
        if self.last_press_position is not None:
            current_time = int(time.time() * 1000)
            self.drag_positions.append((x, y))
            self.drag_times.append(current_time)

    def on_click(self, x, y, button, pressed):
        """
        Handle mouse click events, including drag operations.

        Parameters
        ----------
        x : int
            The x-coordinate of the mouse.
        y : int
            The y-coordinate of the mouse.
        button : Button
            The mouse button that was clicked.
        pressed : bool
            Whether the button was pressed or released.

        Returns
        -------
        bool
            True if the event should be tracked, False otherwise.
        """
        if not self.running:
            return False
            
        # Check if we should track this type of event
        if pressed and not config.should_track_mouse_press():
            return True
        if not pressed and not config.should_track_mouse_release():
            return True
            
        self.counter += 1
        current_time = int(time.time() * 1000)
        time_total = current_time - self.start_time
        neto_time = time_total - self.current_test.total_time_in_screenshot_dialog
        time_diff = neto_time - self.last_event_time

        # Determine if this is a drag operation
        is_drag = False
        if pressed:
            self.last_press_position = (x, y)
            self.last_press_time = current_time
            self.drag_positions = [(x, y)]  # Initialize drag positions
            self.drag_times = [current_time]  # Initialize drag times
        elif self.last_press_position is not None:
            # Calculate distance moved
            dx = x - self.last_press_position[0]
            dy = y - self.last_press_position[1]
            distance = (dx * dx + dy * dy) ** 0.5  # Euclidean distance
            
            # If moved more than 5 pixels, consider it a drag
            if distance > config.get_track_drag_threshold():
                is_drag = True
                # Add final position and time
                self.drag_positions.append((x, y))
                self.drag_times.append(current_time)
            self.last_press_position = None
            self.last_press_time = None

        # Different action text for press and release, including drag information
        if pressed:
            action_text = f"Mouse {button.name} pressed"
        else:
            action_text = f"Mouse {button.name} released"
            if is_drag:
                action_text = f"Mouse {button.name} drag released"
        
        event = Event(
            counter=self.counter,
            time=time_total,  # Total time since start
            neto_time=neto_time,
            position=(x, y),
            event_type=f"mouse_{button.name}",
            action=action_text,
            priority=config.get_event_priority(),
            step_on=f"{config.get_step_prefix()} {self.counter}",
            time_from_last=time_diff,
            step_desc="none",
            step_accep="none",
            step_resau="none",
            pic_path="none",
            screenshot_counter=0,
            image_name="none"
        )

        # Add drag movement data if this is a drag release
        if not pressed and is_drag and len(self.drag_positions) > 1:
            event.step_desc = "Drag movement"
            event.step_resau = json.dumps({
                'positions': self.drag_positions,
                'times': self.drag_times
            })

        if self.save == True:
            # Add event to current test
            self.current_test.add_event(event)
            
            # Update the floating window
            self.event_window.update_event(event)
            self.last_event_time = neto_time
 

    def on_press(self, key):
        """
        Handle keyboard press events.

        Parameters
        ----------
        key : Key
            The key that was pressed.

        Returns
        -------
        bool
            True if the event should be tracked, False otherwise.
        """
        self.counter += 1
        current_time = int(time.time() * 1000)
        time_total = current_time - self.start_time
        neto_time = time_total - self.current_test.total_time_in_screenshot_dialog
        time_diff = neto_time - self.last_event_time

        event = None  # <-- Initialize event to None
        try: # the "try" part deal with all the NOT speaceial keys tha one that got valid {key.char}
           event = Event(
                counter=self.counter,
                time=time_total,
                neto_time=neto_time,
                position=(0, 0),
                action=f"Key '{key.char}' pressed",
                event_type="keyboard",
                priority=config.get_event_priority(),
                step_on=f"{config.get_step_prefix()} {self.counter}",
                time_from_last=time_diff
            )
        except AttributeError:
            # Handle special keys such as print and quit ....
            if key.name in config.get_special_keys() :
                # Create base event for special keys
                event = Event(
                    counter=self.counter,
                    time=time_total,
                    neto_time=neto_time,
                    position=(0, 0),
                    event_type="keyboard",
                    action=f"Special key '{key.name}' pressed",
                    priority=config.get_event_priority(),
                    step_on=f"{config.get_step_prefix()} {self.counter}",
                    time_from_last=time_diff,
                    step_desc="none",
                    step_accep="none",
                    step_resau="none",
                    pic_path="none",
                    screenshot_counter=0,
                    image_name="none"
                )

                
                if key.name == self.print_screen_key:
                    #event.event_type="keyboard - snapshot command"
                    self.save = False # stop the saving of the listener data while deal with the snapshot 
                    print("\nPrint screen key pressed...")
                    
                    # Start timing the dialog
                    dialog_start_time = int(time.time() * 1000)
                    
                    # Create dialog and wait for it
                    dialog = ScreenshotDialog(self.screenshot_counter)
                    dialog.dialog.wait_window()
                    
                    # Calculate time spent in dialog
                    dialog_end_time = int(time.time() * 1000)
                    time_in_dialog = dialog_end_time - dialog_start_time
                    
                    time.sleep(0.1)  # 100ms delay for close the snapshot window 
                    # Only proceed if user clicked OK
                    event.pic_width = dialog.result['ps_width']
                    event.pic_height = dialog.result['ps_height']
                    event.pic_x = dialog.result['ps_x']
                    event.pic_y = dialog.result['ps_y']

                    if dialog.result:
                        #Add a small delay to allow the window to update
                        time.sleep(0.1)  # 100ms delay
                        screenshot = capture_screen(event.pic_x, event.pic_y, event.pic_width, event.pic_height) # capture the screen
                        if screenshot:
                            # Generate screenshot filename with test name
                            self.screenshot_counter += 1
                            screenshot_filename, screenshot_path = generate_screenshot_filename(
                                self.test_name, self.screenshot_counter, dialog.result['image_name'],"Recording","none")
                            
                            if screenshot_filename and screenshot_path:
                                self.save = True # Resume saving events
                                # Store screenshot in event and save it
                               
                                # Use dialog results
                                event.step_desc = dialog.result['step_desc']
                                event.step_accep = dialog.result['step_accep']
                                event.priority = dialog.result['priority']
                                event.pic_path =  save_screenshot(screenshot, screenshot_path)
                                event.time_in_screenshot_dialog = time_in_dialog  # Store the time spent in dialog
                                self.current_test.numOfSteps += 1
                                self.current_test.stepResult.append([dialog.result['image_name'], "-"])
                                event.screenshot_counter = self.screenshot_counter
                                event.image_name = dialog.result['image_name']
                                self.current_test.total_time_in_screenshot_dialog += time_in_dialog

                                
                                run_log.add(str(event.pic_path), level="IMAGE")
                                run_log.add("screenshot taken with name " + dialog.result['image_name'], level="INFO")


                     
                    self.save = True
            

                if key.name == self.quit_key:

                    print("\nStopping event listener...")
                    self.running = False
                    self.current_test.add_event(event)  # Add event to current test
                    self.event_window.update_event(event) # Update the floating window

                    # Save the test data using the imported save_test function
                    filepath = save_test(self.current_test, self.test_name, "recording")
                    if not filepath:
                        print("Error saving test data")
                    
                    run_log.add("stop recording test " + self.test_name, level="INFO")
                    run_log.save_to_file()
                    # Schedule window destruction and control panel restart in the main thread
                    self.event_window.after(0, lambda: cleanup_and_restart(self.event_window))
                    return False
            else:
                self.save = True  
        if self.save == True and event is not None:        # <-- Only use event if it was assigned
            self.current_test.add_event(event)
            self.event_window.update_event(event)
        self.last_event_time = neto_time

    def on_scroll(self, x, y, dx, dy):
        """
        Handle mouse scroll events.

        Parameters
        ----------
        x : int
            The x-coordinate of the mouse.
        y : int
            The y-coordinate of the mouse.
        dx : int
            The horizontal scroll amount.
        dy : int
            The vertical scroll amount.

        Returns
        -------
        bool
            True if the event should be tracked, False otherwise.
        """
        if not self.running:
            return False
            
        if not config.should_track_mouse_scroll():
            return True
            
        self.counter += 1
        current_time = int(time.time() * 1000)
        time_total = current_time - self.start_time
        neto_time = time_total - self.current_test.total_time_in_screenshot_dialog
        time_diff = neto_time - self.last_event_time

        # Determine scroll direction
        direction = "up" if dy > 0 else "down"
        
        event = Event(
            counter=self.counter,
            time=time_total,
            neto_time=neto_time,
            position=(x, y),
            event_type="mouse_scroll",
            action=f"Mouse scroll {direction}",
            priority=config.get_event_priority(),
            step_on=f"{config.get_step_prefix()} {self.counter}",
            time_from_last=time_diff,
            step_desc=f"Scroll {direction} at position ({x}, {y})",
            step_accep="none",
            step_resau=f"Scroll amount: {abs(dy)}",
            pic_path="none",
            screenshot_counter=0,
            image_name="none"
        )

        if self.save == True:
            # Add event to current test
            self.current_test.add_event(event)
            
            # Update the floating window
            self.event_window.update_event(event)
            self.last_event_time = neto_time

def main(test_name=None, starting_point="none", precondition="nothing for now"):
    """
    Main function to start the test recording process.

    This function initializes the event window and event listener, starts mouse and keyboard listeners,
    and runs the main event loop for recording test events. It is the entry point for running a test recording session.

    Parameters
    ----------
    test_name : str, optional
        The name of the test being recorded. If None, a default name is used.
    starting_point : str, optional
        The starting point for the test recording. Defaults to "none".

    Returns
    -------
    Test
        The Test object containing all recorded events and metadata.
    """
    # # Check if another instance is already running
    # if is_already_running(lock_file):
    #     sys.exit(1)
    run_log.add("*************************************", level="INFO")
    run_log.add("start recording test " + test_name)    
    # Register cleanup function
    register_cleanup(lock_file)
    
    # Close any existing mouse listener threads
    close_existing_mouse_threads()
    
    # Create the floating window with test name
    event_window = EventWindow(test_name=test_name, run_number=1, run_total=1)
    
    # Create the event listener
    listener = EventListener(event_window, test_name, starting_point, precondition)
    
    # Start the mouse listener
    mouse_listener = mouse.Listener(
        on_click=listener.on_click,
        on_move=listener.on_move,  # Add mouse movement tracking
        on_scroll=listener.on_scroll  # Add scroll tracking
    )
    mouse_listener.name = "MouseListener"
    mouse_listener.start()
    
    # Start the keyboard listener
    keyboard_listener = keyboard.Listener(
        on_press=listener.on_press
    )
    keyboard_listener.start()
    
    # Start the main loop
    event_window.mainloop()
    
    # Stop the listeners
    mouse_listener.stop()
    keyboard_listener.stop()
    
    # Join the threads
    mouse_listener.join()
    keyboard_listener.join()
    
    return listener.current_test

if __name__ == "__main__":
    main() 