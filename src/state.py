import threading
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod


class ISyncState(ABC):
    def __init__(self):
        self.lock = threading.Lock()

    @abstractmethod
    def Read(self):
        '''
        '''
        pass

    @abstractmethod
    def Write(self, state):
        pass


class ReportState(Enum):
    INIT = 0,
    STAGED = 1,
    DOWNLOADED = 2,
    NOT_DOWNLOADED = 3,
    DONE = 4


@dataclass
class Report:
    name: str
    id: int
    url: str
    status: ReportState


class ReportSyncState(ISyncState):
    def __init__(self):
        super().__init__()
        self.reports: list[Report] = []

    def Read(self) -> list[Report]:
        with self.lock:
            return self.reports.copy()

    def Write(self, _report: Report):
        with self.lock:
            self.reports.append(_report)

    def Count(self):
        with self.lock:
            return len(self.reports)
