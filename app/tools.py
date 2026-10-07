def get_employee(employee_id):
    employees = {
        "EMP001": {
            "name": "Rahul Sharma",
            "role": "Software Engineer",
            "department": "Engineering"
        },
        "EMP002": {
            "name": "Priya Singh",
            "role": "QA Engineer",
            "department": "Engineering"
        },
        "EMP003": {
            "name": "Arjun Mehta",
            "role": "Data Analyst",
            "department": "Analytics"
        }
    }

    return employees.get(employee_id, "Employee not found")


def check_documents(employee_id):
    return {
        "employee_id": employee_id,
        "documents_verified": True,
        "status": "Documents verified successfully"
    }


def create_onboarding_task(employee_id, task_name):
    return {
        "employee_id": employee_id,
        "task": task_name,
        "status": "Task created successfully"
    }


def request_github_access(employee_id):
    return {
        "employee_id": employee_id,
        "system": "GitHub",
        "status": "Access request created"
    }


def request_aws_access(employee_id):
    return {
        "employee_id": employee_id,
        "system": "AWS",
        "status": "Access granted successfully"
    }


def send_welcome_email(employee_id):
    return {
        "employee_id": employee_id,
        "status": "Welcome email sent successfully"
    }


# Controlled failure tool used for testing error recovery
def simulate_tool_failure(employee_id):
    return {
        "success": False,
        "error": "Simulated tool failure: downstream onboarding service unavailable.",
        "status_code": 500
    }


TOOL_SCHEMAS = {

    "get_employee": {
        "name": "get_employee",
        "description": "Get employee details using employee ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "employee_id": {
                    "type": "string",
                    "description": "Unique employee ID"
                }
            },
            "required": ["employee_id"]
        }
    },

    "check_documents": {
        "name": "check_documents",
        "description": "Verify the required employee documents.",
        "parameters": {
            "type": "object",
            "properties": {
                "employee_id": {
                    "type": "string",
                    "description": "Unique employee ID"
                }
            },
            "required": ["employee_id"]
        }
    },

    "create_onboarding_task": {
        "name": "create_onboarding_task",
        "description": "Create an onboarding task for an employee.",
        "parameters": {
            "type": "object",
            "properties": {
                "employee_id": {
                    "type": "string"
                },
                "task_name": {
                    "type": "string"
                }
            },
            "required": ["employee_id", "task_name"]
        }
    },

    "request_github_access": {
        "name": "request_github_access",
        "description": "Request GitHub access for an employee.",
        "parameters": {
            "type": "object",
            "properties": {
                "employee_id": {
                    "type": "string"
                }
            },
            "required": ["employee_id"]
        }
    },

    "request_aws_access": {
        "name": "request_aws_access",
        "description": "Request AWS access for an employee. Requires human approval.",
        "parameters": {
            "type": "object",
            "properties": {
                "employee_id": {
                    "type": "string"
                }
            },
            "required": ["employee_id"]
        }
    },

    "send_welcome_email": {
        "name": "send_welcome_email",
        "description": "Send a welcome email to an employee.",
        "parameters": {
            "type": "object",
            "properties": {
                "employee_id": {
                    "type": "string"
                }
            },
            "required": ["employee_id"]
        }
    },

    # New tool for Task 9A error-recovery evaluation
    "simulate_tool_failure": {
        "name": "simulate_tool_failure",
        "description": "Simulate a downstream service failure for testing error recovery.",
        "parameters": {
            "type": "object",
            "properties": {
                "employee_id": {
                    "type": "string",
                    "description": "Unique employee ID"
                }
            },
            "required": ["employee_id"]
        }
    }
}


def execute_tool(tool_name, arguments):

    if tool_name == "get_employee":
        return get_employee(arguments["employee_id"])

    elif tool_name == "check_documents":
        return check_documents(arguments["employee_id"])

    elif tool_name == "create_onboarding_task":
        return create_onboarding_task(
            arguments["employee_id"],
            arguments["task_name"]
        )

    elif tool_name == "request_github_access":
        return request_github_access(arguments["employee_id"])

    elif tool_name == "request_aws_access":
        return request_aws_access(arguments["employee_id"])

    elif tool_name == "send_welcome_email":
        return send_welcome_email(arguments["employee_id"])

    elif tool_name == "simulate_tool_failure":
        return simulate_tool_failure(arguments["employee_id"])

    else:
        return {
            "error": f"Unknown tool: {tool_name}"
        }