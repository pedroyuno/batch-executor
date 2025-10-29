#!/usr/bin/env python3
"""
Example script demonstrating how to use the batch executor.

This script shows how to use the BatchExecutor class programmatically
instead of using the command line interface.
"""

import os
import sys
from batch_executor import BatchExecutor

def main():
    """Run an example batch execution."""
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define file paths
    command_file = os.path.join(script_dir, 'example_command.txt')
    csv_file = os.path.join(script_dir, 'example_ids.csv')
    
    # Check if example files exist
    if not os.path.exists(command_file):
        print(f"Error: Example command file not found: {command_file}")
        print("Please make sure example_command.txt exists in the same directory.")
        sys.exit(1)
    
    if not os.path.exists(csv_file):
        print(f"Error: Example CSV file not found: {csv_file}")
        print("Please make sure example_ids.csv exists in the same directory.")
        sys.exit(1)
    
    print("🚀 Starting Batch Executor Example")
    print("=" * 50)
    print(f"Command file: {command_file}")
    print(f"CSV file: {csv_file}")
    print("=" * 50)
    
    try:
        # Create batch executor
        executor = BatchExecutor(command_file, csv_file)
        
        # Run in dry-run mode first to show what would be executed
        print("\n🔍 DRY RUN - Showing what would be executed:")
        print("-" * 50)
        executor.run_batch_execution(dry_run=True)
        
        print("\n" + "=" * 50)
        print("📝 Note: The script will now print the response from each command")
        print("   when you run it for real. This includes both success and error responses.")
        print("   You can also control the delay between executions with --delay parameter.")
        
        # Ask user if they want to proceed with actual execution
        print("\n" + "=" * 50)
        response = input("Do you want to proceed with actual execution? (y/N): ").strip().lower()
        
        if response in ['y', 'yes']:
            print("\n🏃 ACTUAL EXECUTION:")
            print("-" * 50)
            executor.run_batch_execution(dry_run=False)
        else:
            print("Execution cancelled by user.")
            
    except Exception as e:
        print(f"❌ Error during batch execution: {e}")
        sys.exit(1)
    
    print("\n✅ Example completed!")

if __name__ == "__main__":
    main()
