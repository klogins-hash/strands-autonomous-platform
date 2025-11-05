"""
E2B Sandbox Manager - Provides isolated environments for agents

Each agent gets its own sandbox with:
- Ubuntu 24.04 environment
- Python 3.11+ and Node.js 18+
- Full internet access
- File system persistence
- Screen streaming capabilities
- Resource limits (2 CPU, 4GB RAM)
"""

import asyncio
import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from e2b import Sandbox
from ..core.config import settings


class SandboxManager:
    """Manages E2B sandboxes for agent execution"""
    
    def __init__(self):
        self.active_sandboxes: Dict[str, Sandbox] = {}
        self.sandbox_metadata: Dict[str, Dict[str, Any]] = {}
        self.max_concurrent = settings.max_concurrent_agents
        self.default_timeout = settings.sandbox_timeout
        
    async def create_sandbox(self, agent_id: str, template: str = "base") -> str:
        """
        Create a new sandbox for an agent
        
        Args:
            agent_id: Unique identifier for the agent
            template: Sandbox template to use
            
        Returns:
            Sandbox ID for reference
        """
        try:
            # Check concurrent limit
            if len(self.active_sandboxes) >= self.max_concurrent:
                await self._cleanup_idle_sandboxes()
            
            # Create E2B sandbox (updated API - use Sandbox.create())
            sandbox = await asyncio.to_thread(Sandbox.create)
            
            sandbox_id = f"sandbox_{agent_id}_{uuid.uuid4().hex[:8]}"
            
            # Configure sandbox environment
            await self._configure_sandbox(sandbox, agent_id)
            
            # Store sandbox reference
            self.active_sandboxes[sandbox_id] = sandbox
            self.sandbox_metadata[sandbox_id] = {
                "agent_id": agent_id,
                "created_at": datetime.utcnow(),
                "last_activity": datetime.utcnow(),
                "template": template,
                "status": "active"
            }
            
            return sandbox_id
            
        except Exception as e:
            raise Exception(f"Failed to create sandbox for {agent_id}: {str(e)}")
    
    async def _configure_sandbox(self, sandbox: Sandbox, agent_id: str):
        """Configure sandbox with required tools and environment"""
        try:
            # Install Python packages
            python_packages = [
                "requests", "beautifulsoup4", "pandas", "numpy",
                "matplotlib", "seaborn", "scikit-learn", "openai",
                "anthropic", "selenium", "pytest", "black", "flake8"
            ]
            
            for package in python_packages:
                try:
                    await asyncio.to_thread(
                        sandbox.process.start_and_wait,
                        f"pip install {package} --quiet",
                        timeout=30
                    )
                except:
                    print(f"Failed to install {package}, continuing...")
            
            # Install Node.js packages
            node_packages = ["npm", "axios", "cheerio", "puppeteer"]
            
            for package in node_packages:
                try:
                    await asyncio.to_thread(
                        sandbox.process.start_and_wait,
                        f"npm install -g {package} --silent",
                        timeout=30
                    )
                except:
                    print(f"Failed to install {package}, continuing...")
            
            # Create workspace directory
            await asyncio.to_thread(
                sandbox.filesystem.write,
                f"/home/user/workspace_{agent_id}/README.md",
                f"# Workspace for Agent {agent_id}\n\nCreated: {datetime.utcnow()}\n"
            )
            
            # Set up Python path
            await asyncio.to_thread(
                sandbox.process.start_and_wait,
                f'echo "export PYTHONPATH=$PYTHONPATH:/home/user/workspace_{agent_id}" >> ~/.bashrc',
                timeout=5
            )
            
        except Exception as e:
            print(f"Sandbox configuration warning: {str(e)}")
    
    async def execute_python(self, sandbox_id: str, code: str, timeout: int = 30) -> str:
        """
        Execute Python code in the specified sandbox
        
        Args:
            sandbox_id: ID of the sandbox
            code: Python code to execute
            timeout: Execution timeout in seconds
            
        Returns:
            Output from code execution
        """
        if sandbox_id not in self.active_sandboxes:
            raise Exception(f"Sandbox {sandbox_id} not found")
        
        sandbox = self.active_sandboxes[sandbox_id]
        
        try:
            # Write code to temporary file
            temp_file = f"/tmp/execute_{uuid.uuid4().hex[:8]}.py"
            await asyncio.to_thread(
                sandbox.filesystem.write,
                temp_file,
                code
            )
            
            # Execute the code
            process = await asyncio.to_thread(
                sandbox.process.start,
                f"python {temp_file}",
                timeout=timeout
            )
            
            # Wait for completion and get output
            result = await asyncio.to_thread(process.wait)
            
            # Clean up temp file
            await asyncio.to_thread(
                sandbox.filesystem.remove,
                temp_file
            )
            
            # Update activity timestamp
            self._update_activity(sandbox_id)
            
            return result.stdout or result.stderr or "Execution completed"
            
        except Exception as e:
            return f"Python execution failed: {str(e)}"
    
    async def execute_shell(self, sandbox_id: str, command: str, timeout: int = 30) -> str:
        """
        Execute shell command in the specified sandbox
        
        Args:
            sandbox_id: ID of the sandbox
            command: Shell command to execute
            timeout: Execution timeout in seconds
            
        Returns:
            Output from command execution
        """
        if sandbox_id not in self.active_sandboxes:
            raise Exception(f"Sandbox {sandbox_id} not found")
        
        sandbox = self.active_sandboxes[sandbox_id]
        
        try:
            process = await asyncio.to_thread(
                sandbox.process.start,
                command,
                timeout=timeout
            )
            
            result = await asyncio.to_thread(process.wait)
            
            # Update activity timestamp
            self._update_activity(sandbox_id)
            
            return result.stdout or result.stderr or "Command completed"
            
        except Exception as e:
            return f"Shell command failed: {str(e)}"
    
    async def read_file(self, sandbox_id: str, file_path: str) -> str:
        """Read file contents from sandbox"""
        if sandbox_id not in self.active_sandboxes:
            raise Exception(f"Sandbox {sandbox_id} not found")
        
        sandbox = self.active_sandboxes[sandbox_id]
        
        try:
            content = await asyncio.to_thread(
                sandbox.filesystem.read,
                file_path
            )
            
            self._update_activity(sandbox_id)
            return content
            
        except Exception as e:
            return f"Failed to read file {file_path}: {str(e)}"
    
    async def write_file(self, sandbox_id: str, file_path: str, content: str) -> bool:
        """Write content to file in sandbox"""
        if sandbox_id not in self.active_sandboxes:
            raise Exception(f"Sandbox {sandbox_id} not found")
        
        sandbox = self.active_sandboxes[sandbox_id]
        
        try:
            await asyncio.to_thread(
                sandbox.filesystem.write,
                file_path,
                content
            )
            
            self._update_activity(sandbox_id)
            return True
            
        except Exception as e:
            print(f"Failed to write file {file_path}: {str(e)}")
            return False
    
    async def list_files(self, sandbox_id: str, directory: str = "/home/user") -> List[str]:
        """List files in sandbox directory"""
        if sandbox_id not in self.active_sandboxes:
            raise Exception(f"Sandbox {sandbox_id} not found")
        
        sandbox = self.active_sandboxes[sandbox_id]
        
        try:
            result = await asyncio.to_thread(
                sandbox.process.start_and_wait,
                f"find {directory} -type f | head -50",
                timeout=10
            )
            
            files = result.stdout.strip().split('\n') if result.stdout else []
            return [f for f in files if f]  # Filter empty strings
            
        except Exception as e:
            print(f"Failed to list files: {str(e)}")
            return []
    
    async def get_screenshot(self, sandbox_id: str) -> Optional[bytes]:
        """Get screenshot of sandbox screen"""
        if sandbox_id not in self.active_sandboxes:
            return None
        
        sandbox = self.active_sandboxes[sandbox_id]
        
        try:
            # Take screenshot using E2B's screenshot capability
            screenshot = await asyncio.to_thread(
                sandbox.screenshot,
                format="png"
            )
            
            self._update_activity(sandbox_id)
            return screenshot
            
        except Exception as e:
            print(f"Failed to capture screenshot: {str(e)}")
            return None
    
    async def stream_terminal(self, sandbox_id: str, callback):
        """Stream terminal output from sandbox"""
        if sandbox_id not in self.active_sandboxes:
            raise Exception(f"Sandbox {sandbox_id} not found")
        
        sandbox = self.active_sandboxes[sandbox_id]
        
        # Start a bash session for streaming
        process = await asyncio.to_thread(
            sandbox.process.start,
            "bash -i",
            timeout=3600  # Long running session
        )
        
        try:
            while True:
                # Read output in chunks
                output = await asyncio.to_thread(
                    process.read_output,
                    timeout=1
                )
                
                if output:
                    await callback(output)
                
                await asyncio.sleep(0.1)  # Small delay to prevent overwhelming
                
        except Exception as e:
            print(f"Terminal streaming error: {str(e)}")
        finally:
            await asyncio.to_thread(process.kill)
    
    async def cleanup_sandbox(self, sandbox_id: str):
        """Clean up and close a sandbox"""
        if sandbox_id in self.active_sandboxes:
            sandbox = self.active_sandboxes[sandbox_id]
            
            try:
                await asyncio.to_thread(sandbox.close)
            except:
                pass  # Ignore cleanup errors
            
            del self.active_sandboxes[sandbox_id]
            if sandbox_id in self.sandbox_metadata:
                del self.sandbox_metadata[sandbox_id]
    
    async def _cleanup_idle_sandboxes(self):
        """Clean up sandboxes that have been idle too long"""
        current_time = datetime.utcnow()
        idle_timeout = timedelta(minutes=30)
        
        to_cleanup = []
        for sandbox_id, metadata in self.sandbox_metadata.items():
            if current_time - metadata["last_activity"] > idle_timeout:
                to_cleanup.append(sandbox_id)
        
        for sandbox_id in to_cleanup:
            await self.cleanup_sandbox(sandbox_id)
            print(f"Cleaned up idle sandbox: {sandbox_id}")
    
    def _update_activity(self, sandbox_id: str):
        """Update the last activity timestamp for a sandbox"""
        if sandbox_id in self.sandbox_metadata:
            self.sandbox_metadata[sandbox_id]["last_activity"] = datetime.utcnow()
    
    async def get_sandbox_status(self, sandbox_id: str) -> Dict[str, Any]:
        """Get status information about a sandbox"""
        if sandbox_id not in self.sandbox_metadata:
            return {"status": "not_found"}
        
        metadata = self.sandbox_metadata[sandbox_id]
        
        # Get resource usage
        try:
            sandbox = self.active_sandboxes[sandbox_id]
            # TODO: Get actual resource usage from E2B when available
            resource_usage = {
                "cpu_percent": 0.0,
                "memory_mb": 0,
                "disk_mb": 0
            }
        except:
            resource_usage = {"error": "Unable to get resource usage"}
        
        return {
            "status": metadata["status"],
            "agent_id": metadata["agent_id"],
            "created_at": metadata["created_at"].isoformat(),
            "last_activity": metadata["last_activity"].isoformat(),
            "uptime_seconds": (datetime.utcnow() - metadata["created_at"]).total_seconds(),
            "resource_usage": resource_usage
        }
    
    async def list_active_sandboxes(self) -> List[Dict[str, Any]]:
        """List all active sandboxes and their status"""
        sandboxes = []
        for sandbox_id in self.sandbox_metadata:
            status = await self.get_sandbox_status(sandbox_id)
            sandboxes.append({
                "sandbox_id": sandbox_id,
                **status
            })
        
        return sandboxes
    
    async def shutdown_all(self):
        """Shutdown all active sandboxes"""
        for sandbox_id in list(self.active_sandboxes.keys()):
            await self.cleanup_sandbox(sandbox_id)


