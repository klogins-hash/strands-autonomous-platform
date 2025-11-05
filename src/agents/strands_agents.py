"""
Strands-Native Agent Implementation

Properly using the Strands Agent framework with:
- Strands Agent class
- Tool-Agent pattern for multi-agent orchestration
- Proper system prompts
- Callback handlers for progress tracking
"""

import os
import subprocess
from typing import Dict, Any, List, Optional
import json

from strands import Agent, tool
from strands.handlers import CallbackHandler

from .prompts import (
    CODE_AGENT_PROMPT,
    RESEARCH_AGENT_PROMPT,
    DESIGNER_AGENT_PROMPT,
    CONTENT_AGENT_PROMPT,
    GENERAL_AGENT_PROMPT,
    ORCHESTRATOR_PROMPT
)
from .code_editor import code_editor
from ..core.config import settings


# ============================================================================
# TOOLS - Shared across agents
# ============================================================================

@tool
async def file_reader(file_path: str) -> str:
    """Read file contents with line numbers"""
    return await code_editor.read_file(file_path)


@tool
async def file_writer(file_path: str, content: str) -> str:
    """Write or create a file"""
    result = await code_editor.create_file(file_path, content)
    if result.get("success"):
        return f"✅ File created: {file_path}"
    else:
        return f"❌ Error: {result.get('error')}"


@tool
async def file_editor(file_path: str, old_string: str, new_string: str, explanation: str = "") -> str:
    """Edit a file by replacing old_string with new_string"""
    result = await code_editor.edit_file(file_path, old_string, new_string, explanation)
    if result.get("success"):
        return f"✅ File edited: {file_path}\n{explanation}"
    else:
        return f"❌ Error: {result.get('error')}"


@tool
async def code_search(query: str, file_pattern: str = "*.py") -> str:
    """Search for code in the workspace"""
    results = await code_editor.search_code(query, file_pattern)
    if not results:
        return f"No results found for: {query}"
    
    output = [f"Found {len(results)} matches for '{query}':\n"]
    for match in results[:10]:  # Limit to 10 results
        output.append(f"  {match['file']}:{match['line']} - {match['content'][:100]}")
    
    return "\n".join(output)


