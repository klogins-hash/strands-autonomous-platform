#!/usr/bin/env python3
"""
Natural Language Chat Interface for Strands Agents

Just describe what you want in plain English, and the agents will figure it out.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import uuid

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.agents.meta_orchestrator import MetaOrchestrator
from src.core.config import settings
from src.core import database as db_module
from src.core.database import Database


class AgentChat:
    """Natural language interface to agents"""
    
    def __init__(self):
        self.orchestrator = None
        self.current_task_id = None
        
    async def initialize(self):
        """Initialize the platform"""
        print("🤖 Initializing Strands Agents...")
        
        # Initialize database (optional)
        try:
            db_module.db = Database(settings.database_url)
            await db_module.db.setup_vector_extension()
            await db_module.db.create_tables()
        except Exception as e:
            pass  # Continue without database
        
        # Initialize orchestrator
        self.orchestrator = MetaOrchestrator()
        await self.orchestrator.initialize()
        
        print("✅ Ready!\n")
    
    async def chat(self):
        """Main chat loop"""
        print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                    STRANDS AUTONOMOUS AGENTS                                 ║
║                                                                              ║
║              Just tell me what you want to build!                            ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

Examples:
  • "Create a todo list API with FastAPI"
  • "Build a web scraper for news articles"
  • "Make a Python script that analyzes CSV files"
  • "Write a blog post about AI agents"

Type 'quit' or 'exit' to stop.
Type 'help' for more options.
""")
        
        while True:
            try:
                # Get user input
                print("\n" + "─" * 80)
                user_input = input("\n💬 You: ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye!")
                    break
                
                if user_input.lower() == 'help':
                    self.show_help()
                    continue
                
                if user_input.lower().startswith('status'):
                    await self.show_status()
                    continue
                
                # Process as a task
                await self.process_task(user_input)
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
    
    async def process_task(self, task_description: str):
        """Process a task from natural language"""
        print(f"\n🤔 Thinking about: \"{task_description}\"")
        print("\n⏳ Creating execution plan...")
        
        try:
            # Generate IDs
            project_id = str(uuid.uuid4())
            self.current_task_id = str(uuid.uuid4())
            
            # Create execution plan
            plan = await self.orchestrator.orchestrate_task(
                task_description=task_description,
                project_id=project_id
            )
            
            # Show the plan
            print("\n✅ Plan Created!")
            print("=" * 80)
            print(f"\n📊 Overview:")
            print(f"   • {len(plan.phases)} phases")
            print(f"   • {len(plan.agents)} agents needed")
            print(f"   • ~{plan.estimated_duration} minutes estimated")
            
            # Show phases
            print(f"\n📋 Execution Plan:")
            for i, phase in enumerate(plan.phases, 1):
                phase_dict = phase if isinstance(phase, dict) else phase.__dict__
                phase_name = phase_dict.get('phase_name', f'Phase {i}')
                role = phase_dict.get('required_role', 'unknown')
                duration = phase_dict.get('estimated_duration', '?')
                
                print(f"\n   {i}. {phase_name}")
                print(f"      Agent: {role.upper()}")
                print(f"      Time: ~{duration} min")
                
                # Show first deliverable
                deliverables = phase_dict.get('deliverables', [])
                if deliverables:
                    print(f"      Output: {deliverables[0]}")
            
            # Show agent team
            print(f"\n👥 Agent Team:")
            agent_roles = set()
            for agent in plan.agents:
                agent_dict = agent if isinstance(agent, dict) else agent.__dict__
                role = agent_dict.get('role', 'unknown')
                agent_roles.add(role)
            
            for role in agent_roles:
                print(f"   • {role.upper()} Agent")
            
            print("\n" + "=" * 80)
            
            # Ask if they want to execute
            response = input("\n🚀 Execute this plan? (yes/no): ").strip().lower()
            
            if response in ['yes', 'y']:
                print("\n⏳ Starting execution...")
                print("   (This will spawn agents in E2B sandboxes)")
                print("   (Press Ctrl+C to cancel)\n")
                
                try:
                    # Execute the plan
                    results = await self.orchestrator.execute_plan(plan, self.current_task_id)
                    
                    # Show results
                    print("\n" + "=" * 80)
                    print("✅ EXECUTION COMPLETE!")
                    print("=" * 80)
                    
                    if results:
                        print("\n📊 Results:")
                        for phase_id, result in results.items():
                            status = result.get('status', 'unknown') if isinstance(result, dict) else 'completed'
                            print(f"   • Phase {phase_id}: {status}")
                    
                    print(f"\n💾 Task ID: {self.current_task_id}")
                    print("   Use this ID to retrieve results later")
                    
                except Exception as e:
                    print(f"\n❌ Execution failed: {str(e)}")
                    print("   The plan was created successfully, but execution encountered an error.")
                    print("   This is often due to E2B sandbox configuration.")
            else:
                print("\n📝 Plan saved but not executed.")
                print(f"   Task ID: {self.current_task_id}")
                
        except Exception as e:
            print(f"\n❌ Failed to create plan: {str(e)}")
            import traceback
            traceback.print_exc()
    
    async def show_status(self):
        """Show current status"""
        print("\n📊 Platform Status:")
        print(f"   • Orchestrator: ✅ Active")
        print(f"   • Agents: {len(self.orchestrator.agent_pool)} available")
        if self.current_task_id:
            print(f"   • Last Task: {self.current_task_id}")
    
    def show_help(self):
        """Show help information"""
        print("""
📚 Help:

NATURAL LANGUAGE:
  Just describe what you want! Examples:
  • "Create a REST API for managing tasks"
  • "Build a web scraper for product prices"
  • "Write a Python script to analyze sales data"
  • "Make a CLI tool for file organization"

COMMANDS:
  help     - Show this help
  status   - Show platform status
  quit     - Exit the chat

TIPS:
  • Be specific about what you want
  • Mention tech stack if you have preferences
  • Include any constraints or requirements
  • The agents will figure out the details!

EXAMPLES:
  "Create a FastAPI server with user authentication and a PostgreSQL database"
  "Build a React dashboard that shows real-time crypto prices"
  "Write a Python script that converts CSV to JSON with validation"
  "Make a Discord bot that posts daily motivational quotes"
""")


async def main():
    """Main entry point"""
    chat = AgentChat()
    
    try:
        await chat.initialize()
        await chat.chat()
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
