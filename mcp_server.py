#!/usr/bin/env python3
"""
MCP Server for Strands Agents

Allows Claude (and other MCP clients) to interact with the autonomous agents.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.agents.meta_orchestrator import MetaOrchestrator
from src.core.config import settings
from src.core import database as db_module
from src.core.database import Database

# Global orchestrator instance
orchestrator = None
active_tasks = {}


async def initialize_platform():
    """Initialize the platform"""
    global orchestrator
    
    if orchestrator is not None:
        return
    
    # Initialize database (optional)
    try:
        db_module.db = Database(settings.database_url)
        await db_module.db.setup_vector_extension()
        await db_module.db.create_tables()
    except:
        pass
    
    # Initialize orchestrator
    orchestrator = MetaOrchestrator()
    await orchestrator.initialize()


async def handle_task_request(task_description: str) -> dict:
    """
    Submit a task to the agents
    
    Args:
        task_description: Natural language description of what to build
        
    Returns:
        Execution plan with phases, agents, and estimated time
    """
    await initialize_platform()
    
    import uuid
    project_id = str(uuid.uuid4())
    task_id = str(uuid.uuid4())
    
    # Create plan
    plan = await orchestrator.orchestrate_task(
        task_description=task_description,
        project_id=project_id
    )
    
    # Store for execution
    active_tasks[task_id] = {
        "plan": plan,
        "project_id": project_id,
        "status": "planned"
    }
    
    # Format response
    phases = []
    for i, phase in enumerate(plan.phases, 1):
        phase_dict = phase if isinstance(phase, dict) else phase.__dict__
        phases.append({
            "number": i,
            "name": phase_dict.get('phase_name', f'Phase {i}'),
            "agent": phase_dict.get('required_role', 'unknown'),
            "duration_minutes": phase_dict.get('estimated_duration', 5),
            "deliverables": phase_dict.get('deliverables', [])
        })
    
    agents = []
    for agent in plan.agents:
        agent_dict = agent if isinstance(agent, dict) else agent.__dict__
        agents.append({
            "role": agent_dict.get('role', 'unknown'),
            "tools": agent_dict.get('tools', [])
        })
    
    return {
        "task_id": task_id,
        "status": "planned",
        "phases": phases,
        "agents": agents,
        "estimated_minutes": plan.estimated_duration,
        "message": f"Plan created with {len(phases)} phases and {len(agents)} agents"
    }


async def execute_task(task_id: str) -> dict:
    """
    Execute a planned task
    
    Args:
        task_id: ID of the task to execute
        
    Returns:
        Execution status and results
    """
    if task_id not in active_tasks:
        return {"error": "Task not found"}
    
    task = active_tasks[task_id]
    
    if task["status"] != "planned":
        return {"error": f"Task is already {task['status']}"}
    
    task["status"] = "executing"
    
    try:
        # Execute the plan
        results = await orchestrator.execute_plan(task["plan"], task_id)
        
        task["status"] = "completed"
        task["results"] = results
        
        return {
            "task_id": task_id,
            "status": "completed",
            "message": "Task executed successfully",
            "results": results
        }
    except Exception as e:
        task["status"] = "failed"
        task["error"] = str(e)
        
        return {
            "task_id": task_id,
            "status": "failed",
            "error": str(e)
        }


async def get_task_status(task_id: str) -> dict:
    """
    Get status of a task
    
    Args:
        task_id: ID of the task
        
    Returns:
        Current task status
    """
    if task_id not in active_tasks:
        return {"error": "Task not found"}
    
    task = active_tasks[task_id]
    
    return {
        "task_id": task_id,
        "status": task["status"],
        "project_id": task["project_id"]
    }


async def list_agents() -> dict:
    """
    List all available agents
    
    Returns:
        List of agent roles and capabilities
    """
    await initialize_platform()
    
    agents = []
    for role, agent in orchestrator.agent_pool.items():
        agents.append({
            "role": role.value if hasattr(role, 'value') else str(role),
            "status": "active"
        })
    
    return {
        "agents": agents,
        "count": len(agents)
    }


# MCP Server Implementation
async def handle_mcp_request(method: str, params: dict) -> dict:
    """Handle MCP protocol requests"""
    
    if method == "tools/list":
        return {
            "tools": [
                {
                    "name": "submit_task",
                    "description": "Submit a task to the autonomous agents. Describe what you want to build in natural language.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "task_description": {
                                "type": "string",
                                "description": "Natural language description of what to build (e.g., 'Create a REST API for todos with FastAPI')"
                            }
                        },
                        "required": ["task_description"]
                    }
                },
                {
                    "name": "execute_task",
                    "description": "Execute a planned task with the agents",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "ID of the task to execute"
                            }
                        },
                        "required": ["task_id"]
                    }
                },
                {
                    "name": "get_task_status",
                    "description": "Check the status of a task",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "ID of the task to check"
                            }
                        },
                        "required": ["task_id"]
                    }
                },
                {
                    "name": "list_agents",
                    "description": "List all available autonomous agents",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                }
            ]
        }
    
    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "submit_task":
            result = await handle_task_request(arguments["task_description"])
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }
                ]
            }
        
        elif tool_name == "execute_task":
            result = await execute_task(arguments["task_id"])
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }
                ]
            }
        
        elif tool_name == "get_task_status":
            result = await get_task_status(arguments["task_id"])
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }
                ]
            }
        
        elif tool_name == "list_agents":
            result = await list_agents()
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }
                ]
            }
    
    return {"error": "Unknown method"}


async def main():
    """Run MCP server"""
    print("🤖 Strands Agents MCP Server", file=sys.stderr)
    print("Initializing...", file=sys.stderr)
    
    await initialize_platform()
    
    print("✅ Ready for MCP requests", file=sys.stderr)
    
    # Read from stdin, write to stdout (MCP protocol)
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            request = json.loads(line)
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")
            
            result = await handle_mcp_request(method, params)
            
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
            
            print(json.dumps(response))
            sys.stdout.flush()
            
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": request.get("id") if 'request' in locals() else None,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()


if __name__ == "__main__":
    asyncio.run(main())
