#!/usr/bin/env python3
"""
Test script for Python Sandbox Service
"""

import requests
import json
import time

def test_service(base_url="http://localhost:8080"):
    """Test the Python sandbox service"""
    
    print("🧪 Testing Python Sandbox Service")
    print(f"Base URL: {base_url}")
    print("-" * 50)
    
    # Test 1: Health check
    print("1. Testing health check...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        assert response.status_code == 200
        print("   ✅ Health check passed")
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")
        return
    
    print()
    
    # Test 2: Basic code execution (legacy format)
    print("2. Testing basic code execution (legacy format)...")
    try:
        code = "print('Hello from Python Sandbox!')"
        response = requests.post(f"{base_url}/execute", 
                               json={"code": code})
        result = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Success: {result['success']}")
        print(f"   Output: {repr(result['output'])}")
        print(f"   Execution time: {result['execution_time']:.4f}s")
        assert response.status_code == 200
        assert result['success'] == True
        print("   ✅ Basic execution (legacy) passed")
    except Exception as e:
        print(f"   ❌ Basic execution (legacy) failed: {e}")
    
    print()
    
    # Test 2b: Snowflake format - single row
    print("2b. Testing Snowflake format - single row...")
    try:
        snowflake_data = {
            "data": [
                [0, "print('Hello from Snowflake format!')"]
            ]
        }
        response = requests.post(f"{base_url}/execute", json=snowflake_data)
        result = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Data length: {len(result['data'])}")
        row_result = result['data'][0]
        print(f"   Row index: {row_result[0]}")
        print(f"   Success: {row_result[1]['success']}")
        print(f"   Output: {repr(row_result[1]['output'])}")
        assert response.status_code == 200
        assert len(result['data']) == 1
        assert row_result[0] == 0
        assert row_result[1]['success'] == True
        print("   ✅ Snowflake format (single row) passed")
    except Exception as e:
        print(f"   ❌ Snowflake format (single row) failed: {e}")
    
    print()
    
    # Test 2c: Snowflake format - multiple rows
    print("2c. Testing Snowflake format - multiple rows...")
    try:
        snowflake_data = {
            "data": [
                [0, "result = 2 + 2\nprint(f'2 + 2 = {result}')"],
                [1, "import math\nprint(f'Pi = {math.pi:.3f}')"],
                [2, "names = ['Alice', 'Bob']\nprint(f'Names: {\", \".join(names)}')"]
            ]
        }
        response = requests.post(f"{base_url}/execute", json=snowflake_data)
        result = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Rows processed: {len(result['data'])}")
        
        for i, row_result in enumerate(result['data']):
            row_index = row_result[0]
            execution_result = row_result[1]
            print(f"   Row {row_index}: Success={execution_result['success']}, Output={repr(execution_result['output'][:30])}...")
            assert row_index == i
            assert execution_result['success'] == True
        
        assert response.status_code == 200
        assert len(result['data']) == 3
        print("   ✅ Snowflake format (multiple rows) passed")
    except Exception as e:
        print(f"   ❌ Snowflake format (multiple rows) failed: {e}")
    
    print()
    
    # Test 3: Data science operations
    print("3. Testing data science operations...")
    try:
        code = """
import pandas as pd
import numpy as np

# Create a simple dataset
data = {
    'name': ['Alice', 'Bob', 'Charlie', 'Diana'],
    'age': [25, 30, 35, 28],
    'score': [85, 92, 78, 95]
}
df = pd.DataFrame(data)
print("DataFrame:")
print(df)
print(f"\\nAverage age: {df['age'].mean()}")
print(f"Max score: {df['score'].max()}")
print(f"Correlation between age and score: {df['age'].corr(df['score']):.3f}")
"""
        response = requests.post(f"{base_url}/execute", 
                               json={"code": code})
        result = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Success: {result['success']}")
        print(f"   Output snippet: {result['output'][:100]}...")
        assert response.status_code == 200
        assert result['success'] == True
        print("   ✅ Data science operations passed")
    except Exception as e:
        print(f"   ❌ Data science operations failed: {e}")
    
    print()
    
    # Test 4: Error handling
    print("4. Testing error handling...")
    try:
        code = "print(1/0)"  # Division by zero
        response = requests.post(f"{base_url}/execute", 
                               json={"code": code})
        result = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Success: {result['success']}")
        print(f"   Error type: {result['error']['type']}")
        print(f"   Error message: {result['error']['message']}")
        assert response.status_code == 200
        assert result['success'] == False
        assert "ZeroDivisionError" in result['error']['type']
        print("   ✅ Error handling passed")
    except Exception as e:
        print(f"   ❌ Error handling failed: {e}")
    
    print()
    
    # Test 5: Syntax error
    print("5. Testing syntax error handling...")
    try:
        code = "print('unclosed string"  # Syntax error
        response = requests.post(f"{base_url}/execute", 
                               json={"code": code})
        result = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Success: {result['success']}")
        print(f"   Error: {result['error']}")
        assert response.status_code == 200
        assert result['success'] == False
        print("   ✅ Syntax error handling passed")
    except Exception as e:
        print(f"   ❌ Syntax error handling failed: {e}")
    
    print()
    
    # Test 6: JSON operations
    print("6. Testing JSON operations...")
    try:
        code = """
import json
data = {"name": "test", "values": [1, 2, 3, 4, 5]}
json_str = json.dumps(data)
parsed = json.loads(json_str)
print(f"Original: {data}")
print(f"JSON string: {json_str}")
print(f"Parsed back: {parsed}")
print(f"Sum of values: {sum(parsed['values'])}")
"""
        response = requests.post(f"{base_url}/execute", 
                               json={"code": code})
        result = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Success: {result['success']}")
        print(f"   Output: {repr(result['output'])}")
        assert response.status_code == 200
        assert result['success'] == True
        print("   ✅ JSON operations passed")
    except Exception as e:
        print(f"   ❌ JSON operations failed: {e}")
    
    print()
    
    # Test 7: Custom timeout
    print("7. Testing custom timeout...")
    try:
        code = """
import time
print("Starting...")
time.sleep(1)
print("Finished after 1 second")
"""
        response = requests.post(f"{base_url}/execute", 
                               json={"code": code, "timeout": 5})
        result = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Success: {result['success']}")
        print(f"   Execution time: {result['execution_time']:.4f}s")
        print(f"   Output: {repr(result['output'])}")
        assert response.status_code == 200
        assert result['success'] == True
        assert result['execution_time'] >= 1.0
        print("   ✅ Custom timeout passed")
    except Exception as e:
        print(f"   ❌ Custom timeout failed: {e}")
    
    print()
    print("🎉 All tests completed!")

if __name__ == "__main__":
    test_service()
