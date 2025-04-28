import logging
import os
from typing import Any

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from odps import ODPS

logger = logging.getLogger('maxcompute-mcp-server')
# logger.setLevel(logging.DEBUG)
# logger.addHandler(logging.FileHandler('/Users/xxx/maxcompute-mcp-server.log'))

logger.info("Starting MaxCompute MCP Server")


class MaxCompute:
    def __init__(self):
        self.project = ODPS(
            os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID'),
            os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET'),
            os.getenv("ALIBABA_CLOUD_MAXCOMPUTE_PROJECT"),
            os.getenv("ALIBABA_CLOUD_MAXCOMPUTE_ENDPOINT")
        )

    def _list_tables(self) -> list[str]:
        return [table.name for table in self.project.list_tables()]

    def _execute_query(self, query: str) -> list[dict[str, Any]]:
        """Execute a SQL query and return results as a list of dictionaries"""
        logger.debug(f"Executing query: {query}")
        try:
            with self.project.execute_sql(query).open_reader() as reader:
                if query.strip().upper().startswith('DESC'):
                    return [{'data': reader.raw}]

                results = [dict(row) for row in reader]
                logger.debug(f"Read query returned {len(results)} rows")
                return results
        except Exception as e:
            logger.error(f"Database error executing query: {e}")
            raise


async def main():
    maxcompute = MaxCompute()
    server = Server("maxcompute-mcp-server")

    # Register handlers
    logger.debug("Registering handlers")

    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        logger.debug("Handling list_tools request")
        return [
            types.Tool(
                name="list_tables",
                description="List all tables in the MaxCompute project",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            types.Tool(
                name="describe_table",
                description="Get the schema information for a specific table",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "table_name": {"type": "string", "description": "Name of the table"},
                    },
                    "required": ["table_name"],
                },
            ),
            types.Tool(
                name="get_latest_partition",
                description="Get the latest partition name for a specific table",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "table_name": {"type": "string", "description": "Name of the table"},
                    },
                    "required": ["table_name"],
                },
            ),
            types.Tool(
                name="read_query",
                description="Execute a SELECT query on the MaxCompute project, only SELECT query is allowed",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The SELECT SQL query"},
                    },
                    "required": ["query"],
                },
            ),
        ]

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict[str, Any] | None) -> list[types.TextContent]:
        logger.debug(f"Handling call_tool request for {name} with args {arguments}")
        try:
            if name == "list_tables":
                results = maxcompute._execute_query("SELECT table_name, table_comment FROM information_schema.tables")
                return [types.TextContent(type="text", text=str(results))]

            elif name == "describe_table":
                if not arguments or "table_name" not in arguments:
                    raise ValueError("Missing table_name argument")
                results = maxcompute._execute_query(f"DESC {arguments['table_name']}")
                return [types.TextContent(type="text", text=str(results[0]['data']))]

            elif name == 'get_latest_partition':
                if not arguments or "table_name" not in arguments:
                    raise ValueError("Missing table_name argument")
                results = maxcompute._execute_query(
                    f"SELECT partition_name FROM information_schema.partitions WHERE table_name='{arguments['table_name']}' ORDER BY create_time DESC LIMIT 1")
                return [types.TextContent(type="text", text=str(results[0]['partition_name']))]

            if not arguments:
                raise ValueError("Missing arguments")

            if name == "read_query":
                if not arguments["query"].strip().upper().startswith("SELECT"):
                    raise ValueError("Only SELECT queries are allowed for read_query")
                results = maxcompute._execute_query(arguments["query"])
                return [types.TextContent(type="text", text=str(results))]

            else:
                raise ValueError(f"Unknown tool: {name}")

        except Exception as e:
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        logger.info("Server running with stdio transport")
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="maxcompute-mcp-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )
