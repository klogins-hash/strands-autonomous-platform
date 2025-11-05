"""
MCP Client for Agents

Allows agents to access external MCP servers for additional capabilities.
"""

import asyncio
import json
import subprocess
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class MCPServer:
    """MCP Server configuration"""
    name: str
    command: str
    args: List[str]
    env: Dict[str, str]
    url: Optional[str] = None
    transport: Optional[str] = None


class MCPClient:
    """Client for interacting with MCP servers"""
    
    def __init__(self):
        self.servers = self._load_servers()
        self.active_connections = {}
    
    def _load_servers(self) -> Dict[str, MCPServer]:
        """Load MCP server configurations"""
        return {
            "deepwiki": MCPServer(
                name="deepwiki",
                command="",
                args=[],
                env={},
                url="https://mcp.deepwiki.com/sse"
            ),
            "livekit-docs": MCPServer(
                name="livekit-docs",
                command="",
                args=[],
                env={},
                url="https://docs.livekit.io/mcp",
                transport="http"
            ),
            "mattermost": MCPServer(
                name="mattermost",
                command="node",
                args=["/Users/franksimpson/CascadeProjects/mattermost-mcp-server/index.js"],
                env={
                    "MATTERMOST_TOKEN": "tfszhco5sfy1jbfif9cfyz4gyy",
                    "MATTERMOST_URL": "https://docker-production-a32b.up.railway.app"
                }
            ),
            "n8n": MCPServer(
                name="n8n",
                command="npx",
                args=["-y", "@klogins313/n8n-mcp-server"],
                env={
                    "N8N_API_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5NGFhZTQ4Ni04NGJkLTQ1MDEtYWE1MC02Y2E4ZmUwN2UxNDAiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzYyMjY4NjQwLCJleHAiOjE3NjQ4MjQ0MDB9.DKYgmio9Tn9zpGrLNPApxfnZKDJ4RD4zfvI6Hs6sd_8",
                    "N8N_BASE_URL": "https://primary-production-1774.up.railway.app"
                }
            ),
            "strands-agents": MCPServer(
                name="strands-agents",
                command="uvx",
                args=["strands-agents-mcp-server"],
                env={"FASTMCP_LOG_LEVEL": "INFO"}
            )
        }
    
    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call a tool on an MCP server
        
        Args:
            server_name: Name of the MCP server
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool result
        """
        if server_name not in self.servers:
            raise ValueError(f"Unknown MCP server: {server_name}")
        
        server = self.servers[server_name]
        
        # For HTTP/SSE servers, make HTTP request
        if server.url:
            return await self._call_http_tool(server, tool_name, arguments)
        
        # For command-based servers, use subprocess
        return await self._call_subprocess_tool(server, tool_name, arguments)
    
    async def _call_http_tool(self, server: MCPServer, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call tool via HTTP"""
        import aiohttp
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(server.url, json=request) as response:
                result = await response.json()
                return result.get("result")
    
    async def _call_subprocess_tool(self, server: MCPServer, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call tool via subprocess"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        # Start MCP server process
        process = await asyncio.create_subprocess_exec(
            server.command,
            *server.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**server.env}
        )
        
        # Send request
        stdout, stderr = await process.communicate(
            input=json.dumps(request).encode() + b'\n'
        )
        
        if process.returncode != 0:
            raise Exception(f"MCP server error: {stderr.decode()}")
        
        # Parse response
        response = json.loads(stdout.decode())
        return response.get("result")
    
    async def list_tools(self, server_name: str) -> List[Dict[str, Any]]:
        """
        List available tools on an MCP server
        
        Args:
            server_name: Name of the MCP server
            
        Returns:
            List of tool definitions
        """
        if server_name not in self.servers:
            raise ValueError(f"Unknown MCP server: {server_name}")
        
        server = self.servers[server_name]
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }
        
        if server.url:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(server.url, json=request) as response:
                    result = await response.json()
                    return result.get("result", {}).get("tools", [])
        else:
            # Use subprocess
            process = await asyncio.create_subprocess_exec(
                server.command,
                *server.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**server.env}
            )
            
            stdout, stderr = await process.communicate(
                input=json.dumps(request).encode() + b'\n'
            )
            
            if process.returncode == 0:
                response = json.loads(stdout.decode())
                return response.get("result", {}).get("tools", [])
            
            return []
    
    def get_available_servers(self) -> List[str]:
        """Get list of available MCP servers"""
        return list(self.servers.keys())


# Global MCP client instance
mcp_client = MCPClient()
