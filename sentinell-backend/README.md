# Sentinell Observer Node 👁️

The "nervous system" that monitors all victim containers in real-time.

## Features

- **Real-time Log Streaming**: Streams logs from all victim containers
- **Docker Event Monitoring**: Detects container die, oom, restart events
- **Resource Metrics**: Tracks CPU and memory usage
- **WebSocket API**: Real-time data streaming to dashboard
- **Structured Logging**: All logs parsed and formatted as JSON

## Architecture

```
Docker Engine
    ↓
Observer (Docker SDK)
    ↓
Log Parser & Event Processor
    ↓
WebSocket Streams
    ↓
Dashboard / Agent
```

## API Endpoints

### HTTP Endpoints

- `GET /` - Service info and health
- `GET /health` - Health check
- `GET /containers` - List all monitored containers
- `GET /stats` - Get resource stats for all containers
- `POST /events/anomaly` - Report anomaly to observer

### WebSocket Endpoints

- `WS /ws/logs` - Stream all logs and events
- `WS /ws/logs/{container_name}` - Stream logs from specific container

## Usage

### Local Development

```bash
cd sentinell-backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

### Docker (Production)

```bash
# Built and started via docker-compose
docker-compose up -d sentinell-observer
```

## Event Format

All events are JSON structured:

```json
{
  "type": "log|event|anomaly|heartbeat",
  "timestamp": "2025-11-22T12:00:00",
  "container": "sentinell-nginx",
  "message": "Error message here",
  "level": "ERROR"
}
```

## WebSocket Client Example

```javascript
const ws = new WebSocket('ws://localhost:8001/ws/logs');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`[${data.container}] ${data.message}`);
};
```

## Monitored Events

- `die` - Container stopped
- `oom` - Out of memory
- `restart` - Container restarted
- `start` - Container started
- `kill` - Container killed
- `stop` - Container stopped

## Requirements

- Docker socket access (`/var/run/docker.sock`)
- Python 3.11+
- FastAPI
- Docker SDK for Python
