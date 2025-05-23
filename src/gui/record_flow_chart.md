flowchart TD
    run_ATA_2 --> init_ControlPanel

    run_ATA_2(["run the ATA APP"])
    init_ControlPanel("run Main GUI form in ControlPanel(root)<br><br>Main GUI = class ControlPanel")

    init_ControlPanel -->|press Record button| start_recording_control_Panel

    subgraph start_recording_control_Panel["def start_recording(self)"]
    start_recording_button>"Start recording a new test."] --> killOldListener

    killOldListener("self.killOldListener() <br> kill any existing listener")

    killOldListener --> TestNameDialog
    TestNameDialog("TestNameDialog() <br> run New Test Data form GUI <br><br> Test Name - string <br> Test Purpose - string <br> Accuracy Level - number <br> starting point - enumeration <br> OK/CANCEL button")

    TestNameDialog -->|press OK| go_to_starting_point
    go_to_starting_point("go_to_starting_point(starting_point) <br><br> Navigate to the specified starting point before beginning test recording like desktop\\googlemap\\etc..")

    go_to_starting_point --> start_recording
    start_recording("start_recording(test_name, starting_point) <br><br>Start Recording") 

    end
    TestNameDialog -->|press CANCEL| init_ControlPanel

    subgraph recordTest["def_main(test_name,starting_point)"]
    start_recording --> main
    main>" Main function to start the event listener"]

    main-->register_cleanup
    register_cleanup("register_cleanup(lock_file) <br><br>delete the cursor_listener.lock on exit, avoid leftover files or resources ")

    register_cleanup-->close_existing_mouse_threads
    close_existing_mouse_threads("close_existing_mouse_threads() <br><br>Close any existing mouse listener threads")
    
    close_existing_mouse_threads-->EventWindow
    EventWindow(" EventWindow(test_name=test_name) <br><br> Create the floating window with test name")
    
    EventWindow-->EventListener
    EventListener("EventListener (event_window, test_name, starting_point) <br><br> Create the event listener, will be use while running to present the user commands  ")
    
    EventListener-->mouse.Listener
    mouse.Listener("mouse.Listener(
        on_click=listener.on_click,
        on_move=listener.on_move,
        on_scroll=listener.on_scroll <br><br>
        add listener to all the mouse operation 
        + name the listenr
        + start the listener")

    mouse.Listener-->  keyboard.Listener
    keyboard.Listener("keyboard.Listener(
        on_press=listener.on_press)<br><br>
        add listener to all the keyboard operation 
        + name the listenr
        + start the listener") 

    keyboard.Listener-->run_EventWindow["event_window.mainloop() <br><br>run trnasperent event window "]
    end
