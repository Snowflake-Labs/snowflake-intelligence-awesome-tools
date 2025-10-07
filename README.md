# Snowflake Intelligence Awesome Tools

A collection of open source samples and tools that you can use to enhance your Snowflake Intelligence agents or Cortex agents. Each folder in this repository represents a custom tool that can be integrated into your Snowflake Intelligence setup.

## Repository Structure

Each tool in this repository follows a consistent structure:
- **README.md**: Instructions for getting up and running with the specific tool
- **Implementation files**: Notebooks, SQL scripts, or other artifacts needed to deploy the tool

## Getting Started

1. **Choose a tool** that fits your needs from the available tools above
2. **Navigate to the tool's folder** and read its README.md
3. **Follow the installation instructions** specific to that tool
4. **Configure the tool** in your Snowflake Intelligence agent

## Contributing a Tool

We welcome contributions! If you'd like to add a custom tool to this repository:

1. **Fork this repository**
2. **Create a new folder** for your tool (use a descriptive name)
3. **Add a comprehensive README.md** that includes:
   - Tool description and use cases
   - Installation instructions
   - Tool parameter table (see format below)
   - Usage examples
4. **Include implementation artifacts** such as:
   - Snowflake notebooks (preferred for easy import)
   - SQL scripts that can be pasted into worksheets
   - Other necessary files for deployment
5. **Open a pull request** - we'll review on a best-effort basis

### Required README Format

Each tool's README must include a tool parameter table at the top with the following format:

| Field | Value |
|-------|-------|
| **Tool Description** | Brief description of what the tool does and when to use it |
| **Parameter 1** | Description of the first parameter, including format requirements |
| **Parameter 2** | Description of the second parameter, including format requirements |
| **Parameter N** | Description of additional parameters as needed |

**Example:**
| Field | Value |
|-------|-------|
| **Tool Description** | Use this tool anytime you need to send an email |
| **Recipients** | The email recipients you want to send to (comma-separated). Always ask the user for this value. |
| **Subject** | The subject of the email. Automatically infer the subject of the email. |
| **Body** | The body content of the email |

## Important Disclaimers

⚠️ **Community-Driven**: This repository is community-driven and open source. These tools are not official Snowflake features.

⚠️ **No Guarantees**: We make no guarantees about the tools themselves. You are responsible for any code you run in your Snowflake account.

⚠️ **Not Supported**: This repository is part of Snowflake Labs, which means it is not supported by Snowflake support.

⚠️ **Use at Your Own Risk**: Please review all code before deploying to your Snowflake environment.

## License

This project is open source. Please review individual tool implementations for any specific licensing requirements.

## Getting Help

- For Snowflake Intelligence questions: [Snowflake Documentation](https://docs.snowflake.com/)
- For tool-specific issues: Open an issue in this repository
- For general Snowflake questions: [Snowflake Community](https://community.snowflake.com/)

---

**Happy building!** 🚀
