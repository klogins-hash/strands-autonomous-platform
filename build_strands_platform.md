# Build Strands Autonomous Agent Platform - Full MVP

## Project Overview

Build a complete autonomous AI agent platform where users describe what they want in natural language, and self-organizing agent teams execute tasks while providing real-time visualization of their work.

## Core Requirements

### 1. Frontend (React + TypeScript)

**Chat Interface:**
- Natural language chat interface (no forms)
- Markdown support with syntax highlighting
- WebSocket for real-time updates
- Conversation history with timestamps
- Mobile-responsive design
- Autosave conversation state

**Real-Time Visualization:**
- React Flow canvas showing agent graph
- Custom agent nodes with status (idle/active/done/error)
- Animated edges showing data flow between agents
- Color-coded status indicators
- Click nodes for details
- Auto-layout with dagre algorithm
- Mini-map and zoom controls
- Dark mode theme
- Smooth animations with Framer Motion

**Agent Screens:**
- Grid view of active agent E2B sandbox screens
- Real-time screen streaming (1-2 FPS)
- Terminal output streaming
- Click to focus/expand agent screen
- Show agent name, role, and current task

**Tech Stack:**
- React 18+ with TypeScript
- Vite for build
- TailwindCSS + shadcn/ui components
- React Flow v11+ for visualization
- Socket.io-client for WebSocket
- Zustand for state management
- react-markdown for rendering
- Framer Motion for animations

### 2. Backend (FastAPI + Python)

**API Endpoints:**
- POST /api/chat - Submit user message
- POST /api/orchestrate - Create execution plan
- POST /api/execute - Start execution
- GET /api/status/{task_id} - Get task status
- GET /api/results/{task_id} - Get results
- WebSocket /ws - Real-time updates

**Meta-Orchestrator:**
- Parse natural language goals
- Decompose into executable phases
- Determine optimal agent team (1-10 agents)
- Create execution plan with dependencies
- Identify parallel vs sequential tasks
- Monitor execution in real-time
- Handle errors and recovery
- Synthesize results from multiple agents

**Agent System:**
- 7 specialized agent types: Research, Code, Writer, Designer, Analyst, QA, Tool Builder
- Each agent gets isolated E2B sandbox
- Agent-to-agent communication via Redis pub/sub
- Progress tracking per agent
- Lifecycle management (spawn, execute, terminate)

**Database (PostgreSQL + pgvector):**
- Store execution plans and results
- Vector embeddings for similar task search
- Agent performance metrics
- Tool library (successful tools persist)
- Conversation history

**Tech Stack:**
- FastAPI with async/await
- Strands SDK for agents
- E2B SDK for sandboxes
- Claude Sonnet 4 for orchestration
- Redis for pub/sub messaging
- PostgreSQL + pgvector
- MinIO for file storage
- Socket.io for WebSocket

### 3. E2B Sandbox Integration

**Per-Agent Sandboxes:**
- Ubuntu 24.04 base
- Python 3.11+ and Node.js 18+
- Package installation (pip, npm)
- File system access
- Web browsing capability
- Screen streaming via VNC/screenshot API
- Terminal output streaming
- Auto-terminate after 1 hour or completion
- Resource limits: 2 CPU, 4GB RAM

**Streaming:**
- Screen capture at 1-2 FPS
- Terminal output via WebSocket
- Real-time to frontend

### 4. Key Features

**Autonomous Execution:**
- Self-organizing agent teams
- Parallel execution for independent tasks
- Sequential execution for dependencies
- Automatic tool generation when needed
- Error recovery and retry logic
- Learning from successful executions

**Real-Time Transparency:**
- Watch agents work in their sandboxes
- See agent reasoning and decisions
- View data flowing between agents
- Monitor progress per agent
- See terminal output live

**Learning System:**
- Save successful execution plans
- Persist useful tools to library
- Vector search for similar past tasks
- Reuse proven approaches
- Track agent performance metrics

