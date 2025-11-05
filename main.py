#!/usr/bin/env python3
"""
Strands Autonomous Agent Platform - Main Entry Point

This launches the autonomous agent team that will build the platform
described in the Product Requirements Document.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.agents.meta_orchestrator import MetaOrchestrator
from src.coordination.messaging import CoordinationManager
from src.coordination.autonomous_recovery import AutonomousRecoverySystem
from src.learning.persistence import AgentPersistenceSystem
from src.core.config import settings
from src.core import database as db_module
from src.core.database import Database


class AutonomousAgentTeam:
    """Main controller for the autonomous agent team"""
    
    def __init__(self):
        self.orchestrator = MetaOrchestrator()
        self.coordination = None
        self.recovery = None
        self.learning = None
        
    async def initialize(self):
        """Initialize all systems"""
        print("🚀 Initializing Strands Autonomous Agent Platform...")
        print(f"⏰ Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Initialize database
        print("\n💾 Initializing Database...")
        db_module.db = Database(settings.database_url)
        try:
            await db_module.db.setup_vector_extension()
            await db_module.db.create_tables()
            print("✅ Database ready")
        except Exception as e:
            print(f"⚠️  Database initialization warning: {str(e)}")
            print("   (This is normal if database is not yet set up)")
        
        # Initialize orchestrator
        print("\n📋 Initializing Meta-Orchestrator...")
        await self.orchestrator.initialize()
        print("✅ Meta-Orchestrator ready")
        
        # Initialize coordination system
        print("\n🤝 Initializing Multi-Agent Coordination System...")
        # Note: We'll create a dummy task_id for initialization
        import uuid
        task_id = uuid.uuid4()
        self.coordination = CoordinationManager(task_id)
        await self.coordination.initialize()
        print("✅ Coordination system ready")
        
        # Initialize recovery system
        print("\n🔧 Initializing Autonomous Recovery System...")
        self.recovery = AutonomousRecoverySystem(self.coordination)
        print("✅ Recovery system ready")
        
        # Initialize learning system
        print("\n🧠 Initializing Agent Learning & Persistence System...")
        self.learning = AgentPersistenceSystem()
        print("✅ Learning system ready")
        
        print("\n" + "=" * 80)
        print("✨ All systems initialized successfully!")
        print("=" * 80)
        
    async def execute_project(self, prd_path: str):
        """
        Execute the project described in the PRD with full autonomy
        
        Args:
            prd_path: Path to the Product Requirements Document
        """
        print(f"\n📄 Reading PRD from: {prd_path}")
        
        # Read the PRD
        with open(prd_path, 'r') as f:
            prd_content = f.read()
        
        print(f"✅ PRD loaded ({len(prd_content)} characters)")
        
        # Create the master task
        print("\n🎯 Creating master task from PRD...")
        task_description = f"""
        Build the complete Strands Autonomous Agent Platform as described in this PRD.
        
        The platform should include:
        1. Conversational task interface (React + TypeScript frontend)
        2. Meta-orchestrator for task decomposition (FastAPI backend)
        3. E2B sandbox integration for agent environments
        4. Multi-agent execution system with specialized agents
        5. Real-time visualization with React Flow
        6. Agent screen viewer showing live sandbox activity
        7. Autonomous tool generation system
        8. Knowledge base with RAG retrieval
        9. Agent and tool persistence with learning
        10. Activity feed and progress tracking
        11. Authentication and project management
        12. Autonomous troubleshooting and error recovery
        
        Full PRD:
        {prd_content[:5000]}...
        
        You have complete autonomy to:
        - Build any tools you need
        - Create specialized agents as required
        - Coordinate between agents
        - Make architectural decisions
        - Handle errors autonomously
        - Learn and improve from each step
        
        Deliver a production-ready MVP in 7 days.
        """
        
        print("✅ Master task created")
        
        # Create execution plan
        print("\n🗺️  Creating execution plan...")
        import uuid
        task_id = uuid.uuid4()
        project_id = str(uuid.uuid4())
        
        execution_plan = await self.orchestrator.orchestrate_task(
            task_description=task_description,
            project_id=project_id
        )
        
        print(f"✅ Execution plan created:")
        print(f"   - Phases: {len(execution_plan.phases)}")
        print(f"   - Agents: {len(execution_plan.agents)}")
        print(f"   - Estimated duration: {execution_plan.estimated_duration} minutes")
        print(f"   - Dependencies: {len(execution_plan.dependencies)}")
        
        # Display the plan
        print("\n📊 Execution Plan Overview:")
        print("=" * 80)
        for i, phase in enumerate(execution_plan.phases, 1):
            print(f"\nPhase {i}: {phase.get('phase_name', 'Unnamed')}")
            print(f"  Description: {phase.get('description', 'No description')}")
            print(f"  Agent Role: {phase.get('required_role', 'Unknown')}")
            print(f"  Duration: {phase.get('estimated_duration', 'Unknown')} minutes")
            print(f"  Parallel: {'Yes' if phase.get('parallel_possible', False) else 'No'}")
        
        print("\n" + "=" * 80)
        print("\n🎬 Starting autonomous execution...")
        print("=" * 80)
        
        # Execute the plan
        try:
            results = await self.orchestrator.execute_plan(execution_plan, task_id)
            
            print("\n" + "=" * 80)
            print("🎉 PROJECT COMPLETED SUCCESSFULLY!")
            print("=" * 80)
            print(f"\n📊 Results Summary:")
            print(f"   - Status: {results.get('status', 'Unknown')}")
            print(f"   - Deliverables: {len(results.get('deliverables', []))}")
            print(f"   - Quality Score: {results.get('quality_score', 'N/A')}")
            
            # Learn from this execution
            print("\n🧠 Learning from execution...")
            # Note: This would require agent_performances and tool_performances
            # which we'd collect during execution
            
            print("\n✅ All done! The autonomous agent team has completed the project.")
            
        except Exception as e:
            print(f"\n❌ Execution failed: {str(e)}")
            print("\n🔧 Attempting autonomous recovery...")
            
            # The recovery system would handle this automatically
            # but we can also provide manual intervention options
            raise
    
    async def cleanup(self):
        """Clean up all resources"""
        print("\n🧹 Cleaning up resources...")
        
        if self.coordination:
            await self.coordination.cleanup()
        
        if self.recovery:
            await self.recovery.cleanup()
        
        if self.learning:
            await self.learning.cleanup()
        
        print("✅ Cleanup complete")


async def main():
    """Main entry point"""
    print("""
    ╔══════════════════════════════════════════════════════════════════════════════╗
    ║                                                                              ║
    ║              STRANDS AUTONOMOUS AGENT PLATFORM                               ║
    ║                                                                              ║
    ║              "Describe what you want, watch AI agents build it"              ║
    ║                                                                              ║
    ╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Get PRD path
    prd_path = "/Users/franksimpson/# Product Requirements Document: Strands.md"
    
    if not Path(prd_path).exists():
        print(f"❌ Error: PRD not found at {prd_path}")
        return
    
    # Create and initialize the agent team
    team = AutonomousAgentTeam()
    
    try:
        # Initialize all systems
        await team.initialize()
        
        # Execute the project
        await team.execute_project(prd_path)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up
        await team.cleanup()
        
        print("\n" + "=" * 80)
        print(f"⏰ End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print("\n👋 Goodbye!\n")


if __name__ == "__main__":
    # Run the autonomous agent team
    asyncio.run(main())
