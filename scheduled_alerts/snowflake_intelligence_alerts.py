# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "markdown",
#     "snowflake-connector-python[secure-local-storage]",
#     "snowflake-snowpark-python[pandas]",
#     "pyyaml",
#     "urllib3",
# ]
# ///
"""Snowflake Intelligence Scheduled Alerts - Process and send scheduled alerts daily."""

from __future__ import annotations

import getpass
import json
import logging
import os
import sys
import traceback
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import markdown
import requests
import yaml
from snowflake.snowpark import Session
from snowflake.snowpark.context import get_active_session


def get_snowflake_session() -> Session:
    """Create and return a Snowflake session."""
    airflow_path = Path("./config/profiles.yml")
    if airflow_path.exists():
        config = yaml.safe_load(airflow_path.read_text())["snowscience"]
    else:
        config = {
            "account": "snowhouse",
            "user": getpass.getuser(),
            "authenticator": "externalbrowser",
        }

    return Session.builder.configs(config).create()


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION - Update these for your environment
# =============================================================================
TARGET_DATABASE = "YOUR_DATABASE"        # e.g., "snowscience"
TARGET_SCHEMA = "YOUR_SCHEMA"            # e.g., "streamlit_apps"
ADMIN_EMAILS = ["your.email@company.com"]

# Derived configuration (no need to change these)
ALERTS_TABLE = f"{TARGET_DATABASE}.{TARGET_SCHEMA}.snowflake_intelligence_scheduled_alerts"
EMAIL_PROC = f"{TARGET_DATABASE}.{TARGET_SCHEMA}.standalone_email_formatted"
DEFAULT_SUBJECT = "Snowflake Intelligence Alert: {question}"

# Preview mode settings (set to True for local testing)
PREVIEW_MODE = False
PREVIEW_EMAIL = "tyler.richards@snowflake.com"
PREVIEW_MAX_ALERTS = 10



@dataclass
class ScheduledAlert:
    """Data class for a scheduled alert."""

    user_email: str
    overall_question: str
    sql_statement: str
    created_at: datetime
    frequency: str = "Daily"

    def __post_init__(self):
        """Set default frequency if not provided."""
        if not self.frequency:
            self.frequency = "Daily"


def run_agent(prompt: str, session: Session) -> str:
    """
    Call PDS_AGENT using Snowflake Intelligence API.

    Args:
        prompt: The question/prompt to send to the agent
        session: Snowflake session

    Returns:
        The agent's response as a string
    """
    database = "SNOWFLAKE_INTELLIGENCE"
    schema = "AGENTS"
    agent = "PDS_AGENT"
    host = os.getenv(
        "SNOWFLAKE_HOST", "snowhouse.prod1.us-west-2.aws.snowflakecomputing.com"
    )

    # Try to get token from session
    token = None
    try:
        # SPCS token file
        token = open("/snowflake/session/token", "r").read()
    except Exception:
        try:
            # Try session REST token
            if hasattr(session, "conf"):
                rest_conf = session.conf.get("rest")
                if hasattr(rest_conf, "token"):
                    token = rest_conf.token
        except Exception:
            pass

    if not token:
        raise Exception(
            "Unable to get Snowflake authentication token. "
            "Ensure you're running in an environment with REST API support."
        )

    url = f"https://{host}/api/v2/databases/{database}/schemas/{schema}/agents/{agent}:run"
    headers = {
        "Authorization": f'Snowflake Token="{token}"',
        "Content-Type": "application/json",
    }

    request_data = {
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}],
            },
        ],
    }

    # Call the agent API with timeout
    response = requests.post(
        url, headers=headers, json=request_data, stream=False, timeout=300
    )

    # Extract all text content from the streaming response
    final_text = ""
    chunks = response.text.split("\n\n")

    for chunk in chunks:
        lines = chunk.strip().split("\n")
        if len(lines) >= 2:
            event_line = lines[0]
            data_line = lines[1]

            if event_line == "event: response.text":
                chars_to_strip = "data: "
                if data_line.startswith(chars_to_strip):
                    json_data = data_line[len(chars_to_strip) :]
                    try:
                        parsed_data = json.loads(json_data)
                        if "text" in parsed_data:
                            final_text += parsed_data["text"]
                    except json.JSONDecodeError:
                        continue

    return final_text


