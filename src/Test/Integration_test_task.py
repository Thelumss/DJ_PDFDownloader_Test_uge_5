import unittest
import os
import sys
import pandas as pd
import time
from tempfile import NamedTemporaryFile
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from task import FileReaderTask, TaskState, ReportState, Report

class FileReaderTaskIntegrationTest(unittest.TestCase):

    def setUp(self):
        with NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            self.tempfile_name = tmp.name

        df = pd.DataFrame([
            {'BRnum': 'BR001', 'Pdf_URL': 'http://cdn12.a1.net/m/resources/media/pdf/A1-Umwelterkl-rung-2016-2017.pdf'},
            {'BRnum': 'BR002', 'Pdf_URL': 'invalid-url'}
        ])

        with pd.ExcelWriter(self.tempfile_name, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)


    def tearDown(self):
        for _ in range(5):
            try:
                if os.path.exists(self.tempfile_name):
                    os.remove(self.tempfile_name)
                break
            except PermissionError:
                time.sleep(0.2)



    def test_start_integration(self):
        task = FileReaderTask(self.tempfile_name, '/tmp/pdfs')
        task.name = 'IntegrationTest'

        class ReportStateList(list):
            def Append(self, report):
                self.append(report)
            def Count(self):
                return len(self)

        task.report_state = ReportStateList()

        def validate_url(url):
            return url.startswith('http://') or url.startswith('https://')
        task.ValidateURL = validate_url


        task.FileExists = lambda path: False

        task.timer = type('timer', (), {'Start': lambda s: None, 'Stop': lambda s: None})()


        task.Start()

        self.assertEqual(task.status, TaskState.DONE)


        self.assertEqual(task.report_state.Count(), 2)

        valid_report = next((r for r in task.report_state if r.name == 'BR001'), None)
        self.assertIsNotNone(valid_report)
        self.assertEqual(valid_report.url, 'http://cdn12.a1.net/m/resources/media/pdf/A1-Umwelterkl-rung-2016-2017.pdf')
        self.assertIn(valid_report.status, (ReportState.INIT, ReportState.DOWNLOADED))

        invalid_report = next((r for r in task.report_state if r.name == 'BR002'), None)
        self.assertIsNotNone(invalid_report)
        self.assertEqual(invalid_report.url, 'None')
        self.assertEqual(invalid_report.status, ReportState.NOT_DOWNLOADED)


if __name__ == '__main__':
    unittest.main()
