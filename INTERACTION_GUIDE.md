# How to Interact with Strands Agents

There are multiple ways to interact with the Strands Autonomous Agent Platform:

## 🎯 Method 1: Command Line Interface (Recommended)

### Quick Start
```bash
source venv/bin/activate
python interact.py
```

This launches an interactive CLI where you can:
- Submit tasks in natural language
- Monitor agent progress in real-time
- View execution plans
- Check agent status
- Review results

### Example Session
```
🤖 Strands Agent Platform CLI
> What would you like the agents to build?

You: Create a REST API for a todo list with FastAPI

🗺️  Creating execution plan...
✅ Plan created: 8 phases, 3 agents, ~180 minutes

📋 Phases:
  1. Project setup (Code Agent)
  2. Database models (Code Agent)
  3. API endpoints (Code Agent)
  ...

🚀 Execute this plan? (yes/no): yes

⏳ Spawning agents...
✅ Code Agent spawned in sandbox_abc123
✅ QA Agent spawned in sandbox_def456
✅ Writer Agent spawned in sandbox_ghi789

🔄 Phase 1: Project setup (In Progress)
   Code Agent: Setting up FastAPI project structure...
   
✅ Phase 1: Complete
   Output: Created project structure with 5 files
   
🔄 Phase 2: Database models (In Progress)
...
```

---

## 🎯 Method 2: Python API

### Direct Integration

```python
from src.agents.meta_orchestrator import MetaOrchestrator
import asyncio

async def build_something():
    # Initialize
    orchestrator = MetaOrchestrator()
    await orchestrator.initialize()
    
    # Submit task
    task = """
    Create a simple calculator CLI app in Python
    with add, subtract, multiply, and divide functions
    """
    
    # Create plan
    plan = await orchestrator.orchestrate_task(
        task_description=task,
        project_id="my-project-123"
    )
    
    print(f"Plan: {len(plan.phases)} phases")
    
    # Execute
    results = await orchestrator.execute_plan(plan, "task-456")
    
    # Get results
    for phase_id, result in results.items():
        print(f"Phase {phase_id}: {result['status']}")

asyncio.run(build_something())
```

---

## 🎯 Method 3: File-Based Tasks

### Using Markdown Files

Create a task file (e.g., `my_task.md`):

```markdown
# Build a Weather Dashboard

Create a web dashboard that:
- Shows current weather for a city
- Displays 5-day forecast
- Has a search function
- Uses OpenWeather API
- Built with React + FastAPI

Tech stack: React, TypeScript, TailwindCSS, FastAPI
```

Then run:
```bash
python run_task.py my_task.md
```

---

## 🎯 Method 4: Watch Mode (Continuous)

Monitor a directory and auto-execute tasks:

```bash
python watch_tasks.py ./tasks/
```

Drop `.md` files into `./tasks/` and agents automatically:
1. Pick up the file
2. Create execution plan
3. Execute with appropriate agents
4. Save results to `./results/`

---

## 🎯 Method 5: Web Interface (Coming Soon)

A React-based dashboard for:
- Visual task submission
- Real-time agent monitoring
- Execution history
- Agent performance metrics
- Cost tracking

---

## 📊 Monitoring Agent Activity

### Real-Time Progress

```bash
# Terminal 1: Run your task
python interact.py

# Terminal 2: Monitor Redis messages
docker exec -it strands-redis redis-cli
> SUBSCRIBE agent:*

# Terminal 3: Watch agent logs
tail -f logs/agents.log
```

### Check Agent Status

```python
from src.coordination.messaging import CoordinationManager

async def check_agents():
    coord = CoordinationManager("task-123")
    await coord.initialize()
    
    # Get all active agents
    agents = await coord.get_active_agents()
    
    for agent in agents:
        print(f"Agent: {agent['role']}")
        print(f"Status: {agent['status']}")
        print(f"Current Phase: {agent['current_phase']}")
```

---

## 🔍 Viewing Results

### After Execution

Results are saved to:
- **Code**: MinIO bucket `strands-platform/code/`
- **Documents**: MinIO bucket `strands-platform/docs/`
- **Artifacts**: MinIO bucket `strands-platform/artifacts/`
- **Database**: PostgreSQL `tasks` and `activity_logs` tables

### Access Results

```bash
# Via MinIO Console
open http://localhost:9001
# Login: minioadmin / minioadmin

# Via CLI
python get_results.py task-123

# Via Python
from src.core.storage import StorageManager

storage = StorageManager()
results = await storage.download_task_results("task-123")
```

---

## 💬 Agent Communication

### Send Messages to Agents

```python
from src.coordination.messaging import CoordinationManager

async def talk_to_agent():
    coord = CoordinationManager("task-123")
    await coord.initialize()
    
    # Send message to specific agent
    await coord.send_message(
        from_agent="user",
        to_agent="code_agent_1",
        message_type="instruction",
        content={
            "instruction": "Add error handling to the API",
            "priority": "high"
        }
    )
    
    # Broadcast to all agents
    await coord.broadcast_message(
        from_agent="user",
        message_type="update",
        content={"message": "Please add more comments to your code"}
    )
```

