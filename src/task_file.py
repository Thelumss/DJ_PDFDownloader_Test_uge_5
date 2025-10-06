from task import ITask, TaskState
import pandas as pd
from logger import Logger
from state import ReportSyncState, Report, ReportState


class FileWriterTask(ITask):
    ''' File writer task.
    Class for implementation of interface of ITask
    '''
    def __init__(self):
        super().__init__()

    def Start(self):
        self.status = TaskState.RUNNING

    def Stop(self):
        self.status = TaskState.DONE


class FileReaderTask(ITask):
    ''' File reading task.
    Class for implementation of interface of ITask
    '''
    def __init__(self, _file_path: str,
                 _name: str = "FileReader",
                 _continious: bool = False):
        super().__init__(_name, _continious)
        self.file_path = _file_path
        self.report_state = ReportSyncState()

    def Start(self):
        self.status = TaskState.RUNNING
        try:
            df = pd.ExcelFile(self.file_path).parse()
            for row in df.rows:

                report = Report(name=row['BRnum'], url=row['Pdf_URL'],
                                status=ReportState.INIT)
            self.report_state.Write(report)
        except Exception as e:
            Logger().Error(f"Exception: {e}, on file read {self.file_path}")
            report = self.report_state.Read()
            report.status = ReportState.NOT_DOWNLOADED
            self.report_state.Write(report)

    def Stop(self):
        self.status = TaskState.DONE

    def ReadData(self):
        ''' Virtual method to be overidden
        '''
        return self.report_state.Read()