def generate_cortex_prompt(question: str, sql_statement: str) -> str:
    """Generate a prompt for the agent to analyze the alert."""
    prompt = f"""Analyze the following question and provide
    an executive narrative summary for a business email. The user
    has asked to be subscribed to this alert via the Product Data
    Science Agent.

CONTEXT:
- User's Question: {question}
- Current Date: {datetime.now().strftime("%Y-%m-%d")}

INSTRUCTIONS:
Analyze the results and provide insights.
Focus on insights and narrative, NOT data repetition.
IMPORTANT: This will be sent in an email, so use only standard characters
and proper markdown formatting. Avoid special characters that might cause
email rendering issues.

STRUCTURE:
## Executive Summary
Write 2-3 sentences that directly answer the user's question based on the data. Include:
- Overall key findings or performance metrics
- Important trends, patterns, or anomalies
- Business implications or follow-up opportunities

## Key Insights
Use bullet points to highlight only the most significant findings:
- Call out notable trends, changes, or patterns in the data
- Highlight any outliers, anomalies, or unexpected results
- Identify opportunities or risks that warrant attention
- Include specific numbers and context when relevant (e.g., "Account X showed a 45% increase")
- Focus on actionable insights, not just data description

REQUIREMENTS:
- Keep it concise (200-300 words total)
- Format with markdown: ## for headers, - for bullets
- Use **bold** for: important metrics, entity names,
    and key numbers for emphasis
- Be specific with numbers and include context (e.g.,
    "increased to 1.2M credits" rather than just "increased")
- Focus on the "so what?" - why does this data matter?
- Do not mention subscribing to alerts or future updates
- If the data is empty or shows no notable patterns,
    acknowledge this clearly and suggest potential next steps
- At the very end, thank the user for subscribing to this alert,
    and tell them to contact Tyler Richards for feedback or questions
"""
    return prompt


