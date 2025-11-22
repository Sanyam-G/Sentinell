# Sentinell Chaos Engine 🔥

The villain of the demo. Intentionally breaks the victim cluster in realistic ways.

## Installation

```bash
cd chaos
pip install -r requirements.txt
```

## Usage

```bash
# Make executable
chmod +x chaos_engine.py

# Show help
./chaos_engine.py --help

# Check cluster status
./chaos_engine.py status

# Break nginx config (502 errors)
./chaos_engine.py break-config

# Cause memory leak
./chaos_engine.py leak-memory --size-mb 500

# Block port (prevent DB startup)
./chaos_engine.py block-port --port 5432 --duration 60

# Restore everything
./chaos_engine.py restore
```

## Scenarios

### 1. Break Config (Nginx)
Injects a syntax error into `nginx.conf` and attempts reload:
- **Impact:** 502 Bad Gateway on entire site
- **Fix:** Sentinell detects, patches config, reloads nginx

### 2. Memory Leak
Spawns a Python process that rapidly allocates memory:
- **Impact:** High RAM usage, potential OOM killer
- **Fix:** Sentinell detects high memory, restarts container

### 3. Port Blocker
Binds to port 5432 preventing PostgreSQL startup:
- **Impact:** Database fails to start
- **Fix:** Sentinell identifies rogue process, kills it, restarts DB

## Demo Flow

```bash
# 1. Start cluster
make up

# 2. Verify everything is healthy
./chaos_engine.py status

# 3. Break something
./chaos_engine.py break-config

# 4. Watch Sentinell detect and fix it
# (Observer → Agent → Repair)

# 5. Restore if needed
./chaos_engine.py restore
```
