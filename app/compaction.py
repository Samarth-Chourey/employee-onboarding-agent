from dotenv import load_dotenv

load_dotenv()

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI


llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash",
    temperature=0,
    timeout=30,
)


def compact_messages(messages):

    if len(messages) <= 10:
        return messages

    print("\n[COMPACTION]")
    print("Message limit exceeded.")
    print("Summarizing first 8 messages...")

    first_eight = messages[:8]
    remaining_messages = messages[8:]

    conversation_text = ""

    for message in first_eight:
        conversation_text += (
            f"{message}\n"
        )

    prompt = f"""
Summarize the following agent conversation
into ONE concise paragraph.

Preserve:
- important employee information
- tool requests
- tool results
- errors
- approvals
- important decisions
- workflow progress

Do not invent information.

Conversation:

{conversation_text}
"""

    response = llm.invoke(
        [HumanMessage(content=prompt)]
    )

    summary = response.content

    if isinstance(summary, list):
        summary = summary[0]["text"]

    summary = summary.strip()

    summary_message = {
        "role": "system",
        "type": "conversation_summary",
        "content": summary
    }

    compacted_messages = [
        summary_message
    ] + remaining_messages

    print(
        "[COMPACTION] Original messages:",
        len(messages)
    )

    print(
        "[COMPACTION] New messages:",
        len(compacted_messages)
    )

    print(
        "[COMPACTION] Summary created:"
    )

    print(summary)

    return compacted_messages