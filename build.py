# Credit: https://github.com/thewilltejeda/htmx-desktop-app-01/blob/main/run.py

import webview
from threading import Thread, Event
from main import app

# This event will be set when we need to stop the Flask server
stopEvent = Event()

appTitle = "PictoPy"
host = "http://127.0.0.1"
port = 5000

def run():
    while not stopEvent.is_set():
        app.run(port=port, use_reloader=False)

if __name__ == '__main__':
    t = Thread(target=run)
    t.daemon = True  # This ensures the thread will exit when the main program exits
    t.start()

    webview.create_window(
        appTitle,
        f"{host}:{port}",
        # resizable=False,
        # height=710,
        # width=225,
        # frameless=True,
        easy_drag=True,
        on_top=True
        )
    
    webview.start()

    stopEvent.set()  # Signal the Flask server to shut down