# Phase 1: Foundation & Core Infrastructure

## Goal
Set up the basic infrastructure and get a minimal working system where a user can chat with the platform and see a simple agent execute a task.

## Scope
Build the absolute minimum to prove the concept works end-to-end.

## Deliverables

### 1. Backend Foundation (FastAPI)
- Basic FastAPI app with CORS
- Health check endpoint: GET /health
- Chat endpoint: POST /api/chat
- Simple orchestrator endpoint: POST /api/orchestrate
- Environment configuration with pydantic-settings
- Basic error handling

### 2. Frontend Foundation (React + Vite)
- Vite + React + TypeScript setup
- TailwindCSS + shadcn/ui installed
- Basic layout with header
- Simple chat interface component
- Message display with markdown support
- Input field with send button
- Dark mode theme

### 3. Database Setup
- Docker Compose with PostgreSQL
- Basic database models:
  - Tasks table (id, description, status, created_at)
  - Messages table (id, task_id, role, content, created_at)
- Alembic migrations setup
- Database connection in FastAPI

### 4. Simple Agent Test
- Single Code agent that can execute one simple task
- Use existing meta_orchestrator.py
- Test: "Create a Python script that prints hello world"
- Agent creates the file
- Returns result to user

### 5. Docker Infrastructure
- docker-compose.yml with:
  - PostgreSQL
  - Redis (for future use)
  - Backend service
  - Frontend service (dev mode)

## Success Criteria
- User can open http://localhost:3000
- User can type a message in chat
- Message sends to backend
- Backend creates simple plan
- Single agent executes task
- Result displays in chat
- All in under 5 minutes of execution time

## File Structure
```
strands-platform/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Chat.tsx
│   │   │   └── MessageList.tsx
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models.py
│   │   └── routes.py
│   ├── requirements.txt
│   └── .env
├── docker-compose.yml
└── README.md
```

## Technical Details

### Backend Stack
- FastAPI 0.104+
- SQLAlchemy 2.0+ (async)
- Pydantic v2
- Python 3.11+

### Frontend Stack
- React 18
- TypeScript 5
- Vite 5
- TailwindCSS 3
- shadcn/ui components

### API Endpoints
```
POST /api/chat
{
  "message": "Create a hello world script"
}

Response:
{
  "task_id": "uuid",
  "status": "processing",
  "message": "Creating execution plan..."
}

POST /api/orchestrate
{
  "task_description": "Create a hello world script"
}

Response:
{
  "plan": {
    "phases": [...],
    "agents": [...],
    "estimated_duration": 5
  }
}
```

## Implementation Notes
- Use existing strands-autonomous-platform backend code as base
- Keep it simple - no WebSocket yet (polling is fine)
- No E2B sandboxes yet - agents run locally
- No React Flow visualization yet - just chat
- Focus on proving the core flow works

## Time Estimate
- Setup: 10 minutes
- Backend: 15 minutes
- Frontend: 15 minutes
- Integration: 10 minutes
- Testing: 10 minutes
**Total: ~1 hour**
