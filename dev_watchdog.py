import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from watchdog import *

watchdog.



if __name__ == "__main__":
    patterns = "*"
    ignore_patterns = ""
    ignore_directories = False
    case_sensitive = True
    my_event_handler = PatternMatchingEventHandler(patterns, ignore_patterns, ignore_directories, case_sensitive)

class MyHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        print(event.event_type, event.src_path)

    def on_created(self, event):
        print("on_created", event.src_path)

    def on_deleted(self, event):
        print("on_deleted", event.src_path)

    def on_modified(self, event):
        print("on_modified", event.src_path)

    def on_moved(self, event):
        print("on_moved", event.src_path)


event_handler = MyHandler()
observer = Observer()
observer.schedule(event_handler, path='/dev/', recursive=False)
observer.start()

while True:
    try:
        pass
    except KeyboardInterrupt:
        observer.stop()