import time


class Timer:
    def __init__(self):
        self.start_stamp = 0
        self.stop_stamp = 0

    def Start(self):
        self.start_stamp = time.time()

    def Stop(self):
        self.stop_stamp = time.time()

    def DurationMS(self) -> float:
        return (self.stop_stamp - self.start_stamp)*1000
