# ⭐ SENTINELL - The Autonomous SRE Agent for Self-Healing Systems

**"Fixing production before humans even wake up."**

An AI-powered agent that observes your microservices cluster, detects failures, identifies root causes using RAG, and self-repairs in real-time.

## 🎯 Quick Start

### Prerequisites
- Docker & Docker Compose
- Make (optional, for convenience commands)

### Start the Victim Cluster

```bash
# Build and start all services
make build
make up

# Or use docker-compose directly
docker-compose build
docker-compose up -d

# Check health status
make health
```

Access the application:
- **Frontend:** http://localhost
- **Product API:** http://localhost:8000
- **Payment Service:** http://localhost:3002

## 🧱 Architecture

### Victim Environment (Current)
Five microservices designed to demonstrate realistic failure scenarios:

1. **Frontend (Next.js)** - E-commerce UI
2. **Product API (FastAPI)** - Product catalog service
3. **Payment Service (Node.js)** - Payment processing
4. **PostgreSQL** - Database
5. **Nginx** - Reverse proxy

### Coming Soon
- **Observer Node** - Container monitoring & log streaming
- **LangGraph Agent** - AI-powered root cause analysis
- **RAG System** - ChromaDB with SRE documentation
- **Dashboard** - Real-time monitoring & agent reasoning
- **Chaos Engine** - Controlled failure injection

## 📁 Project Structure

```
/Sentinell
├── BLUEPRINT.md              # Complete project vision
├── README.md                 # This file
├── docker-compose.yml        # Orchestration config
├── Makefile                  # Convenience commands
├── victim/                   # Microservices cluster
│   ├── frontend/            # Next.js UI
│   ├── product-api/         # FastAPI service
│   ├── payment-service/     # Node.js service
│   └── nginx/               # Reverse proxy config
├── agent/                    # (Coming) LangGraph agent
└── dashboard/               # (Coming) Admin panel
```

## 🎮 Makefile Commands

```bash
make help          # Show all available commands
make build         # Build all services
make up            # Start the cluster
make down          # Stop the cluster
make restart       # Restart the cluster
make logs          # View logs
make logs-follow   # Follow logs in real-time
make ps            # Show running containers
make health        # Check service health
make clean         # Remove everything (containers, volumes, images)
make dev           # Build + start (one command)
```

## 🔥 Failure Scenarios (For Demo)

The victim cluster will be intentionally broken to demonstrate Sentinell's healing capabilities:

### Scenario 1: Broken Nginx Config
- Chaos injects syntax error into nginx.conf
- Entire site returns 502 Bad Gateway
- **Sentinell:** Detects error, reads logs, patches config, reloads nginx

### Scenario 2: Memory Leak
- Python service leaks memory
- Container hits OOM
- **Sentinell:** Detects high RAM usage, identifies PID, restarts container

### Scenario 3: Port Conflict
- Rogue process grabs port 5432
- PostgreSQL fails to start
- **Sentinell:** Scans ports, kills rogue process, restarts Postgres

## 🛠️ Tech Stack

### Infrastructure
- Docker & Docker Compose

### Victim Services
- **Frontend:** Next.js 14 (App Router)
- **Backend:** FastAPI (Python), Express (Node.js)
- **Database:** PostgreSQL 15
- **Proxy:** Nginx

### Agent System (Coming)
- **Agent Framework:** LangGraph
- **Vector DB:** ChromaDB
- **API:** FastAPI
- **Container SDK:** Docker SDK for Python

### Dashboard (Coming)
- **Framework:** Next.js 14
- **Styling:** TailwindCSS + Shadcn/UI
- **Real-time:** WebSockets / SSE

## 🎤 Demo Flow

1. **Show working cluster** - Browse e-commerce site
2. **Trigger chaos** - Break nginx config
3. **System fails** - 502 error page
4. **Sentinell detects** - Dashboard shows agent reasoning
5. **Propose fix** - Show diff view
6. **Authorize repair** - Click button
7. **System healed** - Site back online

**Total demo time:** ~90 seconds
**Impact:** Judges lose their minds

## 📊 Service Health Checks

All services expose health endpoints:

```bash
curl http://localhost:8000/health    # Product API
curl http://localhost:3002/health    # Payment Service
curl http://localhost                # Frontend (via Nginx)
```

## 🚀 Development

### Adding New Services

1. Create service directory in `victim/`
2. Add Dockerfile
3. Update `docker-compose.yml`
4. Update nginx routing if needed
5. Rebuild: `make build && make up`

### Viewing Logs

```bash
# All services
make logs

# Specific service
docker-compose logs frontend
docker-compose logs -f product-api
```

## 🧪 Testing

```bash
# Check all services are running
make ps

# Verify health
make health

# Test API endpoints
curl http://localhost:8000/products
curl -X POST http://localhost:3002/charge \
  -H "Content-Type: application/json" \
  -d '{"amount":100,"currency":"USD","token":"tok_test"}'
```

## 🎯 Next Steps

1. ✅ Victim environment setup (DONE)
2. ⏳ Build Chaos Engine
3. ⏳ Implement Observer Node
4. ⏳ Build LangGraph Agent
5. ⏳ Create RAG system
6. ⏳ Build Dashboard
7. ⏳ Integrate Fish Audio (voice commands)

## 📝 License

Built for hackathon demonstration purposes.

## 🤝 Contributing

This is a hackathon project. Speed over perfection!

---

**Built with ❤️ for the future of autonomous operations**
