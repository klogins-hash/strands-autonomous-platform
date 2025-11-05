# Quick Start - Talk to Your Agents

## 🚀 Start Chatting in 3 Steps

### 1. Start Services
```bash
./scripts/start-services.sh
```

### 2. Activate Environment
```bash
source venv/bin/activate
```

### 3. Start Chatting
```bash
python chat.py
```

That's it! Now just describe what you want in plain English.

---

## 💬 Example Conversation

```
🤖 Initializing Strands Agents...
✅ Ready!

╔══════════════════════════════════════════════════════════════════════════════╗
║                    STRANDS AUTONOMOUS AGENTS                                 ║
║              Just tell me what you want to build!                            ║
╚══════════════════════════════════════════════════════════════════════════════╝

────────────────────────────────────────────────────────────────────────────────

💬 You: Create a simple REST API for a todo list with FastAPI

🤔 Thinking about: "Create a simple REST API for a todo list with FastAPI"

⏳ Creating execution plan...

✅ Plan Created!
================================================================================

📊 Overview:
   • 8 phases
   • 3 agents needed
   • ~180 minutes estimated

📋 Execution Plan:

   1. Project Setup
      Agent: CODE
      Time: ~20 min
      Output: Project structure with dependencies

   2. Database Models
      Agent: CODE
      Time: ~30 min
      Output: SQLAlchemy models for todos

   3. API Endpoints
      Agent: CODE
      Time: ~45 min
      Output: CRUD endpoints

   ... (more phases)

👥 Agent Team:
   • CODE Agent
   • QA Agent
   • WRITER Agent

================================================================================

🚀 Execute this plan? (yes/no): yes

⏳ Starting execution...
   (This will spawn agents in E2B sandboxes)

🔄 Spawning agents...
✅ Code Agent ready in sandbox_abc123
✅ QA Agent ready in sandbox_def456
✅ Writer Agent ready in sandbox_ghi789

🔄 Phase 1: Project Setup (In Progress)
   Code Agent: Creating FastAPI project structure...

✅ Phase 1: Complete
   Created 8 files, installed 12 dependencies

... (execution continues)

================================================================================
✅ EXECUTION COMPLETE!
================================================================================

📊 Results:
   • Phase 1: completed
   • Phase 2: completed
   • Phase 3: completed
   ... (all phases)

💾 Task ID: abc123-def456-ghi789
   Use this ID to retrieve results later

────────────────────────────────────────────────────────────────────────────────

💬 You: 
```

---

## 🎯 What Can You Ask For?

### Web Applications
```
"Build a blog platform with user authentication using Django"
"Create a real-time chat app with WebSockets"
"Make a portfolio website with React and TailwindCSS"
```

### APIs & Backend
```
"Create a REST API for managing inventory with FastAPI"
"Build a GraphQL API for a social media app"
"Make a webhook handler for Stripe payments"
```

### Scripts & Tools
```
"Write a Python script to analyze CSV files and generate reports"
"Create a CLI tool for managing Docker containers"
"Build a web scraper for news articles"
```

### Data & Analysis
```
"Analyze this sales data and create visualizations"
"Build a data pipeline from CSV to PostgreSQL"
"Create a dashboard showing real-time metrics"
```

### Bots & Automation
```
"Make a Discord bot that posts daily weather updates"
"Create a Slack bot for team standup reminders"
"Build a Twitter bot that shares tech news"
```

---

## 💡 Tips for Best Results

### ✅ Good Requests
- **Specific**: "Create a FastAPI todo list with PostgreSQL and JWT auth"
- **Clear deliverables**: "Build a CLI tool that converts CSV to JSON"
- **Tech stack mentioned**: "Make a React dashboard with real-time updates"

### ❌ Vague Requests
- "Make something cool"
- "Build a website"
- "Do some coding"

### 🎯 Pro Tips

1. **Be Specific**: The more details, the better the plan
2. **Mention Tech**: Specify frameworks/languages if you have preferences
3. **Set Constraints**: "Keep it under 500 lines" or "Must be production-ready"
4. **Review Plans**: Always review before executing
5. **Start Small**: Test with simple tasks first

---

## 🔧 Commands

While chatting, you can use:

- **help** - Show available commands
- **status** - Check platform status
- **quit** or **exit** - Stop chatting

---

## 📊 Monitoring Execution

### Watch Agent Activity
Open a second terminal:
```bash
# Watch Redis messages
docker exec -it strands-redis redis-cli
> SUBSCRIBE agent:*

# Or watch logs
tail -f logs/agents.log
```

### Check Results
After execution:
```bash
# View in MinIO Console
open http://localhost:9001
# Login: minioadmin / minioadmin

# Or use the task ID
python get_results.py <task-id>
```

---

## 🚨 Troubleshooting

### Services Not Running
```bash
./scripts/stop-services.sh
./scripts/start-services.sh
```

### E2B Errors
Make sure your E2B API key is set in `.env`:
```bash
E2B_API_KEY=your_key_here
```

### Database Errors
Reset the database:
```bash
docker-compose down -v
docker-compose up -d
```

---

## 🎓 Example Sessions

### Session 1: Quick Script
```
💬 You: Write a Python script that fetches GitHub stars for a repo

✅ Plan: 3 phases, 1 agent, ~25 minutes
🚀 Execute? yes

✅ Complete! Created github_stars.py with requests library
```

### Session 2: Full Application
```
💬 You: Build a task management API with FastAPI, PostgreSQL, and JWT auth

✅ Plan: 12 phases, 3 agents, ~240 minutes
🚀 Execute? yes

✅ Complete! Full API with tests, docs, and deployment config
```

### Session 3: Data Analysis
```
💬 You: Analyze this CSV file and create visualizations of top trends

✅ Plan: 5 phases, 2 agents, ~45 minutes
🚀 Execute? yes

✅ Complete! Analysis report with 5 charts and insights
```

---

## 🎉 You're Ready!

Just run:
```bash
python chat.py
```

And start describing what you want to build. The agents will handle the rest!

---

**Need more help?** Check out:
- `INTERACTION_GUIDE.md` - Detailed interaction methods
- `STATUS.md` - Platform capabilities
- `RECOMMENDATIONS.md` - Best practices and tips
