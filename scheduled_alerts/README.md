# Scheduled Intelligence Alerts

Subscribe to recurring analyses delivered via email. Users can ask your agent to schedule any question, and receive automated insights based on fresh data - daily or weekly.

## What This Tool Does

The magic of this tool is not actually in the custom tool itself, but in the scheduled python job that we run via airflow. The custom tool does nothing more than insert a row into a table, the custom python job runs every morning and creates beautiful HTML emails with fresh insights using the Cortex Agent API. 


## Tool Parameters

| Field | Value |
|-------|-------|
| **Tool Description** | Use this tool when a user asks to subscribe to an analysis, get recurring updates, or receive scheduled reports. This tool stores their subscription request for automated processing. |
| **user_email** | The email address of the user who wants to subscribe. Always use the email of the user making the request. Required. |
| **overall_question** | The natural language question the user wants to receive updates about. This should be the general question that will be re-run on a schedule. Required. |
| **frequency** | How often to send the alert. Must be either "Daily" or "Weekly". Always ask the user which frequency they prefer. Required. |





## Architecture Overview

The system consists of three main components:

1. **Custom Tool (SQL)**: Stored procedure that captures subscription requests from the agent
2. **Python Processing Script**: Runs the analyses using Cortex Agent API and generates emails
3. **Scheduler**: Orchestrates daily execution at 8am PST (Airflow, cron, etc.)

```
User asks agent → Custom tool stores subscription → Scheduler runs daily →
→ Python script calls Agent API → Generates insights → Sends email
```


## Files Included

This directory contains:
- **`schedule_analysis.sql`** - SQL script to create the custom tool, table, and alert management tools
- **`email_procedure.sql`** - SQL script to create the email sending stored procedure
- **`snowflake_intelligence_alerts.py`** - Python processing script
- **`snowflake_intelligence_alerts_DAG.py`** - Airflow DAG definition (example)

## Installation Instructions

### Part 1: Custom Tool Setup 

This enables users to subscribe via your agent.

**Step 1: Configure and create the alerts table**

Update the database and schema at the top of `schedule_analysis.sql`:

```sql
-- Update these for your environment
USE DATABASE YOUR_DATABASE;     
USE SCHEMA YOUR_SCHEMA;          
```

Then create the table:

```sql
CREATE TABLE IF NOT EXISTS snowflake_intelligence_scheduled_alerts (
    user_email VARCHAR NOT NULL,
    overall_question VARCHAR NOT NULL,
    alert_frequency VARCHAR NOT NULL DEFAULT 'Daily',
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
```

**Step 2: Create the stored procedures**

```sql
CREATE OR REPLACE PROCEDURE log_snowflake_intelligence_scheduled_alert(
    user_email STRING,
    overall_question STRING,
    alert_frequency STRING
)
RETURNS STRING
LANGUAGE SQL
EXECUTE AS OWNER
COMMENT = 'Custom tool for agent to log scheduled alert subscriptions'
AS
$$
BEGIN
  IF (alert_frequency NOT IN ('Daily', 'Weekly')) THEN
    RETURN 'ERROR: Frequency must be either Daily or Weekly';
  END IF;
  
  INSERT INTO snowflake_intelligence_scheduled_alerts
    (user_email, overall_question, alert_frequency)
  VALUES
    (:user_email, :overall_question, :alert_frequency);
  
  RETURN 'OK: Scheduled alert subscription created successfully';
END;
$$;
```

**Step 3: Grant permissions**

```sql
-- Grant to your agent's role (update YOUR_AGENT_ROLE)
GRANT USAGE ON PROCEDURE log_snowflake_intelligence_scheduled_alert(STRING, STRING, STRING) 
  TO ROLE YOUR_AGENT_ROLE; --you will need to make sure your end user has all the necessary access to databases and schemas as well
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

**Step 5: (Optional) Add Alert Management Tools**

To let users view and delete their alerts through the agent, the `schedule_analysis.sql` file already includes these procedures (Step 3 in that file):

- **`view_alerts_by_user`** - Returns JSON array of user's active alerts
- **`drop_alerts_by_user`** - Deletes a specific alert for a user

These are already created when you run `schedule_analysis.sql`. Just make sure to grant permissions:

**Grant permissions:**
```sql
GRANT USAGE ON PROCEDURE view_alerts_by_user(STRING) 
  TO ROLE YOUR_AGENT_ROLE;

GRANT USAGE ON PROCEDURE drop_alerts_by_user(STRING, STRING) 
  TO ROLE YOUR_AGENT_ROLE;
```

**Add to your agent as custom tools:**

| Tool | Parameters | Description |
|------|------------|-------------|
| `view_alerts_by_user` | `p_user_email` (STRING) | Returns JSON array of user's active alerts. Use when user asks "What alerts do I have?" or "Show my subscriptions" |
| `drop_alerts_by_user` | `user_email` (STRING), `overall_question` (STRING) | Deletes a specific alert. Use when user asks to "unsubscribe" or "cancel" an alert |

**Usage examples:**
```
User: "What alerts do I have subscribed to?"
Agent: [Uses view_alerts_by_user] 
       "You have 2 active alerts:
       1. Daily updates on Streamlit usage (Daily)
       2. Weekly customer report (Weekly)"

