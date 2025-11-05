# Migration to Proper Strands Agent Framework

## Current State
We're importing Strands (`from strands import Agent, tool`) but not using it properly:
- ❌ Using custom `BaseSpecializedAgent` class instead of Strands `Agent`
- ❌ Manually calling Anthropic API instead of using Strands agent execution
- ✅ Using `@tool` decorator (correct!)
- ❌ Not using Strands system prompts pattern
- ❌ Not using Strands callback handlers

## Proper Strands Pattern (from docs)

```python
from strands import Agent, tool

# Define tools
@tool
def calculator(expression: str) -> str:
    """Calculate mathematical expressions"""
    # implementation
    pass

# Create agent with Strands
math_agent = Agent(
    system_prompt=MATH_ASSISTANT_SYSTEM_PROMPT,
    tools=[calculator],
    callback_handler=None  # or custom handler
)

# Use agent
response = math_agent("Solve x^2 + 5x + 6 = 0")
```

## What We Need to Change

### 1. Refactor BaseSpecializedAgent
Instead of:
```python
class BaseSpecializedAgent:
    def __init__(self, role: AgentRole):
        self.anthropic = AsyncAnthropic(...)  # ❌ Manual API calls
```

Should be:
```python
def create_code_agent(task_id: str) -> Agent:
    return Agent(
        system_prompt=CODE_AGENT_PROMPT,
        tools=[file_reader, file_writer, python_repl, ...],
        callback_handler=CustomCallbackHandler()
    )
```

### 2. Use Strands Multi-Agent Patterns
- **Tool-Agent Pattern**: Wrap agents as tools for orchestrator
- **Agent2Agent (A2A)**: For agent communication
- **Workflow Pattern**: For phase-based execution

### 3. System Prompts
Define clear system prompts for each agent role:
```python
CODE_AGENT_PROMPT = """
You are a specialized code agent...
Your capabilities include:
- Writing clean, well-documented code
- Debugging and fixing errors
- Installing dependencies
...
"""
```

### 4. Callback Handlers
Use Strands callback system for progress tracking:
```python
from strands.handlers import CallbackHandler

class ProgressCallbackHandler(CallbackHandler):
    def on_agent_start(self, agent_name: str):
        print(f"[{agent_name}] Starting...")
    
    def on_tool_start(self, tool_name: str):
        print(f"Using tool: {tool_name}")
```

## Migration Steps

1. ✅ **Keep current @tool decorators** - they're correct
2. **Create system prompts** for each agent role
3. **Refactor agents** to use Strands `Agent` class
4. **Implement callback handlers** for progress tracking
5. **Use Tool-Agent pattern** for orchestrator
6. **Test with Strands patterns** (Graph, Swarm, or Workflow)

## Benefits

- ✅ Proper Strands framework usage
- ✅ Better streaming and callbacks
- ✅ Cleaner architecture
- ✅ Easier debugging
- ✅ Community patterns and best practices
- ✅ Better integration with Strands ecosystem

## Next Steps

1. Create system prompt templates
2. Refactor one agent (CodeAgent) as proof of concept
3. Test the refactored agent
4. Apply pattern to all agents
5. Update orchestrator to use Tool-Agent pattern
