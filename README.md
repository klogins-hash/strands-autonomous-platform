# Strands Autonomous Agent Platform

**Talk to your agents in natural language. They figure out the rest.**

An autonomous multi-agent platform where you describe what you want, and AI agents build it. Works from terminal or Claude Desktop via MCP.

## 🚀 Quick Start (30 seconds)

```bash
# 1. Start services
./scripts/start-services.sh

# 2. Activate environment
source venv/bin/activate

# 3. Chat with your agents
python chat.py
```

Then just describe what you want:
```
💬 You: Create a REST API for a todo list with FastAPI

🤔 Thinking...
✅ Plan: 6 phases, 2 agents, ~5 minutes
🚀 Execute? yes
✅ Complete! Your API is ready.
```

## 💬 Two Ways to Interact

### 1. Terminal Chat (Simplest)
```bash
python chat.py
```
Natural language interface - just describe what you want!

### 2. Claude Desktop (Most Powerful)
Add MCP integration (2 min setup) and chat with your agents through Claude!

See `MCP_SETUP.md` for setup instructions.

## ⚡ Realistic Speed

AI agents work **fast** - seconds to minutes, not hours:
- Simple script: 30 sec - 2 min
- REST API: 2-5 min
- Full web app: 5-15 min
- Complex system: 15-30 min

## 🎯 Overview

