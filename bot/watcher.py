import os
import subprocess
import sys
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

WATCH_EXTENSIONS = (".py",)


class RestartHandler(FileSystemEventHandler):
    def __init__(self, process_starter):
        self.process_starter = process_starter
        self.process = self.process_starter()
        self.last_modified = time.time()

    def restart_process(self):
        now = time.time()
        if now - self.last_modified < 1:
            return
        self.last_modified = now

        print("🔁 Перезапуск бота...")
        self.process.terminate()
        self.process.wait()
        self.process = self.process_starter()

    def on_modified(self, event):
        if (
            event.is_directory
            or "__pycache__" in event.src_path
            or not event.src_path.endswith(WATCH_EXTENSIONS)
        ):
            return
        self.restart_process()


def start_bot():
    return subprocess.Popen([sys.executable, "main.py"])


if __name__ == "__main__":
    watch_path = os.path.abspath(".")
    event_handler = RestartHandler(start_bot)
    observer = Observer()
    observer.schedule(event_handler, watch_path, recursive=True)
    observer.start()

    print(f"👀 Watchdog следит за изменениями в: {watch_path}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        event_handler.process.terminate()

    observer.join()
