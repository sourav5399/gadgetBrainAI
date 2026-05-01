# Gadget Brain AI

A small assistant that helps you choose between gadgets. You list candidate products; the model asks follow-up questions when budget, currency, usage, or category are unclear, then returns a structured recommendation.

You can run it in two ways:

- **Streamlit web UI** (`app.py`) — chat-style interface with sidebar settings.
- **Terminal** (`compareAgent.py`) — interactive CLI over stdin/stdout.

Both use the OpenAI Chat Completions API through the official `openai` Python SDK.

## Requirements

- Python 3.10 or newer
- An OpenAI API key with access to the models you select

This repository does not ship a `requirements.txt`. Install dependencies explicitly:

```bash
pip install streamlit openai python-dotenv
```

## Configuration

Create a `.env` file in the project root and keep it out of version control:

```env
OPENAI_API_KEY=sk-...
```

`compareAgent.py` loads environment variables with `python-dotenv` when imported. The Streamlit app uses the same module, so `OPENAI_API_KEY` is available on the server.

## Models and API keys (Streamlit)

Allowed models are defined in `compareAgent.py` as `MODEL` (currently `gpt-5-nano` and `gpt-4.1-mini`).

In the sidebar:

- **`gpt-5-nano`** — you can rely on `OPENAI_API_KEY` from `.env`. The optional API key field can stay empty if the env var is set.
- **`gpt-4.1-mini`** — you must enter an API key before **Start New Chat** is enabled. The handler also validates again on click so bypassing the disabled button in the browser does not skip the requirement.

The CLI always uses `create_client()` with `OPENAI_API_KEY` from the environment.

## Run the web app

From the project root:

```bash
streamlit run app.py
```

Open the URL Streamlit prints (often `http://localhost:8501`).

1. Choose a model and, if required, enter an API key.
2. In the first message, enter products separated by commas (for example: `MacBook Air, Dell XPS 13`).
3. Answer follow-up questions until you receive a final recommendation.
4. Use **Start New Chat** to clear the conversation.

## Run the CLI

```bash
python compareAgent.py
```

Enter comma-separated products, then reply to prompts until the script prints the recommendation.

## How it works

- The **system prompt** in `compareAgent.py` requires JSON-only replies in one of two shapes: `need_more_info` (with `question`) or `final_recommendation` (with `recommendation`).
- **`get_json_reply`** parses that JSON. If parsing fails, it sends a repair turn with `temperature=0` and parses again.
- **`app.py`** maintains `messages` for the API (including serialized assistant JSON where needed) and `ui_messages` for the chat UI.

## Project layout

| File | Purpose |
|------|---------|
| `app.py` | Streamlit UI and session state |
| `compareAgent.py` | Client, prompts, helpers, CLI entry |
| `.env` | Local secrets (do not commit) |
