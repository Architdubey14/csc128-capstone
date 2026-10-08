"""
CSC-128 Capstone: the tool calling loop and the dispatch guard
Archit Dubey

dispatch() imports nothing from Streamlit or groq, so the tests can exercise
the guard with no API key.
"""
import json

from tools import AVAILABLE_TOOLS, TOOL_SCHEMAS

MODEL = "openai/gpt-oss-20b"
MAX_ROUNDS = 5

# Tools that change state. These never run from a model request alone.
WRITE_TOOLS = {"book_training_session"}

SYSTEM_PROMPT = """You are the GYMARC front desk assistant.

You know nothing about GYMARC on your own. Everything you say about the gym has to come from a tool result in this conversation.

Your tools:
- search_gym_info for anything about how the gym works: hours, prices, joining, cancelling, freezing, classes, guests, facilities, equipment.
- check_training_slots for which personal training times are open on a day.
- book_training_session to reserve a training slot.

Rules:
- Never state a price, a time, a policy, or an open slot unless a tool told you in this conversation. If you did not call a tool, you do not know.
- If a tool result starts with "NOT FOUND", say plainly that you do not have that information and name what you can help with. Do not fill the gap yourself.
- To book, you need the day, the time, and the name. If any is missing, ask for it. Never invent a name.
- Once you have all three, call book_training_session straight away. Do not ask the member to confirm in chat, because the system shows them a confirmation button.
- If a tool result starts with "Not done yet", the booking is waiting on that button. Say the details are ready and point them to it. Do not say it is booked.
- You cannot cancel, move, or look up an existing booking or membership. There is no tool for it. Say so plainly and send them to the front desk at support@gym.com.
- If a tool returns an error, tell the member what it said. Do not retry the same call with the same arguments.

Keep answers short and plain. Do not use tables, bullet points, bold, or backticks. Write in ordinary sentences."""


def dispatch(name, raw_arguments, allow_write=False):
    """
    Run one tool call and return a string for the model.

    Validates the tool name against the allow list BEFORE any lookup happens,
    so a name the model invented never reaches a function. A tool that changes
    state runs only when allow_write is True, which the interface sets after
    the member presses confirm. The model cannot set it by asking.
    """
    # The name came from the model, so it is untrusted. Check membership first.
    if name not in AVAILABLE_TOOLS:
        return (
            "Error: there is no tool called '" + str(name) + "'. "
            "The available tools are: " + ", ".join(sorted(AVAILABLE_TOOLS)) + "."
        )

    try:
        arguments = json.loads(raw_arguments)
    except (json.JSONDecodeError, TypeError):
        return "Error: the arguments for " + name + " were not valid JSON. Send them again."

    if not isinstance(arguments, dict):
        return "Error: the arguments for " + name + " must be a JSON object."

    # A prompt rule asking the model to confirm is a request it can ignore.
    # This is the same check in code, where it cannot be talked around.
    if name in WRITE_TOOLS and not allow_write:
        return (
            "Not done yet: " + name + " changes the schedule, so it needs the member "
            "to press the confirm button. Read these details back and wait: "
            + json.dumps(arguments)
        )

    function = AVAILABLE_TOOLS[name]

    try:
        return function(**arguments)
    except TypeError as error:
        return (
            "Error: " + name + " was called with the wrong arguments (" + str(error) + "). "
            "Check the required fields in the tool schema and try again."
        )
    except Exception as error:
        return "Error: " + name + " failed with " + type(error).__name__ + ": " + str(error) + "."


def pending_write(log):
    """
    Return the arguments of a write tool that was blocked, or None.

    The interface uses this to show a confirm button for exactly the call the
    model made, rather than trusting the model to describe it.
    """
    for entry in reversed(log):
        if entry["name"] in WRITE_TOOLS and entry["result"].startswith("Not done yet:"):
            try:
                return json.loads(entry["arguments"])
            except (json.JSONDecodeError, TypeError):
                return None
    return None


def run_agent(client, messages, log, allow_write=False):
    """
    Run the tool calling loop until the model answers or the cap is hit.

    messages is the running conversation, which is how the bot remembers
    earlier turns. log collects a record of every tool call for the interface.
    allow_write is passed to dispatch and is only True right after the member
    pressed confirm.
    """
    rounds = 0

    while rounds < MAX_ROUNDS:
        rounds += 1

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
        )
        reply = response.choices[0].message

        # No tool calls means the model is answering, so the loop is done.
        if not reply.tool_calls:
            return reply.content or "", messages

        messages.append(
            {
                "role": "assistant",
                "content": reply.content or "",
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments,
                        },
                    }
                    for call in reply.tool_calls
                ],
            }
        )

        for call in reply.tool_calls:
            name = call.function.name
            raw_arguments = call.function.arguments
            result = dispatch(name, raw_arguments, allow_write)

            log.append({"name": name, "arguments": raw_arguments, "result": result})

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "name": name,
                    "content": result,
                }
            )

    return (
        "I tried a few times and could not finish that. "
        "Try asking for one thing at a time.",
        messages,
    )
