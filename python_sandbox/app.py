#!/usr/bin/env python3
"""
Python Sandbox Service for Snowpark Container Services
Executes Python code safely and returns results as JSON
"""

import json
import sys
import traceback
import io
import contextlib
import threading
import time
from typing import Dict, Any
from flask import Flask, request, jsonify
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExecutionTimeoutError(Exception):
    """Custom timeout error for code execution"""
    pass

def execute_python_code(code: str, timeout: int = 90) -> Dict[str, Any]:
    """
    Execute Python code and return results
    
    Args:
        code: Python code string to execute
        timeout: Maximum execution time in seconds
        
    Returns:
        Dictionary containing execution results
    """
    result = {
        "success": False,
        "output": "",
        "error": None,
        "execution_time": 0
    }
    
    start_time = time.time()
    
    # Capture stdout and stderr
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    
    # Shared state for thread communication
    execution_state = {
        "completed": False,
        "exception": None,
        "output": "",
        "error_output": ""
    }
    
    def execute_code():
        """Execute code in a separate thread"""
        try:
            # Use full global namespace - no restrictions
            exec_globals = globals().copy()
            # Add common imports to make them available
            exec_globals.update({
                # Standard library modules
                'json': __import__('json'),
                'math': __import__('math'),
                'datetime': __import__('datetime'),
                're': __import__('re'),
                'random': __import__('random'),
                'os': __import__('os'),
                'sys': __import__('sys'),
                
                # Flask and web-related
                'flask': __import__('flask'),
                'Flask': __import__('flask').Flask,
                'werkzeug': __import__('werkzeug'),
                'requests': __import__('requests'),
                
                # Data science and numerical computing
                'numpy': __import__('numpy'),
                'np': __import__('numpy'),
                'pandas': __import__('pandas'),
                'pd': __import__('pandas'),
                'scipy': __import__('scipy'),
                
                # Visualization
                'matplotlib': __import__('matplotlib'),
                'plt': __import__('matplotlib.pyplot'),
                'seaborn': __import__('seaborn'),
                'sns': __import__('seaborn'),
                
                # Machine learning
                'sklearn': __import__('sklearn'),
                'scikit_learn': __import__('sklearn'),
                
                # Time series forecasting
                'prophet': __import__('prophet'),
                'cmdstanpy': __import__('cmdstanpy'),
            })
            exec_locals = {}
            
            # Redirect stdout and stderr
            with contextlib.redirect_stdout(stdout_buffer), \
                 contextlib.redirect_stderr(stderr_buffer):
                
                # Execute the code with full access
                exec(code, exec_globals, exec_locals)
            
            # Get output
            execution_state["output"] = stdout_buffer.getvalue()
            execution_state["error_output"] = stderr_buffer.getvalue()
            execution_state["completed"] = True
            
        except Exception as e:
            execution_state["exception"] = e
            execution_state["output"] = stdout_buffer.getvalue()
            execution_state["error_output"] = stderr_buffer.getvalue()
            execution_state["completed"] = True
    
    try:
        # Start execution in a separate thread
        thread = threading.Thread(target=execute_code, daemon=True)
        thread.start()
        
        # Wait for completion or timeout
        thread.join(timeout=timeout)
        
        if thread.is_alive():
            # Timeout occurred
            result["error"] = f"Code execution timed out after {timeout} seconds"
        elif execution_state["completed"]:
            # Normal completion
            if execution_state["exception"]:
                # Exception during execution
                e = execution_state["exception"]
                if isinstance(e, SyntaxError):
                    result["error"] = f"Syntax Error: {str(e)}"
                else:
                    error_details = {
                        "type": type(e).__name__,
                        "message": str(e),
                        "traceback": traceback.format_exc()
                    }
                    result["error"] = error_details
            else:
                # Successful execution
                if execution_state["error_output"]:
                    result["error"] = execution_state["error_output"]
                else:
                    result["success"] = True
                    
            result["output"] = execution_state["output"]
        else:
            # Thread completed but state not set properly
            result["error"] = "Execution completed with unknown state"
        
    except Exception as e:
        # Unexpected error in the timeout mechanism itself
        error_details = {
            "type": type(e).__name__,
            "message": str(e),
            "traceback": traceback.format_exc()
        }
        result["error"] = error_details
        
    result["execution_time"] = time.time() - start_time
    return result

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "python-sandbox"})

