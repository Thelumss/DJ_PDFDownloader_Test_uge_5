from enum import Enum
import signal
import time
import argparse
from collections import deque
from logger import Logger, LogLevel
from task_handler import ThreadPoolHandler
from task import FileReaderTask, FileWriterTask, URLDownloaderTask
from state import Report, ReportState


class ApplicationState(Enum):
    ''' Application states
    '''
    INITIALIZING = 0,
    READ = 1,
    DOWNLOAD = 2,
    WRITE = 3,
    SHUTDOWN = 4


class Config:
    def __init__(self, args: list[str]):
        self.in_file_path = args.in_file
        self.out_file = args.out_file
        self.out_dir_path = args.out_pdf_dir
        self.concurrent_tasks = args.tasks
        self.log_level = LogLevel.TRACE if args.verbose else LogLevel.INFO


class PDFDownloader:
    ''' Top level class for handling application related tasks
    '''

    def __init__(self, conf: Config):
        self.status = ApplicationState.INITIALIZING
        self.is_running: bool = True

        self.config = conf

        Logger().SetLevel(self.config.log_level)
        signal.signal(signal.SIGINT, self.HandleSigint)
        self.task_handler = ThreadPoolHandler(self.config.concurrent_tasks)

        # Read file task
        self.read_task = FileReaderTask(self.config.in_file_path)
        self.reports: list[Report] = []

        # Download task
        self.download_task_queue: deque[URLDownloaderTask] = deque()
        self.report_queue: deque[Report] = deque()

        Logger().Info("----- PDF-Downloader -----")
        Logger().Info(" Configuration:")
        Logger().Info(f" * Input file: \"{self.config.in_file_path}\"")
        Logger().Info(f" * Output dir: \"{self.config.out_dir_path}\"")
        Logger().Info(
            f" * Number of concurrent tasks: {self.config.concurrent_tasks}")

    def Run(self):

        self.status = ApplicationState.READ
        self.task_handler.Start(self.read_task)

        while self.is_running:
            match self.status:
                case ApplicationState.READ:
                    if self.task_handler.IsDone(self.read_task):
                        Logger().Info(f" {self.read_task.name} task completed")
                        self.reports = self.read_task.ReadData()
                        self.report_queue = \
                            [item for item in self.reports
                             if item.status == ReportState.INIT]
                        self.files_to_download = len(self.report_queue)
                        if self.files_to_download == 0:
                            self.status = ApplicationState.SHUTDOWN
                        else:
                            Logger().Info((
                                f" {self.files_to_download}"
                                " documents to download"))
                            self.status = ApplicationState.DOWNLOAD
                case ApplicationState.DOWNLOAD:
                    if self.RefillDownloadQueue():
                        Logger().Info(
                            (" All files have been downloaded to dir"
                             f"{self.config.out_dir_path}"))
                        Logger().Info((f" Writing {len(self.reports)}"
                                       f" entries to {self.config.out_file}"))
                        task = FileWriterTask(self.reports,
                                              self.config.out_file)
                        self.task_handler.Start(task)
                        self.status = ApplicationState.WRITE
                case ApplicationState.WRITE:
                    if self.RefillWriteQueue():
                        Logger().Info(" All files have been written")
                        self.status = ApplicationState.SHUTDOWN
                case ApplicationState.SHUTDOWN:
                    Logger().Info(" Shutting down program")
                    self.is_running = False
            time.sleep(0.1)

    def RefillDownloadQueue(self) -> bool:
        while self.task_handler.ActiveTaskCount() \
              < self.config.concurrent_tasks:
            if len(self.report_queue) == 0:
                break
            report = self.report_queue.pop()
            report.status = ReportState.STAGED
            task = URLDownloaderTask(report, self.config.out_dir_path)
            downloaded_files = self.files_to_download - len(self.report_queue)
            Logger().Info((f" Downloading: {report.name}.pdf"
                           f" ({downloaded_files}/{self.files_to_download})"))
            self.task_handler.Start(task)
        if len(self.report_queue) == 0 \
           and self.task_handler.ActiveTaskCount() == 0:
            return True
        return False

    def RefillWriteQueue(self) -> bool:
        if self.task_handler.ActiveTaskCount() == 0:
            return True
        return False

    def DownloadStatus(self) -> int:
        entries_to_download = \
            [item for item in self.reports if item.status == ReportState.INIT]
        return len(entries_to_download)

    def HandleSigint(self, signum, frame):
        Logger().Trace("Shutting down application")
        self.is_running = False
        self.status = ApplicationState.SHUTDOWN


if __name__ == "__main__":
    # argument parsing
    parser = argparse.ArgumentParser(description="PDF downloader program")
    parser.add_argument("-i", "--in_file",
                        type=str,
                        help="Path to input file in .xlsx format")
    parser.add_argument("-d", "--out_pdf_dir",
                        type=str,
                        help="Directory to store the downloaded pdf tiles")
    parser.add_argument("-o", "--out_file",
                        type=str,
                        help="Path to output file to store results")
    parser.add_argument("-n", "--tasks",
                        nargs='?', type=int,
                        help="Number of tasks to run in parallel")
    parser.add_argument("-v", "--verbose",
                        action='store_true', help="Verbose output for program")
    args = parser.parse_args()
    config = Config(args)
    app = PDFDownloader(config)
    app.Run()
