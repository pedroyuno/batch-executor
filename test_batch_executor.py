#!/usr/bin/env python3
"""
Unit tests for the batch executor script.

This test suite covers all functionalities of the BatchExecutor class
and aims for at least 90% code coverage.
"""

import unittest
import tempfile
import os
import csv
import subprocess
from unittest.mock import patch, mock_open, MagicMock
import sys
import io
from contextlib import redirect_stdout, redirect_stderr

# Add the current directory to the path so we can import the module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from batch_executor import BatchExecutor, main


class TestBatchExecutor(unittest.TestCase):
    """Test cases for the BatchExecutor class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.command_file = os.path.join(self.temp_dir, 'command.txt')
        self.csv_file = os.path.join(self.temp_dir, 'ids.csv')
        
        # Create test command file
        with open(self.command_file, 'w') as f:
            f.write('echo "Processing ID: <id>"')
        
        # Create test CSV file
        with open(self.csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id1'])
            writer.writerow(['id2'])
            writer.writerow(['id3'])
    
    def tearDown(self):
        """Clean up after each test method."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_init(self):
        """Test BatchExecutor initialization."""
        executor = BatchExecutor(self.command_file, self.csv_file)
        self.assertEqual(executor.command_file, self.command_file)
        self.assertEqual(executor.csv_file, self.csv_file)
        self.assertEqual(executor.delay_ms, 1000)  # Default delay
    
    def test_init_with_custom_delay(self):
        """Test BatchExecutor initialization with custom delay."""
        executor = BatchExecutor(self.command_file, self.csv_file, delay_ms=2000)
        self.assertEqual(executor.command_file, self.command_file)
        self.assertEqual(executor.csv_file, self.csv_file)
        self.assertEqual(executor.delay_ms, 2000)
    
    def test_read_command_template_success(self):
        """Test reading command template successfully."""
        executor = BatchExecutor(self.command_file, self.csv_file)
        command = executor.read_command_template()
        self.assertEqual(command, 'echo "Processing ID: <id>"')
    
    def test_read_command_template_file_not_found(self):
        """Test reading command template when file doesn't exist."""
        executor = BatchExecutor('nonexistent.txt', self.csv_file)
        with self.assertRaises(FileNotFoundError):
            executor.read_command_template()
    
    def test_read_ids_from_csv_success(self):
        """Test reading IDs from CSV successfully."""
        executor = BatchExecutor(self.command_file, self.csv_file)
        ids = executor.read_ids_from_csv()
        self.assertEqual(ids, ['id1', 'id2', 'id3'])
    
    def test_read_ids_from_csv_empty_file(self):
        """Test reading IDs from empty CSV file."""
        empty_csv = os.path.join(self.temp_dir, 'empty.csv')
        with open(empty_csv, 'w') as f:
            pass
        
        executor = BatchExecutor(self.command_file, empty_csv)
        ids = executor.read_ids_from_csv()
        self.assertEqual(ids, [])
    
    def test_read_ids_from_csv_with_empty_rows(self):
        """Test reading IDs from CSV with empty rows."""
        csv_with_empty = os.path.join(self.temp_dir, 'empty_rows.csv')
        with open(csv_with_empty, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id1'])
            writer.writerow([''])  # Empty row
            writer.writerow(['id2'])
            writer.writerow([])  # Completely empty row
        
        executor = BatchExecutor(self.command_file, csv_with_empty)
        ids = executor.read_ids_from_csv()
        self.assertEqual(ids, ['id1', 'id2'])
    
    def test_read_ids_from_csv_file_not_found(self):
        """Test reading IDs when CSV file doesn't exist."""
        executor = BatchExecutor(self.command_file, 'nonexistent.csv')
        with self.assertRaises(FileNotFoundError):
            executor.read_ids_from_csv()
    
    def test_replace_id_in_command(self):
        """Test replacing ID placeholder in command."""
        executor = BatchExecutor(self.command_file, self.csv_file)
        command_template = 'echo "Processing ID: <id>"'
        result = executor.replace_id_in_command(command_template, 'test123')
        self.assertEqual(result, 'echo "Processing ID: test123"')
    
    def test_replace_id_in_command_multiple_placeholders(self):
        """Test replacing multiple ID placeholders in command."""
        executor = BatchExecutor(self.command_file, self.csv_file)
        command_template = 'echo "ID: <id> and also <id>"'
        result = executor.replace_id_in_command(command_template, 'test123')
        self.assertEqual(result, 'echo "ID: test123 and also test123"')
    
    @patch('subprocess.run')
    def test_execute_command_success(self, mock_run):
        """Test successful command execution."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = 'Success output'
        mock_result.stderr = ''
        mock_run.return_value = mock_result
        
        executor = BatchExecutor(self.command_file, self.csv_file)
        exit_code, stdout, stderr = executor.execute_command('echo test')
        
        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout, 'Success output')
        self.assertEqual(stderr, '')
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_execute_command_failure(self, mock_run):
        """Test failed command execution."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ''
        mock_result.stderr = 'Error message'
        mock_run.return_value = mock_result
        
        executor = BatchExecutor(self.command_file, self.csv_file)
        exit_code, stdout, stderr = executor.execute_command('invalid_command')
        
        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'Error message')
    
    @patch('subprocess.run')
    def test_execute_command_timeout(self, mock_run):
        """Test command execution timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired('cmd', 300)
        
        executor = BatchExecutor(self.command_file, self.csv_file)
        exit_code, stdout, stderr = executor.execute_command('sleep 1000')
        
        self.assertEqual(exit_code, -1)
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'Command timed out')
    
    @patch('subprocess.run')
    def test_execute_command_exception(self, mock_run):
        """Test command execution with exception."""
        mock_run.side_effect = Exception('Test exception')
        
        executor = BatchExecutor(self.command_file, self.csv_file)
        exit_code, stdout, stderr = executor.execute_command('test_command')
        
        self.assertEqual(exit_code, -1)
        self.assertEqual(stdout, '')
        self.assertEqual(stderr, 'Test exception')
    
    @patch('batch_executor.BatchExecutor.execute_command')
    def test_run_batch_execution_success(self, mock_execute):
        """Test successful batch execution."""
        mock_execute.return_value = (0, 'Success', '')
        
        executor = BatchExecutor(self.command_file, self.csv_file)
        
        # Capture logging output
        with patch('batch_executor.logger') as mock_logger:
            executor.run_batch_execution()
            
            # Verify execute_command was called for each ID
            self.assertEqual(mock_execute.call_count, 3)
            
            # Verify logging calls
            self.assertTrue(mock_logger.info.called)
    
    @patch('batch_executor.BatchExecutor.execute_command')
    def test_run_batch_execution_with_failures(self, mock_execute):
        """Test batch execution with some failures."""
        # First call succeeds, second fails, third succeeds
        mock_execute.side_effect = [
            (0, 'Success 1', ''),
            (1, '', 'Error 2'),
            (0, 'Success 3', '')
        ]
        
        executor = BatchExecutor(self.command_file, self.csv_file)
        
        with patch('batch_executor.logger') as mock_logger:
            executor.run_batch_execution()
            
            # Verify execute_command was called for each ID
            self.assertEqual(mock_execute.call_count, 3)
    
    def test_run_batch_execution_dry_run(self):
        """Test batch execution in dry run mode."""
        executor = BatchExecutor(self.command_file, self.csv_file)
        
        with patch('batch_executor.logger') as mock_logger:
            executor.run_batch_execution(dry_run=True)
            
            # Verify no actual execution occurred
            # Just verify logging was called
            self.assertTrue(mock_logger.info.called)
    
    def test_run_batch_execution_no_ids(self):
        """Test batch execution with no IDs."""
        empty_csv = os.path.join(self.temp_dir, 'empty.csv')
        with open(empty_csv, 'w') as f:
            pass
        
        executor = BatchExecutor(self.command_file, empty_csv)
        
        with patch('batch_executor.logger') as mock_logger:
            executor.run_batch_execution()
            
            # Should log warning about no IDs
            mock_logger.warning.assert_called_with("No IDs to process")
    
    @patch('time.sleep')
    @patch('batch_executor.BatchExecutor.execute_command')
    def test_run_batch_execution_with_delay(self, mock_execute, mock_sleep):
        """Test batch execution with delay between commands."""
        mock_execute.return_value = (0, 'Success', '')
        
        executor = BatchExecutor(self.command_file, self.csv_file, delay_ms=500)
        
        with patch('batch_executor.logger') as mock_logger:
            executor.run_batch_execution()
            
            # Verify execute_command was called for each ID
            self.assertEqual(mock_execute.call_count, 3)
            
            # Verify sleep was called between executions (2 times for 3 IDs)
            self.assertEqual(mock_sleep.call_count, 2)
            
            # Verify sleep was called with correct delay (500ms = 0.5 seconds)
            for call in mock_sleep.call_args_list:
                self.assertEqual(call[0][0], 0.5)


class TestMainFunction(unittest.TestCase):
    """Test cases for the main function."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.command_file = os.path.join(self.temp_dir, 'command.txt')
        self.csv_file = os.path.join(self.temp_dir, 'ids.csv')
        
        # Create test files
        with open(self.command_file, 'w') as f:
            f.write('echo "Processing ID: <id>"')
        
        with open(self.csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id1'])
    
    def tearDown(self):
        """Clean up after each test."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @patch('sys.argv', ['batch_executor.py', 'command.txt', 'ids.csv'])
    @patch('batch_executor.BatchExecutor')
    @patch('os.path.exists')
    def test_main_success(self, mock_exists, mock_executor_class):
        """Test main function with valid arguments."""
        mock_exists.return_value = True
        mock_executor = MagicMock()
        mock_executor_class.return_value = mock_executor
        
        with patch('sys.exit') as mock_exit:
            main()
            mock_executor.run_batch_execution.assert_called_once_with(dry_run=False)
            mock_exit.assert_not_called()
    
    @patch('sys.argv', ['batch_executor.py', 'command.txt', 'ids.csv', '--delay', '2000'])
    @patch('batch_executor.BatchExecutor')
    @patch('os.path.exists')
    def test_main_with_delay(self, mock_exists, mock_executor_class):
        """Test main function with delay parameter."""
        mock_exists.return_value = True
        mock_executor = MagicMock()
        mock_executor_class.return_value = mock_executor
        
        with patch('sys.exit') as mock_exit:
            main()
            # Verify BatchExecutor was created with delay_ms=2000
            mock_executor_class.assert_called_once_with('command.txt', 'ids.csv', delay_ms=2000)
            mock_executor.run_batch_execution.assert_called_once_with(dry_run=False)
            mock_exit.assert_not_called()
    
    @patch('sys.argv', ['batch_executor.py', 'command.txt', 'ids.csv', '--dry-run'])
    @patch('batch_executor.BatchExecutor')
    @patch('os.path.exists')
    def test_main_dry_run(self, mock_exists, mock_executor_class):
        """Test main function with dry run flag."""
        mock_exists.return_value = True
        mock_executor = MagicMock()
        mock_executor_class.return_value = mock_executor
        
        with patch('sys.exit') as mock_exit:
            main()
            mock_executor.run_batch_execution.assert_called_once_with(dry_run=True)
            mock_exit.assert_not_called()
    
    @patch('sys.argv', ['batch_executor.py', 'nonexistent.txt', 'ids.csv'])
    @patch('os.path.exists')
    def test_main_command_file_not_found(self, mock_exists):
        """Test main function when command file doesn't exist."""
        def exists_side_effect(path):
            if path == 'nonexistent.txt':
                return False
            return True
        mock_exists.side_effect = exists_side_effect
        
        with patch('sys.exit') as mock_exit:
            main()
            # Should exit with code 1 when command file doesn't exist
            mock_exit.assert_called_with(1)
    
    @patch('sys.argv', ['batch_executor.py', 'command.txt', 'nonexistent.csv'])
    @patch('os.path.exists')
    def test_main_csv_file_not_found(self, mock_exists):
        """Test main function when CSV file doesn't exist."""
        def exists_side_effect(path):
            if path == 'nonexistent.csv':
                return False
            return True
        mock_exists.side_effect = exists_side_effect
        
        with patch('sys.exit') as mock_exit:
            main()
            # Should exit with code 1 when CSV file doesn't exist
            mock_exit.assert_called_with(1)
    
    @patch('sys.argv', ['batch_executor.py', 'command.txt', 'ids.csv'])
    @patch('batch_executor.BatchExecutor')
    @patch('os.path.exists')
    @patch('sys.exit')
    def test_main_executor_exception(self, mock_exit, mock_exists, mock_executor_class):
        """Test main function when executor raises exception."""
        mock_exists.return_value = True
        mock_executor_class.side_effect = Exception('Test exception')
        
        main()
        mock_exit.assert_called_once_with(1)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete workflow."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.command_file = os.path.join(self.temp_dir, 'command.txt')
        self.csv_file = os.path.join(self.temp_dir, 'ids.csv')
        
        # Create test command file
        with open(self.command_file, 'w') as f:
            f.write('echo "Processing ID: <id>"')
        
        # Create test CSV file
        with open(self.csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['test_id_1'])
            writer.writerow(['test_id_2'])
    
    def tearDown(self):
        """Clean up after each test."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_full_workflow_success(self):
        """Test the complete workflow with successful execution."""
        executor = BatchExecutor(self.command_file, self.csv_file)
        
        # Capture output
        captured_output = io.StringIO()
        
        with patch('batch_executor.logger') as mock_logger:
            executor.run_batch_execution()
            
            # Verify that execute_command was called twice (once for each ID)
            # We can't easily mock subprocess.run in integration test,
            # so we just verify the workflow completes without errors
            self.assertTrue(mock_logger.info.called)


if __name__ == '__main__':
    # Create a test suite
    test_suite = unittest.TestSuite()
    
    # Add all test cases
    test_suite.addTest(unittest.makeSuite(TestBatchExecutor))
    test_suite.addTest(unittest.makeSuite(TestMainFunction))
    test_suite.addTest(unittest.makeSuite(TestIntegration))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print coverage information
    print(f"\nTest Results:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
