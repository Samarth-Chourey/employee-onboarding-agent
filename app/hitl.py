def request_human_approval(employee_id, tool_name):
    print("\n========== HUMAN APPROVAL REQUIRED ==========")
    print(f"Employee ID: {employee_id}")
    print(f"Requested Tool: {tool_name}")
    print("This is a sensitive operation.")

    while True:
        choice = input("Approve or Reject? (approve/reject): ").strip().lower()

        if choice == "approve":
            return {
                "approved": True,
                "status": "Approved by human"
            }

        elif choice == "reject":
            return {
                "approved": False,
                "status": "Rejected by human"
            }

        else:
            print("Please enter only 'approve' or 'reject'.")


if __name__ == "__main__":

    result = request_human_approval(
        "EMP001",
        "aws_access"
    )

    print("\n========== APPROVAL RESULT ==========")
    print(result)