from enum import Enum
from abc import ABC, abstractmethod
import pandas as pd
from PyPDF2 import PdfReader
import urllib.request
import certifi
import ssl
import csv
import os
import time
from datetime import datetime
from timer import Timer
from logger import Logger, LogEntry, LogLevel, bcolors, LogSyncState
from logger import LogSyncData
from state import ReportSyncState
from state import ReportSyncData, Report, ReportState


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
        self.timer: Timer = Timer()

    @abstractmethod
    def Start(self):
        ''' Starts the task (task entry point).
        Virtual function to be overridden.
        '''
        pass

    @abstractmethod
    def Stop(self):
        ''' Performs the clean up for a task
        and marks its status as Done.
        Virtual function to be overridden.
        '''
        pass

    @abstractmethod
    def ReadData(self) -> object:
        """Returns the sync state data of the task.

        Returns:
            SyncDataObj: returns the implementation specific data object
        """
        pass


class FileWriterTask(ITask):
    ''' File writer task for writing output csv file with download results.
    Implements ITask.
    '''
    def __init__(self, _reports: list[Report], _file_path: str,
                 _name: str = "FileWriter"):
        super().__init__(_name, False)
        self.file_path = _file_path
        self.reports = _reports

    def Start(self):
        """Starts the task.
        """
        self.status = TaskState.RUNNING
        self.timer.Start()
        try:
            with open(self.file_path, 'a+', encoding="utf-8") as f:
                f_writer = csv.writer(f)
                f.seek(0)
                if not f.read(1):
                    # file is empty
                    f_writer.writerow(["BRnum", "Status", "Row", "URL"])
                    Logger().Trace("Filefile header written")

                for report in self.reports:
                    row = [report.name,
                           report.status.name,
                           report.id,
                           report.url]
                    f_writer.writerow(row)
                    Logger().Trace(("Row written to file:"
                                    f" \"{self.file_path}\""))
        except Exception as e:
            Logger().Error(f"Exception: {e}")

    def Stop(self):
        """Stops the task.
        """
        self.timer.Stop()
        self.status = TaskState.DONE

    def ReadData(self):
        """Returns the report data.
        TODO: use a sync object instead

        Returns:
            list[Report]: reports held
        """
        return self.reports


class FileReaderTask(ITask):
    """File reader task. Implements ITask.
    """

    def __init__(self, _file_path: str,
                 _pdf_dir: str,
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
        self.pdf_dir = _pdf_dir
        self.report_state = ReportSyncState()
        self.status = TaskState.IDLE

    def Start(self):
        """Read the file and process it .
        """
        self.status = TaskState.RUNNING
        self.timer.Start()
        try:
            df = pd.ExcelFile(self.file_path).parse()
            for index, row in df.iterrows():

                url: str = str(row['Pdf_URL'])
                status: ReportState = ReportState.INIT
                # Validate url
                if not self.ValidateURL(url):
                    url = "None"
                    status = ReportState.NOT_DOWNLOADED
                # check if file is already downloaded
                if self.FileExists(f"{self.pdf_dir}/{row['BRnum']}.pdf"):
                    status = ReportState.DOWNLOADED
                    Logger().Trace(f"File already downloaded: "
                                   f"\"{self.pdf_dir}/{row['BRnum']}.pdf\"")

                report = Report(name=row['BRnum'], id=index,
                                url=url,
                                status=status)
                Logger().Trace(f"Read entry:\n {report.name} - {report.url}")
                self.report_state.Append(report)
            Logger().Info((f"{self.name} read {self.report_state.Count()}"
                           f" rows from \"{self.file_path}\""))
            self.Stop()
        except Exception as e:
            Logger().Error(f"Exception: {e}, on file read {self.file_path}")
            self.status = TaskState.ERROR

    def Stop(self):
        """Stops the task.
        """
        self.timer.Stop()
        self.status = TaskState.DONE

    def ReadData(self) -> list[Report]:
        """Returns the report list.
        TODO: let this task hold a syncstate object

        Returns:
            list[Report]: list of documents to download
        """
        return self.report_state.Read().reports

    def ValidateURL(self, url: str) -> bool:
        """Checks if a URL is valid .

        Args:
            url (str): http or https

        Returns:
            bool: true if valid
        """
        return url != "" and url != "nan" and url[:4] == "http"

    def FileExists(self, path: str) -> bool:
        """Returns true if the specified file exists in the local filesystem .

        Args:
            path (str): path to file

        Returns:
            bool: true if exists
        """
        return os.path.exists(path)


class URLDownloaderTask(ITask):
    """Downloader task. Implements ITask
    """
    def __init__(self, _report: Report, _out_dir: str):
        super().__init__(f"Download: {_report.name} task")
        self.report_state: ReportSyncState = ReportSyncState()
        self.report_state.Append(_report)
        self.out_dir: str = _out_dir
        self.status: TaskState = TaskState.IDLE

    def Start(self):
        """Tries to downloads the pdf and reports the status.
        """
        self.status = TaskState.RUNNING
        self.timer.Start()

        report_data: ReportSyncData = self.report_state.Read()
        context = ssl.create_default_context(cafile=certifi.where())

        pdf_file = f"{self.out_dir}/{report_data.reports[0].name}.pdf"
        dir_path = os.path.dirname(pdf_file)

        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)

        try:
            if report_data.reports[0].status == ReportState.STAGED:
                # Try to download file
                response = urllib.request.urlopen(
                    report_data.reports[0].url,
                    context=context,
                    timeout=10)
                with open(pdf_file, "wb") as out_file:
                    out_file.write(response.read())
                    # Validate pdf by reading first page
                    reader = PdfReader(pdf_file)
                    _ = reader.pages[0].extract_text()

                report_data.reports[0].status = ReportState.DOWNLOADED

            Logger().Trace(f"File \"{report_data.reports[0].url}\" "
                           "successfully downloaded")
        except Exception as e:
            Logger().Warn(f"Exception: {e},"
                          f" when trying to download: "
                          f"{report_data.reports[0].url}")

            if os.path.exists(pdf_file):
                os.remove(os.path.abspath(pdf_file))
            report_data.reports[0].status = ReportState.NOT_DOWNLOADED
            self.status = TaskState.ERROR
        finally:
            if report_data.reports[0].status == ReportState.STAGED:
                # should not happen
                Logger().Error(f"Unhandler report "
                               f"{report_data.reports[0].name}")
        self.report_state.Write(report_data)

    def Stop(self):
        """Stops the task.
        """
        self.timer.Stop()
        self.status = TaskState.DONE

    def ReadData(self):
        return self.report_state.Read()


class LoggerTask(ITask):
    ''' Logger task which writes to std out and log file.
    Imlpements ITask
    '''
    def __init__(self, _state: LogSyncState, write_log: bool = True):
        super().__init__("Log Task", True)
        self.state: LogSyncState = _state
        now = datetime.now()
        self.log_file: str = f"logs/log_{now.strftime("%Y%m%d_%H%M%S")}.txt"
        self.log_to_file: bool = write_log

    def Start(self):
        """Starts the logger task.
        """
        self.status = TaskState.RUNNING
        self.timer.Start()
        while self.continious:
            while self.state.Count() > 0:
                entry = self.state.Pop()
                self.Print(entry)
                self.WriteFile(entry)
            time.sleep(0.1)

    def Stop(self):
        """Stop the task .
        """
        # clear queue
        while self.state.Count() > 0:
            entry = self.state.Pop()
            self.Print(entry)
            self.WriteFile(entry)
        self.continious = False
        self.timer.Stop()
        self.status = TaskState.DONE

    def ReadData(self) -> LogSyncData:
        """Reads the state of the logger.

        Returns:
            [type]: [description]
        """
        return self.state.Read()

    def Print(self, entry: LogEntry):
        prefix: str = ""

        match entry.severity:
            case LogLevel.TRACE:
                prefix = bcolors.OKBLUE
            case LogLevel.INFO:
                prefix = bcolors.OKGREEN
            case LogLevel.WARN:
                prefix = bcolors.WARNING
            case LogLevel.ERROR:
                prefix = bcolors.FAIL
            case LogLevel.FATAL:
                prefix = bcolors.FAIL + bcolors.UNDERLINE
        print(f"{prefix}{entry}{bcolors.ENDC}")

    def WriteFile(self, entry: LogEntry):
        with open(self.log_file, "a+") as file:
            file.write(f"{entry.__repr__()}\n")
            file.close()