User: "Unsubscribe me from the daily Streamlit updates"
Agent: [Uses drop_alerts_by_user] 
       ✅ "You've been unsubscribed from that alert."
```

### Part 2: Email Procedure Setup

You can set up emails however you woud like, Airflow has a built in emailer, so does Snowflake, and there are a dozen great vendors who can help you here too. Snowflake's is good, the only downside is that the user needs to verify their email address and you need to create an email integration. There is no way around these two steps. If you want to use your own emailer, awesome! Just skip to part 3. 

Snowflake has a built-in system for emailing users. See the documentation [here](https://docs.snowflake.com/en/user-guide/notifications/email-notifications), but I will walk you though how to use it below. 

To use this system, you need to:
1. Make sure that the intended recipients verify their email addresses.

THIS STEP IS VERY IMPORTANT, EMAILS WILL NOT WORK IF YOU DO NOT DO THIS

2. Create a notification integration.

3. Call a stored procedure to send the notification.

**Step 1: Create an email integration (if you don't have one)**

```sql
CREATE NOTIFICATION INTEGRATION IF NOT EXISTS EXISTING_EMAIL_INTEGRATION
  TYPE=EMAIL
  ENABLED=TRUE;
```

**Step 2: Create the email stored procedure**

Run the SQL from `email_procedure.sql`:

```sql
CREATE OR REPLACE PROCEDURE standalone_email_formatted(
  recipient STRING,
  subject STRING,
  raw_html STRING
)
RETURNS STRING
LANGUAGE PYTHON
RUNTIME_VERSION=3.13
PACKAGES = ('snowflake-snowpark-python', 'premailer')
ARTIFACT_REPOSITORY = snowflake.snowpark.pypi_shared_repository
HANDLER = 'send_formatted_email'
EXECUTE AS CALLER
AS
$$
import premailer

INTEGRATION_NAME = "EXISTING_EMAIL_INTEGRATION"  -- Update this to your integration name

def send_formatted_email(session, recipient: str, subject: str, raw_html: str) -> str:
    """Inline CSS with premailer, then send HTML email via system$send_email."""
    try:
        formatted_html = premailer.transform(raw_html)
        session.call(
            'system$send_email',
            INTEGRATION_NAME,
            recipient,
            subject,
            formatted_html,
            'text/html',
        )
        return f"Email sent to {recipient}"
    except Exception as e:
        return f"Failed to send email: {type(e).__name__}: {e}"
$$;
```

**Important:** Update `INTEGRATION_NAME` in the procedure to match your email integration name.

**Step 3: Test the email procedure**

```sql
CALL standalone_email_formatted(
    'your.email@company.com',
    'Test Email',
    '<html><body><h1>Hello!</h1><p>This is a test email.</p></body></html>'
);
```

### Part 3: Automated Processing 

This adds the automated email delivery system. The included `snowflake_intelligence_alerts.py` file contains the main processing logic.

**Key Functions:**

1. **`run_agent(prompt, session)`** - Calls the Cortex Agent API to analyze data and generate insights
2. **`send_alert_email(session, recipient, subject, html_content)`** - Sends the formatted email via Snowflake's email system
3. **`process_alerts(preview_mode, max_alerts)`** - Main orchestration function that fetches alerts, processes them, and sends emails

**Step 1: Configure the script**

Update these configuration values at the top of `snowflake_intelligence_alerts.py`:

```python
# Update these for your environment
TARGET_DATABASE = "YOUR_DATABASE"        # e.g., "snowscience"
TARGET_SCHEMA = "YOUR_SCHEMA"            # e.g., "streamlit_apps"
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
2. Deploy to wherever you schedule python scripts today (we use Airflow)
3. Schedule to run daily at your preferred time (we use 8am PST)


## Monitoring

### Admin Reports

After each run, admins receive a summary email:
- Total alerts processed
- Success/failure counts
- Detailed results table with any errors
- Timestamps and performance metrics


## Code References

The full implementation is available in this repository:

- **Custom Tools**: `schedule_analysis.sql` - Subscription creation, viewing, and deletion tools
- **Email Procedure**: `email_procedure.sql` - HTML email sending with CSS inlining
- **Python Script**: `snowflake_intelligence_alerts.py` - Automated processing script
- **Airflow DAG**: `snowflake_intelligence_alerts_DAG.py` - Scheduling example

## Resources

- **Cortex Agents REST API**: [Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-rest-api)
- **Snowflake Intelligence**: [Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/snowflake-intelligence)
- **Email Integration**: [Documentation](https://docs.snowflake.com/en/user-guide/email-stored-procedures)

---

**Happy scheduling!** 🚀



