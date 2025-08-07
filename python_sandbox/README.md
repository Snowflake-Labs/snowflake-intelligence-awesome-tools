# Python Sandbox Service

A Python code execution service designed to run in Snowpark Container Services as a Service Function. This service accepts Python code as input, executes it in a full Python environment, and returns the results as JSON.

## Features

- 🐍 Execute Python code with full library access
- ⏱️ Configurable execution timeout (1-300 seconds)
- 📊 JSON response format with execution results
- 🚀 Ready for Snowpark Container Services deployment
- 🔍 Health check endpoint for monitoring
- 📝 Comprehensive error handling and logging
- 📦 Includes popular data science libraries (numpy, pandas, scikit-learn, etc.)

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

