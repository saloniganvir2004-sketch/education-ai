import threading
import time
import webbrowser
import urllib.request

from dotenv import load_dotenv
import os
import sys

def run_server():
    import uvicorn
    if getattr(sys, "frozen", False):
        env_path = os.path.join(os.getcwd(), ".env")
    else:
        env_path = os.path.join(os.path.dirname(__file__), ".env")

    load_dotenv(env_path)
    from api import app

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
)

server_thread = threading.Thread(target=run_server)
server_thread.start()

for _ in range(60):
    try:
        urllib.request.urlopen("http://127.0.0.1:8000/docs", timeout=1)
        break
    except Exception:
        time.sleep(1)

webbrowser.open("http://127.0.0.1:8000/docs")

while server_thread.is_alive():
    try:
        server_thread.join(timeout=1)
    except KeyboardInterrupt:
        os._exit(0)