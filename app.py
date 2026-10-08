"""
CSC-128 Capstone: GYMARC front desk assistant
Archit Dubey

Run locally:  streamlit run app.py
The deployed app reads its key from the Secrets panel on share.streamlit.io.
"""
import json

import streamlit as st
from groq import Groq, APIError, RateLimitError

import tools
from agent import MAX_ROUNDS, MODEL, SYSTEM_PROMPT, dispatch, pending_write, run_agent

GREETING = (
    "Hi, I am the GYMARC front desk assistant. I can answer questions about the "
    "gym from its own documents, tell you which personal training slots are open, "
    "and book one for you. I cannot cancel or change anything, so email "
    "support@gym.com for that."
)

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def get_client():
    """Read the key from st.secrets and fail with a message instead of a crash."""
    try:
        key = st.secrets["GROQ_API_KEY"]
    except (KeyError, FileNotFoundError):
        st.error(
            "This app is not configured with an API key yet. Locally, create "
            ".streamlit/secrets.toml with GROQ_API_KEY. On Streamlit Community "
            "Cloud, paste the key into the Secrets panel in app settings."
        )
        st.stop()
    return Groq(api_key=key)


def show_log(entries):
    """Show every tool call, its arguments, and its result."""
    if not entries:
        return
    with st.expander("Tool calls (" + str(len(entries)) + ")"):
        for entry in entries:
            st.markdown("**" + entry["name"] + "**")
            st.code(entry["arguments"], language="json")
            st.text(entry["result"])


def remember_slots(log):
    """
    Keep the booking details the member has given so far.

    The model collects day, time and name across however many turns it takes.
    Storing them here is what lets the sidebar show the half filled form, and
    it survives a Streamlit rerun because it lives in session state.
    """
    for entry in log:
        if entry["name"] != "book_training_session":
            continue
        try:
            arguments = json.loads(entry["arguments"])
        except (json.JSONDecodeError, TypeError):
            continue
        for field in ["day", "time", "name"]:
            value = arguments.get(field)
            if value:
                st.session_state.slots[field] = value


def ask_model(client, allow_write=False):
    """Run the agent once and record what happened for display."""
    log = []
    try:
        reply, updated = run_agent(client, st.session_state.messages, log, allow_write)
        st.session_state.messages = updated
    except RateLimitError:
        reply = (
            "I am getting too many requests right now. "
            "Wait about a minute, then ask again."
        )
    except APIError:
        reply = (
            "I could not reach the language model just now. Try again in a moment. "
            "If it keeps happening, the front desk can help at support@gym.com."
        )
    except Exception:
        reply = (
            "Something went wrong on my end. Try asking again, or email "
            "support@gym.com if it keeps happening."
        )

    remember_slots(log)
    st.session_state.display.append({"role": "assistant", "content": reply, "log": log})
    st.session_state.pending = pending_write(log)


def draw_sidebar():
    """Show what the bot is holding, so its state is visible rather than hidden."""
    with st.sidebar:
        st.subheader("Booking details collected")
        slots = st.session_state.slots
        for field in ["day", "time", "name"]:
            value = slots.get(field)
            if value:
                st.write(field.capitalize() + ":", value)
            else:
                st.write(field.capitalize() + ": not given yet")

        st.subheader("Training slots open")
        for day in DAYS:
            open_slots = tools.TRAINING_SLOTS[day]
            if open_slots:
                st.write(day + ":", ", ".join(open_slots))
            else:
                st.write(day + ": none")

        st.subheader("Sessions booked")
        if not tools.BOOKINGS:
            st.caption("None yet.")
        for booking in tools.BOOKINGS:
            st.write(booking["day"], booking["time"], "for", booking["name"])

        st.divider()
        st.caption(
            "Model: " + MODEL + ". Up to " + str(MAX_ROUNDS) + " tool rounds per turn. "
            "There is deliberately no tool that can cancel or change a booking."
        )

        if st.button("Start over"):
            st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            st.session_state.display = []
            st.session_state.pending = None
            st.session_state.slots = {}
            st.rerun()


def main():
    st.set_page_config(page_title="GYMARC Assistant", page_icon="🏋")
    st.title("GYMARC Assistant")
    st.caption(
        "You are chatting with software, not a person. It answers only from "
        "GYMARC's own documents, and every tool call it makes is shown under the "
        "reply."
    )

    client = get_client()

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if "display" not in st.session_state:
        st.session_state.display = []
    if "pending" not in st.session_state:
        st.session_state.pending = None
    if "slots" not in st.session_state:
        st.session_state.slots = {}

    draw_sidebar()

    with st.chat_message("assistant"):
        st.markdown(GREETING)

    for item in st.session_state.display:
        with st.chat_message(item["role"]):
            st.markdown(item["content"])
            if item["role"] == "assistant":
                show_log(item.get("log", []))

    # A write was requested and blocked. Nothing has changed yet.
    if st.session_state.pending:
        details = st.session_state.pending
        st.warning(
            "Confirm this session: "
            + str(details.get("day"))
            + " at "
            + str(details.get("time"))
            + " for "
            + str(details.get("name"))
            + ". Nothing is booked yet."
        )
        left, right = st.columns(2)

        if left.button("Confirm booking", type="primary"):
            # Run the exact arguments that were blocked, with no model round
            # trip in between, so nothing can change after the member agreed.
            result = dispatch(
                "book_training_session", json.dumps(details), allow_write=True
            )
            st.session_state.messages.append(
                {"role": "user", "content": "I pressed confirm. Result: " + result}
            )
            st.session_state.display.append({"role": "user", "content": "Confirmed."})
            st.session_state.display.append(
                {
                    "role": "assistant",
                    "content": result,
                    "log": [
                        {
                            "name": "book_training_session",
                            "arguments": json.dumps(details),
                            "result": result,
                        }
                    ],
                }
            )
            st.session_state.pending = None
            st.session_state.slots = {}
            st.rerun()

        if right.button("Cancel"):
            st.session_state.messages.append(
                {"role": "user", "content": "No, do not book that."}
            )
            st.session_state.display.append(
                {"role": "user", "content": "No, do not book that."}
            )
            st.session_state.pending = None
            ask_model(client)
            st.rerun()

    question = st.chat_input("Ask about the gym, or book a training session")

    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        st.session_state.display.append({"role": "user", "content": question})
        ask_model(client)
        st.rerun()


if __name__ == "__main__":
    main()
