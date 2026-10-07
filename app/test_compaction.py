from app.compaction import compact_messages


messages = []

for i in range(12):
    messages.append({
        "role": "assistant",
        "type": "test_message",
        "content": f"Test message number {i + 1}"
    })


print("\n========== BEFORE COMPACTION ==========")
print("Message count:", len(messages))

for message in messages:
    print(message)


compacted_messages = compact_messages(
    messages
)


print("\n========== AFTER COMPACTION ==========")
print("Message count:", len(compacted_messages))

for message in compacted_messages:
    print(message)


print("\n========== VERIFICATION ==========")

if len(compacted_messages) == 5:
    print("PASS: 12 messages became 5 messages.")
else:
    print(
        "FAIL: Expected 5 messages but got",
        len(compacted_messages)
    )


if compacted_messages[0]["type"] == "conversation_summary":
    print("PASS: Summary message was created.")
else:
    print("FAIL: Summary message was not created.")


remaining_test_messages = [
    message
    for message in compacted_messages
    if message.get("type") == "test_message"
]

if len(remaining_test_messages) == 4:
    print(
        "PASS: 4 original messages were preserved."
    )
else:
    print(
        "FAIL: Expected 4 remaining messages but got",
        len(remaining_test_messages)
    )

print("====================================")