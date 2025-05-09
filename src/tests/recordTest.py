"""
Test recording module for capturing mouse and keyboard events.
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
from src.utils.picture_handle import capture_screen, generate_screenshot_filename
from src.utils.event_mouse_keyboard import Event
from src.utils.process_utils import is_already_running, register_cleanup, cleanup_and_restart, save_test
from src.utils.app_lifecycle import restart_control_panel
from src.gui.event_window import EventWindow
from src.gui.screenshot_dialog import ScreenshotDialog
from src.utils.starting_points import go_to_starting_point


# Global lock file
lock_file = "cursor_listener.lock"
config = Config()

def close_existing_mouse_threads():
    """Close any existing mouse listener threads."""
    for thread in threading.enumerate():
        if thread.name == "MouseListener":
            thread._stop()
            thread.join()


class EventListener:
    def __init__(self, event_window, test_name=None,starting_point="none"):
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
        
        # Create a new test instance
        self.current_test = Test(
            config="nothing for now",
            comment1=f"Test: {test_name}" if test_name else "Test started",
            comment2=f"Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            starting_point=starting_point,
            total_time_in_screenshot_dialog=0

        )
        
    def on_click(self, x, y, button, pressed):
        if not self.running:
            return False
            
        # Check if we should track this type of event
        if pressed and not config.should_track_mouse_press():
            return True
        if not pressed and not config.should_track_mouse_release():
            return True
            
        # self.counter += 1
        # current_time = int(time.time() * 1000)
        # #print(f"current_time: {current_time}")
        # time_diff = current_time - self.last_event_time
        # #print(f"time_diff: {time_diff} , current_time: {current_time} , last_event_time: {self.last_event_time}")
        # time_total = current_time - self.start_time
        # #print(f"time_total: {time_total} , current_time: {current_time} , start_time: {self.start_time}")
        
        self.counter += 1
        current_time = int(time.time() * 1000)
        time_total = current_time - self.start_time
        neto_time = time_total - self.current_test.total_time_in_screenshot_dialog
        time_diff = neto_time - self.last_event_time




        # Different action text for press and release
        action_text = f"Mouse {button.name} pressed" if pressed else f"Mouse {button.name} released"
        
        event = Event(
            counter=self.counter,
            time=time_total,  # Total time since start
            neto_time=neto_time ,
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
            image_name="none",

        )
        #print(f"neto_time: {event.neto_time} , current_time: {current_time} , total_time_in_screenshot_dialog: {self.current_test.total_time_in_screenshot_dialog}")
        if self.save == True:
            # Add event to current test
            self.current_test.add_event(event)
            
            # Update the floating window
            self.event_window.update_event(event)
            self.last_event_time =neto_time
 

    def on_press(self, key):

        # self.counter += 1
        # current_time = int(time.time() * 1000)
        # time_total = current_time - self.start_time - self.current_test.total_time_in_screenshot_dialog
        # time_diff = time_total - self.last_event_time - self.current_test.total_time_in_screenshot_dialog
        # print(f"time_total: {time_total} , current_time: {current_time} , start_time: {self.start_time} , total_time_in_screenshot_dialog: {self.current_test.total_time_in_screenshot_dialog}")
        # print(f"time_diff: {time_diff} , current_time: {current_time} , last_event_time: {self.last_event_time} , total_time_in_screenshot_dialog: {self.current_test.total_time_in_screenshot_dialog}")
        self.counter += 1
        current_time = int(time.time() * 1000)
        time_total = current_time - self.start_time
        neto_time = time_total - self.current_test.total_time_in_screenshot_dialog
        time_diff = neto_time - self.last_event_time

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
                    if dialog.result:
                        #Add a small delay to allow the window to update
                        time.sleep(0.1)  # 100ms delay
                        screenshot = capture_screen() # capture the screen
                        if screenshot:
                            # Generate screenshot filename with test name
                            self.screenshot_counter += 1
                            screenshot_filename, screenshot_path = generate_screenshot_filename(
                                self.test_name, self.screenshot_counter, dialog.result['image_name'],"Recording","none")
                            
                            if screenshot_filename and screenshot_path:
                                self.save = True # Resume saving events
                                # Store screenshot in event and save it
                                event.screenshot = screenshot
                                event.save_screenshot(screenshot_path)
                                # Use dialog results
                                event.step_desc = dialog.result['step_desc']
                                event.step_accep = dialog.result['step_accep']
                                event.priority = dialog.result['priority']
                                event.pic_path = screenshot_path
                                event.time_in_screenshot_dialog = time_in_dialog  # Store the time spent in dialog
                                self.current_test.numOfSteps += 1
                                self.current_test.stepResult.append([dialog.result['image_name'], "-"])
                                event.screenshot_counter = self.screenshot_counter
                                event.image_name = dialog.result['image_name']
                                self.current_test.total_time_in_screenshot_dialog += time_in_dialog

                     
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
                    
                    # Schedule window destruction and control panel restart in the main thread
                    self.event_window.after(0, lambda: cleanup_and_restart(self.event_window))
                    return False
            else:
                self.save = True  
        if self.save == True:        
            # Add event to current test
            self.current_test.add_event(event)
            
            # Update the floating window
            self.event_window.update_event(event)
            
        self.last_event_time = neto_time

def main(test_name=None, starting_point="none"):
    """Main function to start the event listener."""
    # Check if another instance is already running
    if is_already_running(lock_file):
        sys.exit(1)
        
    # Register cleanup function
    register_cleanup(lock_file)
    
    # Close any existing mouse listener threads
    close_existing_mouse_threads()
    
    # Create the floating window
    event_window = EventWindow()
    
    # Create the event listener
    listener = EventListener(event_window, test_name,starting_point)
    
    # Start the mouse listener
    mouse_listener = mouse.Listener(
        on_click=listener.on_click
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