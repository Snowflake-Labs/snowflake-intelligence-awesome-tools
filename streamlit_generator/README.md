# Streamlit Generator Tool

Generate interactive Streamlit applications based on natural language prompts and deploy them directly to your Snowflake environment.

## Contributors

- [@jeffhollan](https://github.com/jeffhollan) - Tool creator

## Tool Parameters

| Field | Value |
|-------|-------|
| **Tool Description** | This generates a Streamlit app. It is used anytime the customer wants to generate a Streamlit app or create a report. |
| **Prompt** | Pass in the prompt that would be used to generate a Streamlit app. This prompt should include all necessary information to render the Streamlit app, including SQL queries that were used to generate any charts and context from the conversation. This will create a Streamlit app based only on the information in this prompt. |

‼️ You should also likely add the following to your planning instructions

"Whenever you call the generate_streamlit tool, be sure to return the URL to the user so they can click the streamlit app."

## Installation Instructions

1. **Download the notebook**: Download the `generate_streamlit_tool.ipynb` file from this folder
2. **Import into Snowflake**: 
   - Open Snowflake and create a new notebook
   - Select "Import from IPYNB File" 
   - Upload the downloaded notebook file
3. **Configure cross-region access** (optional): 
   - Uncomment the lines in the notebook to enable account cross-region enabling if you need to turn on cross-region access
4. **Run the notebook**: Execute all cells in the notebook
## What This Tool Does

This tool creates a custom tool called `generate_streamlit` that:
- Accepts a prompt from your Snowflake Intelligence agent
- Uses Snowflake Cortex Complete API to generate a Streamlit application based on the prompt
- Publishes the generated Streamlit app to your defined database and schema
- Returns the URL and metadata for the created application

## Default Configuration

The tool will use the following defaults (which you can override in the notebook):
- **Database**: Current database from your session
- **Schema**: Current schema from your session  
- **Warehouse**: Current warehouse from your session
- **Stage**: Creates a stage called `awesome_tools` for storing the generated files

## Usage

Once installed, you can use this tool in your Snowflake Intelligence agents by:
1. Adding it as a custom tool in your agent configuration
2. Providing a detailed prompt describing the Streamlit app you want to create
3. The tool will generate and deploy the app, returning the URL for access

## Requirements

- Snowflake account with Cortex Complete API access
- Appropriate permissions to create stored procedures and Streamlit apps

## Example Prompts

- "Create a sales dashboard showing monthly revenue trends with interactive filters"
- "Build a customer analytics app with charts showing customer segments and purchase patterns"
- "Generate a data quality report with visualizations for missing values and outliers"

## Troubleshooting

- Ensure you have the necessary permissions to create stored procedures and Streamlit apps
- Check that your Snowflake account has access to the Cortex Complete API
- Verify that cross-region access is enabled if you're using models that require it
- Review the generated JSON response for any error messages

## Technical Details

- Uses Snowpark Python stored procedures
- Leverages Snowflake Cortex Complete API for code generation
- Supports multiple AI models (Claude 4 Sonnet, GPT-4, etc.)
- Generates self-contained Streamlit applications
- Includes proper error handling and logging
