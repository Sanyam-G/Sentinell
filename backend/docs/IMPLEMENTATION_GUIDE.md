# Implementation Guide: Making the AI SRE Agent Production-Ready

## 1. Connect to Frontend

### Current Setup
The WebSocket server auto-starts the agent when connected. You might want it to wait for triggers.

### Option A: Auto-start (Current)
```bash
python app.py
# Frontend connects to ws://localhost:8000/stream
# Agent runs automatically
```

### Option B: Trigger-based (Recommended)
Modify `app.py` to accept incoming log events from frontend:

```python
@app.websocket("/stream")
async def stream(ws: WebSocket):
    await ws.accept()

    try:
        # Wait for incoming log data from frontend
        while True:
            data = await ws.receive_json()

            # Create state with incoming logs
            initial_state = SREState(logs=data.get("logs"))

            # Stream agent execution back to frontend
            async for event in graph.astream(initial_state):
                await ws.send_json(event)

    except WebSocketDisconnect:
        print("Client disconnected")
```

### Frontend Integration Example

```javascript
const ws = new WebSocket('ws://localhost:8000/stream');

ws.onopen = () => {
  // Send logs to trigger the agent
  ws.send(JSON.stringify({
    logs: "ERROR: service unreachable; connection timeout"
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  const nodeName = Object.keys(data)[0];
  const state = data[nodeName];

  // Update UI based on node
  if (nodeName === 'observe') {
    showLogs(state.logs);
  } else if (nodeName === 'reason') {
    showIssue(state.issue);
    showSuggestedAction(state.actions[state.actions.length - 1]);
  } else if (nodeName === 'act') {
    showActionExecuting(state.actions[state.actions.length - 1]);
  } else if (nodeName === 'evaluate') {
    if (state.resolved) {
      showResolved();
    } else {
      showRetrying();
    }
  }
};
```

---

## 2. Make It Work for Real

### A. Real Log Ingestion (nodes/observe.py)

Replace the stubbed error log with real data sources:

#### Option 1: Slack Integration
```python
# nodes/observe.py
from slack_sdk import WebClient
from state import SREState
import os

slack_client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])

def observe(state: SREState) -> SREState:
    """Fetch recent Slack messages from #alerts channel"""

    # Get messages from last 5 minutes
    response = slack_client.conversations_history(
        channel="C1234567890",  # Your alerts channel ID
        limit=10
    )

    # Combine recent messages into logs
    messages = []
    for message in response["messages"]:
        if "error" in message["text"].lower() or "alert" in message["text"].lower():
            messages.append(message["text"])

    state.logs = "\n".join(messages) if messages else "No alerts found"
    return state
```

Add to requirements.txt:
```
slack-sdk==3.23.0
```

#### Option 2: CloudWatch Logs
```python
# nodes/observe.py
import boto3
from datetime import datetime, timedelta
from state import SREState

logs_client = boto3.client('logs')

def observe(state: SREState) -> SREState:
    """Fetch recent CloudWatch logs"""

    end_time = datetime.now()
    start_time = end_time - timedelta(minutes=5)

    response = logs_client.filter_log_events(
        logGroupName='/aws/lambda/my-function',
        startTime=int(start_time.timestamp() * 1000),
        endTime=int(end_time.timestamp() * 1000),
        filterPattern='ERROR'
    )

    log_lines = [event['message'] for event in response['events']]
    state.logs = "\n".join(log_lines) if log_lines else "No errors found"

    return state
```

Add to requirements.txt:
```
boto3==1.34.0
```

#### Option 3: File-based Logs
```python
# nodes/observe.py
from state import SREState
import subprocess

def observe(state: SREState) -> SREState:
    """Tail system logs for errors"""

    # Use tail to get last 50 lines with errors
    result = subprocess.run(
        ["tail", "-n", "50", "/var/log/syslog"],
        capture_output=True,
        text=True
    )

    # Filter for ERROR lines
    error_lines = [
        line for line in result.stdout.split('\n')
        if 'ERROR' in line or 'CRITICAL' in line
    ]

    state.logs = "\n".join(error_lines) if error_lines else "No errors found"
    return state
```

#### Option 4: HTTP Endpoint (Accept logs from anywhere)
```python
# app.py - Add this endpoint
@app.post("/ingest")
async def ingest_logs(data: dict):
    """Accept logs via HTTP POST"""
    initial_state = SREState(logs=data.get("logs", ""))

    # Run agent synchronously
    result = graph.invoke(initial_state)

    return {
        "issue": result.get("issue"),
        "actions": result.get("actions"),
        "resolved": result.get("resolved")
    }
```

Then external systems can POST to it:
```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"logs": "ERROR: database connection failed"}'
```

---

### B. Real Action Execution (nodes/act.py)

Replace print statements with actual remediation:

#### Option 1: Kubernetes Actions
```python
# nodes/act.py
from kubernetes import client, config
from state import SREState
import subprocess

# Load k8s config
config.load_kube_config()
v1 = client.CoreV1Api()

def act(state: SREState) -> SREState:
    """Execute remediation actions on Kubernetes"""

    if not state.actions:
        return state

    action = state.actions[-1]
    print(f"[ACTION] {action}")

    # Parse action and execute
    if "restart" in action.lower():
        # Restart pods
        namespace = "default"
        label_selector = "app=my-service"

        pods = v1.list_namespaced_pod(namespace, label_selector=label_selector)

        for pod in pods.items:
            v1.delete_namespaced_pod(pod.metadata.name, namespace)
            print(f"  → Restarted pod: {pod.metadata.name}")

    elif "scale" in action.lower():
        # Scale deployment
        apps_v1 = client.AppsV1Api()
        apps_v1.patch_namespaced_deployment_scale(
            name="my-service",
            namespace="default",
            body={"spec": {"replicas": 3}}
        )
        print(f"  → Scaled deployment to 3 replicas")

    return state
```

