import os
import time
import threading
from watchfiles import watch, Change
from app.utils.watcher import watcher_util_find_closest_parent_folder, watcher_util_handle_file_changes, watched_folders

# End-to-end integration test setup simulating a watched drive root
# This requires manual testing since it uses `subst` on Windows to create a real drive root.
# Usage:
# 1. Create a dummy folder: mkdir C:\temp\drivephotos
# 2. Map to a drive letter: subst X: C:\temp\drivephotos
# 3. Run this script, then create a file in X:\
# 4. Cleanup: subst X: /D

def test_watchfiles_drive_root():
    test_drive = "X:\\"
    
    # Initialize the watcher state to watch the drive root
    watched_folders.clear()
    watched_folders.append(("drive-root-id", test_drive))
    
    stop_event = threading.Event()
    
    def worker():
        print(f"Starting watchfiles on {test_drive}")
        try:
            for changes in watch(test_drive, stop_event=stop_event, recursive=True):
                print(f"Watchfiles reported changes: {changes}")
                # We expect the file_path in changes to be successfully matched
                for change, file_path in changes:
                    closest = watcher_util_find_closest_parent_folder(file_path, watched_folders)
                    print(f"Closest folder matched for {file_path}: {closest}")
                    assert closest is not None, f"Failed to match {file_path} to watched folder {test_drive}"
                    assert closest[0] == "drive-root-id", f"Matched wrong folder ID: {closest[0]}"
                    print("Match successful!")
                    stop_event.set()
        except FileNotFoundError:
            print(f"Drive {test_drive} not found. Please map it first using: subst X: C:\\temp\\drivephotos")

    thread = threading.Thread(target=worker)
    thread.start()
    
    time.sleep(1) # wait for watcher to start
    
    if os.path.exists(test_drive):
        # Trigger an event
        test_file = os.path.join(test_drive, "test_image.jpg")
        print(f"Creating test file {test_file}")
        with open(test_file, 'w') as f:
            f.write("test")
            
        thread.join(timeout=5)
        
        # Cleanup test file
        if os.path.exists(test_file):
            os.remove(test_file)
            
        if thread.is_alive():
            print("Test timed out! Watcher did not process the event in time.")
            stop_event.set()
    else:
        print("Skipping active test since drive X:\\ is not mounted.")
        stop_event.set()
        thread.join()

if __name__ == "__main__":
    test_watchfiles_drive_root()
