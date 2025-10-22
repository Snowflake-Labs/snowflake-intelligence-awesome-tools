# Scheduled Intelligence Alerts

Subscribe to recurring analyses delivered via email. Users can ask your agent to schedule any question, and receive automated insights based on fresh data - daily or weekly.

## Contributors

- Zachary Blackwood
- Tyler Richards

## Tool Parameters

| Field | Value |
|-------|-------|
| **Tool Description** | Use this tool when a user asks to subscribe to an analysis, get recurring updates, or receive scheduled reports. This tool stores their subscription request for automated processing. |
| **user_email** | The email address of the user who wants to subscribe. Always use the email of the user making the request. Required. |
| **overall_question** | The natural language question the user wants to receive updates about. This should be the general question that will be re-run on a schedule. Required. |
| **frequency** | How often to send the alert. Must be either "Daily" or "Weekly". Always ask the user which frequency they prefer. Required. |

## What This Tool Does

The magic of this tool is not actually in the custom tool itself, but in the scheduled python job that we run via airflow. The custom tool does nothing more than insert a row into a table, the custom python job runs every morning and creates Beautiful HTML emails with fresh insights. 

**Example Use Cases:**
- Sales teams tracking weekly customer usage patterns
- Product teams monitoring daily feature adoption metrics
- DevRel tracking new agent creation trends
- Executives receiving automated performance summaries

## Architecture Overview

The system consists of three main components:

1. **Custom Tool (SQL)**: Stored procedure that captures subscription requests from the agent
2. **Python Processing Script**: Runs the analyses using Cortex Agent API and generates emails
3. **Airflow Scheduler**: Orchestrates daily execution at 8am PST

```
User asks agent → Custom tool stores subscription → Airflow runs daily →
→ Python script calls Agent API → Generates insights → Sends email
```


## Files Included

This directory contains:
- **`custom_tool.sql`** - SQL script to create the custom tool and table
- **`snowflake_intelligence_alerts.py`** - Python processing script (example from production)
- **`snowflake_intelligence_alerts_DAG.py`** - Airflow DAG definition (example from production)

## Installation Instructions

### Part 1: Custom Tool Setup 

This enables users to subscribe via your agent.

**Step 1: Create the alerts table**

Make sure to replace the fully qualified table names with one where your roles have access!

```sql
CREATE TABLE IF NOT EXISTS snowscience.streamlit_apps.snowflake_intelligence_scheduled_alerts (
    user_email VARCHAR NOT NULL,
    overall_question VARCHAR NOT NULL,
    alert_frequency VARCHAR NOT NULL DEFAULT 'Daily',
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
```

**Step 2: Create the stored procedure**

```sql
CREATE OR REPLACE PROCEDURE snowscience.streamlit_apps.log_snowflake_intelligence_scheduled_alert(
    user_email STRING,
    overall_question STRING,
    alert_frequency STRING
)
RETURNS STRING
LANGUAGE SQL
EXECUTE AS CALLER
COMMENT = 'Custom tool for agent to log scheduled alert subscriptions'
AS
$$
BEGIN
  IF (alert_frequency NOT IN ('Daily', 'Weekly')) THEN
    RETURN 'ERROR: Frequency must be either Daily or Weekly';
  END IF;
  
  INSERT INTO snowscience.streamlit_apps.snowflake_intelligence_scheduled_alerts
    (user_email, overall_question, alert_frequency)
  VALUES
    (:user_email, :overall_question, :alert_frequency);
  
  RETURN 'OK: Scheduled alert subscription created successfully';
END;
$$;
```

**Step 3: Grant permissions**

```sql
-- Grant to your agent's role
GRANT USAGE ON PROCEDURE snowscience.streamlit_apps.log_snowflake_intelligence_scheduled_alert(STRING, STRING, STRING) 
  TO ROLE YOUR_AGENT_ROLE; --make sure to grant usage to the roles that people use for your agent as well!
```

**Step 4: Add to your Snowflake Intelligence agent**

In your agent configuration, add this custom tool with the parameters shown in the Tool Parameters table above. Tell the agent:
- Use this when users ask to "subscribe", "get updates", or "schedule" an analysis
- Always ask users if they want "Daily" or "Weekly" frequency
- Confirm the subscription was created successfully

**Test it:**
```
User: "Can I get daily updates on Streamlit usage?"
Agent: [Uses tool to create subscription] 
       ✅ "You've been subscribed! You'll receive daily updates at 8am PST."
```

### Part 2: Automated Processing 

This adds the automated email delivery system. The included `snowflake_intelligence_alerts.py` file contains the main processing logic.

**Key Functions:**

1. **`run_agent(prompt, session)`** - Calls the Cortex Agent API to analyze data and generate insights
2. **`send_alert_email(session, recipient, subject, html_content)`** - Sends the formatted email via Snowflake's email system
3. **`process_alerts(preview_mode, max_alerts)`** - Main orchestration function that fetches alerts, processes them, and sends emails

**Step 1: Configure the script**

Update these configuration values in `snowflake_intelligence_alerts.py`:

```python
# Update these for your environment
ALERTS_TABLE = "your_db.your_schema.snowflake_intelligence_scheduled_alerts"
EMAIL_PROC = "your_db.your_schema.your_email_procedure"
ADMIN_EMAILS = ["your.email@company.com"]

# For testing, enable preview mode
PREVIEW_MODE = True  # Set to True for testing, False for production
PREVIEW_EMAIL = "your.email@company.com"  # Receives all preview emails
```

**Step 2: Test locally with Preview Mode**

Preview mode is crucial for testing - it redirects all emails to a single address and limits the number of alerts processed:

```python
# In snowflake_intelligence_alerts.py, set:
PREVIEW_MODE = True
PREVIEW_EMAIL = "your.email@company.com"
PREVIEW_MAX_ALERTS = 10

# Then run:
python snowflake_intelligence_alerts.py
```

This will:
- Send all emails to your preview email (not real users)
- Limit processing to 10 alerts max
- Add "[PREVIEW]" prefix to email subjects

**Step 3: Deploy to Production**

Once testing is complete:

1. Set `PREVIEW_MODE = False` in the script
2. Deploy to your scheduler (Airflow, cron, etc.)
3. Schedule to run daily at your preferred time (we use 8am PST)

## Usage Examples

### Example: Daily Product Metrics

```
User: "Show me how many new agents were created yesterday"
Agent: [Provides analysis]
User: "Can I get this every morning?"
Agent: "I'll set up a daily alert for you. You'll receive this analysis 
       every morning at 8am PST."
```

**Email delivered next day:**
```
Subject: Snowflake Intelligence Alert: How many new agents...

## Executive Summary
Yesterday saw 23 new agents created across 15 companies, representing 
a 15% increase from the previous Tuesday average...

## Key Insights
- Top creator: john@acme.com created 5 new agents
- Most popular type: RAG agents (45% of new agents)
- New milestone: TechStart Inc created their first production agent
...
```


**Happy scheduling!** 🚀


