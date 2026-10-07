import asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


server_params = StdioServerParameters(
    command="python",
    args=["-m", "app.mcp_server"],
)


async def discover_tools():

    async with stdio_client(server_params) as (read, write):

        async with ClientSession(read, write) as session:

            await session.initialize()

            result = await session.list_tools()

            return result.tools


async def call_tool(tool_name, arguments):

    async with stdio_client(server_params) as (read, write):

        async with ClientSession(read, write) as session:

            await session.initialize()

            result = await session.call_tool(
                tool_name,
                arguments
            )

            return result


if __name__ == "__main__":

    result = asyncio.run(
        call_tool(
            "check_employee_documents",
            {
                "employee_id": "EMP001"
            }
        )
    )

    print("\n========== MCP TOOL RESULT ==========")
    print(result)
    print("=====================================")