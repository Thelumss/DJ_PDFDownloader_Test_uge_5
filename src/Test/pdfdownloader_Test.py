from itertools import chain, repeat
import os
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch,MagicMock
from collections import deque
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pdfdownloader import PDFDownloader
from logger import LogLevel


class TestPdfdownloader(unittest.TestCase):

    def setUp(self):
        self.dummy_conf = SimpleNamespace(
            log_level=LogLevel.INFO,
            concurrent_tasks=5,
            in_file_path='dummy_input.csv',
            out_dir_path='dummy_output_dir'
        )

    @patch('pdfdownloader.ThreadPoolHandler')
    def test_files_written_true(self, MockHandler):
        mock_task_handler = MagicMock()
        mock_task_handler.ActiveTaskCount.return_value = 1
        MockHandler.return_value = mock_task_handler

        obj = PDFDownloader(self.dummy_conf)
        obj.task_handler = mock_task_handler

        self.assertTrue(obj.FilesWritten())

    @patch('pdfdownloader.ThreadPoolHandler')
    def test_files_written_false(self, MockHandler):

        mock_task_handler = MagicMock()
        mock_task_handler.ActiveTaskCount.return_value = 2
        MockHandler.return_value = mock_task_handler

        obj = PDFDownloader(self.dummy_conf)
        obj.task_handler = mock_task_handler

        self.assertFalse(obj.FilesWritten())
    

if __name__ == '__main__':
    unittest.main()
