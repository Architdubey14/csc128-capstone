"""
CSC-128 Capstone: tests for retrieval, the tools, and the dispatch guard
Archit Dubey

Run:  python test_capstone.py

No API key is needed. Retrieval, the tool functions, and the dispatch guard
are deterministic Python, which is the part of an agent you can unit test.
"""
from agent import dispatch
from retriever import DEFAULT_THRESHOLD, Retriever, stem
import tools
from tools import (
    book_training_session,
    check_training_slots,
    normalize_day,
    normalize_time,
    search_gym_info,
)

# Questions a member would really ask, with the document that should come back.
SHOULD_RETRIEVE = [
    ("what time do you open on saturday", "hours"),
    ("how much is a membership", "membership_price"),
    ("what are the costs", "membership_price"),
    ("what are your prices", "membership_price"),
    ("is there a student discount", "membership_price"),
    ("i want to cancel my membership", "cancel"),
    ("i want a break from the gym for a couple months", "freeze"),
    ("do you have yoga classes", "classes"),
    ("how much does a trainer cost", "personal_training"),
    ("can i bring a friend with me", "guests"),
    ("do you have a sauna", "facilities"),
    ("do i need to bring my own towel", "facilities"),
    ("do you have squat racks", "equipment"),
    ("how do i sign up", "joining"),
    ("is parking free", "facilities"),
]

# Close to a gym, but covered by no document. These must retrieve nothing.
SHOULD_REFUSE = [
    "do you sell protein powder",
    "are you hiring right now",
    "can i get a massage here",
    "is there a basketball court",
    "do you have a tanning bed",
]


def fresh_state():
    """Reset module state so each group of tests starts from the same place."""
    tools.TRAINING_SLOTS["Monday"] = ["9:00 AM", "1:00 PM", "6:00 PM"]
    tools.TRAINING_SLOTS["Tuesday"] = ["10:00 AM", "2:00 PM", "7:00 PM"]
    tools.TRAINING_SLOTS["Wednesday"] = ["9:00 AM", "12:00 PM", "6:00 PM"]
    tools.TRAINING_SLOTS["Thursday"] = ["11:00 AM", "3:00 PM", "7:00 PM"]
    tools.TRAINING_SLOTS["Friday"] = ["8:00 AM", "1:00 PM", "5:00 PM"]
    tools.TRAINING_SLOTS["Saturday"] = ["9:00 AM", "11:00 AM"]
    tools.TRAINING_SLOTS["Sunday"] = ["10:00 AM", "12:00 PM"]
    tools.BOOKINGS.clear()


def retrieval_cases(retriever):
    """Retrieval tests, plus the scores the threshold was chosen from."""
    cases = []
    retrieve_scores = []
    refuse_scores = []

    for question, expected_id in SHOULD_RETRIEVE:
        retrieve_scores.append(retriever.best_score(question))
        hits = retriever.search(question)
        actual_id = hits[0][0]["id"] if hits else None
        cases.append(("retrieval: " + question, actual_id, expected_id))

    for question in SHOULD_REFUSE:
        refuse_scores.append(retriever.best_score(question))
        cases.append(("refusal: " + question, retriever.search(question), []))

    return cases, retrieve_scores, refuse_scores


