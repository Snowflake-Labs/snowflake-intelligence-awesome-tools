# Python Sandbox Tool

Execute Python code in a secure containerized environment using Snowpark Container Services. This tool allows your Snowflake Intelligence agents to run Python code and return results as JSON.

## Contributors

- [@jeffhollan](https://github.com/jeffhollan) - Tool creator

## Tool Parameters

| Field | Value |
|-------|-------|
| **Tool Description** | Use this tool anytime you need to execute Python code or perform data analysis with Python libraries. The following libraries are available: requests, numpy, pandas, scipy, matplotlib, seaborn, scikit-learn, prophet. Context is limited to a single execution, so pass in all context and content in as little tool calls as possible. |
| **Code** | The Python code to execute. Can include imports, data processing, analysis, and any Python operations |
| **Timeout** | Optional execution timeout in seconds (1-300, defaults to 30 seconds) |

## Installation Instructions

1. **Deploy the container service**: Follow the setup instructions in the `setup.sql` file
2. **Configure the service**: Update the database and schema references in the setup script
3. **Test the deployment**: Run the test script to verify the service is working
4. **Add to your agent**: Configure the service endpoint in your Snowflake Intelligence agent

## What This Tool Does

This tool creates a Python execution environment that:
- Accepts Python code as input from your Snowflake Intelligence agents
- Executes the code in a secure containerized environment
- Returns results as structured JSON with execution details
- Supports popular data science libraries (numpy, pandas, scikit-learn, etc.)
- Includes comprehensive error handling and timeout controls

## Features

- 🐍 Execute Python code with full library access
- ⏱️ Configurable execution timeout (1-300 seconds)
- 📊 JSON response format with execution results
- 🚀 Ready for Snowpark Container Services deployment
- 🔍 Health check endpoint for monitoring
- 📝 Comprehensive error handling and logging
- 📦 Includes popular data science libraries (numpy, pandas, scikit-learn, etc.)

## Usage

Once deployed, you can use this tool in your Snowflake Intelligence agents by:
1. Adding it as a custom tool in your agent configuration
2. Providing Python code as input
3. Optionally specifying a timeout value
4. The tool will execute the code and return structured results

## API Endpoints

### POST /execute
Executes Python code and returns results. Supports both Snowflake Service Function format and legacy format.

#### Snowflake Service Function Format
**Request Body:**
```json
{
  "data": [
    [0, "print('Hello, World!')"],
    [1, "x = 5 + 3\nprint(x)"],
    [2, "import pandas as pd\ndf = pd.DataFrame({'a': [1,2,3]})\nprint(df.sum())"]
  ]
}
```

**Response:**
```json
{
  "data": [
    [0, {"success": true, "output": "Hello, World!\n", "error": null, "execution_time": 0.001}],
    [1, {"success": true, "output": "8\n", "error": null, "execution_time": 0.002}],
    [2, {"success": true, "output": "a    6\ndtype: int64\n", "error": null, "execution_time": 0.015}]
  ]
}
```

## Prerequisites

- Snowflake account with Snowpark Container Services enabled
- Appropriate permissions to create compute pools and services
- Docker environment for local testing (optional)

## Troubleshooting

- **Service not responding**: Check that the container service is running and healthy
- **Permission errors**: Ensure you have the necessary roles and permissions
- **Timeout errors**: Increase the timeout value for long-running operations
- **Import errors**: Verify that required libraries are included in the container image

## Security Notes

- Code execution is sandboxed in a containerized environment
- No persistent storage between executions
- Network access is controlled and limited
- All executions are logged for audit purposes


