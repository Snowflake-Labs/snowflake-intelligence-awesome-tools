-- Snowflake Intelligence Scheduled Alerts - Custom Tool
-- This stored procedure is registered as a custom tool in your Snowflake Intelligence agent
-- It captures user subscription requests and stores them for scheduled processing

-- Step 1: Create the alerts table
CREATE TABLE IF NOT EXISTS snowscience.streamlit_apps.snowflake_intelligence_scheduled_alerts (
    user_email VARCHAR NOT NULL,
    overall_question VARCHAR NOT NULL,
    alert_frequency VARCHAR NOT NULL DEFAULT 'Daily',
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Step 2: Create the custom tool stored procedure
CREATE OR REPLACE PROCEDURE snowscience.streamlit_apps.log_snowflake_intelligence_scheduled_alert(
    user_email STRING,
    overall_question STRING,
    alert_frequency STRING
)
RETURNS STRING
LANGUAGE SQL
EXECUTE AS CALLER
COMMENT = 'Custom tool for Product Data Science Agent to log scheduled alert subscriptions'
AS
$$
BEGIN
  -- Validate frequency
  IF (alert_frequency NOT IN ('Daily', 'Weekly')) THEN
    RETURN 'ERROR: Frequency must be either Daily or Weekly';
  END IF;
  
  -- Insert the subscription
  INSERT INTO snowscience.streamlit_apps.snowflake_intelligence_scheduled_alerts
    (user_email, overall_question, alert_frequency)
  VALUES
    (:user_email, :overall_question, :alert_frequency);
  
  RETURN 'OK: Scheduled alert subscription created successfully';
END;
$$;

-- Step 3: Grant necessary permissions
-- Update these role names for your environment
GRANT USAGE ON PROCEDURE snowscience.streamlit_apps.log_snowflake_intelligence_scheduled_alert(STRING, STRING, STRING) 
  TO ROLE SNOWSCIENCE_AGENT_ROLE;

GRANT SELECT ON TABLE snowscience.streamlit_apps.snowflake_intelligence_scheduled_alerts 
  TO ROLE AIRFLOW_ROLE;

-- Management queries

-- View all active subscriptions
SELECT
    user_email,
    overall_question,
    alert_frequency,
    created_at
FROM snowscience.streamlit_apps.snowflake_intelligence_scheduled_alerts
ORDER BY created_at DESC;

-- Count subscriptions by frequency
SELECT
    alert_frequency,
    COUNT(*) AS subscription_count,
    COUNT(DISTINCT user_email) AS unique_users
FROM snowscience.streamlit_apps.snowflake_intelligence_scheduled_alerts
GROUP BY alert_frequency;

-- Find subscriptions for a specific user
SELECT
    overall_question,
    alert_frequency,
    created_at
FROM snowscience.streamlit_apps.snowflake_intelligence_scheduled_alerts
WHERE user_email = 'example.user@snowflake.com'
ORDER BY created_at DESC;

-- Unsubscribe a user from a specific alert
-- DELETE FROM snowscience.streamlit_apps.snowflake_intelligence_scheduled_alerts
-- WHERE user_email = 'user@email.com' 
--   AND overall_question = 'specific question text';


