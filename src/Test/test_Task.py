
from types import SimpleNamespace
import unittest
import os
import sys
from unittest.mock import MagicMock, patch

import pandas as pd
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from state import ReportState
from task import FileReaderTask, TaskState
from logger import LogLevel


class URLDownloaderTask_Test(unittest.TestCase):
    def Setup(self):
        self.dummy_conf = SimpleNamespace(
            log_level=LogLevel.INFO,
            concurrent_tasks=5,
            in_file_path='dummy_input.csv',
            out_dir_path='dummy_output_dir'
        )
        self.obj = FileReaderTask(self.dummy_conf)


    import unittest
from unittest.mock import patch, MagicMock
import pandas as pd

from task import FileReaderTask, TaskState  # Adjust import path

class URLDownloaderTask_Test(unittest.TestCase):

    @patch('task.Logger')
    @patch.object(FileReaderTask, 'FileExists')
    @patch.object(FileReaderTask, 'ValidateURL')
    @patch('task.pd.ExcelFile')
    def test_start_Download_true(self, mock_excel_file, mock_validate_url, mock_file_exists, mock_logger):
        
        task = FileReaderTask('file.xlsx', '/pdfs')
        task.name = 'TestTask'

        
        task.timer = MagicMock()
        task.timer.Start = MagicMock()
        task.Stop = MagicMock(side_effect=lambda: setattr(task, 'status', TaskState.DONE))


        
        mock_report_state = MagicMock()
        mock_report_state.Count = MagicMock(return_value=1)
        mock_report_state.Append = MagicMock()
        task.report_state = mock_report_state

        
        df = pd.DataFrame([{
            'BRnum': '123',
            'Pdf_URL': 'http://example.com/doc.pdf'
        }])
        mock_excel_file.return_value.parse.return_value = df

        
        mock_validate_url.return_value = True
        mock_file_exists.return_value = False

        
        task.Start()

        
        self.assertEqual(task.status, TaskState.DONE)  # Final state
        task.timer.Start.assert_called_once()
        task.Stop.assert_called_once()
        mock_report_state.Append.assert_called_once()
        mock_logger.return_value.Trace.assert_any_call('Read entry:\n 123 - http://example.com/doc.pdf')
        mock_logger.return_value.Info.assert_called_once()




    @patch('task.Logger')
    @patch.object(FileReaderTask, 'FileExists')
    @patch.object(FileReaderTask, 'ValidateURL')
    @patch('task.pd.ExcelFile')
    def test_start_Download_false_URL(self, mock_excel_file, mock_validate_url, mock_file_exists, mock_logger):
        
        task = FileReaderTask('file.xlsx', '/pdfs')
        task.name = 'TestTask'

        
        task.timer = MagicMock()
        task.timer.Start = MagicMock()
        task.Stop = MagicMock(side_effect=lambda: setattr(task, 'status', TaskState.DONE))


        
        mock_report_state = MagicMock()
        mock_report_state.Count = MagicMock(return_value=1)
        mock_report_state.Append = MagicMock()
        task.report_state = mock_report_state

        
        df = pd.DataFrame([{
            'BRnum': '123',
            'Pdf_URL': 'http://example.com/doc.pdf'
        }])
        mock_excel_file.return_value.parse.return_value = df

        
        mock_validate_url.return_value = False
        mock_file_exists.return_value = False

        
        task.Start()

        
        self.assertEqual(task.status, TaskState.DONE)  # Final state
        task.timer.Start.assert_called_once()
        task.Stop.assert_called_once()
        mock_report_state.Append.assert_called_once()
        
        appended_report = mock_report_state.Append.call_args[0][0]
        self.assertEqual(appended_report.url,'None')
        self.assertEqual(appended_report.status, ReportState.NOT_DOWNLOADED)
        
        mock_logger.return_value.Trace.assert_any_call('Read entry:\n 123 - None')
        mock_logger.return_value.Info.assert_called_once()




    @patch('task.Logger')
    @patch.object(FileReaderTask, 'FileExists')
    @patch.object(FileReaderTask, 'ValidateURL')
    @patch('task.pd.ExcelFile')
    def test_start_Download_false_Internet_failure(self, mock_excel_file, mock_validate_url, mock_file_exists, mock_logger):
        
        task = FileReaderTask('file.xlsx', '/pdfs')
        task.name = 'TestTask'

        
        task.timer = MagicMock()
        task.timer.Start = MagicMock()
        task.Stop = MagicMock(side_effect=lambda: setattr(task, 'status', TaskState.DONE))


        
        mock_report_state = MagicMock()
        mock_report_state.Count = MagicMock(return_value=0)
        mock_report_state.Append = MagicMock()
        task.report_state = mock_report_state

        
        df = pd.DataFrame([{
            'BRnum': '123',
            'Pdf_URL': 'http://example.com/doc.pdf'
        }])
        mock_excel_file.return_value.parse.side_effect = Exception("Internet connection failed")

        
        mock_validate_url.return_value = True
        mock_file_exists.return_value = False

        
        task.Start()

        
        self.assertEqual(task.status, TaskState.ERROR)  # Final state
        mock_logger.return_value.Error.assert_called()
        error_call_args = mock_logger.return_value.Error.call_args[0][0]
        self.assertIn("Internet connection failed", error_call_args)

if __name__ == '__main__':
    unittest.main()
