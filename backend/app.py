from fastapi import FastAPI, WebSocket
import uvicorn
from dotenv import load_dotenv
from state import SREState
from graph import build_graph

# Load environment variables
load_dotenv()

# Build the graph
graph = build_graph()

# Create FastAPI app
app = FastAPI(title="AI SRE Agent")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "AI SRE Agent is running"}


@app.websocket("/stream")
async def stream(ws: WebSocket):
    """
    WebSocket endpoint for streaming graph execution events.
    Frontend can connect to ws://localhost:8000/stream
    """
    await ws.accept()

    try:
        initial_state = SREState()

        async for event in graph.astream(initial_state):
            await ws.send_json(event)

        await ws.close()
    except Exception as e:
        print(f"WebSocket error: {e}")
        await ws.close(code=1011, reason=str(e))


def run_cli():
    """
    CLI runner for direct execution without WebSocket.
    Run with: python -c "from app import run_cli; run_cli()"
    """
    print("Running AI SRE Agent in CLI mode...")
    result = graph.invoke(SREState())
    print("\n=== Final Result ===")
    print(result)


if __name__ == "__main__":
    # Run the FastAPI server with WebSocket support
    uvicorn.run(app, host="0.0.0.0", port=8000)
