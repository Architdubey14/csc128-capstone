"""
CSC-128 Capstone: the tools and their schemas
Archit Dubey

Three tools. Two read only, one that changes state. No Streamlit and no groq
imports, so the tests run with no API key.
"""
from retriever import Retriever

# Personal training slots, by weekday. A booked slot is removed from this list.
TRAINING_SLOTS = {
    "Monday": ["9:00 AM", "1:00 PM", "6:00 PM"],
    "Tuesday": ["10:00 AM", "2:00 PM", "7:00 PM"],
    "Wednesday": ["9:00 AM", "12:00 PM", "6:00 PM"],
    "Thursday": ["11:00 AM", "3:00 PM", "7:00 PM"],
    "Friday": ["8:00 AM", "1:00 PM", "5:00 PM"],
    "Saturday": ["9:00 AM", "11:00 AM"],
    "Sunday": ["10:00 AM", "12:00 PM"],
}

BOOKINGS = []

# Built once at import. Fitting the vectorizer is the expensive part.
_retriever = Retriever()


def normalize_day(day):
    """Return a capitalized weekday name, or None if it is not a day we have."""
    if not isinstance(day, str):
        return None
    cleaned = day.strip().capitalize()
    if cleaned in TRAINING_SLOTS:
        return cleaned
    return None


def normalize_time(value):
    """
    Return a slot time in the same format the schedule uses, or None.

    Accepts "6pm", "6 PM", and "6:00 PM" as the same thing, because a member
    will type whichever is shortest.
    """
    if not isinstance(value, str):
        return None

    cleaned = value.strip().upper().replace(".", "")
    cleaned = cleaned.replace("A M", "AM").replace("P M", "PM")

    if cleaned.endswith("AM"):
        meridiem = "AM"
        body = cleaned[:-2].strip()
    elif cleaned.endswith("PM"):
        meridiem = "PM"
        body = cleaned[:-2].strip()
    else:
        return None

    if ":" in body:
        hour_part, minute_part = body.split(":", 1)
    else:
        hour_part, minute_part = body, "00"

    if not hour_part.isdigit() or not minute_part.isdigit():
        return None

    hour = int(hour_part)
    if hour < 1 or hour > 12:
        return None

    return str(hour) + ":" + minute_part.zfill(2) + " " + meridiem


def search_gym_info(question):
    """
    Look the question up in the gym's own documents and return what was found.

    Returns an explicit not-found string rather than an empty one, so the model
    is told nothing matched instead of being handed a blank context.
    """
    if not isinstance(question, str) or not question.strip():
        return "NOT FOUND: no question was given to look up."

    hits = _retriever.search(question)
    if not hits:
        return (
            "NOT FOUND: nothing in the GYMARC documents covers that. "
            "Tell the member you do not have that information."
        )
    return _retriever.build_context(hits)


def check_training_slots(day):
    """Return which personal training times are open on a weekday."""
    name = normalize_day(day)
    if name is None:
        return (
            "I do not have a training schedule for '" + str(day) + "'. "
            "Give me a day of the week."
        )

    open_slots = TRAINING_SLOTS[name]
    if not open_slots:
        return "No training slots are open on " + name + "."
    return "Open training slots on " + name + ": " + ", ".join(open_slots) + "."


def book_training_session(day, time, name):
    """
    Reserve a personal training slot and remove it from the schedule.

    This function can only add a booking. It cannot cancel one, move one, or
    look up who booked a slot. There is deliberately no function that can.
    """
    weekday = normalize_day(day)
    if weekday is None:
        return (
            "I cannot book '" + str(day) + "'. Give me a day of the week."
        )

    slot = normalize_time(time)
    if slot is None:
        return (
            "I did not understand the time '" + str(time) + "'. "
            "Give it to me like 6:00 PM."
        )

    if slot not in TRAINING_SLOTS[weekday]:
        open_slots = TRAINING_SLOTS[weekday]
        if not open_slots:
            return "Nothing is open on " + weekday + " any more."
        return (
            slot + " is not open on " + weekday + ". "
            "These are: " + ", ".join(open_slots) + "."
        )

    member = str(name).strip()
    if not member:
        return "I need a name to put the session under."

    TRAINING_SLOTS[weekday].remove(slot)
    BOOKINGS.append({"day": weekday, "time": slot, "name": member})
    return (
        "Booked a personal training session on " + weekday + " at " + slot
        + " for " + member + "."
    )


AVAILABLE_TOOLS = {
    "search_gym_info": search_gym_info,
    "check_training_slots": check_training_slots,
    "book_training_session": book_training_session,
}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_gym_info",
            "description": (
                "Call this for any question about how the gym works: hours, "
                "membership prices, joining, cancelling, freezing an account, "
                "classes, guests, the pool or sauna, parking, or equipment. Pass "
                "the member's question through more or less as they asked it. You "
                "have no knowledge of GYMARC on your own, so call this before "
                "answering anything factual, and never answer from memory. Do not "
                "call it for training slot availability, which is a different tool."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The member's question, in their own words.",
                    }
                },
                "required": ["question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_training_slots",
            "description": (
                "Call this when the member asks what personal training times are "
                "open on a day, or whether a particular time is free. Call it "
                "before booking, so you know the slot actually exists. Do not call "
                "it for the gym's opening hours, which is a question for "
                "search_gym_info."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "day": {
                        "type": "string",
                        "description": "A day of the week, Monday through Sunday.",
                    }
                },
                "required": ["day"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "book_training_session",
            "description": (
                "Call this to reserve a personal training slot, as soon as you have "
                "all three of the day, the time, and the name to book under. Do not "
                "ask the member to confirm first, because the system shows them a "
                "confirmation button and nothing is booked until they press it. If "
                "any of the three details is missing, ask the member for it instead "
                "of guessing, and never invent a name."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "day": {
                        "type": "string",
                        "description": "A day of the week, Monday through Sunday.",
                    },
                    "time": {
                        "type": "string",
                        "description": "A slot time, for example 6:00 PM.",
                    },
                    "name": {
                        "type": "string",
                        "description": "The name to book under, given by the member.",
                    },
                },
                "required": ["day", "time", "name"],
            },
        },
    },
]
