from enum import Enum
import signal
import time
import argparse
import yaml
from collections import deque
from logger import Logger, LogLevel
from task_handler import ThreadPoolHandler
from task import FileReaderTask, FileWriterTask, URLDownloaderTask, LoggerTask
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
    def __init__(self,
                 _in_file: str,
                 _out_file: str,
                 _out_pdf_dir: str,
                 _log_level: bool,
                 _n_tasks: int):
        self.in_file_path = _in_file
        self.out_file = _out_file
        self.out_dir_path = _out_pdf_dir
        self.log_level = LogLevel.TRACE if _log_level\
            else LogLevel.INFO
        self.concurrent_tasks = _n_tasks

    @classmethod
    def Create(cls,  *args, **kwargs) -> object | None:
        if args[0].config:
            yml = Config.LoadYMLFile(args[0].config)
            if not yml:
                return None
            return cls(
                _in_file=yml['in_file'],
                _out_file=yml['out_file'],
                _out_pdf_dir=yml['out_pdf_dir'],
                _log_level=yml['verbose'],
                _n_tasks=yml['tasks'])
        if args[0].in_file:

            # Default params if optional args is None
            out_file = args[0].out_file\
                if args[0].out_file else "data/output.csv"
            out_dir_path = args[0].out_pdf_dir\
                if args[0].out_pdf_dir else "data/out"
            log_level = True\
                if args[0].verbose\
                else False
            tasks = args[0].tasks\
                if args[0].tasks else 10

            return cls(
                _in_file=args[0].in_file,
                _out_file=out_file,
                _out_pdf_dir=out_dir_path,
                _log_level=log_level,
                _n_tasks=tasks)
        return None

    @staticmethod
    def LoadYMLFile(file_path):
        with open(file_path, 'r') as f:
            data = yaml.load(f, Loader=yaml.SafeLoader)
            return data
        return None


class PDFDownloader:
    ''' Top level class for handling application related tasks
    '''

    def __init__(self, conf: Config):
        """Initialize the application .

        Args:
            conf (Config): config build on arguments given to program
        """
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

        # Setup logger task
        self.logger_task = LoggerTask(Logger().GetState())
        self.task_handler.Start(self.logger_task)

        Logger().Info("----- PDF-Downloader -----")
        Logger().Info(" Configuration:")
        Logger().Info(f" * Input file: \"{self.config.in_file_path}\"")
        Logger().Info(f" * Output dir: \"{self.config.out_dir_path}\"")
        Logger().Info(
            f" * Number of concurrent tasks: {self.config.concurrent_tasks}")

    def Run(self):
        """Continuously run the application .
        """

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
                    if self.FilesWritten():
                        Logger().Info(" All files have been written")
                        self.status = ApplicationState.SHUTDOWN
                case ApplicationState.SHUTDOWN:
                    Logger().Info(" Shutting down program")
                    self.task_handler.StopAllTasks()
                    self.is_running = False
            time.sleep(0.1)

    def RefillDownloadQueue(self) -> bool:
        """Refill the queue of files to download .

        Returns:
            bool: true if all files are downloaded
        """
        while self.task_handler.ActiveTaskCount()\
                < self.config.concurrent_tasks + 1:
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
           and self.task_handler.ActiveTaskCount() == 1:
            return True
        return False

    def FilesWritten(self) -> bool:
        """Checks running tasks.

        Returns:
            bool: true if only 1 task is running (logger task)
            otherwise false
        """
        if self.task_handler.ActiveTaskCount() == 1:
            return True
        return False

    def HandleSigint(self, signum, frame):
        """Handle the SIGINT signal .

        Args:
            signum ([type]): unused
            frame ([type]): unused
        """
        Logger().Trace("Shutting down application")
        self.status = ApplicationState.SHUTDOWN

    def ParseArgs() -> Config:
        parser = argparse.ArgumentParser(description="PDF downloader program")
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("-c", "--config",
                           type=str,
                           help="Path to config *.yml file")

        group.add_argument("-i", "--in_file",
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
                            action='store_true',
                            help="Verbose output for program")
        args = parser.parse_args()
        if args.config and (args.in_file or
           args.out_pdf_dir or
           args.out_file or
           args.tasks or
           args.verbose):
            parser.error(
                "Cannot use config file "
                "together with the other arguments")
            return None
        return Config.Create(args)


if __name__ == "__main__":
    config = PDFDownloader.ParseArgs()
    if config:
        app = PDFDownloader(config)
        app.Run()
    else:
        print("Invalid Config")
