# Brave Web Search Tool

Access real-time web search results from your Snowflake Intelligence agents using the Brave Search API.

## Contributors

- [@jeffhollan](https://github.com/jeffhollan) - Tool creator

## Tool Parameters

| Field | Value |
|-------|-------|
| **Tool Description** | This tool calls Brave Web Search APIs and returns the results. Useful if you need to pull information that is current from the public web. |
| **arg1** | The search query |

## Installation Instructions

1. **Download the notebook**: Download the `Brave API Custom Tools.ipynb` file from this folder
2. **Import into Snowflake**: 
   - Open Snowflake and create a new notebook
   - Select "Import from IPYNB File" 
   - Upload the downloaded notebook file
3. **Configure your Brave API key**: 
   - Sign up for a Brave Search API key at [Brave Search API](https://brave.com/search/api/)
   - Replace `<your-brave-api-key>` in the notebook with your actual API key
4. **Run the notebook**: Execute all cells in the notebook one at a time

## Prerequisites

- **Brave Search API key**: Sign up at [Brave Search API](https://brave.com/search/api/) to obtain your API key
- **Network access**: Your Snowflake account must allow external network access
- **Permissions**: Ability to create network rules, secrets, external access integrations, and stored procedures

## What This Tool Does

This tool creates a stored procedure called `brave_search_sproc` that:
- Accepts a search query as a parameter
- Calls the Brave Search API to retrieve current web search results
- Returns structured JSON data with search results
- Can be integrated into your Snowflake Intelligence agents for real-time web information

## Setup Steps

The notebook will automatically:
1. Create a network rule allowing access to `api.search.brave.com`
2. Store your Brave API key securely as a Snowflake secret
3. Create an external access integration for secure API communication
4. Create a custom stage for storing the stored procedure code
5. Deploy the `brave_search_sproc` stored procedure
6. Test the integration with a sample search query

## Usage

Once installed, you can use this tool in your Snowflake Intelligence agents by:
1. Adding it as a custom tool in your agent configuration
2. The agent will automatically call the tool when it needs current web information
3. The tool will return relevant search results from Brave Search

## Example Usage

```sql
-- Test the tool directly
CALL brave_search_sproc('What is Snowflake Intelligence?');

-- Search for current events
CALL brave_search_sproc('latest AI developments 2025');

-- Search for technical information
CALL brave_search_sproc('Python best practices for data engineering');
```

## Response Format

The tool returns a JSON object containing:
- Search results with titles, descriptions, and URLs
- Metadata about the search query
- Relevant snippets from web pages
- Additional context from the Brave Search API

## Permissions

After installation, you may need to grant usage permissions to other roles:

```sql
-- Grant usage to a specific role
GRANT USAGE ON PROCEDURE brave_search_sproc(VARCHAR) TO ROLE <user_role>;

-- Grant usage on the external access integration
GRANT USAGE ON INTEGRATION brave_access_integration TO ROLE <user_role>;

-- Grant usage on the custom stage
GRANT USAGE ON STAGE custom_tools TO ROLE <user_role>;
```

## Troubleshooting

- **API key errors**: Verify your Brave API key is valid and properly entered in the secret
- **Network errors**: Ensure the network rule allows access to `api.search.brave.com:443`
- **Permission errors**: Verify you have the necessary roles to create integrations and procedures
- **Rate limits**: Be aware of your Brave Search API rate limits and plan accordingly
- **No results**: Check that the search query is properly formatted and not empty

## Security Notes

- API keys are stored securely using Snowflake's secret management system
- All API communication uses HTTPS (port 443)
- External access is limited to only the Brave Search API endpoint
- API keys are never exposed in logs or query results
- All network traffic is controlled through the external access integration

## Technical Details

- Uses Snowflake's External Access Integration for secure API calls
- Implements a Python stored procedure using Snowpark
- Leverages the `requests` library for HTTP communication
- Returns structured JSON responses for easy parsing
- Compatible with Snowflake Intelligence agent framework

## Use Cases

- **Current Events**: Get up-to-date information about recent news and events
- **Market Research**: Search for current market trends and competitor information
- **Technical Documentation**: Find the latest technical guides and best practices
- **Data Enrichment**: Augment your data with current web information
- **Fact Checking**: Verify information against current web sources

## API Cost Considerations

- Brave Search API has usage limits based on your subscription tier
- Monitor your API usage to avoid unexpected costs
- Consider implementing rate limiting in production use cases
- Review Brave's pricing at [Brave Search API Pricing](https://brave.com/search/api/)
