from mcp.server import MCPServer

from app.tools import (
    check_documents,
    create_onboarding_task,
    request_github_access,
    request_aws_access,
    send_welcome_email,
    simulate_tool_failure
)


mcp = MCPServer("Employee Onboarding Server")


@mcp.tool()
def check_employee_documents(employee_id: str) -> dict:
    """Verify employee documents."""
    return check_documents(employee_id)


@mcp.tool()
def create_task(employee_id: str, task_name: str) -> dict:
    """Create an onboarding task."""
    return create_onboarding_task(employee_id, task_name)


@mcp.tool()
def github_access(employee_id: str) -> dict:
    """Request GitHub access."""
    return request_github_access(employee_id)


@mcp.tool()
def aws_access(employee_id: str) -> dict:
    """Request AWS access. Human approval is required."""
    return request_aws_access(employee_id)


@mcp.tool()
def welcome_email(employee_id: str) -> dict:
    """Send a welcome email."""
    return send_welcome_email(employee_id)


@mcp.tool()
def simulated_failure(employee_id: str) -> dict:
    """Simulate a downstream service failure for testing error recovery."""
    return simulate_tool_failure(employee_id)


if __name__ == "__main__":
    mcp.run(transport="stdio")