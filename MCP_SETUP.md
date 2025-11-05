# MCP Integration - Chat with Your Agents from Claude

## 🎯 What This Does

The MCP (Model Context Protocol) server lets **Claude Desktop** (or any MCP client) directly interact with your autonomous agents!

### You can:
- Ask Claude to submit tasks to your agents
- Have Claude check task status
- Let Claude execute plans
- Query available agents

### Example:
```
You: "Claude, ask my agents to build a todo API"

Claude: *uses submit_task tool*
"I've submitted the task to your agents. They created a plan with 6 phases 
using the Code and QA agents. Estimated time: 15 minutes. 
Task ID: abc-123. Would you like me to execute it?"

You: "Yes, execute it"

Claude: *uses execute_task tool*
"The agents are now building your todo API..."
```

---

## 🚀 Setup (2 minutes)

### 1. Add to Claude Desktop Config

Edit your Claude Desktop MCP config:
```bash
# Mac
code ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Or manually open:
# ~/Library/Application Support/Claude/claude_desktop_config.json
```

Add this:
```json
{
  "mcpServers": {
    "strands-agents": {
      "command": "python",
      "args": [
        "/Users/franksimpson/CascadeProjects/strands-autonomous-platform/mcp_server.py"
      ],
      "env": {
        "PYTHONPATH": "/Users/franksimpson/CascadeProjects/strands-autonomous-platform",
        "PATH": "/Users/franksimpson/CascadeProjects/strands-autonomous-platform/venv/bin:/usr/local/bin:/usr/bin:/bin"
      }
    }
  }
}
```

### 2. Restart Claude Desktop

Close and reopen Claude Desktop.

### 3. Test It

In Claude Desktop, type:
```
List my available agents
```

Claude should use the `list_agents` tool and show you all 7 agents!

---

## 💬 How to Use

### Submit a Task
```
You: "Submit a task to build a FastAPI todo list"

Claude: *uses submit_task*
Returns: Plan with phases, agents, estimated time
```

### Execute a Task
```
You: "Execute task abc-123"

Claude: *uses execute_task*
Returns: Execution status and results
```

### Check Status
```
You: "What's the status of task abc-123?"

Claude: *uses get_task_status*
Returns: Current status (planned/executing/completed/failed)
```

### List Agents
```
You: "What agents do I have available?"

Claude: *uses list_agents*
Returns: All 7 specialized agents
```

---

## 🎯 Real Examples

### Example 1: Quick Script
```
You: Ask my agents to create a Python script that scrapes Hacker News

Claude: I'll submit that task to your agents.
*uses submit_task*

Your agents have created a plan:
- 4 phases
- Code and QA agents
- Estimated: 8 minutes
- Task ID: task-001

Would you like me to execute it?

You: Yes

Claude: *uses execute_task*
Executing... The agents are working on it now.
```

### Example 2: Full Application
```
You: Have my agents build a blog platform with Django

Claude: *submits task*

Plan created:
- 12 phases
- Code, QA, and Writer agents
- Estimated: 45 minutes
- Includes: models, views, templates, tests, docs

Execute now?

You: Yes, go ahead

Claude: *executes*
Your agents are building the blog platform...
```

---

## 🔧 Available Tools

Claude can use these tools:

### 1. `submit_task`
- **Input**: Task description (natural language)
- **Output**: Execution plan with task ID
- **Example**: "Create a REST API for managing tasks"

### 2. `execute_task`
- **Input**: Task ID
- **Output**: Execution status and results
- **Example**: task-abc-123

### 3. `get_task_status`
- **Input**: Task ID
- **Output**: Current status
- **Example**: task-abc-123

### 4. `list_agents`
- **Input**: None
- **Output**: All available agents
- **Example**: Shows 7 specialized agents

---

## 💡 Pro Tips

### 1. Let Claude Handle the Details
```
❌ Don't: "Submit task abc with parameters xyz"
✅ Do: "Ask my agents to build a todo API"
```

Claude will format the request properly!

### 2. Chain Operations
```
You: "Submit and execute a task to create a web scraper"

Claude will:
1. Submit the task
2. Show you the plan
3. Ask if you want to execute
4. Execute if you confirm
```

### 3. Check Progress
```
You: "What's happening with my last task?"

Claude: *checks status*
"Task task-123 is currently executing, in phase 3 of 5"
```

---

## 🚨 Troubleshooting

### Claude doesn't see the tools
1. Check config file path is correct
2. Restart Claude Desktop
3. Check Python path in config

### "Command not found" error
Add full Python path:
```json
"command": "/Users/franksimpson/CascadeProjects/strands-autonomous-platform/venv/bin/python"
```

### Services not running
```bash
./scripts/start-services.sh
```

---

## 🎓 Advanced: Use from Code

You can also use the MCP server programmatically:

```python
import json
import subprocess

# Start MCP server
process = subprocess.Popen(
    ['python', 'mcp_server.py'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True
)

# Submit task
request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "submit_task",
        "arguments": {
            "task_description": "Create a todo API"
        }
    }
}

process.stdin.write(json.dumps(request) + "\n")
process.stdin.flush()

response = json.loads(process.stdout.readline())
print(response)
```

---

## 🎉 Benefits

### For You:
- Natural language interface through Claude
- No need to remember commands
- Claude handles formatting
- Conversational workflow

### For Claude:
- Direct access to your agents
- Can submit and monitor tasks
- Can help you build things
- Integrated into conversation

---

## 📚 Next Steps

1. **Test it**: Ask Claude to list your agents
2. **Submit a task**: Have Claude create something simple
3. **Monitor**: Watch the agents work
4. **Iterate**: Refine based on results

**Ready?** Restart Claude Desktop and try:
```
"List my available autonomous agents"
```

🚀 **Your agents are now accessible from Claude!**
