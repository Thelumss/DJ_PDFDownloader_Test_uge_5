from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from collections import deque
from state import ISyncState


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


class LogSyncState(ISyncState):
    def __init__(self):
        super().__init__()
        self.msgs: deque[LogEntry] = deque()

    def Read(self) -> deque[LogEntry]:
        """Returns a copy of the message queue.

        Returns:
            deque[LogEntry]: message queue
        """
        with self.lock:
            return self.msgs.copy()

    def Write(self, entry: LogEntry):
        """Writes the given log entry to the queue.

        Args:
            entry (LogEntry): [description]
        """
        with self.lock:
            self.msgs.append(entry)

    def Count(self):
        with self.lock:
            return len(self.msgs)

    def Pop(self):
        with self.lock:
            return self.msgs.pop()


class Logger(metaclass=Singleton):
    def __init__(self, _log_level=LogLevel.INFO):
        self.log_level: LogLevel = _log_level
        self.log_state = LogSyncState()

    def SetLevel(self, _log_level):
        """Sets the log level .

        Args:
            _log_level ([type]): LogLevel
        """
        self.log_level = _log_level

    def Trace(self, msg: str):
        """Log a message at the current state.

        Args:
            msg (str): message to log
        """
        if self.log_level.value <= LogLevel.TRACE.value:
            entry = LogEntry(datetime.now(), LogLevel.TRACE, msg)
            self.log_state.Write(entry)

    def Info(self, msg: str):
        """Log an info message.

        Args:
            msg (str): message to log
        """
        if self.log_level.value <= LogLevel.INFO.value:
            entry = LogEntry(datetime.now(), LogLevel.INFO, msg)
            self.log_state.Write(entry)

    def Warn(self, msg: str):
        """Log a warning message.

        Args:
            msg (str): message to log
        """
        if self.log_level.value <= LogLevel.WARN.value:
            entry = LogEntry(datetime.now(), LogLevel.WARN, msg)
            self.log_state.Write(entry)

    def Error(self, msg: str):
        """Log an error message.

        Args:
            msg (str): message to log
        """
        if self.log_level.value <= LogLevel.ERROR.value:
            entry = LogEntry(datetime.now(), LogLevel.ERROR, msg)
            self.log_state.Write(entry)

    def Fatal(self, msg: str):
        """Log a fatal error message.

        Args:
            msg (str): message to log

        Raises:
            Exception: message to log
        """
        entry = LogEntry(datetime.now(), LogLevel.FATAL, msg)
        self.log_state.Write(entry)
        raise Exception(entry)

    def GetState(self) -> LogSyncState:
        """Retrieves reference to shared state.
        Use only for Logger Task!

        Returns:
            LogSyncState: [description]
        """
        return self.log_state
