# Sentinell - AI-Powered SRE Platform

## Running the Full Stack

You now have 4 processes to run:

### 1. Landing Page (Next.js)
```bash
cd landing
npm run dev
```
Access at: http://localhost:3000

### 2. Dashboard (Vite + React)
```bash
cd frontend  
npm run dev
```
Access at: http://localhost:5173

### 3. Backend API (FastAPI)
```bash
cd backend
source ../.venv/bin/activate
python3 app.py
```
Running on: http://localhost:8000

### 4. Background Worker
```bash
cd backend
source ../.venv/bin/activate
python3 worker.py
```

## Features

### Landing Page
- Modern glassmorphism design
- Animated gradient backgrounds
- Dark/Light theme toggle
- Responsive layout
- Direct link to dashboard

### Dashboard
- Real-time incident monitoring
- AI agent reasoning stream
- Light/Dark theme support
- Slack & log integration
- Auto-polling repository health
- Manual incident creation
- Pull request automation

## Theme System

Both landing page and dashboard support light/dark themes with smooth transitions. Theme preference syncs with system settings automatically.

## Architecture

- **Landing**: Next.js 15 + TypeScript + Tailwind CSS
- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS
- **Backend**: FastAPI + SQLModel + SQLite
- **Agent**: LangGraph + Claude Sonnet 4
- **Vector DB**: Pinecone for codebase search

## Quick Start

1. Install dependencies:
```bash
# Landing
cd landing && npm install

# Frontend  
cd ../frontend && npm install

# Backend
cd ../backend && pip install -r requirements.txt
```

2. Configure `.env` file in root with your API keys

3. Start all services (see commands above)

4. Visit http://localhost:3000 for landing page

5. Click "Launch Dashboard" to access the ops console at http://localhost:5173
