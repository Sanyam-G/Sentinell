# Testing the AI SRE Agent

## Quick Test Commands

### 1. Basic Structure Test (No API key needed)
Tests that the graph and state are built correctly without calling the LLM:

```bash
python test_basic.py
```

### 2. Full Agent Test (Single Invocation)
Runs the full LangGraph loop and shows only the final result:

```bash
python test_agent.py
```

### 3. Streaming Test (See Each Step)
Shows each step of the agent execution in real-time:

```bash
python test_agent.py --stream
```

## Expected Output

When running `python test_agent.py --stream`, you should see:

```
=== AI SRE Agent Test ===

📍 Step 1: observe
- Logs are populated with error message

📍 Step 2: reason
- Claude analyzes the logs
- Identifies the issue
- Suggests an action

📍 Step 3: act
- Executes the action (prints it)

📍 Step 4: evaluate
- Claude determines if issue is resolved
- If resolved: END
- If not resolved: Loop back to observe
```

## WebSocket Server

To test with a frontend or WebSocket client:

```bash
python app.py
```

Then connect to `ws://localhost:8000/stream`

## What the Agent Does

1. **Observe**: Reads logs (currently stubbed with "ERROR: service unreachable; connection timeout")
2. **Reason**: Uses Claude Sonnet 4 to analyze logs and suggest remediation
3. **Act**: Executes the suggested action (currently just prints it)
4. **Evaluate**: Uses Claude to determine if the issue is resolved
5. **Loop**: If not resolved, goes back to observe

## Current Model

The agent uses **Claude Sonnet 4** (`claude-sonnet-4-20250514`) for:
- Root cause analysis
- Action planning
- Resolution evaluation

## Troubleshooting

If you get model errors, check which models your API key has access to:

```bash
python check_models.py
```
