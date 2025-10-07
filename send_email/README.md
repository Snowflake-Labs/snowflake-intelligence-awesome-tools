# Send Email Tool

Send emails directly from your Snowflake Intelligence agents using Snowflake's email integration.

## Tool Parameters

| Field | Value |
|-------|-------|
| **Tool Description** | Use this tool anytime you need to send an email |
| **Recipients** | The email recipients you want to send to (comma-separated). Always ask the user for this value. |
| **Subject** | The subject of the email. Automatically infer the subject of the email. |
| **Body** | The body content of the email |

## Installation Instructions

1. **Download the notebook**: Download the `send_email_tool.ipynb` file from this folder
2. **Import into Snowflake**: 
   - Open Snowflake and create a new notebook
   - Select "Import from IPYNB File" 
   - Upload the downloaded notebook file
3. **Run the notebook**: Execute all cells in the notebook one at a time

## Prerequisites

- **Email verification**: Ensure you have an email address set for your current Snowflake profile and you have gone through the steps to verify it
- **Account admin role**: You need the `ACCOUNTADMIN` role to create the email integration
- **Email integration**: The notebook will create a notification integration for email sending

## What This Tool Does

This tool creates a stored procedure called `send_email_tool` that:
- Accepts recipients, subject, and email content as parameters
- Uses Snowflake's `SYSTEM$SEND_EMAIL` function to send emails
- Returns a boolean indicating success/failure
- Can be called from your Snowflake Intelligence agents

## Setup Steps

The notebook will automatically:
1. Create an email notification integration called `EMAIL_CONNECTOR`
2. Start email verification for your current user
3. Test the email integration with a sample email
4. Create the `send_email_tool` stored procedure

## Usage

Once installed, you can use this tool in your Snowflake Intelligence agents by:
1. Adding it as a custom tool in your agent configuration
2. Providing the required parameters (recipients, subject, body)
3. The tool will send the email and return success/failure status

## Example Usage

```sql
-- Test the tool directly
CALL send_email_tool(
    'user@example.com',
    'Test Email from Snowflake',
    'This is a test email sent from Snowflake Intelligence.'
);
```

## Parameters

- **RECIPIENTS**: Comma-separated list of email addresses
- **SUBJECT**: Email subject line
- **EMAIL_CONTENT**: The body content of the email

## Permissions

After installation, you may need to grant usage permissions to other roles:

```sql
-- Grant usage to a specific role
GRANT USAGE ON PROCEDURE send_email_tool(VARCHAR, VARCHAR, VARCHAR) TO ROLE <user_role>;

-- Grant usage on the email integration
GRANT USAGE ON INTEGRATION email_connector TO ROLE <user_role>;
```

## Troubleshooting

- **Email not received**: Check your spam folder and verify the email integration is working
- **Permission errors**: Ensure you have the necessary roles and permissions
- **Integration errors**: Verify the email integration is enabled and properly configured
- **Verification required**: Complete the email verification process if prompted

## Security Notes

- The tool uses Snowflake's built-in email integration for security
- Email content is passed through Snowflake's secure email service
- No external email services or credentials are required
- All email sending is logged in Snowflake's audit logs

## Technical Details

- Uses Snowflake's `SYSTEM$SEND_EMAIL` function
- Implements a JavaScript stored procedure for parameter handling
- Includes proper error handling and validation
- Compatible with Snowflake Intelligence agent framework
