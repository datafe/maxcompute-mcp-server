# MaxCompute MCP Server

## Overview
A Model Context Protocol (MCP) server for MaxCompute.

## Components

### Tools
The server offers 4 core tools:

#### Query Tools
- `get_latest_partition`
  - Get the latest partition name for a specific table
  - Input:
    - `table_name` (string): Name of the table
  - Returns: The latest partition name

- `read_query`
   - Execute a SELECT query on the MaxCompute project, only SELECT query is allowed
   - Input:
     - `query` (string): The SELECT SQL query
   - Returns: Query results as array of objects

#### Schema Tools
- `list_tables`
   - List all tables in the MaxCompute project
   - No input required
   - Returns: Array of table objects with name and comment

- `describe_table`
   - Get the schema information for a specific table
   - Input:
     - `table_name` (string): Name of the table
   - Returns: Raw output of DESC command

## Usage with Cline

```bash
# Install maxcompute-mcp-server
cd /path/to/maxcompute-mcp-server
uv pip install .
```

```bash
# Add the server to your cline_mcp_settings.json
"mcpServers": {
  "maxcompute-mcp-server": {
    "command": "uv",
    "args": [
      "run",
      "maxcompute-mcp-server"
    ],
    "env": {
      "ALIBABA_CLOUD_ACCESS_KEY_ID": "",
      "ALIBABA_CLOUD_ACCESS_KEY_SECRET": "",
      "ALIBABA_CLOUD_MAXCOMPUTE_PROJECT": "",
      "ALIBABA_CLOUD_MAXCOMPUTE_ENDPOINT": "http://service.cn.maxcompute.aliyun.com/api"
    }
  }
}
```