### Listen to Agent Messages

```python
async def listen_to_agents():
    coord = CoordinationManager("task-123")
    await coord.initialize()
    
    # Subscribe to agent messages
    async for message in coord.subscribe_to_messages():
        print(f"From: {message['from_agent']}")
        print(f"Type: {message['message_type']}")
        print(f"Content: {message['content']}")
        
        # Respond if needed
        if message['message_type'] == 'help_request':
            await coord.send_message(
                from_agent="user",
                to_agent=message['from_agent'],
                message_type="help_response",
                content={"guidance": "Try using the requests library"}
            )
```

---

## 🎮 Interactive Commands

### In the CLI

```bash
# Task management
> submit <task>          # Submit a new task
> status <task_id>       # Check task status
> cancel <task_id>       # Cancel a running task
> retry <task_id>        # Retry a failed task

# Agent management
> agents                 # List all agents
> agent <agent_id>       # Get agent details
> pause <agent_id>       # Pause an agent
> resume <agent_id>      # Resume an agent

# Results
> results <task_id>      # View task results
> download <task_id>     # Download all artifacts
> logs <task_id>         # View execution logs

# System
> stats                  # Platform statistics
> costs                  # API cost breakdown
> health                 # System health check
> help                   # Show all commands
```

---

## 🔧 Advanced: Custom Agent Interactions

### Create Custom Agent Behaviors

```python
from src.agents.specialized_agents import BaseAgent
from strands import tool

class CustomAgent(BaseAgent):
    def __init__(self):
        super().__init__(role="custom")
    
    @tool
    async def custom_action(self, params: dict):
        """Custom agent action"""
        # Your logic here
        return {"result": "success"}
    
    async def execute_phase(self, phase: dict):
        """Custom phase execution"""
        # Override default behavior
        result = await self.custom_action(phase['params'])
        return result

# Register and use
orchestrator.register_agent(CustomAgent())
```

---

## 📱 WebSocket Real-Time Updates

### Connect to Live Updates

```javascript
// Frontend JavaScript
const ws = new WebSocket('ws://localhost:8000/ws/task-123');

ws.onmessage = (event) => {
    const update = JSON.parse(event.data);
    
    if (update.type === 'phase_complete') {
        console.log(`Phase ${update.phase_id} completed!`);
    }
    
    if (update.type === 'agent_message') {
        console.log(`${update.agent}: ${update.message}`);
    }
    
    if (update.type === 'error') {
        console.error(`Error: ${update.error}`);
    }
};
```

---

## 🎯 Best Practices

### 1. Clear Task Descriptions
```
❌ Bad: "Make a website"
✅ Good: "Create a portfolio website with React, 3 pages (Home, About, Projects), responsive design, and dark mode"
```

### 2. Specify Tech Stack
```
✅ Include: "Use Python 3.11, FastAPI, PostgreSQL, and Docker"
```

### 3. Define Success Criteria
```
✅ Include: "Must have 80%+ test coverage and pass all linting checks"
```

### 4. Set Constraints
```
✅ Include: "Keep it under 500 lines of code" or "Must complete in under 2 hours"
```

---

## 🚀 Quick Examples

### Example 1: Simple Script
```bash
python interact.py
> Create a Python script that fetches GitHub stars for a repo
```

### Example 2: Full Application
```bash
python interact.py
> Build a blog platform with user auth, posts, comments, and admin panel using Django
```

### Example 3: Data Analysis
```bash
python interact.py
> Analyze this CSV file and create visualizations of the top 10 trends
```

### Example 4: API Integration
```bash
python interact.py
> Create a Slack bot that posts daily weather updates for San Francisco
```

---

## 📞 Getting Help

### Agent Help Requests

Agents can request help from you or other agents:

```python
# Agent sends help request
await coord.request_help(
    agent_id="code_agent_1",
    issue="Not sure which library to use for PDF generation",
    context={"language": "python", "use_case": "invoice generation"}
)

# You receive notification and can respond
# Via CLI: help <request_id> "Use ReportLab library"
```

---

## 🎓 Learning from Agents

### View Agent Decisions

```bash
python explain_task.py task-123
```

Output:
```
📊 Task Analysis: task-123

🤔 Agent Decisions:
  • Chose FastAPI over Flask (reason: better async support)
  • Selected PostgreSQL over SQLite (reason: production requirements)
  • Added Redis caching (reason: performance optimization)

🛠️ Tools Created:
  • database_migrator: Automated schema migrations
  • api_validator: Input validation helper

📈 Performance:
  • Completed in 142 minutes (estimated 180)
  • 94% test coverage achieved
  • 0 critical issues found
```

---

## 💡 Pro Tips

1. **Start Small**: Test with simple tasks first
2. **Monitor Costs**: Check API usage regularly
3. **Review Plans**: Always review execution plans before running
4. **Save Successful Patterns**: The platform learns from successes
5. **Provide Feedback**: Help agents improve by rating results

---

**Ready to start?** Run `python interact.py` and describe what you want to build!
