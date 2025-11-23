project.md — AI SRE Admin Dashboard (Frontend Design)
📌 Overview

This project is a lightweight frontend dashboard that visualizes what your AI SRE agent is doing in real time.
The goal: give hackathon judges a clear window into the agent’s reasoning loop, context, tools, and execution trace — without needing real infra access.

🎯 Objectives

Show live agent reasoning (streamed tokens or step-by-step graph).

Display Slack context used by the agent (e.g., #prod-alerts).

Display code context (files the agent referenced).

Visualize tool calls (mocked or real) + responses.

Present a timeline of the agent’s “investigation.”

Provide a simple UI for triggering incidents or asking the agent questions.

🧱 Core UI Components
1. Incident Console (Main Pane)

Shows the active incident or question the user asked.

Title (“CPU spike on Worker-17”)

Description / prompt

Buttons:

Ask Agent

Simulate Incident (pre-seeded scenarios)

Subcomponents:

Live Reasoning Stream

token stream OR LangGraph node-by-node updates

collapsible

Agent Steps Timeline

sequential cards: “Search Slack”, “Analyze Code”, “Generate Plan”, “Execute Tool”

each card clickable to show details

Final Output

suggested remediation plan

summary

2. Tool Call Monitor

Think of this like a mini “CloudTrail for the agent.”

Table:

timestamp

tool name (search_slack, read_file, run_command, etc.)

arguments

response (or mock result)

Click row → modal with full payload

Supports your “loop until resolution” demo: judges can literally watch the loop iterations.

3. Slack Context Viewer

A sidebar that shows:

Channel selector (#prod-alerts, #infra-debug)

Messages used by agent

Highlight the subset matching search results

Click message → show “why it was retrieved” (embedding similarity or keyword match)

4. Code Context Viewer

File explorer tree

Preloaded repo snapshot

When agent references a file:

auto-scroll to line

highlight the excerpt used

This massively increases credibility even if back-end is mocked.

5. Agent State Panel

Displays:

Current graph node (if using LangGraph)

Past nodes visited

Memory:

retrieved context

past actions

loop iteration number

This is the “cool factor” panel.

🏛️ Architecture (Frontend)
Stack

React + Vite

Tailwind (ship fast, looks clean)

React Query for polling agent state

WebSockets (optional) for streaming reasoning

Shadcn/UI for polished components

API contract expectations

Backend provides:

GET /agent/state
GET /agent/steps
GET /agent/tool-calls
GET /slack/messages
GET /code/file?path=...
POST /agent/run


No need to literally implement all of these — mock if needed.

⚙️ Data Flow

User clicks “Ask Agent.”

Backend starts agent run → returns runId.

Frontend:

Polls /agent/state?runId=... every 500ms
OR receives WebSocket events.

As events arrive:

Update reasoning stream

Append steps to timeline

Update tool call table

When the final_output event arrives:

Render remediation plan

🧪 Demo Script (for judges)

Click “Simulate Incident.”

Watch Slack messages populate the context viewer.

Agent begins:

“Searching Slack…”

“Reading worker.py…”

“Creating remediation plan…”

Tool call table fills up.

Final plan appears on screen.

Judge goes “wow you made an SRE assistant in a weekend.”

🚀 Stretch Goals (only if time)

Dark mode

Embedding similarity heatmap

Replay mode for past incidents

Multiple agents displayed side-by-side

LangGraph node visualizer (react-flow)

📝 To Build This in 3–4 Hours (realistic hackathon plan)
Hour 1 — Skeleton

Create layout (sidebar + main pane)

Set up routes

Fake data + mock backend JSON

Hour 2 — Real-Time Feed

Build reasoning streaming UI

Build timeline UI

Build simple tool call table

Hour 3 — Polishing

Slack viewer

Code viewer

Color coding for steps

Hour 4 (Optional)

Connect real backend

Add websocket streaming

Polish animations

📡 Backend contract (updated)

The FastAPI backend now exposes concrete routes the UI should call:

- `GET /api/health` – quick heartbeat for status widget.
- `GET /api/repos` / `POST /api/repos` – list + register monitored repos.
- `GET /api/log-sources` / `POST /api/log-sources` – configure log ingestion.
- `GET /api/slack/channels` / `POST /api/slack/channels` – map Slack channels.
- `POST /api/issues` – form in the UI for manual incident submission.
- `POST /api/signals/logs` – advanced panel to push custom log alerts.
- `POST /api/signals/slack` – Slack bot relay endpoint (status page should mention URL).
- `GET /api/incidents` – drive the incident table/timeline.

When a user files an issue from the dashboard, call `/api/issues` and then show the
new incident in the console while the worker picks it up. Poll `/api/incidents`
or subscribe to the WebSocket to reflect status changes.