## MVP Scope

**Must Have:**
- Chat interface with natural language input
- Meta-orchestrator that creates execution plans
- 3-5 agent types working (Code, Research, Writer minimum)
- E2B sandbox per agent with screen streaming
- React Flow visualization of agent graph
- Real-time status updates via WebSocket
- Basic error handling and recovery
- PostgreSQL for persistence
- Redis for messaging

**Nice to Have (Post-MVP):**
- All 7 agent types
- Advanced tool generation
- Sophisticated learning system
- Agent performance analytics
- Cost tracking and limits
- User authentication
- Saved project templates
- Export results in multiple formats

## Technical Architecture

```
Frontend (React + TypeScript)
├── Chat Interface
├── React Flow Visualization
├── Agent Screen Grid
└── WebSocket Client

Backend (FastAPI + Python)
├── API Routes
├── Meta-Orchestrator (Claude Sonnet 4)
├── Agent Manager (Strands SDK)
├── E2B Sandbox Manager
├── Redis Pub/Sub
├── PostgreSQL + pgvector
└── WebSocket Server

Infrastructure
├── Docker Compose
├── PostgreSQL
├── Redis
├── MinIO
└── E2B Cloud Sandboxes
```

## File Structure

```
strands-platform/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Chat.tsx
│   │   │   ├── AgentGraph.tsx
│   │   │   ├── AgentScreens.tsx
│   │   │   └── ...
│   │   ├── hooks/
│   │   ├── stores/
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
├── backend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── routes.py
│   │   │   └── websocket.py
│   │   ├── orchestrator/
│   │   │   └── meta_orchestrator.py
│   │   ├── agents/
│   │   │   ├── base_agent.py
│   │   │   └── specialized_agents.py
│   │   ├── sandbox/
│   │   │   └── e2b_manager.py
│   │   ├── database/
│   │   │   └── models.py
│   │   └── main.py
│   ├── requirements.txt
│   └── .env
├── docker-compose.yml
└── README.md
```

## Success Criteria

**The "Magic Moment" Test:**
1. User types: "Analyze the top 3 CRM tools and create a comparison table"
2. System creates plan with 4 agents (3 research + 1 writer)
3. User sees agents spawn in React Flow graph
4. User watches agent screens as they work
5. 2-3 minutes later: Polished comparison table delivered
6. User thinks: "Holy shit, it actually worked"

**Technical Success:**
- End-to-end flow works: chat → plan → execute → results
- 3+ agents can work in parallel
- Real-time visualization updates smoothly
- Agent screens stream at 1+ FPS
- System completes 80%+ of test tasks successfully
- Response time: Plan in <10s, execution in <5 min for simple tasks

## Development Approach

**Phase 1: Core Infrastructure (Week 1)**
- Set up FastAPI backend with basic routes
- Set up React frontend with chat interface
- PostgreSQL + Redis + MinIO via Docker
- Basic WebSocket connection
- Simple meta-orchestrator (single agent)

**Phase 2: Agent System (Week 2)**
- Integrate Strands SDK
- Implement E2B sandbox manager
- Create 3 agent types (Code, Research, Writer)
- Agent spawning and lifecycle
- Redis pub/sub messaging

**Phase 3: Visualization (Week 3)**
- React Flow integration
- Custom agent nodes
- Real-time graph updates
- Agent screen streaming
- Terminal output display

**Phase 4: Polish & Testing (Week 4)**
- Error handling and recovery
- Learning system (basic)
- Performance optimization
- End-to-end testing
- Documentation

## Notes

- Use existing strands-autonomous-platform codebase as foundation
- Focus on MVP features first
- Prioritize "magic moments" over edge cases
- Make it beautiful and mesmerizing to watch
- Optimize for ADHD-friendly UX (instant feedback, visual progress)

## Deliverables

1. Working full-stack application
2. Docker Compose setup for local development
3. README with setup instructions
4. Basic documentation
5. Demo video showing the "magic moment"
