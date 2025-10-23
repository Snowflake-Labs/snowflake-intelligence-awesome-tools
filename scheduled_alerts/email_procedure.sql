-- Stored procedure for sending formatted HTML emails with inlined CSS
-- This procedure uses premailer to inline CSS styles before sending

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

INTEGRATION_NAME = "EXISTING_EMAIL_INTEGRATION"

def send_formatted_email(session, recipient: str, subject: str, raw_html: str) -> str:
    """Inline CSS with premailer, then send HTML email via system$send_email."""
    try:
        formatted_html = premailer.transform(raw_html)
        # Send email as HTML
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

-- Test the procedure with a sample email
-- Uncomment and update recipient to test
/*
CALL standalone_email_formatted(
    'your.email@company.com',
    'Key Metrics',
    $$
<html>
<head>
  <meta charset="UTF-8" />
  <style>
    body { font-family: Arial, sans-serif; margin:0; padding:0; background:#f6f9fc; }
    .container { max-width: 640px; margin: 0 auto; background: #ffffff; border-radius: 8px; overflow: hidden; }
    .header { background: #0b5cab; color: #fff; padding: 16px 24px; }
    .badge { display:inline-block; padding:2px 8px; border-radius:999px; background:#e3f2fd; color:#0b5cab; font-size:12px; }
    .content { padding: 24px; color:#1f2937; }
    h1 { font-size: 20px; margin: 0 0 8px; }
    p { line-height: 1.5; margin: 0 0 12px; }
    .card { border:1px solid #e5e7eb; border-radius:8px; padding:16px; margin:16px 0; }
    .btn { display:inline-block; background:#0b5cab; color:#fff !important; text-decoration:none; padding:10px 16px; border-radius:6px; }
    @media (max-width: 480px) { .content { padding: 16px; } h1 { font-size: 18px; } }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <span class="badge">Key Metrics</span>
      <h1>Daily metrics update</h1>
    </div>
    <div class="content">
      <p>Here are your key KPIs for today.</p>
      <div class="card">
        <strong>ARR</strong>: $12.3M<br/>
        <strong>New logos</strong>: 18<br/>
        <strong>NPS</strong>: 67
      </div>
      <a class="btn" href="https://example.com">View dashboard</a>
    </div>
  </div>
</body>
</html>
$$);
*/

