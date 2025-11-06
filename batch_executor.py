#!/usr/bin/env python3
"""
Batch Executor Script

This script executes a command template for each ID in a CSV file.
The command template should contain <id> placeholder that will be replaced
with each ID from the CSV file.

Usage:
    python batch_executor.py <command_file> <csv_file>

Example:
    python batch_executor.py command.txt ids.csv
"""

import sys
import os
import csv
import subprocess
import argparse
import time
from typing import List, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BatchExecutor:
    """Handles batch execution of commands with ID replacement."""
    
    def __init__(self, command_file: str, csv_file: str, delay_ms: int = 1000, verify_return: bool = False):
        """
        Initialize the batch executor.
        
        Args:
            command_file: Path to file containing the command template
            csv_file: Path to CSV file containing IDs
            delay_ms: Delay between command executions in milliseconds (default: 1000)
            verify_return: If True, stop execution on HTTP error response codes (4xx, 5xx)
        """
        self.command_file = command_file
        self.csv_file = csv_file
        self.delay_ms = delay_ms
        self.verify_return = verify_return
        
    def read_command_template(self) -> str:
        """Read the command template from file."""
        try:
            with open(self.command_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            logger.error(f"Command file not found: {self.command_file}")
            raise
        except Exception as e:
            logger.error(f"Error reading command file: {e}")
            raise
    
    def read_ids_from_csv(self) -> List[str]:
        """
        Read IDs from CSV file.
        Assumes the first column contains the IDs.
        """
        ids = []
        try:
            with open(self.csv_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row_num, row in enumerate(reader, 1):
                    if row and row[0].strip():  # Skip empty rows
                        ids.append(row[0].strip())
                    elif row:  # Empty cell in non-empty row
                        logger.warning(f"Empty ID found in row {row_num}")
        except FileNotFoundError:
            logger.error(f"CSV file not found: {self.csv_file}")
            raise
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            raise
        
        if not ids:
            logger.warning("No IDs found in CSV file")
        
        return ids
    
    def replace_id_in_command(self, command_template: str, id_value: str) -> str:
        """Replace <id> placeholder with actual ID value."""
        return command_template.replace('<id>', id_value)
    
    def execute_command(self, command: str) -> tuple[int, str, str]:
        """
        Execute a command and return exit code, stdout, and stderr.
        
        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        try:
            # Use shell=True to handle complex commands with pipes, redirects, etc.
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            logger.error("Command timed out after 5 minutes")
            return -1, "", "Command timed out"
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return -1, "", str(e)
    
    def extract_http_response_code(self, command: str, stdout: str, stderr: str) -> Optional[str]:
        """
        Extract HTTP response code from curl command output.
        
        Args:
            command: The executed command
            stdout: Standard output from the command
            stderr: Standard error from the command
            
        Returns:
            HTTP response code as string, or None if not found
        """
        # Check if this is a curl command
        if not command.strip().startswith('curl'):
            return None
        
        # Look for HTTP response codes in stderr (curl writes response codes to stderr)
        import re
        
        # Pattern to match HTTP response codes (e.g., "HTTP/1.1 200 OK", "HTTP/2 404", "HTTP/2 503")
        http_pattern = r'HTTP.*?(\d{3})'
        
        # Search in stderr first (where curl typically writes response codes)
        match = re.search(http_pattern, stderr)
        if match:
            return match.group(1)
        
        # Also search in stdout in case curl is configured differently
        match = re.search(http_pattern, stdout)
        if match:
            return match.group(1)
        
        return None
    
    def extract_response_body(self, command: str, stdout: str, stderr: str) -> str:
        """
        Extract response body from curl command output, removing HTTP headers.
        
        Args:
            command: The executed command
            stdout: Standard output from the command
            stderr: Standard error from the command
            
        Returns:
            Response body without HTTP headers
        """
        # Check if this is a curl command
        if not command.strip().startswith('curl'):
            return stdout
        
        # Look for the first empty line after HTTP headers
        lines = stdout.split('\n')
        body_start = 0
        
        for i, line in enumerate(lines):
            # Look for empty line that indicates end of headers
            if line.strip() == '':
                body_start = i + 1
                break
        
        # Return everything after the empty line (response body)
        if body_start < len(lines):
            return '\n'.join(lines[body_start:]).strip()
        
        # If no empty line found, return the original stdout
        return stdout
    
    def is_valid_http_code(self, http_code: Optional[str]) -> bool:
        """
        Check if HTTP response code is valid (2xx) or an error (4xx, 5xx).
        
        Args:
            http_code: HTTP response code as string (e.g., "200", "404", "500")
            
        Returns:
            True if code is 2xx (success), False if 4xx or 5xx (error), None if code is None
        """
        if http_code is None:
            return None
        
        try:
            code = int(http_code)
            # 2xx codes are success
            if 200 <= code < 300:
                return True
            # 4xx and 5xx codes are errors
            elif 400 <= code < 600:
                return False
            # Other codes (1xx, 3xx) are considered valid for now
            else:
                return True
        except (ValueError, TypeError):
            return None
    
    def run_batch_execution(self, dry_run: bool = False) -> None:
        """
        Execute the command for each ID in the CSV file.
        
        Args:
            dry_run: If True, only print commands without executing them
        """
        logger.info("Starting batch execution...")
        
        # Read command template
        command_template = self.read_command_template()
        logger.info(f"Command template loaded from {self.command_file}")
        
        # Read IDs from CSV
        ids = self.read_ids_from_csv()
        logger.info(f"Found {len(ids)} IDs in {self.csv_file}")
        
        if not ids:
            logger.warning("No IDs to process")
            return
        
        # Process each ID
        successful_executions = 0
        failed_executions = 0
        
        for i, id_value in enumerate(ids, 1):
            logger.info(f"Processing ID {i}/{len(ids)}: {id_value}")
            
            # Replace <id> with actual ID
            command = self.replace_id_in_command(command_template, id_value)
            
            if dry_run:
                logger.info(f"DRY RUN - Would execute: {command[:100]}...")
                logger.info(f"DRY RUN - Full command: {command}")
                successful_executions += 1
                # Add delay even in dry run mode to simulate real execution timing
                if i < len(ids):  # Don't delay after the last item
                    logger.debug(f"DRY RUN - Waiting {self.delay_ms}ms before next execution...")
                    time.sleep(self.delay_ms / 1000.0)
                continue
            
            # Execute command
            exit_code, stdout, stderr = self.execute_command(command)
            
            # Extract HTTP response code for curl commands
            http_code = self.extract_http_response_code(command, stdout, stderr)
            
            # Extract response body (without headers) for curl commands
            response_body = self.extract_response_body(command, stdout, stderr)
            
            # Verify HTTP response code if verify_return is enabled
            if self.verify_return and http_code:
                is_valid = self.is_valid_http_code(http_code)
                if is_valid is False:
                    # HTTP error code detected (4xx, 5xx), stop execution
                    logger.error(f"✗ HTTP Error Response Code: {http_code} for ID {id_value}")
                    logger.error(f"Stopping batch execution due to HTTP error response code")
                    if response_body:
                        logger.error(f"Response: {response_body}")
                    failed_executions += 1
                    break  # Stop execution
                elif is_valid is None:
                    # HTTP code couldn't be validated, continue but warn
                    logger.warning(f"Could not validate HTTP response code: {http_code}")
            
            if exit_code == 0:
                logger.info(f"✓ Success for ID {id_value}")
                if http_code:
                    logger.info(f"HTTP Response Code: {http_code}")
                if response_body:
                    logger.info(f"Response: {response_body}")
                # In verbose mode, also show full response with headers
                if logger.isEnabledFor(logging.DEBUG) and stdout and stdout != response_body:
                    logger.debug(f"Full Response: {stdout}")
                successful_executions += 1
            else:
                logger.error(f"✗ Failed for ID {id_value} (exit code: {exit_code})")
                if http_code:
                    logger.error(f"HTTP Response Code: {http_code}")
                if stderr:
                    logger.error(f"Error: {stderr}")
                if response_body:
                    logger.info(f"Response: {response_body}")
                # In verbose mode, also show full response with headers
                if logger.isEnabledFor(logging.DEBUG) and stdout and stdout != response_body:
                    logger.debug(f"Full Response: {stdout}")
                failed_executions += 1
            
            # Add delay between executions (except for the last one)
            if i < len(ids):
                logger.debug(f"Waiting {self.delay_ms}ms before next execution...")
                time.sleep(self.delay_ms / 1000.0)
        
        # Summary
        logger.info(f"Batch execution completed!")
        logger.info(f"Successful: {successful_executions}")
        logger.info(f"Failed: {failed_executions}")
        logger.info(f"Total: {len(ids)}")


def main():
    """Main function to handle command line arguments and run batch execution."""
    parser = argparse.ArgumentParser(
        description="Execute a command template for each ID in a CSV file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python batch_executor.py command.txt ids.csv
  python batch_executor.py command.txt ids.csv --dry-run
  python batch_executor.py command.txt ids.csv --verbose
  python batch_executor.py command.txt ids.csv --delay 2000
  python batch_executor.py command.txt ids.csv --delay 500 --verbose
  python batch_executor.py command.txt ids.csv --verify-return
  python batch_executor.py command.txt ids.csv --verify-return --verbose
        """
    )
    
    parser.add_argument('command_file', help='Path to file containing command template')
    parser.add_argument('csv_file', help='Path to CSV file containing IDs')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Print commands without executing them')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--delay', type=int, default=1000,
                       help='Delay between command executions in milliseconds (default: 1000)')
    parser.add_argument('--verify-return', action='store_true',
                       help='Stop execution when HTTP error response codes (4xx, 5xx) are received')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate files exist
    if not os.path.exists(args.command_file):
        logger.error(f"Command file does not exist: {args.command_file}")
        sys.exit(1)
    
    if not os.path.exists(args.csv_file):
        logger.error(f"CSV file does not exist: {args.csv_file}")
        sys.exit(1)
    
    try:
        # Create and run batch executor
        executor = BatchExecutor(
            args.command_file, 
            args.csv_file, 
            delay_ms=args.delay,
            verify_return=args.verify_return
        )
        executor.run_batch_execution(dry_run=args.dry_run)
    except Exception as e:
        logger.error(f"Batch execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
