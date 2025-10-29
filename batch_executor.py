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
    
    def __init__(self, command_file: str, csv_file: str, delay_ms: int = 1000):
        """
        Initialize the batch executor.
        
        Args:
            command_file: Path to file containing the command template
            csv_file: Path to CSV file containing IDs
            delay_ms: Delay between command executions in milliseconds (default: 1000)
        """
        self.command_file = command_file
        self.csv_file = csv_file
        self.delay_ms = delay_ms
        
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
            
            if exit_code == 0:
                logger.info(f"✓ Success for ID {id_value}")
                if stdout:
                    logger.info(f"Response: {stdout}")
                successful_executions += 1
            else:
                logger.error(f"✗ Failed for ID {id_value} (exit code: {exit_code})")
                if stderr:
                    logger.error(f"Error: {stderr}")
                if stdout:
                    logger.info(f"Response: {stdout}")
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
        executor = BatchExecutor(args.command_file, args.csv_file, delay_ms=args.delay)
        executor.run_batch_execution(dry_run=args.dry_run)
    except Exception as e:
        logger.error(f"Batch execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
