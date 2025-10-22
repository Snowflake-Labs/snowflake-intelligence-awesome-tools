# Scheduled Intelligence Alerts

Subscribe to recurring analyses delivered via email. Users can ask the Product Data Science Agent to schedule any question, and receive automated insights based on fresh data - daily or weekly.

## Contributors

- [@zachary-blackwood](https://github.com/zachary-blackwood) - Tool creator
- [@tylerjrichards](https://github.com/tylerjrichards) - Tool creator

## Tool Parameters

| Field | Value |
|-------|-------|
| **Tool Description** | Use this tool when a user asks to subscribe to an analysis, get recurring updates, or receive scheduled reports. This tool stores their subscription request for automated processing. |
| **user_email** | The email address of the user who wants to subscribe. Always use the email of the user making the request. Required. |
| **overall_question** | The natural language question the user wants to receive updates about. This should be the general question that will be re-run on a schedule. Required. |
| **frequency** | How often to send the alert. Must be either "Daily" or "Weekly". Always ask the user which frequency they prefer. Required. |

## What This Tool Does

Scheduled Intelligence Alerts solves a common problem: users asking the same questions repeatedly to get updated analyses. Instead of manually re-entering questions, users can subscribe once and receive:

- **Automated Email Reports**: Beautiful HTML emails with AI-generated executive summaries
- **Fresh Insights**: Analysis runs automatically on the latest data
- **Flexible Scheduling**: Daily updates or weekly summaries every Monday
- **No Manual Work**: Set it once, receive updates automatically

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

## Prerequisites

**For Basic Setup:**
- Snowflake account with Snowflake Intelligence enabled
- Access to create tables and stored procedures
- Email integration enabled in Snowflake
- Your Snowflake Intelligence agent configured

**For Full Deployment (Airflow):**
- Airflow environment with Kubernetes support
- Docker image build capabilities
- Admin access to deploy DAGs

**Note**: You can start with just the custom tool to enable subscriptions, then add the automated processing later.

## Files Included

This directory contains:
- **`custom_tool.sql`** - SQL script to create the custom tool and table
- **`snowflake_intelligence_alerts.py`** - Python processing script (example from production)
- **`snowflake_intelligence_alerts_DAG.py`** - Airflow DAG definition (example from production)

## Installation Instructions

### Part 1: Custom Tool Setup (5 minutes)

This enables users to subscribe via your agent.

**Step 1: Create the alerts table**

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
  TO ROLE YOUR_AGENT_ROLE;
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

### Part 2: Automated Processing (Optional, 15 minutes)

This adds the automated email delivery system.

**Prerequisites:**
- Airflow environment
- Python 3.12+
- Access to Cortex Agent API

**Step 1: Use the Python script**

Use the included `snowflake_intelligence_alerts.py` file (or download from the [datascience-airflow repo](https://github.com/Snowflake-Labs/datascience-airflow/blob/main/product/custom/automated_emails/snowflake_intelligence_alerts.py)) and configure:

```python
# Update these for your environment
ALERTS_TABLE = "your_db.your_schema.snowflake_intelligence_scheduled_alerts"
EMAIL_PROC = "your_db.your_schema.your_email_procedure"
ADMIN_EMAILS = ["your.email@company.com"]
```

**Step 2: Use the Airflow DAG**

Use the included `snowflake_intelligence_alerts_DAG.py` file (or download from the [datascience-airflow repo](https://github.com/Snowflake-Labs/datascience-airflow/blob/main/product/custom/automated_emails/snowflake_intelligence_alerts_DAG.py)) and update:

```python
DEFAULT_ARGS = {
    "owner": "your_username",
    "email": ["your.email@company.com"],
    # ... rest of config
}
```

**Step 3: Deploy to Airflow**

```bash
# Copy files to your Airflow environment
cp snowflake_intelligence_alerts.py /path/to/airflow/dags/
cp snowflake_intelligence_alerts_DAG.py /path/to/airflow/dags/

# The DAG will run daily at 8am PST (15:00 UTC)
```

**Step 4: Test**

Option A - Test locally:
```python
# In snowflake_intelligence_alerts.py
PREVIEW_MODE = True
PREVIEW_EMAIL = "your.email@company.com"

# Run
python snowflake_intelligence_alerts.py
```

Option B - Trigger via Airflow UI and check logs

## Usage Examples

### Example 1: Daily Product Metrics

```
User: "Show me how many new agents were created yesterday"
Agent: [Provides analysis]
User: "Can I get this every morning?"
Agent: "I'll set up a daily alert for you. You'll receive this analysis 
       every morning at 8am PST. Subscribe?"
User: "Yes"
Agent: ✅ "Subscribed! You'll get your first email tomorrow morning."
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

### Example 2: Weekly Customer Report

```
User: "How is customer ACME123 using Cortex AI features this month?"
Agent: [Provides detailed analysis]
User: "I need this for my Monday customer meetings. Can you send it weekly?"
Agent: "Absolutely! I'll send you updated analysis every Monday morning. 
       This will include their latest Cortex AI usage, credit consumption,
       and trends. Subscribe?"
User: "Perfect!"
Agent: ✅ "Subscribed! You'll receive weekly updates every Monday at 8am PST."
```

## View Your Subscriptions

```sql
-- See all your subscriptions
SELECT 
    overall_question,
    alert_frequency,
    created_at
FROM snowscience.streamlit_apps.snowflake_intelligence_scheduled_alerts
WHERE user_email = 'your.email@snowflake.com'
ORDER BY created_at DESC;

-- See all subscriptions (admin view)
SELECT 
    user_email,
    overall_question,
    alert_frequency,
    created_at
FROM snowscience.streamlit_apps.snowflake_intelligence_scheduled_alerts
ORDER BY created_at DESC;

-- Count by frequency
SELECT 
    alert_frequency,
    COUNT(*) AS subscription_count,
    COUNT(DISTINCT user_email) AS unique_users
FROM snowscience.streamlit_apps.snowflake_intelligence_scheduled_alerts
GROUP BY alert_frequency;
```

## Unsubscribe

To unsubscribe from an alert:

```sql
-- Find your subscriptions
SELECT * FROM snowscience.streamlit_apps.snowflake_intelligence_scheduled_alerts
WHERE user_email = 'your.email@snowflake.com';

-- Delete specific subscription
DELETE FROM snowscience.streamlit_apps.snowflake_intelligence_scheduled_alerts
WHERE user_email = 'your.email@snowflake.com' 
  AND overall_question = 'your question here';
```

Or contact your admin (check the admin emails in the processing script configuration).

## Configuration Options

### Performance Tuning

For the Python processing script, adjust concurrency based on your alert volume:

**Small scale (< 10 alerts/day):**
```python
MAX_WORKERS = 4
HTTP_POOL_MAX = 16
```

**Medium scale (10-50 alerts/day):**
```python
MAX_WORKERS = 16  # Default
HTTP_POOL_MAX = 64  # Default
```

**Large scale (50+ alerts/day):**
```python
MAX_WORKERS = 32
MAX_WORKERS_CAP = 32
HTTP_POOL_MAX = 128
```

### Schedule Customization

The default schedule is 8am PST (15:00 UTC). To change:

```python
# In the Airflow DAG
schedule="0 16 * * *"  # 8am PST
schedule="0 14 * * *"  # 6am PST
schedule="0 17 * * *"  # 9am PST
```

## How It Works

### Subscription Flow

1. User asks a question in the agent
2. User requests to subscribe ("Can I get this daily?")
3. Agent uses the custom tool to store the subscription
4. Confirmation is returned to the user

### Processing Flow (Daily at 8am PST)

1. Airflow DAG triggers the Python script
2. Script fetches all Daily subscriptions (+ Weekly on Mondays)
3. For each subscription:
   - Calls Cortex Agent API with the user's question
   - Agent analyzes latest data and generates insights
   - Creates beautiful HTML email with executive summary
   - Sends email using Snowflake's email system
4. Sends admin summary report with success/failure counts

### Parallel Processing

The system processes up to 32 alerts concurrently:
- Extracts auth token once for reuse across threads
- Uses ThreadPoolExecutor for parallel agent API calls
- HTTP connection pooling reduces overhead
- Sends emails sequentially to avoid threading issues
- Typical processing time: 30 seconds per alert

## Prompt Engineering

The system generates executive-ready insights using a carefully crafted prompt:

```
CONTEXT:
- User's Question: [their question]
- Current Date: [today's date]

INSTRUCTIONS:
Analyze the results and provide insights.
Focus on insights and narrative, NOT data repetition.
This will be sent in an email, so use only standard characters.

STRUCTURE:
## Executive Summary
2-3 sentences that directly answer the question

## Key Insights
- Notable trends, changes, or patterns
- Outliers, anomalies, or unexpected results
- Opportunities or risks that warrant attention
- Specific numbers with context
- Actionable insights
```

The prompt emphasizes:
- ❌ No SQL shown to the agent (figures out best approach each time)
- ✅ Email-safe formatting (no special characters)
- ✅ Executive focus (insights over data)
- ✅ Consistent structure (scannable emails)
- ✅ Concise length (200-300 words)

## Monitoring

### Admin Reports

After each run, admins receive a summary email:
- Total alerts processed
- Success/failure counts
- Detailed results table with any errors
- Timestamps and performance metrics

### Airflow Monitoring

- Task duration tracking in Airflow UI
- Failure alerts via Slack
- Execution logs for debugging

### Database Monitoring

```sql
-- Recent alert activity
SELECT 
    DATE(created_at) AS subscription_date,
    COUNT(*) AS new_subscriptions
FROM snowscience.streamlit_apps.snowflake_intelligence_scheduled_alerts
WHERE created_at >= DATEADD(day, -7, CURRENT_TIMESTAMP())
GROUP BY DATE(created_at)
ORDER BY subscription_date DESC;
```

## Troubleshooting

### User not receiving emails

**Check:**
1. Verify email address in the database
2. Check user's spam folder
3. Review admin summary email for delivery status

**Common causes:**
- Typo in email address
- Email system configuration issue
- Snowflake email quota exceeded

### Agent not using the tool

**Check:**
1. Tool is properly registered in agent configuration
2. Tool permissions granted to agent role
3. Tool description includes keywords ("subscribe", "schedule", "updates")

**Fix:**
- Update agent instructions to mention this capability
- Add examples in agent configuration

### Processing failures

**Check:**
1. Airflow task logs for error details
2. Admin summary email for specific errors
3. Agent API authentication and quota

**Common causes:**
- Database connection issues
- Agent API rate limiting
- Invalid questions that can't be answered

### Subscription not created

**Check:**
```sql
SELECT * FROM snowscience.streamlit_apps.snowflake_intelligence_scheduled_alerts
WHERE user_email = 'user@company.com'
ORDER BY created_at DESC;
```

**Fix:**
- Verify stored procedure executed successfully
- Check table permissions
- Review agent logs for tool call errors

## Technical Details

### Dependencies

**Python:**
- `snowflake-snowpark-python[pandas]`
- `snowflake-connector-python[secure-local-storage]`
- `markdown`
- `pyyaml`
- `urllib3`
- `requests`

**Snowflake:**
- Snowflake Intelligence enabled
- Email integration configured
- Cortex Agent API access

### Performance Metrics

At Snowflake, we process:
- ~50 daily alerts
- ~15 weekly alerts (Mondays)
- Average processing: 30 seconds per alert
- Total daily runtime: 2-5 minutes
- Parallel execution: 16-32 concurrent alerts

### Security

- Uses Snowflake's built-in email system (no external services)
- Agent API authentication via Snowflake tokens
- All data stays within your Snowflake account
- No external credentials required
- Audit logging via Snowflake's standard mechanisms

## Code References

The full implementation is available in the Snowflake Labs datascience-airflow repository:

- **Python Script**: [`snowflake_intelligence_alerts.py`](https://github.com/Snowflake-Labs/datascience-airflow/blob/main/product/custom/automated_emails/snowflake_intelligence_alerts.py)
- **Airflow DAG**: [`snowflake_intelligence_alerts_DAG.py`](https://github.com/Snowflake-Labs/datascience-airflow/blob/main/product/custom/automated_emails/snowflake_intelligence_alerts_DAG.py)

## Why Airflow Instead of Snowflake Tasks?

As of October 2024, we chose Airflow because:

1. **Agent API reliability**: Better support for HTTP-based Agent API calls
2. **Existing infrastructure**: Our team's pipelines already run in Airflow
3. **Parallel processing**: Superior support for concurrent execution
4. **Monitoring**: Rich logging, alerting, and visualization
5. **Flexibility**: Easier to test locally and adjust settings

> **Note**: We're monitoring improvements to Snowflake Tasks support for Agent API and may migrate in the future.

## Resources

- **Blog Post**: [Scheduling Snowflake Intelligence Analyses](https://medium.com/snowflake/scheduling-snowflake-intelligence-analyses-LINK)
- **Cortex Agent API**: [Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agent-api)
- **Snowflake Intelligence**: [Documentation](https://docs.snowflake.com/en/user-guide/snowflake-intelligence)

## Getting Help

- **General questions**: tyler.richards@snowflake.com
- **Technical issues**: zachary.blackwood@snowflake.com
- **Feature requests**: Open an issue in this repository
- **Deployment help**: Check the [datascience-airflow repo](https://github.com/Snowflake-Labs/datascience-airflow)

---

**Happy scheduling!** 🚀


