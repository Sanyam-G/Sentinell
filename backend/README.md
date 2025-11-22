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

Set your OpenAI API key in `.env`:

```bash
OPENAI_API_KEY=your-key-here
```

Or export it:

```bash
export OPENAI_API_KEY=your-key-here
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
- **nodes/reason.py**: Uses LLM to analyze logs and determine root cause + next action
- **nodes/act.py**: Executes the proposed action (currently just prints it)
- **nodes/evaluate.py**: Uses LLM to determine if the issue is resolved
- **graph.py**: Builds the LangGraph state machine with conditional looping
- **app.py**: FastAPI server with WebSocket streaming + CLI runner

## Extending the Agent

This is an MVP designed to be extended:

- **observe.py**: Replace stub with real Slack/log ingestion
- **act.py**: Implement actual kubectl/aws/docker/terraform commands
- Add authentication and authorization
- Add persistent state storage
- Add more sophisticated evaluation logic
- Add metrics and observability