@app.route('/execute', methods=['POST'])
def execute_code():
    """
    Execute Python code endpoint for Snowflake Service Functions
    
    Expected Snowflake format:
    {
        "data": [
            [0, "print('Hello, World!')"],
            [1, "x = 5 + 3\nprint(x)"],
            ...
        ]
    }
    
    Returns Snowflake format:
    {
        "data": [
            [0, {"success": true, "output": "Hello, World!\n", "error": null, "execution_time": 0.001}],
            [1, {"success": true, "output": "8\n", "error": null, "execution_time": 0.002}],
            ...
        ]
    }
    
    Also supports legacy format for testing:
    {
        "code": "print('Hello, World!')",
        "timeout": 30
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "Missing request body"
            }), 400
        
        # Check if this is Snowflake format (has "data" array)
        if 'data' in data:
            return handle_snowflake_format(data)
        # Legacy format for testing
        elif 'code' in data:
            return handle_legacy_format(data)
        else:
            return jsonify({
                "success": False,
                "error": "Invalid request format. Expected 'data' array (Snowflake format) or 'code' string (legacy format)"
            }), 400
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500

def handle_snowflake_format(data):
    """Handle Snowflake service function format"""
    try:
        rows = data.get('data', [])
        if not isinstance(rows, list):
            return jsonify({
                "success": False,
                "error": "'data' must be an array"
            }), 400
        
        results = []
        
        # Use default timeout or get from request data if provided
        timeout = 600
        for row in rows:
            if not isinstance(row, list) or len(row) < 2:
                return jsonify({
                    "success": False,
                    "error": "Each row must be an array with at least [row_index, code]"
                }), 400
            
            row_index = row[0]
            code = row[1]
            
            if not isinstance(code, str):
                # Return error for this specific row
                result = {
                    "success": False,
                    "output": "",
                    "error": "Code must be a string",
                    "execution_time": 0
                }
                results.append([row_index, result])
                continue
            
            logger.info(f"Executing code for row {row_index}")
            
            # Execute the code with default timeout
            result = execute_python_code(code, timeout)
            results.append([row_index, result])
        
        return jsonify({"data": results})
        
    except Exception as e:
        logger.error(f"Error in Snowflake format handler: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Error processing Snowflake format: {str(e)}"
        }), 500

def handle_legacy_format(data):
    """Handle legacy format for testing"""
    try:
        code = data['code']
        timeout = data.get('timeout', 30)
        
        if not isinstance(code, str):
            return jsonify({
                "success": False,
                "error": "'code' parameter must be a string"
            }), 400
            
        if not isinstance(timeout, int) or timeout <= 0 or timeout > 300:
            return jsonify({
                "success": False,
                "error": "'timeout' must be an integer between 1 and 300 seconds"
            }), 400
        
        logger.info(f"Executing code with timeout {timeout}s")
        
        # Execute the code
        result = execute_python_code(code, timeout)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in legacy format handler: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Error processing legacy format: {str(e)}"
        }), 500

@app.route('/', methods=['GET'])
def root():
    """Root endpoint with service information"""
    return jsonify({
        "service": "Python Sandbox",
        "version": "1.0.0",
        "description": "Execute Python code and return results as JSON for Snowflake Service Functions",
        "endpoints": {
            "/health": "GET - Health check",
            "/execute": "POST - Execute Python code (Snowflake or legacy format)",
            "/": "GET - Service information"
        },
        "usage": {
            "snowflake_format": {
                "method": "POST",
                "content-type": "application/json",
                "description": "Snowflake Service Function format",
                "body": {
                    "data": [
                        "[row_index, python_code_string]",
                        "Example: [0, \"print('Hello')\"]"
                    ]
                },
                "response": {
                    "data": [
                        "[row_index, execution_result_object]"
                    ]
                }
            },
            "legacy_format": {
                "method": "POST", 
                "content-type": "application/json",
                "description": "Legacy format for testing",
                "body": {
                    "code": "Python code string to execute",
                    "timeout": "Optional timeout in seconds (1-300, default: 30)"
                }
            }
        }
    })

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    app.run(host='0.0.0.0', port=port, debug=False)