This is an autonomous agent platform built with [Strands Agents](https://github.com/strands-agents/strands) that creates self-organizing AI agent teams. Users describe complex goals in natural language, and the system spawns specialized agents that autonomously decompose tasks, build required tools, coordinate execution, learn from successes, and deliver production-ready results.

## ✨ Key Features

### 🤖 Autonomous Agent Team
- **Meta-Orchestrator**: Central intelligence that decomposes tasks and forms optimal agent teams
- **Specialized Agents**: Research, Code, Writer, Designer, Analyst, QA, and Tool Builder agents
- **Self-Organization**: Agents autonomously determine roles, responsibilities, and collaboration patterns

### 🛠️ Tool Self-Generation
- Agents can build new tools when they encounter missing capabilities
- Automatic testing and validation of generated tools
- Tool persistence and reuse across tasks
- Learning from successful tool implementations

### 🔄 Multi-Agent Coordination
- Redis-based pub/sub messaging between agents
- Shared state management for collaboration
- Synchronization points for coordinated actions
- Agent-to-agent handoffs and task delegation

### 🔧 Autonomous Error Recovery
- Automatic detection and classification of errors
- Multiple recovery strategies (retry, alternative approach, simplify, request help)
- Learning from successful recoveries
- Escalation to user only after autonomous attempts fail

### 🧠 Learning & Persistence
- Automatic saving of successful agents and tools
- Performance tracking and quality scoring
- Semantic search for similar past executions
- Recommendations based on historical success

### 🏖️ E2B Sandbox Integration
- Isolated execution environments for each agent
- Full Ubuntu 24.04 with Python 3.11+ and Node.js 18+
- Screen streaming and terminal output
- Resource limits and auto-cleanup

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 16+ with pgvector extension
- Redis 7+
- API Keys:
  - OpenAI API key (for embeddings)
  - Anthropic API key (for agent reasoning)
  - E2B API key (for sandboxes)

### Installation

1. **Clone the repository**
```bash
cd /Users/franksimpson/CascadeProjects/strands-autonomous-platform
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your API keys (already configured with provided keys)
```

4. **Set up database**
```bash
# Create PostgreSQL database
createdb strands_platform

# Enable pgvector extension
psql strands_platform -c "CREATE EXTENSION vector;"

# Run migrations (when implemented)
# alembic upgrade head
```

5. **Start Redis**
```bash
redis-server
```

### Running the Autonomous Agent Team

**Launch the autonomous agent team to build the platform:**

```bash
python main.py
```

This will:
1. Initialize the Meta-Orchestrator and all agent systems
2. Read the Product Requirements Document
3. Create an execution plan with phases and agent assignments
4. Spawn specialized agents to execute each phase
5. Coordinate multi-agent collaboration
6. Build tools as needed
7. Handle errors autonomously
8. Learn from the execution
9. Deliver the completed platform

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AUTONOMOUS AGENT TEAM                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           Meta-Orchestrator (The Brain)              │   │
│  │  - Task decomposition                                │   │
│  │  - Agent team formation                              │   │
│  │  - Execution monitoring                              │   │
│  │  - Dynamic replanning                                │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Specialized Agent Pool                  │   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐        │   │
│  │  │Research│ │  Code  │ │ Writer │ │Designer│        │   │
│  │  └────────┘ └────────┘ └────────┘ └────────┘        │   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐                   │   │
│  │  │Analyst │ │   QA   │ │  Tool  │                   │   │
│  │  │        │ │        │ │ Builder│                   │   │
│  │  └────────┘ └────────┘ └────────┘                   │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │          Coordination & Recovery Systems             │   │
│  │  - Multi-agent messaging (Redis pub/sub)            │   │
│  │  - Shared state management                          │   │
│  │  - Autonomous error recovery                        │   │
│  │  - Learning & persistence                           │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              E2B Sandbox Manager                     │   │
│  │  - Isolated execution environments                  │   │
│  │  - Screen streaming                                 │   │
│  │  - Resource management                              │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
strands-autonomous-platform/
├── main.py                          # Main entry point
├── requirements.txt                 # Python dependencies
├── .env                            # Environment configuration
├── README.md                       # This file
│
├── src/
│   ├── core/
│   │   ├── config.py              # Configuration management
│   │   └── database.py            # Database setup
│   │
│   ├── models/
│   │   ├── schemas.py             # Pydantic models
│   │   └── database.py            # SQLAlchemy models
│   │
│   ├── agents/
│   │   ├── meta_orchestrator.py   # Central orchestration
│   │   ├── specialized_agents.py  # Domain-specific agents
│   │   ├── tool_builder.py        # Autonomous tool creation
│   │   └── sandbox_manager.py     # E2B sandbox management
│   │
│   ├── coordination/
│   │   ├── messaging.py           # Agent communication
│   │   └── autonomous_recovery.py # Error recovery system
│   │
│   └── learning/
│       └── persistence.py         # Agent/tool learning
│
└── docs/
    └── PRD.md                     # Product Requirements Document
```

## 🎮 Usage Examples

### Example 1: Build a Web Application

```python
from src.agents.meta_orchestrator import MetaOrchestrator

orchestrator = MetaOrchestrator()
await orchestrator.initialize()

# Describe what you want
task = """
Build a todo list web application with:
- React frontend with modern UI
- FastAPI backend with PostgreSQL
- User authentication
- Real-time updates
- Mobile responsive design
"""

# Let the agents build it
plan = await orchestrator.orchestrate_task(task, project_id)
results = await orchestrator.execute_plan(plan, task_id)
```

### Example 2: Research and Analysis

```python
task = """
Research the top 5 CRM tools in 2024:
- Compare features and pricing
- Analyze user reviews
- Create comparison table
- Provide recommendations
"""

# Agents will autonomously:
# 1. Research each CRM tool
# 2. Extract and analyze data
# 3. Synthesize findings
# 4. Generate comprehensive report
```

### Example 3: Complex Multi-Phase Project

```python
task = """
Build a complete e-commerce platform with:
- Product catalog with search
- Shopping cart and checkout
- Payment integration (Stripe)
- Admin dashboard
- Email notifications
- Analytics tracking
"""

# The orchestrator will:
# 1. Decompose into phases (design, backend, frontend, integration, testing)
# 2. Assign specialized agents to each phase
# 3. Coordinate parallel and sequential execution
# 4. Build custom tools as needed
# 5. Handle errors autonomously
# 6. Deliver production-ready code
```

## 🧪 Agent Capabilities

### Research Agent
- Web search and data extraction
- Source verification and citation
- Information synthesis
- Fact-checking

### Code Agent
- Software development (Python, JavaScript, TypeScript)
- Code review and optimization
- Testing and debugging
- Documentation generation

### Writer Agent
- Content creation and editing
- Technical documentation
- Report generation
- Copywriting

### Tool Builder Agent
- Autonomous tool creation
- Tool testing and validation
- Tool documentation
- Tool persistence

### Analyst Agent
- Data analysis and visualization
- Statistical modeling
- Insight generation
- Report creation

### QA Agent
- Testing and quality assurance
- Bug detection and reporting
- Validation and verification
- Performance testing

## 🔐 Security & Best Practices

- **API Keys**: Never commit API keys to version control
- **Sandboxes**: All code execution happens in isolated E2B sandboxes
- **Resource Limits**: Automatic limits on concurrent agents and execution time
- **Error Handling**: Comprehensive error recovery with escalation
- **Logging**: Full activity logging for monitoring and debugging

## 📊 Monitoring & Observability

The platform provides real-time visibility into:
- Agent status and progress
- Inter-agent communication
- Tool creation and usage
- Error detection and recovery
- Performance metrics
- Learning insights

## 🤝 Contributing

This is an autonomous agent platform that builds itself! The agents can:
- Identify missing features
- Design and implement improvements
- Test and validate changes
- Document new capabilities
- Learn from each iteration

## 📝 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

Built with:
- [Strands Agents](https://github.com/strands-agents/strands) - Multi-agent framework
- [E2B](https://e2b.dev/) - Sandboxed execution environments
- [Anthropic Claude](https://www.anthropic.com/) - Agent reasoning
- [OpenAI](https://openai.com/) - Embeddings and additional AI capabilities

## 📞 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check the documentation
- Review the PRD for detailed specifications

---

**Built by autonomous AI agents, for autonomous AI agents** 🤖✨