def build_cases():
    cases = []
    retriever = Retriever()
    fresh_state()

    retrieval, retrieve_scores, refuse_scores = retrieval_cases(retriever)
    cases.extend(retrieval)

    # --- the stemmer ---
    # A plural and its singular have to land on the same token, or a question
    # phrased one way cannot find a document phrased the other way.
    cases.append(("prices and price agree", stem("prices"), stem("price")))
    cases.append(("classes and class agree", stem("classes"), stem("class")))
    cases.append(("costs and cost agree", stem("costs"), stem("cost")))
    cases.append(("facilities and facility agree", stem("facilities"), stem("facility")))
    cases.append(("trainer and training agree", stem("trainer"), stem("training")))
    cases.append(("a double s is not a plural", stem("class"), "class"))

    # --- normalize_day and normalize_time ---
    cases.append(("lowercase day is accepted", normalize_day("monday"), "Monday"))
    cases.append(("a day with spaces is accepted", normalize_day("  friday "), "Friday"))
    cases.append(("nonsense is rejected", normalize_day("blursday"), None))
    cases.append(("a number does not crash normalize_day", normalize_day(7), None))
    cases.append(("6pm becomes a slot time", normalize_time("6pm"), "6:00 PM"))
    cases.append(("6 PM becomes a slot time", normalize_time("6 PM"), "6:00 PM"))
    cases.append(("9:00 am is already a slot time", normalize_time("9:00 am"), "9:00 AM"))
    cases.append(("a bare number is rejected", normalize_time("6"), None))
    cases.append(("a 13th hour is rejected", normalize_time("13:00 PM"), None))
    cases.append(("a number does not crash normalize_time", normalize_time(6), None))

    # --- search_gym_info, the grounding tool ---
    cases.append((
        "a covered question returns the document text",
        "35 dollars" in search_gym_info("how much is a membership"),
        True,
    ))
    cases.append((
        "an uncovered question says NOT FOUND",
        search_gym_info("do you sell protein powder").startswith("NOT FOUND"),
        True,
    ))
    cases.append((
        "an empty question says NOT FOUND rather than crashing",
        search_gym_info("").startswith("NOT FOUND"),
        True,
    ))

    # --- check_training_slots ---
    cases.append((
        "slots are listed for a real day",
        check_training_slots("Monday"),
        "Open training slots on Monday: 9:00 AM, 1:00 PM, 6:00 PM.",
    ))
    cases.append((
        "a bad day returns a message, not an exception",
        "day of the week" in check_training_slots("Caturday"),
        True,
    ))

    # --- book_training_session, the state changing tool ---
    fresh_state()
    cases.append((
        "booking an open slot succeeds",
        book_training_session("Monday", "6pm", "Archit"),
        "Booked a personal training session on Monday at 6:00 PM for Archit.",
    ))
    cases.append((
        "the booked slot is gone",
        "6:00 PM" in tools.TRAINING_SLOTS["Monday"],
        False,
    ))
    cases.append((
        "the booking was recorded",
        tools.BOOKINGS[0],
        {"day": "Monday", "time": "6:00 PM", "name": "Archit"},
    ))
    cases.append((
        "the same slot cannot be booked twice",
        "is not open" in book_training_session("Monday", "6:00 PM", "Someone Else"),
        True,
    ))
    cases.append((
        "a double booking added no second record",
        len(tools.BOOKINGS),
        1,
    ))

    fresh_state()
    cases.append((
        "a slot that does not exist is refused",
        "is not open" in book_training_session("Monday", "4:00 AM", "Archit"),
        True,
    ))
    cases.append((
        "an empty name is refused",
        book_training_session("Monday", "9:00 AM", "   "),
        "I need a name to put the session under.",
    ))
    cases.append((
        "a refused booking changed nothing",
        "9:00 AM" in tools.TRAINING_SLOTS["Monday"],
        True,
    ))

    # --- the dispatch guard ---
    # The tool name comes from the model, so it is untrusted input choosing
    # which function runs. This is the security model of tool calling.
    fresh_state()
    cases.append((
        "GUARD: an invented tool name is rejected",
        "no tool called" in dispatch("cancel_booking", '{"day": "Monday"}'),
        True,
    ))
    cases.append((
        "GUARD: the rejection names the tools that do exist",
        "search_gym_info" in dispatch("cancel_booking", '{"day": "Monday"}'),
        True,
    ))
    cases.append((
        # list() takes a snapshot. Storing the live list would let a later
        # test mutate it before the comparison runs.
        "GUARD: an invented tool executes nothing",
        list(tools.TRAINING_SLOTS["Monday"]),
        ["9:00 AM", "1:00 PM", "6:00 PM"],
    ))
    cases.append((
        "GUARD: a python builtin name is rejected",
        "no tool called" in dispatch("print", '{"x": 1}'),
        True,
    ))
    cases.append((
        "GUARD: an empty name is rejected",
        "no tool called" in dispatch("", "{}"),
        True,
    ))

    # --- the write gate ---
    cases.append((
        "GATE: a write is blocked without confirmation",
        dispatch(
            "book_training_session",
            '{"day": "Monday", "time": "9:00 AM", "name": "Archit"}',
        ).startswith("Not done yet:"),
        True,
    ))
    cases.append((
        "GATE: a blocked write changed nothing",
        "9:00 AM" in tools.TRAINING_SLOTS["Monday"],
        True,
    ))
    cases.append((
        "GATE: the write runs once confirmation is passed",
        dispatch(
            "book_training_session",
            '{"day": "Monday", "time": "9:00 AM", "name": "Archit"}',
            allow_write=True,
        ).startswith("Booked"),
        True,
    ))
    cases.append((
        "GATE: a confirmed write did change state",
        "9:00 AM" in tools.TRAINING_SLOTS["Monday"],
        False,
    ))
    cases.append((
        "GATE: a read tool never needs confirmation",
        dispatch("check_training_slots", '{"day": "Tuesday"}').startswith("Open"),
        True,
    ))

    # --- malformed arguments ---
    cases.append((
        "malformed JSON is reported, not raised",
        "not valid JSON" in dispatch("check_training_slots", "{day: Monday"),
        True,
    ))
    cases.append((
        "a JSON list instead of an object is rejected",
        "must be a JSON object" in dispatch("check_training_slots", '["Monday"]'),
        True,
    ))
    cases.append((
        "a wrong argument name is reported, not raised",
        "wrong arguments" in dispatch("check_training_slots", '{"weekday": "Monday"}'),
        True,
    ))
    cases.append((
        "a missing required argument is reported",
        "wrong arguments" in dispatch(
            "book_training_session", '{"day": "Monday"}', allow_write=True
        ),
        True,
    ))

    # --- the tool table and the schemas agree ---
    schema_names = sorted(s["function"]["name"] for s in tools.TOOL_SCHEMAS)
    cases.append((
        "every schema has a matching function",
        schema_names,
        sorted(tools.AVAILABLE_TOOLS),
    ))
    cases.append(("there are three tools", len(tools.AVAILABLE_TOOLS), 3))
    cases.append((
        "no tool is named like a delete",
        [n for n in tools.AVAILABLE_TOOLS
         if "delete" in n or "cancel" in n or "remove" in n],
        [],
    ))

    fresh_state()
    return cases, retrieve_scores, refuse_scores


def run_tests():
    cases, retrieve_scores, refuse_scores = build_cases()
    passed = 0
    failed = 0

    for name, actual, expected in cases:
        if actual == expected:
            passed += 1
        else:
            failed += 1
            print("FAILED:", name)
            print("  expected:", expected)
            print("  actual:  ", actual)
            print()

    print("-" * 64)
    print("Threshold in use:", DEFAULT_THRESHOLD)
    print("Lowest score among should-retrieve:", round(min(retrieve_scores), 3))
    print("Highest score among should-refuse: ", round(max(refuse_scores), 3))
    print("Gap:", round(min(retrieve_scores) - max(refuse_scores), 3))
    print()
    print("Passed:", passed)
    print("Failed:", failed)
    print("Total: ", passed + failed)


if __name__ == "__main__":
    run_tests()
