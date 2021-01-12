# can't seem to use fsevents with /dev (?)



# import sys
# import time
# import logging
# from watchdog.observers import Observer
# from watchdog.events import LoggingEventHandler

# if __name__ == "__main__":
#     logging.basicConfig(level=logging.INFO,
#                         format='%(asctime)s - %(message)s',
#                         datefmt='%Y-%m-%d %H:%M:%S')
#     path = sys.argv[1] if len(sys.argv) > 1 else "/dev/"
#     event_handler = LoggingEventHandler()
#     observer = Observer()
#     observer.schedule(event_handler, path, recursive=True)
#     observer.start()
#     try:
#         while True:
#             time.sleep(1)
#     finally:
#         observer.stop()
#         observer.join()

#---------------------------------------------------

# import time, glob

# t0 = time.time()
# for i in range(1000):
# 	a = glob.glob("/dev/cu.usbmodem*")
# print(time.time() - t0)
# print(a)

#---------------------------------------------------

# from fsevents import Observer
# observer = Observer()
# observer.start()

# def callback(FileEvent):
#     print(FileEvent.mask)
#     print(FileEvent.name)

# from fsevents import Stream
# stream = Stream(callback, "/dev/")
# observer.schedule(stream)
