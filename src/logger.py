from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from state import ISyncState
from collections import deque


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args,
                                                                 **kwargs)
        return cls._instances[cls]


class LogLevel(Enum):
    TRACE = 0,
    INFO = 1,
    WARN = 2,
    ERROR = 3,
    FATAL = 4


@dataclass
class LogEntry:
    stamp: datetime
    severity: LogLevel
    msg: str

    def __repr__(self):
        return f"[{self.stamp.isoformat()}:{self.severity.name}]:{self.msg}"


class LogSyncState(ISyncState):
    def __init__(self):
        super().__init__()
        self.msgs: deque[LogEntry] = deque()

    def Read(self):
        with self.lock:
            return self.msgs.copy()

    def Write(self, entry: LogEntry):
        with self.lock:
            self.msgs.append(entry)


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Logger(metaclass=Singleton):
    def __init__(self, _log_level=LogLevel.INFO):
        self.log_level: LogLevel = _log_level
        self.log_state = LogSyncState()

    def SetLevel(self, _log_level):
        self.log_level = _log_level

    def Trace(self, msg: str):
        if self.log_level.value <= LogLevel.TRACE.value:
            entry = LogEntry(datetime.now(), LogLevel.TRACE, msg)            
            self.log_state.Write(entry)
            print(f"{bcolors.OKBLUE}{entry}{bcolors.ENDC}")

    def Info(self, msg: str):
        if self.log_level.value <= LogLevel.INFO.value:
            entry = LogEntry(datetime.now(), LogLevel.INFO, msg)
            self.log_state.Write(entry)
            print(f"{bcolors.OKGREEN}{entry}{bcolors.ENDC}")       

    def Warn(self, msg: str):
        if self.log_level.value <= LogLevel.WARN.value:
            entry = LogEntry(datetime.now(), LogLevel.WARN, msg)
            self.log_state.Write(entry)
            print(f"{bcolors.WARNING}{entry}{bcolors.ENDC}")

    def Error(self, msg: str):
        if self.log_level.value <= LogLevel.ERROR.value:
            entry = LogEntry(datetime.now(), LogLevel.ERROR, msg)
            self.log_state.Write(entry)
            print(f"{bcolors.FAIL}{entry}{bcolors.ENDC}")

    def Fatal(self, msg: str):
        entry = LogEntry(datetime.now(), LogLevel.FATAL, msg)
        self.log_state.Write(entry)
        print(f"{bcolors.FAIL}{bcolors.UNDERLINE}{entry}{bcolors.ENDC}")
