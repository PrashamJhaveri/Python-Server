import time
import threading

class Timer:
    def __init__(self, callback, time):
        self.time = time
        self.callback = callback
        self.timer = threading.Timer(time, callback)

    def start(self):
        self.timer.start()

    def pause(self):
        self.timer.cancel()

    def resume(self):
        self.timer = threading.Timer(self.time, self.callback)
        self.timer.start()