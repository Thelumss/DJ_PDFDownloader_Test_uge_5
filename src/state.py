import threading
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod


class ISyncState(ABC):
    def __init__(self):
        self.lock = threading.Lock()
        self.elapsed_time = 0

    @abstractmethod
    def Read(self):
        '''
        '''
        pass

    @abstractmethod
    def Write(self, state):
        pass

    @abstractmethod
    def Append(self, state):
        pass

    @abstractmethod
    def Count(self, state):
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


@dataclass
class ReportSyncData:
    reports: list[Report]
    duration: float


class ReportSyncState(ISyncState):
    def __init__(self):
        super().__init__()
        self.reports: list[Report] = []
        self.data = ReportSyncData([], 0)

    def Read(self) -> ReportSyncData:
        with self.lock:
            return self.data

    def Write(self, data: ReportSyncData):
        with self.lock:
            self.data = data

    def Append(self, _report: Report):
        with self.lock:
            self.data.reports.append(_report)

    def Count(self):
        with self.lock:
            return len(self.data.reports)
