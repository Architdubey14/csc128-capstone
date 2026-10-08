# GYMARC Assistant

CSC-128 Capstone

Archit Dubey

A front desk assistant for a gym called GYMARC. It answers member questions
using only the gym's own documents, tells members which personal training
slots are open, and books one for them.

## What it does

| Intent | How it is handled |
| --- | --- |
| Questions about the gym | `search_gym_info` retrieves from ten documents and the model answers only from what came back |
| Which training slots are open | `check_training_slots`, a read only tool |
| Book a training session | `book_training_session`, which collects day, time and name across turns and cannot run until the member presses confirm |
| Cancel or change a booking | No tool exists. The bot says so and sends the member to the front desk |

## How to run it locally

1. Open a terminal in this folder and activate a virtual environment.
2. `pip install -r requirements.txt`
3. Create `.streamlit/secrets.toml` containing `GROQ_API_KEY = "your key"`.
4. `streamlit run app.py`

To run the tests: `python test_capstone.py`. These need no API key, because
retrieval, the tool functions and the dispatch guard are all deterministic.

## Files

- `knowledge.py` holds the ten documents and imports nothing.
- `retriever.py` does TF-IDF retrieval over them.
- `tools.py` holds the three tools, the training schedule, and the schemas.
- `agent.py` holds the dispatch guard and the tool calling loop.
- `app.py` is the Streamlit interface and the entry point.
- `test_capstone.py` covers all three layers. 58 tests, all passing.

## Deployment

The deployed app does not use `.streamlit/secrets.toml`, which is gitignored
and never leaves this machine. The key is pasted into the Secrets panel in app
settings on share.streamlit.io instead, where `st.secrets` reads it the same
way. Every version in `requirements.txt` is pinned, because an unpinned
package picks up a new release at build time.

## What I would fix with more time

State lives in module level lists, so everything resets when the app restarts
and two people using it would not see each other's bookings. A real version
needs a database, and `book_training_session` would then have to handle two
people claiming the same slot at once.

Retrieval matches words, so a question phrased in vocabulary I did not think of
fails even when the answer is in the documents. Every mismatch I have fixed
came from a test question I wrote myself.

The confirmation flow only handles one blocked write at a time. A second write
tool would need `pending_write` to deal with more than the most recent call.
