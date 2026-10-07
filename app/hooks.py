def pre_tool_hook(tool_name, arguments):
    """
    Runs before an MCP tool is executed.
    """

    print("\n[PRE-HOOK]")
    print("Tool:", tool_name)
    print("Arguments:", arguments)

    # Simulate a validation error
    if tool_name == "github_access":
        if arguments.get("employee_id") != "EMP001":
            return {
                "ok": False,
                "status_code": 400,
                "error": "Invalid employee ID for GitHub access request."
            }

    return {
        "ok": True
    }


def post_tool_hook(tool_name, result):
    """
    Runs after an MCP tool is executed.
    """

    print("\n[POST-HOOK]")
    print("Tool:", tool_name)
    print("Result:", result)

    return {
        "ok": True
    }

async def execute_with_hooks(tool_name, arguments, call_mcp_tool):

    # 1. PRE-HOOK
    pre_result = pre_tool_hook(tool_name, arguments)

    if not pre_result["ok"]:
        return {
            "success": False,
            "error": pre_result,
            "tool_executed": False
        }

    # 2. EXECUTE MCP TOOL
    tool_result = await call_mcp_tool(
        tool_name,
        arguments
    )

    # 3. POST-HOOK
    post_result = post_tool_hook(
        tool_name,
        tool_result
    )

    if not post_result["ok"]:
        return {
            "success": False,
            "error": post_result,
            "tool_executed": True
        }

    return {
        "success": True,
        "result": tool_result,
        "tool_executed": True
    }