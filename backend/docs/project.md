project.md
📌 AI SRE Looping Agent — Project Overview

This project implements a minimal LangGraph-based AI SRE agent capable of:

reading incoming signals (logs/Slack/etc.)

reasoning about root cause

executing an action

evaluating whether the issue is resolved

looping until resolution

exposing events via WebSocket for a frontend UI

The goal is to provide a clean, minimal, hackathon-ready foundation you can extend.

🗂 Folder Structure
ai-sre-agent/
  ├── app.py
  ├── graph.py
  ├── state.py
  ├── nodes/
  │     ├── observe.py
  │     ├── reason.py
  │     ├── act.py
  │     ├── evaluate.py
  ├── .env
  ├── requirements.txt
  └── project.md

🔧 Dependencies

Install required packages:

pip install langgraph langchain langchain-openai fastapi uvicorn python-dotenv


Set your API key in .env:

OPENAI_API_KEY=your-key-here


Or export it:

export OPENAI_API_KEY=your-key-here

🧠 State Definition (state.py)
from pydantic import BaseModel
from typing import Optional, List

class SREState(BaseModel):
    logs: Optional[str] = None
    issue: Optional[str] = None
    actions: List[str] = []
    resolved: bool = False


This is the global memory passed through each node of the graph.

🔵 Nodes (nodes/*.py)
observe.py
def observe(state):
    # Replace with real Slack/log ingestion later.
    state.logs = "ERROR: service unreachable; connection timeout"
    return state

reason.py
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini")

def reason(state):
    resp = llm.invoke(f"""
    Logs: {state.logs}
    What is the issue and next action?
    Respond JSON: {{ "issue": "...", "action": "..." }}
    """).json()

    state.issue = resp["issue"]
    state.actions.append(resp["action"])
    return state

act.py
def act(state):
    print("[ACTION]", state.actions[-1])
    # Stub: replace with kubectl/aws/docker/etc.
    return state

evaluate.py
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini")

def evaluate(state):
    resp = llm.invoke(f"""
    Logs: {state.logs}
    Actions: {state.actions}
    Is the issue resolved?
    Respond JSON: {{ "resolved": true/false }}
    """).json()

    state.resolved = resp["resolved"]
    return state

🔁 LangGraph Loop (graph.py)
from langgraph.graph import StateGraph, END
from state import SREState
from nodes.observe import observe
from nodes.reason import reason
from nodes.act import act
from nodes.evaluate import evaluate

def build_graph():
    builder = StateGraph(SREState)

    builder.add_node("observe", observe)
    builder.add_node("reason", reason)
    builder.add_node("act", act)
    builder.add_node("evaluate", evaluate)

    # Flow
    builder.add_edge("observe", "reason")
    builder.add_edge("reason", "act")
    builder.add_edge("act", "evaluate")

    # Loop condition
    builder.add_conditional_edges(
        "evaluate",
        lambda s: s.resolved,
        {True: END, False: "observe"}
    )

    builder.set_entry_point("observe")
    return builder.compile()


This creates:

observe → reason → act → evaluate
                     ↑         |
                     └─────────┘   (loop until resolved)

▶️ Direct CLI Runner (app.py)
from state import SREState
from graph import build_graph
from dotenv import load_dotenv

load_dotenv()
graph = build_graph()

if __name__ == "__main__":
    result = graph.invoke(SREState())
    print(result)


Run:

python app.py

🌐 WebSocket Streaming (for UI) — also inside app.py
from fastapi import FastAPI, WebSocket
import uvicorn
from graph import build_graph
from state import SREState

app = FastAPI()
graph = build_graph()

@app.websocket("/stream")
async def stream(ws: WebSocket):
    await ws.accept()
    initial = SREState()
    async for event in graph.astream(initial):
        await ws.send_json(event)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)


Frontend can connect to:

ws://localhost:8000/stream

🧪 Testing the Graph Flow

Expected loop:

1. observe
2. reason
3. act
4. evaluate
(loop…)
