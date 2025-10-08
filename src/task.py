from enum import Enum
from abc import ABC, abstractmethod
import pandas as pd
import urllib.request
import certifi
import ssl
import csv
from logger import Logger
from state import ReportSyncState, Report, ReportState


class TaskState(Enum):
    IDLE = 0,
    RUNNING = 1,
    DONE = 2,
    ERROR = -1


class ITask(ABC):
    ''' Task interface
    '''
    def __init__(self, _name: str, _continious: bool = False):
        self.status: TaskState = TaskState.IDLE
        self.handle: object = None
        self.continious: bool = _continious
        self.name: str = _name

    @abstractmethod
    def Start(self):
        ''' Virtual method to be overidden
        '''
        pass

    @abstractmethod
    def Stop(self):
        ''' Virtual method to be overidden
        '''
        pass

    @abstractmethod
    def ReadData(self):
        ''' Virtual method to be overidden
        '''
        pass


class FileWriterTask(ITask):
    ''' File writer task. Implements ITask.
    '''
    def __init__(self, _reports: list[Report], _file_path: str,
                 _name: str = "FileWriter"):
        super().__init__(_name, False)
        self.file_path = _file_path
        self.reports = _reports

    def Start(self):
        self.status = TaskState.RUNNING
        try:
            with open(self.file_path, 'a+') as f:
                f_writer = csv.writer(f)
                f.seek(0)
                if not f.read(1):
                    # file is empty
                    f_writer.writerow(["BRnum", "Row", "URL", "Status"])
                    Logger().Trace("Filefile header written")

                for report in self.reports:
                    row = [report.name,
                           report.id,
                           report.url,
                           report.status.name]
                    f_writer.writerow(row)
                    Logger().Trace(("Row written to file:"
                                    f" \"{self.file_path}\""))
        except Exception as e:
            Logger().Error(f"Exception: {e}")

    def Stop(self):
        self.status = TaskState.DONE

    def ReadData(self):
        return self.reports


class FileReaderTask(ITask):
    """File reader task. Implements ITask.
    """

    def __init__(self, _file_path: str,
                 _name: str = "FileReader"):
        """Contructs FileReader task to run async.

        Args:
            _file_path (str): Path to excel file to read
            _name (str, optional): Name of task. Defaults to "FileReader".
            _continious (bool, optional): Restarts on completion.
            Defaults to False.
        """
        super().__init__(_name, False)
        self.file_path = _file_path
        self.report_state = ReportSyncState()
        self.status = TaskState.IDLE

    def Start(self):
        """Read the file and process it .
        """
        self.status = TaskState.RUNNING
        try:
            df = pd.ExcelFile(self.file_path).parse()
            for index, row in df.iterrows():
                url: str = str(row['Pdf_URL'])
                status: ReportState = ReportState.INIT
                if not self.ValidateURL(url):
                    url = "None"
                    status = ReportState.NOT_DOWNLOADED
                report = Report(name=row['BRnum'], id=index,
                                url=url,
                                status=status)
                Logger().Trace(f"Read entry:\n {report.name} - {report.url}")
                self.report_state.Write(report)
            Logger().Info((f"{self.name} read {self.report_state.Count()}"
                           f" rows from \"{self.file_path}\""))
            self.Stop()
        except Exception as e:
            Logger().Error(f"Exception: {e}, on file read {self.file_path}")
            report = self.report_state.Read()
            report.status = ReportState.NOT_DOWNLOADED
            self.report_state.Write(report)

    def Stop(self):
        """Stops the task.
        """
        self.status = TaskState.DONE

    def ReadData(self) -> list[Report]:
        """Reads the report state .

        Returns:
            list[Report]: list of documents to download
        """
        return self.report_state.Read()

    def ValidateURL(self, url: str) -> bool:
        return url != "" and url != "nan" and url[:4] == "http"


class URLDownloaderTask(ITask):
    """Downloader task. Implements ITask
    """
    def __init__(self, _report: Report, _out_dir: str):
        super().__init__(f"Download: {_report.name} task")
        self.report_state: ReportSyncState = ReportSyncState()
        self.report_state.Write(_report)
        self.out_dir: str = _out_dir
        self.status: TaskState = TaskState.IDLE

    def Start(self):
        """Tries to downloads the pdf and reports the status.
        """
        self.status = TaskState.RUNNING
        report: Report = self.report_state.Read()[0]
        context = ssl.create_default_context(cafile=certifi.where())
        try:
            if report.status == ReportState.STAGED:
                response = urllib.request.urlopen(report.url, context=context)
                out_file = open(f"{self.out_dir}/{report.name}.pdf", "wb")
                out_file.write(response.read())
                report.status = ReportState.DOWNLOADED

            Logger().Trace(f" File \"{report.url}\" successfully downloaded")
        except Exception as e:
            Logger().Warn(f"Exception: {e},"
                          f" when trying to download: {report.url}")
            report.status = ReportState.NOT_DOWNLOADED

            self.status = TaskState.ERROR
        finally:
            if report.status == ReportState.STAGED:
                # should not happen
                Logger().Error(f"Unhandler report {report.name}")
        self.report_state.Write(report)

    def Stop(self):
        """Stops the task.
        """
        self.status = TaskState.DONE

    def ReadData(self):
        return self.report_state.Read()


class LoggerTask(ITask):
    ''' Logger task. Imlpements ITask
    '''
    def __init__(self):
        super().__init__()

    def Start(self):
        self.status = TaskState.RUNNING

    def Stop(self):
        self.status = TaskState.DONE
