# Batch Executor - A Command Execution Story

## The Journey Begins 🚀

Once upon a time, there was a developer who needed to execute the same command hundreds of times, but with different parameters each time. The command was complex, involving API calls with authentication headers, and the parameters were stored in a CSV file. Manual execution would have taken forever, and the developer was about to lose their sanity...

But then, the **Batch Executor** was born! 🎉

## What is Batch Executor?

The Batch Executor is a Python script that takes a command template and executes it for each ID in a CSV file. It's like having a magical assistant that reads your command, looks at your list of IDs, and runs the command for each one automatically.

### The Magic Behind the Scenes ✨

• **The Command Template**: You write your command once, using `<id>` as a placeholder where the actual ID should go
• **The CSV File**: Contains all the IDs you want to process, one per row
• **The Script**: Reads both files, replaces `<id>` with each actual ID, and executes the command
• **The Results**: You get a detailed log of what happened for each execution

## Installation & Setup 🛠️

### Prerequisites
• Python 3.6 or higher
• A command template file
• A CSV file with your IDs

### Getting Started
1. **Clone or download** the batch executor script
2. **Make it executable** (optional but recommended):
   ```bash
   chmod +x batch_executor.py
   ```
3. **Prepare your files**:
   - Create a command file with your template
   - Create a CSV file with your IDs

## The Adventure of Usage 🗺️

### Basic Usage
```bash
python batch_executor.py command.txt ids.csv
```

### Advanced Usage with Options
```bash
# Dry run - see what would be executed without actually running
python batch_executor.py command.txt ids.csv --dry-run

# Verbose output - see detailed information about each step
python batch_executor.py command.txt ids.csv --verbose

# Custom delay between executions (2000ms = 2 seconds)
python batch_executor.py command.txt ids.csv --delay 2000

# Fast execution with 500ms delay
python batch_executor.py command.txt ids.csv --delay 500

# Combine options for maximum visibility
python batch_executor.py command.txt ids.csv --dry-run --verbose --delay 1000
```

## The Tale of File Formats 📖

### Command File Format
Your command file should contain the exact command you want to execute, with `<id>` as a placeholder:

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

### CSV File Format
Your CSV file should contain one ID per row in the first column:

```csv
customer_001
customer_002
customer_003
customer_004
customer_005
```

## The Epic Journey of Execution 🌟

### What Happens During Execution

1. **The Reading Phase**: The script reads your command template and CSV file
2. **The Preparation Phase**: It validates that both files exist and contain data
3. **The Execution Phase**: For each ID in the CSV:
   • The script replaces `<id>` with the actual ID
   • Executes the command
   • Captures the results (success/failure, output, errors)
4. **The Reporting Phase**: Provides a summary of all executions

### The Logging Adventure 📝

The script provides detailed logging throughout the journey:

• **INFO**: General progress updates
• **SUCCESS**: When a command executes successfully (✓)
• **ERROR**: When a command fails (✗)
• **WARNING**: When something unexpected happens
• **DEBUG**: Detailed information (when using --verbose)
• **DELAY**: Shows when the script is waiting between executions

### Example Output
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

## The Safety Features 🛡️

### Error Handling
• **File Not Found**: Graceful handling when files don't exist
• **Empty Files**: Warnings when CSV files are empty
• **Command Failures**: Individual command failures don't stop the batch
• **Timeouts**: Commands that run too long are automatically terminated
• **Exception Handling**: Unexpected errors are caught and logged

### Dry Run Mode
Before running the actual batch, you can use `--dry-run` to see what would be executed without actually running the commands. This is like having a crystal ball that shows you the future!

## The Testing Saga 🧪

The script comes with comprehensive unit tests that cover:
• **File Reading**: Testing command and CSV file reading
• **ID Replacement**: Testing the `<id>` placeholder replacement
• **Command Execution**: Testing successful and failed executions
• **Error Handling**: Testing various error scenarios
• **Integration**: Testing the complete workflow

### Running the Tests
```bash
python test_batch_executor.py
```

The tests aim for at least 90% code coverage, ensuring the script is robust and reliable.

## The Real-World Examples 🌍

### API Customer Creation
```bash
# Command file (api_command.txt)
curl --location 'https://api.example.com/v1/customers' \
--header 'Authorization: Bearer YOUR_TOKEN' \
--header 'Content-Type: application/json' \
--data '{"customer_id": "<id>", "name": "Customer <id>"}'

# CSV file (customer_ids.csv)
CUST_001
CUST_002
CUST_003

# Execution
python batch_executor.py api_command.txt customer_ids.csv
```

### Database Operations
```bash
# Command file (db_command.txt)
psql -d mydb -c "UPDATE users SET status='active' WHERE user_id='<id>';"

# CSV file (user_ids.csv)
user_123
user_456
user_789

# Execution
python batch_executor.py db_command.txt user_ids.csv
```

## The Troubleshooting Guide 🔧

### Common Issues and Solutions

**"Command file not found"**
• Check that the file path is correct
• Ensure the file exists and is readable

**"CSV file not found"**
• Verify the CSV file path
• Make sure the file exists and is accessible

**"No IDs found in CSV file"**
• Check that your CSV file has data
• Ensure the first column contains the IDs
• Remove any empty rows

**"Command timed out"**
• The command is taking too long to execute
• Consider breaking it into smaller batches
• Check if the command is hanging

**"Permission denied"**
• Make sure the script has execute permissions
• Check file permissions for the command and CSV files

## The Performance Chronicles ⚡

### Optimization Tips
• **Batch Size**: For very large datasets, consider processing in smaller batches
• **Parallel Processing**: For CPU-intensive commands, the script processes them sequentially to avoid overwhelming the system
• **Timeout Settings**: Commands have a 5-minute timeout by default
• **Memory Usage**: The script loads all IDs into memory, so very large CSV files might need special handling

## The Future Roadmap 🗺️

### Potential Enhancements
• **Parallel Execution**: Running multiple commands simultaneously
• **Progress Bars**: Visual progress indicators
• **Resume Capability**: Continuing from where it left off after interruption
• **Custom Timeouts**: Configurable timeout settings
• **Output Redirection**: Saving command outputs to files
• **Retry Logic**: Automatically retrying failed commands

## The Conclusion 🎯

The Batch Executor is your trusty companion for automating repetitive command executions. It handles the complexity of file reading, ID replacement, command execution, and error handling, so you can focus on what matters most - getting your work done efficiently!

Whether you're processing hundreds of API calls, updating database records, or performing any other repetitive task, the Batch Executor is here to make your life easier. Just prepare your command template and CSV file, and let the magic happen! ✨

---

*Happy batch executing! 🚀*
