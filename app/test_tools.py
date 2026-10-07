from app.tools import execute_tool


tool_request = {
    "tool": "check_documents",
    "arguments": {
        "employee_id": "EMP001"
    }
}


result = execute_tool(
    tool_request["tool"],
    tool_request["arguments"]
)


print("Tool Request:")
print(tool_request)

print("\nTool Result:")
print(result)