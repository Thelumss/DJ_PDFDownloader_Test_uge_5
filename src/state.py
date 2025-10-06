import threading
from enum import Enum
from dataclasses import dataclass


class ISyncState:
    def __init__(self):
        self.lock = threading.Lock()

    def Read(self):
        '''
        '''
        pass

    def Write(self, state):
        pass


class ReportState(Enum):
    INIT = 0,
    DOWNLOADED = 1,
    NOT_DOWNLOADED = 2


@dataclass
class Report:
    name: str
    url: str
    path: str
    status: ReportState


class ReportSyncState(ISyncState):
    def __init__(self):
        super().__init__()
        self.report: list[Report] = []

    def Read(self) -> Report:
        with self.lock:
            return self.report

    def Write(self, _report: Report):
        with self.lock:
            self.report = _report
