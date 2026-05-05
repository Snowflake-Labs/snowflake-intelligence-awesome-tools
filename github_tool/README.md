# GitHub Tool for Snowflake Intelligence

Query GitHub repositories directly from your Snowflake Intelligence or Cortex agents — read issues, pull requests, file contents, and search across any repo.

## Contributors

- [@yashukreddy](https://github.com/yashukreddy) - Tool creator

## Tool Parameters

| Field | Value |
|-------|-------|
| **Tool Description** | Use this tool to query GitHub repositories. Use it when you need to look up issues, pull requests, file contents, or search for information in a GitHub repository. |
| **action** | The operation to perform. Must be one of: `list_issues`, `get_issue`, `list_prs`, `get_file`, `search_issues` |
| **repo** | The GitHub repository in `owner/repo` format (e.g. `Snowflake-Labs/snowflake-intelligence-awesome-tools`) |
| **query** | Context-dependent: issue number for `get_issue`, file path for `get_file`, search keyword for `search_issues`, optional label filter for `list_issues`. Leave empty for `list_prs`. |

## Installation Instructions

1. **Download the notebook**: Download the `github_tool.ipynb` file from this folder
2. **Import into Snowflake**:
   - Open Snowflake and create a new notebook
   - Select **"Import from IPYNB File"**
   - Upload the downloaded notebook file
3. **Add your GitHub token**: In Cell 5, replace `<your-github-pat-token>` with your actual token
4. **Update database and schema**: In Cells 3–8, replace `YOUR_DB` and `YOUR_SCHEMA` with your actual database and schema names
5. **Run all cells** one at a time in order

## Prerequisites

- **GitHub Personal Access Token (PAT)**: Generate a Classic token at [github.com/settings/tokens](https://github.com/settings/tokens)
  - For public repos: select `public_repo` scope
  - For private repos: select the full `repo` scope
- **ACCOUNTADMIN role**: Required to create network rules, secrets, and external access integrations
- **Network access**: Your Snowflake account must support external network access (not available on trial accounts)

## What This Tool Does

This tool creates a stored procedure called `github_tool_sproc` that:
- Accepts an `action`, `repo`, and optional `query` parameter
- Authenticates to the GitHub REST API using your securely stored PAT
- Returns clean, readable text results — not raw JSON — so agents can reason over them directly
- Caps results at 10 items and truncates large files at 3,000 characters to stay within agent context limits

## Supported Actions

| Action | Description | `query` value |
|---|---|---|
| `list_issues` | List open issues in a repo | Optional: label name to filter by |
| `get_issue` | Get full details of a specific issue | Issue number (e.g. `42`) |
| `list_prs` | List open pull requests | Leave empty |
| `get_file` | Fetch the contents of a file | File path (e.g. `README.md`) |
| `search_issues` | Search issues and PRs by keyword | Search keyword |

## Example Usage

```sql
-- List open issues
CALL github_tool_sproc('list_issues', 'Snowflake-Labs/snowflake-intelligence-awesome-tools', '');

-- Get a specific issue
CALL github_tool_sproc('get_issue', 'Snowflake-Labs/snowflake-intelligence-awesome-tools', '5');

-- List open pull requests
CALL github_tool_sproc('list_prs', 'Snowflake-Labs/snowflake-intelligence-awesome-tools', '');

-- Fetch a file
CALL github_tool_sproc('get_file', 'Snowflake-Labs/snowflake-intelligence-awesome-tools', 'README.md');

-- Search issues by keyword
CALL github_tool_sproc('search_issues', 'Snowflake-Labs/snowflake-intelligence-awesome-tools', 'bug');
```

## Example Agent Instruction

Add this as the tool description when configuring your Snowflake Intelligence agent:

> Use the `github_tool_sproc` tool when you need to look up information from a GitHub repository — such as open issues, pull requests, file contents, or searching for a topic. Always ask the user for the repository name in `owner/repo` format if not already provided.

## Permissions

After installation, grant access to additional roles as needed:

```sql
-- Grant usage on the stored procedure
GRANT USAGE ON PROCEDURE github_tool_sproc(VARCHAR, VARCHAR, VARCHAR) TO ROLE <your_role>;

-- Grant usage on the external access integration
GRANT USAGE ON INTEGRATION github_access_integration TO ROLE <your_role>;

-- Grant usage on the stage
GRANT USAGE ON STAGE custom_tools TO ROLE <your_role>;
```

## Setup Steps (What the Notebook Does)

The notebook will automatically:
1. Create a dedicated database and schema for the tool objects
2. Create a network rule allowing egress to `api.github.com:443`
3. Store your GitHub PAT securely as a Snowflake secret
4. Create an external access integration linking the rule and secret
5. Create a stage to host the stored procedure
6. Deploy the `github_tool_sproc` stored procedure
7. Run 5 test calls to verify everything works

## Troubleshooting

- **401 Unauthorized**: Your PAT is invalid or expired — generate a new one at [github.com/settings/tokens](https://github.com/settings/tokens)
- **403 Forbidden**: Your PAT doesn't have the required scopes — private repos need full `repo` scope
- **404 Not Found**: The repo or file path doesn't exist, or the repo is private and your token lacks access
- **Network errors**: Ensure the network rule allows `api.github.com:443` and the external access integration is enabled
- **External access not supported**: External Access Integrations are not available on Snowflake trial accounts — use a paid account
- **Rate limits**: GitHub allows 5,000 API requests/hour for authenticated users

## Security Notes

- The GitHub PAT is stored securely using Snowflake's secret management — never in plain text
- External network access is restricted exclusively to `api.github.com` via the network rule
- This tool is **read-only** — it cannot create, modify, or delete any GitHub resources
- All API communication uses HTTPS (port 443)
- PATs are never exposed in query results or logs

## Technical Details

- Uses Snowflake's External Access Integration for secure outbound API calls
- Implements a Python stored procedure using Snowpark
- Uses the GitHub REST API v2022-11-28
- Returns plain text output optimised for LLM agent consumption
- Large files automatically truncated at 3,000 characters
- Results capped at 10 items per request