@tool
def python_repl(code: str) -> str:
    """Execute Python code and return output"""
    try:
        # Create a temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        # Execute it
        result = subprocess.run(
            ['python', temp_file],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Clean up
        os.unlink(temp_file)
        
        output = result.stdout
        if result.stderr:
            output += f"\nErrors:\n{result.stderr}"
        
        return output or "Code executed successfully (no output)"
        
    except subprocess.TimeoutExpired:
        return "❌ Execution timed out (30s limit)"
    except Exception as e:
        return f"❌ Error executing code: {str(e)}"


@tool
def execute_shell(command: str) -> str:
    """Execute a shell command"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.getcwd()
        )
        
        output = result.stdout
        if result.stderr:
            output += f"\nErrors:\n{result.stderr}"
        
        return output or "Command executed successfully"
        
    except subprocess.TimeoutExpired:
        return "❌ Command timed out (30s limit)"
    except Exception as e:
        return f"❌ Error executing command: {str(e)}"


@tool
def install_package(package_name: str, package_manager: str = "pip") -> str:
    """Install a package using pip or npm"""
    try:
        if package_manager == "pip":
            cmd = f"pip install {package_name}"
        elif package_manager == "npm":
            cmd = f"npm install {package_name}"
        else:
            return f"❌ Unknown package manager: {package_manager}"
        
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            return f"✅ Installed {package_name}"
        else:
            return f"❌ Failed to install {package_name}:\n{result.stderr}"
            
    except Exception as e:
        return f"❌ Error: {str(e)}"


@tool
def run_tests(test_path: str = "tests/") -> str:
    """Run tests using pytest"""
    try:
        result = subprocess.run(
            f"pytest {test_path} -v",
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        return result.stdout + result.stderr
        
    except subprocess.TimeoutExpired:
        return "❌ Tests timed out"
    except Exception as e:
        return f"❌ Error running tests: {str(e)}"


@tool
def web_search(query: str, max_results: int = 5) -> str:
    """Search the web for information (placeholder - needs API)"""
    # TODO: Implement with Tavily or Serper API
    return f"Web search for '{query}' - API integration needed"


@tool
def analyze_error(error_message: str, context: str = "") -> str:
    """Analyze an error and suggest fixes"""
    # This will use code_editor's analyze_and_fix_error
    return f"Analyzing error: {error_message}\nContext: {context}"


# ============================================================================
# CALLBACK HANDLER - For progress tracking
# ============================================================================

class ProgressCallbackHandler(CallbackHandler):
    """Custom callback handler for tracking agent progress"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
    
    def on_agent_start(self, **kwargs):
        print(f"[{self.agent_name}] Starting...")
    
    def on_agent_end(self, **kwargs):
        print(f"[{self.agent_name}] Completed")
    
    def on_tool_start(self, tool_name: str, **kwargs):
        print(f"[{self.agent_name}] Using tool: {tool_name}")
    
    def on_tool_end(self, tool_name: str, **kwargs):
        pass  # Don't spam output
    
    def on_llm_start(self, **kwargs):
        pass  # Silent
    
    def on_llm_end(self, **kwargs):
        pass  # Silent


# ============================================================================
# AGENT FACTORY - Create Strands agents properly
# ============================================================================

def create_code_agent() -> Agent:
    """Create a code agent using Strands framework"""
    return Agent(
        system_prompt=CODE_AGENT_PROMPT,
        tools=[
            file_reader,
            file_writer,
            file_editor,
            code_search,
            python_repl,
            execute_shell,
            install_package,
            run_tests,
            analyze_error
        ],
        callback_handler=ProgressCallbackHandler("code"),
        model_name=settings.anthropic_model
    )


def create_research_agent() -> Agent:
    """Create a research agent using Strands framework"""
    return Agent(
        system_prompt=RESEARCH_AGENT_PROMPT,
        tools=[
            web_search,
            file_reader,
            file_writer
        ],
        callback_handler=ProgressCallbackHandler("research"),
        model_name=settings.anthropic_model
    )


def create_designer_agent() -> Agent:
    """Create a designer agent using Strands framework"""
    return Agent(
        system_prompt=DESIGNER_AGENT_PROMPT,
        tools=[
            file_reader,
            file_writer,
            file_editor,
            code_search
        ],
        callback_handler=ProgressCallbackHandler("designer"),
        model_name=settings.anthropic_model
    )


def create_content_agent() -> Agent:
    """Create a content agent using Strands framework"""
    return Agent(
        system_prompt=CONTENT_AGENT_PROMPT,
        tools=[
            file_reader,
            file_writer,
            file_editor
        ],
        callback_handler=ProgressCallbackHandler("content"),
        model_name=settings.anthropic_model
    )


def create_general_agent() -> Agent:
    """Create a general agent using Strands framework"""
    return Agent(
        system_prompt=GENERAL_AGENT_PROMPT,
        tools=[
            file_reader,
            file_writer
        ],
        callback_handler=ProgressCallbackHandler("general"),
        model_name=settings.anthropic_model
    )


# ============================================================================
# TOOL-AGENT PATTERN - Wrap agents as tools for orchestrator
# ============================================================================

@tool
def code_agent(task: str) -> str:
    """
    Delegate coding tasks to the specialized code agent.
    
    Use for: programming, debugging, testing, code review, refactoring
    """
    print("🔀 Routing to Code Agent")
    agent = create_code_agent()
    response = agent(task)
    
    # Extract text from response
    if hasattr(response, 'content'):
        return response.content[0].text if response.content else str(response)
    return str(response)


@tool
def research_agent(task: str) -> str:
    """
    Delegate research tasks to the specialized research agent.
    
    Use for: information gathering, analysis, documentation research
    """
    print("🔀 Routing to Research Agent")
    agent = create_research_agent()
    response = agent(task)
    
    if hasattr(response, 'content'):
        return response.content[0].text if response.content else str(response)
    return str(response)


@tool
def designer_agent(task: str) -> str:
    """
    Delegate design tasks to the specialized designer agent.
    
    Use for: UI/UX design, frontend architecture, styling, components
    """
    print("🔀 Routing to Designer Agent")
    agent = create_designer_agent()
    response = agent(task)
    
    if hasattr(response, 'content'):
        return response.content[0].text if response.content else str(response)
    return str(response)


@tool
def content_agent(task: str) -> str:
    """
    Delegate content tasks to the specialized content agent.
    
    Use for: writing, documentation, technical writing, editing
    """
    print("🔀 Routing to Content Agent")
    agent = create_content_agent()
    response = agent(task)
    
    if hasattr(response, 'content'):
        return response.content[0].text if response.content else str(response)
    return str(response)


# ============================================================================
# ORCHESTRATOR - Coordinates all specialized agents
# ============================================================================

def create_orchestrator() -> Agent:
    """
    Create the meta-orchestrator using Tool-Agent pattern.
    
    The orchestrator has all specialized agents as tools and routes
    work to them based on the task requirements.
    """
    return Agent(
        system_prompt=ORCHESTRATOR_PROMPT,
        tools=[
            code_agent,
            research_agent,
            designer_agent,
            content_agent
        ],
        callback_handler=ProgressCallbackHandler("orchestrator"),
        model_name=settings.anthropic_model
    )


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def execute_task(task: str, agent_type: str = "orchestrator") -> str:
    """
    Execute a task using the specified agent type.
    
    Args:
        task: The task description
        agent_type: Type of agent (orchestrator, code, research, designer, content)
    
    Returns:
        Agent's response
    """
    agent_factories = {
        "orchestrator": create_orchestrator,
        "code": create_code_agent,
        "research": create_research_agent,
        "designer": create_designer_agent,
        "content": create_content_agent,
        "general": create_general_agent
    }
    
    factory = agent_factories.get(agent_type, create_orchestrator)
    agent = factory()
    
    response = agent(task)
    
    if hasattr(response, 'content'):
        return response.content[0].text if response.content else str(response)
    return str(response)
