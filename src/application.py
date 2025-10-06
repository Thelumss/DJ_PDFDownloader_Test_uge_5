from enum import Enum
from logger import Logger, LogLevel
# from task import TaskHandler
from handler_threadpool import ThreadPoolHandler
from task_file import FileReaderTask
# from state import Report
import signal
import time


class ApplicationState(Enum):
    ''' Application states
    '''
    INITIALIZING = 0,
    RUNNING = 1,
    SHUTTING_DOWN = 2


class Application:
    ''' Top level class for handling application related tasks
    '''

    def __init__(self):
        self.status = ApplicationState.INITIALIZING
        self.is_running: bool = True
        Logger().SetLevel(LogLevel.TRACE)
        signal.signal(signal.SIGINT, self.HandleSigint)
        self.task_handler = ThreadPoolHandler(2)
        Logger().Trace("PDF downloader initialized")

    def Run(self):
        self.status = ApplicationState.RUNNING
        task = FileReaderTask("data/GRI_2017_2020 (1).xlsx")
        self.task_handler.Start(task)

        while self.is_running:
            if self.task_handler.IsDone(task):
                Logger().Info(f"Task Completed: {task.name}")
            time.sleep(0.1)

    def HandleSigint(self, signum, frame):
        Logger().Trace("Shutting down application")
        self.is_running = False
        self.status = ApplicationState.SHUTTING_DOWN
