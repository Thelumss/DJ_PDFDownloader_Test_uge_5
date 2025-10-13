from itertools import chain, repeat
from types import SimpleNamespace
import unittest
from unittest.mock import patch,MagicMock
from pdfdownloader import PDFDownloader
from logger import LogLevel
from collections import deque
from state import ReportState


class TestPdfdownloader(unittest.TestCase):

    def setUp(self):
        self.dummy_conf = SimpleNamespace(
            log_level=LogLevel.INFO,
            concurrent_tasks=5,
            in_file_path='dummy_input.csv',
            out_dir_path='dummy_output_dir'
        )
        self.obj = PDFDownloader(self.dummy_conf)
        self.obj.task_handler = MagicMock()

        patcher = patch('pdfdownloader.URLDownloaderTask', autospec=True)
        self.mock_URLDownloaderTask = patcher.start()
        self.addCleanup(patcher.stop)

    def test_files_written_true(self):
        with patch('pdfdownloader.ThreadPoolHandler') as MockHandler:
            mock_task_handler = MagicMock()
            mock_task_handler.ActiveTaskCount.return_value = 1

            obj = PDFDownloader(self.dummy_conf)
            obj.task_handler = mock_task_handler

            self.assertTrue(obj.FilesWritten())

    def test_files_written_false(self):
        with patch('pdfdownloader.ThreadPoolHandler') as MockHandler:
            mock_task_handler = MagicMock()
            mock_task_handler.ActiveTaskCount.return_value = 2

            obj = PDFDownloader(self.dummy_conf)
            obj.task_handler = mock_task_handler

            self.assertFalse(obj.FilesWritten())
    
    def test_refill_download_queue_with_reports(self):
        with patch('pdfdownloader.ThreadPoolHandler') as MockHandler:
            
            report1 = MagicMock()
            report1.name = "report1"
            report1.status = None
            report2 = MagicMock()
            report2.name = "report2"
            report2.status = None

            self.obj.report_queue = deque([report1, report2])
            self.obj.files_to_download = 2

            self.obj.task_handler.ActiveTaskCount.side_effect = [1, 2, 3, 3]  

            result = self.obj.RefillDownloadQueue()

            
            self.assertEqual(report1.status, ReportState.STAGED)
            self.assertEqual(report2.status, ReportState.STAGED)

            
            self.assertEqual(self.mock_URLDownloaderTask.call_count, 2)

            
            self.assertEqual(self.obj.task_handler.Start.call_count, 2)

            self.assertFalse(result)

    def test_refill_download_queue_all_done(self):
        with patch('pdfdownloader.ThreadPoolHandler') as MockHandler:
            
            self.obj.report_queue = deque()
            self.obj.files_to_download = 0

            
            self.obj.task_handler.ActiveTaskCount.return_value = 1

            
            result = self.obj.RefillDownloadQueue()

            
            self.assertTrue(result)

    def test_refill_download_queue_partial(self):
        with patch('pdfdownloader.ThreadPoolHandler') as MockHandler:
            mock_task_handler = MagicMock()
    
            
            mock_task_handler.ActiveTaskCount.side_effect = chain([2, 1], repeat(1))
    
            self.obj.task_handler = mock_task_handler
    
           
            report = MagicMock()
            report.name = "test_doc"
            report.status = ReportState.INIT
    
            self.obj.report_queue = deque([report])
            self.obj.files_to_download = 1
    
            result = self.obj.RefillDownloadQueue()
    
           
            self.assertEqual(report.status, ReportState.STAGED)
            mock_task_handler.Start.assert_called_once()
            self.assertTrue(result)  
    

if __name__ == '__main__':
    unittest.main()