Add to requirements.txt:
```
kubernetes==28.1.0
```

#### Option 2: AWS Actions
```python
# nodes/act.py
import boto3
from state import SREState

ec2 = boto3.client('ec2')
ecs = boto3.client('ecs')

def act(state: SREState) -> SREState:
    """Execute remediation actions on AWS"""

    if not state.actions:
        return state

    action = state.actions[-1]
    print(f"[ACTION] {action}")

    if "restart" in action.lower() and "service" in action.lower():
        # Restart ECS service
        ecs.update_service(
            cluster='my-cluster',
            service='my-service',
            forceNewDeployment=True
        )
        print(f"  → Triggered ECS service restart")

    elif "restart" in action.lower() and "instance" in action.lower():
        # Restart EC2 instance
        ec2.reboot_instances(InstanceIds=['i-1234567890abcdef0'])
        print(f"  → Rebooted EC2 instance")

    return state
```

#### Option 3: Shell Commands (Be Careful!)
```python
# nodes/act.py
import subprocess
from state import SREState

ALLOWED_COMMANDS = {
    "restart nginx": ["systemctl", "restart", "nginx"],
    "clear cache": ["rm", "-rf", "/tmp/cache/*"],
    "restart service": ["systemctl", "restart", "my-service"],
}

def act(state: SREState) -> SREState:
    """Execute safe shell commands"""

    if not state.actions:
        return state

    action = state.actions[-1].lower()
    print(f"[ACTION] {action}")

    # Only execute pre-approved commands
    for allowed_action, cmd in ALLOWED_COMMANDS.items():
        if allowed_action in action:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"  → Executed successfully: {' '.join(cmd)}")
            else:
                print(f"  → Failed: {result.stderr}")
            break
    else:
        print(f"  → Action not in allowed list, skipping")

    return state
```

---

### C. Better Evaluation (nodes/evaluate.py)

Replace LLM guessing with real health checks:

```python
# nodes/evaluate.py
import requests
import json
from langchain_anthropic import ChatAnthropic
from state import SREState

def check_service_health(service_url: str) -> bool:
    """Check if service is actually healthy"""
    try:
        response = requests.get(f"{service_url}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def evaluate(state: SREState) -> SREState:
    """Evaluate with real health checks + LLM reasoning"""

    # First, check actual service health
    service_healthy = check_service_health("http://my-service:8080")

    if service_healthy:
        state.resolved = True
        print("  ✓ Service health check passed")
        return state

    # If still unhealthy, ask LLM if we should retry
    llm = ChatAnthropic(model="claude-sonnet-4-20250514")

    prompt = f"""You are an SRE evaluating if more actions are needed.

Original Logs: {state.logs}
Actions taken: {state.actions}
Service health check: FAILED

Should we try more actions or give up? Consider:
- Have we already tried {len(state.actions)} actions
- Are we repeating the same action?

Respond with ONLY JSON: {{"resolved": true/false, "reason": "..."}}"""

    response = llm.invoke(prompt)

    try:
        content = response.content.strip()
        if "{" in content:
            start = content.find("{")
            end = content.rfind("}") + 1
            parsed = json.loads(content[start:end])
            state.resolved = parsed.get("resolved", len(state.actions) >= 3)
    except:
        # Give up after 3 attempts
        state.resolved = len(state.actions) >= 3

    return state
```

Add to requirements.txt:
```
requests==2.32.5
```

---

## Quick Start Production Checklist

### Minimal Production Setup (1-2 hours):

1. **Choose your log source** and update `nodes/observe.py`:
   - Slack alerts channel (easiest)
   - CloudWatch/Datadog logs
   - HTTP endpoint accepting logs

2. **Choose your actions** and update `nodes/act.py`:
   - Start with safe, read-only actions (check status, get metrics)
   - Add kubectl commands (restart, scale)
   - Add AWS/GCP commands

3. **Add health checks** in `nodes/evaluate.py`:
   - HTTP health endpoint
   - Kubernetes pod status
   - Metrics from monitoring system

4. **Security**:
   - Add API key authentication to `/stream` and `/ingest`
   - Whitelist allowed actions in `act.py`
   - Add approval flow for destructive actions

5. **Run it**:
   ```bash
   python app.py
   ```

### Example Full Flow:

1. User reports issue in Slack #alerts
2. `observe()` fetches Slack messages
3. `reason()` Claude analyzes: "Pod is crashing due to OOM"
4. `act()` increases memory limit via kubectl
5. `evaluate()` checks pod health endpoint
6. If healthy → resolved, if not → loop back

---

## Next Steps

Want me to implement any specific integration? I can help you:

1. Set up Slack integration
2. Add kubectl commands for Kubernetes
3. Create an HTTP endpoint for log ingestion
4. Add authentication/security
5. Implement specific health checks for your services

Just let me know what your infrastructure looks like!
