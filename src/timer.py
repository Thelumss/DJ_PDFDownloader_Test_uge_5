import time


class Timer:
    """Simple timer class to display duration between
    start and stop in miliseconds.
    """
    def __init__(self):
        self.start_stamp: time = None
        self.stop_stamp: time = None

    def Start(self):
        """Starts the timer.
        """
        self.start_stamp = time.time()

    def Stop(self):
        """Stops the timer.
        """
        self.stop_stamp = time.time()

    def DurationMS(self) -> float:
        """Returns the Duration in miliseconds between start and
        stop timestamps.

        Returns:
            float: miliseconds
        """
        return (self.stop_stamp - self.start_stamp)*1000
