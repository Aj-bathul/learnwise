import os
import webbrowser
from threading import Timer
from app import create_app

app = create_app()

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == "__main__":
    debug = os.environ.get("FLASK_ENV") == "development"
    Timer(1, open_browser).start()
    app.run(host="127.0.0.1", port=5000, debug=debug)