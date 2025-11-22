# Sentinell Victim Environment

This directory contains the "victim" microservices cluster that Sentinell will monitor and self-heal.

## Services

### 1. Frontend (Next.js)
- **Port:** 3000 (internal)
- **Tech:** Next.js 14 App Router
- **Purpose:** E-commerce UI displaying products and checkout
- **Location:** `victim/frontend/`

### 2. Product API (FastAPI)
- **Port:** 8000 (internal)
- **Tech:** Python FastAPI
- **Endpoints:**
  - `GET /products` - List all products
  - `GET /products/{id}` - Get single product
  - `GET /health` - Health check
- **Location:** `victim/product-api/`

### 3. Payment Service (Node.js)
- **Port:** 3002 (internal)
- **Tech:** Node.js + Express
- **Endpoints:**
  - `POST /charge` - Process payment
  - `GET /health` - Health check
- **Location:** `victim/payment-service/`

### 4. PostgreSQL Database
- **Port:** 5432
- **Credentials:** admin/admin123
- **Database:** products_db

### 5. Nginx Reverse Proxy
- **Port:** 80
- **Purpose:** Routes traffic to appropriate services
- **Config:** `victim/nginx/nginx.conf`

## Architecture

```
[User Browser] → [Nginx :80] → [Frontend :3000]
                        ↓
                   [Product API :8000]
                        ↓
                   [Payment Service :3002]
                        ↓
                   [PostgreSQL :5432]
```

## Quick Start

See the main project Makefile for commands:
```bash
make build    # Build all services
make up       # Start cluster
make down     # Stop cluster
make health   # Check service health
```

## Intentional Failure Scenarios

These services are designed to be broken by the Chaos Engine:

1. **Nginx Config Error** - Syntax errors causing 502
2. **Memory Leak** - Resource exhaustion
3. **Port Conflict** - Service startup failures
4. **Container Crashes** - Unexpected terminations

Sentinell will detect and fix these automatically.
