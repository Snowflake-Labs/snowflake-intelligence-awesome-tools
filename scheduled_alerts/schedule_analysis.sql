-- Snowflake Intelligence Scheduled Alerts - Custom Tool
-- This stored procedure is registered as a custom tool in your Snowflake Intelligence agent
-- It captures user subscription requests and stores them for scheduled processing

-- =============================================================================
-- CONFIGURATION - Update these for your environment
-- =============================================================================
USE DATABASE YOUR_DATABASE;      
USE SCHEMA YOUR_SCHEMA;          

-- Step 1: Create the alerts table
CREATE TABLE IF NOT EXISTS snowflake_intelligence_scheduled_alerts (
    user_email VARCHAR NOT NULL,
    overall_question VARCHAR NOT NULL,
    alert_frequency VARCHAR NOT NULL DEFAULT 'Daily',
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Step 2: Create the custom tool stored procedure
CREATE OR REPLACE PROCEDURE log_snowflake_intelligence_scheduled_alert(
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
  INSERT INTO snowflake_intelligence_scheduled_alerts
    (user_email, overall_question, alert_frequency)
  VALUES
    (:user_email, :overall_question, :alert_frequency);
  
  RETURN 'OK: Scheduled alert subscription created successfully';
END;
$$;

-- Step 3: Create alert management tools (optional)
-- These procedures allow users to view and delete their alerts via the agent

CREATE OR REPLACE PROCEDURE view_alerts_by_user(
    p_user_email STRING
)
RETURNS STRING
LANGUAGE SQL
EXECUTE AS OWNER
COMMENT = 'Custom tool to view all scheduled alerts for a user'
AS
$$
DECLARE
  alerts_json STRING;
BEGIN
  SELECT 
    TO_JSON(
      ARRAY_AGG(
        OBJECT_CONSTRUCT(
          'overall_question', t.overall_question,
          'frequency', t.alert_frequency,
          'created_at', t.created_at
        )
      ) WITHIN GROUP (ORDER BY t.created_at DESC)
    )
  INTO :alerts_json
  FROM snowflake_intelligence_scheduled_alerts AS t
  WHERE t.user_email = :p_user_email;

  RETURN COALESCE(alerts_json, '[]')::string;
END;
$$;

CREATE OR REPLACE PROCEDURE drop_alerts_by_user(
    user_email STRING,
    overall_question STRING
)
RETURNS STRING
LANGUAGE SQL
EXECUTE AS OWNER
COMMENT = 'Custom tool to delete a scheduled alert for a user'
AS
$$
DECLARE
  rows_deleted INTEGER;
BEGIN
  DELETE FROM snowflake_intelligence_scheduled_alerts
  WHERE user_email = :user_email
    AND overall_question = :overall_question;
  
  rows_deleted := SQLROWCOUNT;
  
  IF (rows_deleted > 0) THEN
    RETURN 'OK: Successfully unsubscribed from alert: ' || :overall_question;
  ELSE
    RETURN 'ERROR: No alert found matching that question. Please check your subscriptions.';
  END IF;
END;
$$;

-- Step 4: Grant necessary permissions
-- Update YOUR_AGENT_ROLE and YOUR_AIRFLOW_ROLE for your environment
GRANT USAGE ON PROCEDURE log_snowflake_intelligence_scheduled_alert(STRING, STRING, STRING) 
  TO ROLE YOUR_AGENT_ROLE;

GRANT USAGE ON PROCEDURE view_alerts_by_user(STRING) 
  TO ROLE YOUR_AGENT_ROLE;

GRANT USAGE ON PROCEDURE drop_alerts_by_user(STRING, STRING) 
  TO ROLE YOUR_AGENT_ROLE;

GRANT SELECT ON TABLE snowflake_intelligence_scheduled_alerts 
  TO ROLE YOUR_AIRFLOW_ROLE;

--Step 5: Give you agent access to the tools
-- You can add these by pressing the + button next to the agent, and then briefly describing the tool and its parameters.

-- =============================================================================
-- MANAGEMENT QUERIES (for manual use)
-- =============================================================================

-- View all active subscriptions
SELECT
    user_email,
    overall_question,
    alert_frequency,
    created_at
FROM snowflake_intelligence_scheduled_alerts
ORDER BY created_at DESC;

-- Count subscriptions by frequency
SELECT
    alert_frequency,
    COUNT(*) AS subscription_count,
    COUNT(DISTINCT user_email) AS unique_users
FROM snowflake_intelligence_scheduled_alerts
GROUP BY alert_frequency;

-- Find subscriptions for a specific user
SELECT
    overall_question,
    alert_frequency,
    created_at
FROM snowflake_intelligence_scheduled_alerts
WHERE user_email = 'example.user@company.com'
ORDER BY created_at DESC;

-- Unsubscribe a user from a specific alert
-- DELETE FROM snowflake_intelligence_scheduled_alerts
-- WHERE user_email = 'user@email.com' 
--   AND overall_question = 'specific question text';


