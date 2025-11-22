import threading
import webbrowser
import time
from app import app

# Specify the URL where your Dash app will be running
app_url = "http://127.0.0.1:8050" 

def open_browser():
    # Give the server a few seconds to start up before opening the browser
    time.sleep(2) 
    webbrowser.open(app_url)

if __name__ == '__main__':
    # Prevents the webbrowser.open call from blocking the main thread 
    # where the Dash server needs to run.
    threading.Thread(target=open_browser).start()
    app.run(debug=True, use_reloader=False)