def generate_alert_summary(
    question: str,
    sql_statement: str,
    session: Session,
) -> str:
    """Generate AI summary by having the agent run the query and analyze results."""
    logger.info(f"📝 Generating prompt for question: {question[:100]}...")
    prompt = generate_cortex_prompt(question, sql_statement)
    logger.info(f"📤 Sending prompt to agent (length: {len(prompt)} chars)...")

    try:
        summary = run_agent(prompt, session)

        if not summary or not summary.strip():
            raise ValueError("Agent returned empty response")

        logger.info(f"✅ Agent returned summary (length: {len(summary)} chars)")
        return summary.strip()

    except Exception as e:
        logger.error(f"❌ Agent analysis failed: {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        raise


def generate_alert_email(
    alert: ScheduledAlert,
    ai_summary: str,
    error_message: str | None = None,
) -> str:
    """Generate HTML email content for an alert."""
    timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    # Convert markdown to HTML for better email rendering
    if ai_summary and not error_message:
        ai_summary_html = markdown.markdown(ai_summary)
    else:
        ai_summary_html = ai_summary

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background-color: #f8f9fa;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0 0 10px 0;
            color: #1976d2;
            font-size: 24px;
        }}
        .header p {{
            margin: 0;
            color: #666;
            font-size: 14px;
        }}
        .content {{
            background-color: white;
            padding: 30px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
        }}
        .section {{
            margin-bottom: 30px;
        }}
        .section h2 {{
            color: #424242;
            font-size: 18px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e0e0e0;
        }}
        .ai-summary {{
            background-color: #e3f2fd;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #1976d2;
            font-size: 15px;
            line-height: 1.8;
        }}
        .error {{
            background-color: #ffebee;
            color: #c62828;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #d32f2f;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            font-size: 12px;
            color: #666;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 {alert.overall_question}</h1>
            <p>Snowflake Intelligence Alert • {timestamp}</p>
        </div>

        <div class="content">
            {
        '<div class="section"><div class="error"><strong>⚠️ Error:</strong><br>'
        + error_message
        + "</div></div>"
        if error_message
        else f'''
            <div class="section">
                <h2>🤖 AI Analysis</h2>
                <div class="ai-summary">
                    {ai_summary_html}
                </div>
            </div>
            '''
    }
        </div>

        <div class="footer">
            <p>
                This is an automated alert from Snowflake Intelligence.<br>
                To modify or unsubscribe from this alert, please update your settings in the
                Snowflake Intelligence app.
            </p>
        </div>
    </div>
</body>
</html>
"""

    return html


def send_alert_email(
    session: Session, recipient: str, subject: str, html_content: str
) -> bool:
    """Send email using Snowflake stored procedure."""
    try:
        session.sql(
            f"CALL {EMAIL_PROC}(?, ?, ?)", params=[recipient, subject, html_content]
        ).collect()

        logger.info(f"📧 Email sent to {recipient}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to send email to {recipient}: {str(e)}")
        return False


def fetch_alerts(session: Session, frequencies: list[str]) -> list[ScheduledAlert]:
    """Fetch alerts for the given frequencies from the database."""
    all_alerts = []

    for frequency in frequencies:
        query = f"""
        SELECT
            user_email,
            overall_question,
            sql_statement,
            frequency,
            created_at
        FROM {ALERTS_TABLE}
        WHERE UPPER(COALESCE(frequency, 'DAILY')) = UPPER(?)
        ORDER BY created_at DESC
        """

        logger.info(f"📊 Fetching {frequency} alerts...")
        results = session.sql(query, params=[frequency]).to_pandas()

        for _, row in results.iterrows():
            alert = ScheduledAlert(
                user_email=row["USER_EMAIL"],
                overall_question=row["OVERALL_QUESTION"],
                sql_statement=row["SQL_STATEMENT"],
                frequency=row["FREQUENCY"],
                created_at=row["CREATED_AT"],
            )
            all_alerts.append(alert)

        logger.info(f"✅ Found {len(results)} {frequency} alerts")

    logger.info(f"📋 Total alerts to process: {len(all_alerts)}")
    return all_alerts


def process_alert(
    alert: ScheduledAlert,
    session: Session,
    preview_mode: bool = False,
    preview_email: str = PREVIEW_EMAIL,
    alert_num: int = 1,
    total_alerts: int = 1,
) -> dict:
    """Process a single alert and return result."""
    logger.info("=" * 80)
    logger.info(f"🔔 Processing alert {alert_num}/{total_alerts}")
    logger.info(f"   User: {alert.user_email}")
    logger.info(f"   Question: {alert.overall_question}")
    logger.info("=" * 80)

    result = {
        "email": alert.user_email,
        "question": alert.overall_question,
        "success": False,
        "error": None,
    }

    try:
        # Generate AI summary - the agent will run the SQL itself
        logger.info("🤖 Starting agent analysis...")
        ai_summary = generate_alert_summary(
            alert.overall_question, alert.sql_statement, session
        )
        logger.info("✅ Agent analysis completed successfully")

        # Generate email HTML
        logger.info("📧 Generating email HTML...")
        html_content = generate_alert_email(alert, ai_summary, error_message=None)

        # Determine recipient (preview mode or actual user)
        recipient = preview_email if preview_mode else alert.user_email

        # Send email
        subject = DEFAULT_SUBJECT.format(question=alert.overall_question[:50])
        if preview_mode:
            subject = f"[PREVIEW] {subject}"

        logger.info(f"📤 Sending email to {recipient}...")
        success = send_alert_email(session, recipient, subject, html_content)

        result["success"] = success
        if success:
            logger.info(f"✅ Alert {alert_num}/{total_alerts} completed successfully")
        else:
            logger.error(f"❌ Alert {alert_num}/{total_alerts} failed to send email")

    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        logger.error(f"❌ Error processing alert: {error_type}: {error_msg}")
        traceback.print_exc()
        result["error"] = f"{error_type}: {error_msg}"

        # In preview mode, send error notification
        if preview_mode:
            logger.info("🧪 Preview mode: Sending error notification email")
            error_html = generate_alert_email(
                alert, "", f"Alert processing failed: {error_type}: {error_msg}"
            )
            subject = f"[PREVIEW] Error: {alert.overall_question[:50]}"
            send_alert_email(session, preview_email, subject, error_html)

    return result


def send_summary_report(session: Session, results: list[dict]) -> None:
    """Send summary report to admins."""
    total_success = sum(1 for r in results if r["success"])
    total_failed = len(results) - total_success

    summary_html = f"""<html>
<body style="font-family: sans-serif;">
<h1>Snowflake Intelligence Alerts Status Report -- Airflow Version</h1>
<p><strong>Date:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
<p><strong>Total Processed:</strong> {len(results)}</p>
<p><strong>Successful:</strong> {total_success}</p>
<p><strong>Failed:</strong> {total_failed}</p>

<h2>Details</h2>
<table border="1" style="border-collapse: collapse; width: 100%;">
<tr style="background-color: #f0f0f0;">
    <th style="padding: 8px;">User Email</th>
    <th style="padding: 8px;">Question</th>
    <th style="padding: 8px;">Status</th>
    <th style="padding: 8px;">Error</th>
</tr>
"""

    for result in results:
        status = "✅ Success" if result["success"] else "❌ Failed"
        error = result["error"] or "-"
        question_truncated = (
            result["question"][:60] + "..."
            if len(result["question"]) > 60
            else result["question"]
        )
        error_truncated = error[:100] if error != "-" else "-"

        summary_html += f"""
<tr>
    <td style="padding: 8px;">{result["email"]}</td>
    <td style="padding: 8px;">{question_truncated}</td>
    <td style="padding: 8px;">{status}</td>
    <td style="padding: 8px; font-size: 0.9em;">{error_truncated}</td>
</tr>
"""

    summary_html += """</table>
</body>
</html>"""

    # Send to admins
    admin_recipients = ", ".join(ADMIN_EMAILS)
    subject = (
        f"Snowflake Intelligence Alerts Status - {datetime.now().strftime('%Y-%m-%d')}"
    )

    logger.info(f"📧 Sending summary report to admins: {admin_recipients}")
    send_alert_email(session, admin_recipients, subject, summary_html)
    logger.info("✅ Summary report sent")


def process_alerts(
    preview_mode: bool = PREVIEW_MODE, max_alerts: int | None = None
) -> None:
    """Main function to process scheduled alerts and send emails."""
    logger.info("Starting Snowflake Intelligence Alerts processing")
    logger.info(f"Current time: {datetime.now()}")
    logger.info(f"Preview mode: {preview_mode}")
    if preview_mode:
        logger.info(f"Preview email: {PREVIEW_EMAIL}")
        logger.info(f"Preview max alerts: {PREVIEW_MAX_ALERTS}")

    # Get Snowflake session
    try:
        session = get_active_session()
        logger.info("✅ Using active Snowpark session")
    except Exception:
        try:
            session = get_snowflake_session()
        except Exception as e:
            logger.error(f"❌ Failed to get Snowflake session: {e}")
            sys.exit(1)

    # Determine which frequencies to process based on day of week
    day_of_week = datetime.now().strftime("%A")
    frequencies_to_process = (
        ["Daily", "Weekly"] if day_of_week == "Monday" else ["Daily"]
    )

    logger.info(f"📅 Today is {day_of_week}")
    logger.info(f"📋 Will process: {', '.join(frequencies_to_process)} alerts")

    # Fetch alerts
    all_alerts = fetch_alerts(session, frequencies_to_process)

    # Apply max alerts limit if specified
    if max_alerts and len(all_alerts) > max_alerts:
        logger.info(f"🔢 Limiting to {max_alerts} alert(s)")
        all_alerts = all_alerts[:max_alerts]

    # Apply preview mode limit
    if preview_mode and PREVIEW_MAX_ALERTS and len(all_alerts) > PREVIEW_MAX_ALERTS:
        logger.info(f"🧪 Preview mode: Limiting to {PREVIEW_MAX_ALERTS} alert(s)")
        all_alerts = all_alerts[:PREVIEW_MAX_ALERTS]

    if not all_alerts:
        logger.info("No alerts to process")
        return

    # Process alerts sequentially
    results = []
    logger.info("🚶 Processing alerts sequentially...")
    for i, alert in enumerate(all_alerts, 1):
        result = process_alert(
            alert,
            session,
            preview_mode=preview_mode,
            preview_email=PREVIEW_EMAIL,
            alert_num=i,
            total_alerts=len(all_alerts),
        )
        results.append(result)

    # Print summary
    total_success = sum(1 for r in results if r["success"])
    logger.info("=" * 80)
    logger.info("✅ Processing complete!")
    logger.info(f"   Total alerts: {len(all_alerts)}")
    logger.info(f"   Successful: {total_success}")
    logger.info(f"   Failed: {len(all_alerts) - total_success}")
    logger.info("=" * 80)

    # Send summary report to admins
    send_summary_report(session, results)


if __name__ == "__main__":
    process_alerts(preview_mode=PREVIEW_MODE)