# Predefined sandbox templates
class SandboxTemplates:
    """Predefined sandbox configurations for different agent types"""
    
    BASE_TEMPLATE = {
        "python_packages": [
            "requests", "beautifulsoup4", "pandas", "numpy",
            "matplotlib", "openai", "anthropic"
        ],
        "node_packages": ["npm", "axios"],
        "system_packages": ["curl", "wget", "git"]
    }
    
    RESEARCH_TEMPLATE = {
        "python_packages": [
            "requests", "beautifulsoup4", "selenium", "newspaper3k",
            "textblob", "spacy", "nltk", "pandas", "numpy"
        ],
        "node_packages": ["npm", "puppeteer", "cheerio"],
        "system_packages": ["curl", "wget", "chromium-browser"]
    }
    
    CODE_TEMPLATE = {
        "python_packages": [
            "pytest", "black", "flake8", "mypy", "pre-commit",
            "virtualenv", "pip-tools", "setuptools", "wheel"
        ],
        "node_packages": ["npm", "node", "typescript", "eslint"],
        "system_packages": ["git", "build-essential", "curl"]
    }
    
    DATA_SCIENCE_TEMPLATE = {
        "python_packages": [
            "pandas", "numpy", "scikit-learn", "tensorflow", "torch",
            "matplotlib", "seaborn", "plotly", "jupyter", "statsmodels"
        ],
        "node_packages": ["npm"],
        "system_packages": ["curl", "wget"]
    }
