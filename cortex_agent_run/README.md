# # Cortex Agent Run

Run Snowflake Cortex Agents as Custom Tool. This stored procedure provides a flexible way to execute your agents as a Custom Tool and retrieve responses, enabling automation and integration with your existing SQL workflows.

## Contributors
- [Shankar Narayanan SGS](https://github.com/sgsshankar)
- [Vivek Srinivasan](https://github.com/viveksrinivasanss)

## What This Tool Does

This stored procedure wraps the Cortex Agents REST API, allowing you to run agents directly as a Custom tool enabling to call one Agent from another. It handles the API communication, parses the event stream responses, and returns either just the agent's text response or the full response details including all events.

## Procedure Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| **DB_NAME** | VARCHAR | Required | The database containing your Cortex Agent |
| **SCHEMA_NAME** | VARCHAR | Required | The schema containing your Cortex Agent |
| **AGENT_NAME** | VARCHAR | Required | The name of your Cortex Agent |
| **PROMPT** | VARCHAR | Required | The natural language prompt/question to send to the agent |
| **API_TIMEOUT** | NUMBER | 50000 | Timeout in milliseconds for the API request |
| **AGENT_RESPONSE_ONLY** | BOOLEAN | TRUE | If TRUE, returns only the text response. If FALSE, returns full response object with events and metadata |

## Return Values

**When AGENT_RESPONSE_ONLY = TRUE (default):**
Returns a STRING containing just the agent's text response.

**When AGENT_RESPONSE_ONLY = FALSE:**
Returns a JSON STRING with the following structure:
```json
{
  "ok": true,
  "status": 200,
  "agent_response": "The agent's text response",
  "response.events": [...]
}
```

On error, returns:
```json
{
  "ok": false,
  "status": <status_code>,
  "response": {...},
  "payload": {...},
  "api_endpoint": "..."
}
```

## Installation Instructions

**Step 1: Configure your database and schema**

Update the database and schema where you want to create this procedure:

```sql
USE DATABASE YOUR_DATABASE;     
USE SCHEMA YOUR_SCHEMA;          
```

**Step 2: Create the stored procedure**

Run the SQL from `cortex_agent_run.sql` to create the procedure. The full code is included in that file.

**Step 3: Grant permissions**

```sql
-- Grant to roles that need to run agents programmatically
GRANT USAGE ON PROCEDURE CORTEX_AGENT_RUN(VARCHAR, VARCHAR, VARCHAR, VARCHAR, NUMBER, BOOLEAN) 
  TO ROLE YOUR_ROLE;
```

## Usage Examples

### Basic Usage (Text Response Only)

```sql
-- Simple question to your agent
CALL CORTEX_AGENT_RUN(
    'MY_DATABASE',
    'MY_SCHEMA',
    'MY_AGENT',
    'What were our top selling products last month?'
);
-- Returns: "Based on the data, your top selling products were..."
```

### Advanced Usage (Full Response Details)

```sql
-- Get full response with events and metadata
CALL CORTEX_AGENT_RUN(
    'MY_DATABASE',
    'MY_SCHEMA',
    'MY_AGENT',
    'Analyze customer churn trends',
    50000,  -- timeout in ms
    FALSE   -- return full response
);
-- Returns: {"ok": true, "status": 200, "agent_response": "...", "response.events": [...]}
```

### Custom Timeout

```sql
-- For complex analyses that might take longer
CALL CORTEX_AGENT_RUN(
    'MY_DATABASE',
    'MY_SCHEMA',
    'MY_AGENT',
    'Generate a comprehensive quarterly report',
    120000  -- 2 minute timeout
);
```

## How It Works

The procedure:
1. Constructs the proper API endpoint based on your agent location
2. Formats your prompt into the required message structure
3. Sends a POST request to the Cortex Agents REST API
4. Parses the line-delimited JSON event stream response
5. Extracts the final text from `response.text` and `response.text.delta` events
6. Returns either the simple text or the full response object

## Error Handling

The procedure includes comprehensive error handling:
- API failures return an error object with status code and details
- Timeout errors are caught and returned with context
- Response parsing errors are handled gracefully
- All errors are logged for debugging

## Use Cases

- **Agent to Agent**: Run another Cortex Agent as a Custom Tool from an Cortex Agent
- **Multi-Agent Orchestration**: Chain agent calls with one another

## Files Included

This directory contains:
- **`cortex_agent_run.sql`** - The stored procedure implementation
- **`README.md`** - This documentation file

## Resources

- **Cortex Agents REST API**: [Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-rest-api)
- **Snowflake Intelligence**: [Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/snowflake-intelligence)
- **Stored Procedures**: [Documentation](https://docs.snowflake.com/en/sql-reference/stored-procedures)

---

**Happy agent running!** 🤖