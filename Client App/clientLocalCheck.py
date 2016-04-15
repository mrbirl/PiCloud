import time
import eventWatch
import threading
import watchdog.observers as observers


class localCheck:

    killThreads = False

    def __init__(self, paths):
        threadList = []
        for path in paths:
            # Create a monitoring thread for each path to be monitored
            t = threading.Thread(target=self.start, args=(path,))
            threadList.append(t)
            t.daemon = True
            t.start()

    def start(self, path):
        thePath = path
        event_handler = eventWatch.watcher()
        observer = observers.Observer()
        observer.schedule(event_handler, thePath, recursive=True)
        observer.start()
        while not localCheck.killThreads:
            time.sleep(1)
        observer.stop()
        observer.join()

    def stopThreads(self):
        # Depreciated - threads stop when main stops
        localCheck.killThreads = True
