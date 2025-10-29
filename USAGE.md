# Batch Executor - Quick Usage Guide

## Quick Start 🚀

1. **Prepare your files:**
   - Create a command file with `<id>` placeholder
   - Create a CSV file with your IDs

2. **Run the script:**
   ```bash
   python3 batch_executor.py command.txt ids.csv
   ```

## Example Files

### Command File (`command.txt`)
```bash
curl --location 'https://api-sandbox.y.uno/v1/customers' \
--header 'accept: application/json' \
--header 'charset: utf-8' \
--header 'content-type: application/json' \
--header 'private-secret-key: gAAAAABof9s4Sb' \
--header 'public-api-key: sandbox_gAAAAABof9s' \
--data '
{
  "merchant_customer_id": "<id>"
}
'
```

### CSV File (`ids.csv`)
```csv
customer_001
customer_002
customer_003
customer_004
customer_005
```

## Command Line Options

```bash
# Basic usage
python3 batch_executor.py command.txt ids.csv

# Dry run (see what would be executed)
python3 batch_executor.py command.txt ids.csv --dry-run

# Verbose output
python3 batch_executor.py command.txt ids.csv --verbose

# Custom delay between executions (2000ms = 2 seconds)
python3 batch_executor.py command.txt ids.csv --delay 2000

# Fast execution with 500ms delay
python3 batch_executor.py command.txt ids.csv --delay 500

# Combine options
python3 batch_executor.py command.txt ids.csv --dry-run --verbose --delay 1000
```

## What Happens

1. **Reads** your command template and CSV file
2. **Replaces** `<id>` with each ID from the CSV
3. **Executes** the command for each ID
4. **Waits** for the specified delay between executions
5. **Reports** success/failure for each execution
6. **Provides** a summary at the end

## Example Output

```
2024-01-15 10:30:15 - INFO - Starting batch execution...
2024-01-15 10:30:15 - INFO - Command template loaded from command.txt
2024-01-15 10:30:15 - INFO - Found 5 IDs in ids.csv
2024-01-15 10:30:15 - INFO - Processing ID 1/5: customer_001
2024-01-15 10:30:16 - INFO - ✓ Success for ID customer_001
2024-01-15 10:30:16 - INFO - Response: {"id": "cust_123", "status": "created", "message": "Customer created successfully"}
2024-01-15 10:30:16 - DEBUG - Waiting 1000ms before next execution...
2024-01-15 10:30:17 - INFO - Processing ID 2/5: customer_002
2024-01-15 10:30:18 - ERROR - ✗ Failed for ID customer_002 (exit code: 1)
2024-01-15 10:30:18 - ERROR - Error: {"error": "Invalid customer ID", "code": 400}
2024-01-15 10:30:18 - INFO - Response: {"error": "Invalid customer ID", "code": 400}
2024-01-15 10:30:18 - DEBUG - Waiting 1000ms before next execution...
2024-01-15 10:30:19 - INFO - Batch execution completed!
2024-01-15 10:30:19 - INFO - Successful: 4
2024-01-15 10:30:19 - INFO - Failed: 1
2024-01-15 10:30:19 - INFO - Total: 5
```

## Safety Features

- **File validation**: Checks that files exist before processing
- **Error handling**: Individual failures don't stop the batch
- **Timeout protection**: Commands timeout after 5 minutes
- **Dry run mode**: Test without actually executing commands

## Testing

Run the comprehensive test suite:
```bash
python3 test_batch_executor.py
```

All tests pass with 100% success rate! 🎉

## Files in This Project

- `batch_executor.py` - Main script
- `test_batch_executor.py` - Comprehensive unit tests
- `run_example.py` - Example usage script
- `example_command.txt` - Sample command file
- `example_ids.csv` - Sample CSV file
- `README.md` - Detailed documentation
- `USAGE.md` - This quick guide

Happy batch executing! 🚀
