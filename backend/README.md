# AI SRE Looping Agent

A minimal LangGraph-based AI SRE agent that can observe issues, reason about root causes, execute actions, and loop until resolution.

## Setup

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Set your Anthropic API key in `.env`:

```bash
ANTHROPIC_API_KEY=your-key-here
```

Or export it:

```bash
export ANTHROPIC_API_KEY=your-key-here
```

## Usage

### Run WebSocket Server (for Frontend UI)

```bash
python app.py
```

The server will start on `http://localhost:8000`. Frontend can connect to the WebSocket at:
```
ws://localhost:8000/stream
```

### REST API surface

The FastAPI instance now exposes JSON endpoints under `/api` so the frontend (or
other services) can configure integrations and submit incidents:

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/api/repos` | Register a repository to monitor |
| `GET` | `/api/repos` | List configured repositories |
| `POST` | `/api/log-sources` | Register log ingestion endpoints (Loki, CW, etc.) |
| `POST` | `/api/slack/channels` | Map Slack channels to repos |
| `POST` | `/api/issues` | Manual issue submission from UI |
| `POST` | `/api/signals/logs` | Push log-based alerts into the incident queue |
| `POST` | `/api/signals/slack` | Ingest Slack escalations (used by the Slack bot) |
| `POST` | `/api/signals/github` | Store GitHub webhook payloads for later correlation |
| `GET` | `/api/incidents` | Retrieve queued incidents for display |

All configuration/incident data lives in the SQL database configured via
`DATABASE_URL` (SQLite by default, Postgres in production).

### Background worker

Run `python worker.py` in a separate process to continuously drain queued
incidents (submitted via the APIs above). The worker:

- Clones/updates monitored repos (temporary cache in `/tmp/sentinell/repos`)
- Hydrates LangGraph state with repo/log/Slack context
- Generates a remediation plan and simulates execution
- Invokes the stub `PullRequestService` so we have a hook for real GitHub PRs

💡 Hook this worker up to a process manager (Supervisor, systemd, K8s cron job)
once you connect the APIs to real signals.

### Pinecone context store

Signals ingested via `/api/signals/*` are now mirrored into Pinecone so the agent
can retrieve relevant log lines, Slack messages, and commit summaries.

Environment variables required:

- `PINECONE_API_KEY`
- `PINECONE_INDEX` (default `sentinell-context`)
- `PINECONE_ENV` (default `us-east-1`)
- `OPENAI_API_KEY` (used for embedding generation)

If these are not set, the REST calls still succeed but the backend logs a warning
and skips vector ingestion.

### Run CLI Mode

```python
from app import run_cli
run_cli()
```

Or:

```bash
python -c "from app import run_cli; run_cli()"
```

### Run Basic Tests

```bash
python test_basic.py
```

## Architecture

The agent follows this flow:

```
observe → reason → act → evaluate
             ↑         |
             └─────────┘   (loop until resolved)
```

### Components

- **state.py**: Defines the `SREState` that tracks logs, issues, actions, and resolution status
- **nodes/observe.py**: Observes incoming signals (currently stubbed with sample error log)
- **nodes/reason.py**: Uses Claude to analyze logs and determine root cause + next action
- **nodes/act.py**: Executes the proposed action (currently just prints it)
- **nodes/evaluate.py**: Uses Claude to determine if the issue is resolved
- **graph.py**: Builds the LangGraph state machine with conditional looping
- **app.py**: FastAPI server with WebSocket streaming + CLI runner

The agent uses **Claude Sonnet 4** (`claude-sonnet-4-20250514`) via Anthropic's API for reasoning and evaluation.

## Extending the Agent

This is an MVP designed to be extended:

- **observe.py**: Replace stub with real Slack/log ingestion
- **act.py**: Implement actual kubectl/aws/docker/terraform commands
- Add authentication and authorization
- Add persistent state storage
- Add more sophisticated evaluation logic
- Add metrics and observability
