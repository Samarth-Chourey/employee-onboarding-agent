import json


def create_tool_request(
    request_id,
    tool_name,
    arguments
):
    """
    Create a JSON-RPC 2.0 tool request.
    """

    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }


def create_tool_response(
    request_id,
    result
):
    """
    Create a JSON-RPC 2.0 success response.
    """

    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": result
    }


def create_error_response(
    request_id,
    code,
    message
):
    """
    Create a JSON-RPC 2.0 error response.
    """

    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {
            "code": code,
            "message": message
        }
    }


def validate_jsonrpc_request(request):
    """
    Validate a JSON-RPC 2.0 tool request.
    """

    if not isinstance(request, dict):
        return False, "Request must be a JSON object."

    if request.get("jsonrpc") != "2.0":
        return False, "Invalid or missing jsonrpc version."

    if "id" not in request:
        return False, "Missing request id."

    if request.get("method") != "tools/call":
        return False, "Unsupported method."

    params = request.get("params")

    if not isinstance(params, dict):
        return False, "Missing params object."

    if "name" not in params:
        return False, "Missing tool name."

    if "arguments" not in params:
        return False, "Missing tool arguments."

    return True, ""


def parse_jsonrpc_response(response_text):
    """
    Parse Gemini's JSON response into a JSON-RPC request.
    """

    if isinstance(response_text, list):
        response_text = response_text[0]["text"]

    response_text = response_text.strip()

    # Remove markdown code fences if Gemini adds them
    if response_text.startswith("```"):
        lines = response_text.splitlines()

        if lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        response_text = "\n".join(lines)

    request = json.loads(response_text)

    valid, error = validate_jsonrpc_request(request)

    if not valid:
        raise ValueError(
            f"Invalid JSON-RPC request: {error}"
        )

    return request
