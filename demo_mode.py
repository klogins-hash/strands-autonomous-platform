#!/usr/bin/env python3
"""
Demo Mode - Run the platform without E2B sandboxes for testing

This demonstrates the orchestration, planning, and coordination
without requiring E2B API access.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.agents.meta_orchestrator import MetaOrchestrator
from src.core.config import settings
from src.core import database as db_module
from src.core.database import Database
from src.core.progress_tracker import progress_tracker, ProgressStatus


async def demo_execution():
    """Run a demo execution without E2B sandboxes"""
    
    print("""
    ╔══════════════════════════════════════════════════════════════════════════════╗
    ║                                                                              ║
    ║              STRANDS AUTONOMOUS AGENT PLATFORM - DEMO MODE                   ║
    ║                                                                              ║
    ║              "See the orchestration in action"                               ║
    ║                                                                              ║
    ╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Initialize database
    print("💾 Initializing Database...")
    db_module.db = Database(settings.database_url)
    print("✅ Database ready (demo mode - no actual DB required)\n")
    
    # Initialize orchestrator
    print("📋 Initializing Meta-Orchestrator...")
    orchestrator = MetaOrchestrator()
    await orchestrator.initialize()
    print("✅ Meta-Orchestrator ready\n")
    
    # Demo task
    demo_task = """
    Create a simple web application with:
    - A landing page with modern design
    - User authentication (login/signup)
    - A dashboard showing user stats
    - Dark mode toggle
    - Responsive mobile design
    
    Tech stack: React, TypeScript, Tailwind CSS, FastAPI backend
    """
    
    print("🎯 Demo Task:")
    print(demo_task)
    print("\n" + "=" * 80)
    
    # Track progress
    await progress_tracker.update(
        "orchestrator",
        "system",
        ProgressStatus.IN_PROGRESS,
        10.0,
        "Analyzing task requirements"
    )
    
    # Create execution plan
    print("\n🗺️  Creating Execution Plan...")
    import uuid
    project_id = str(uuid.uuid4())
    
    try:
        execution_plan = await orchestrator.orchestrate_task(
            task_description=demo_task,
            project_id=project_id
        )
        
        await progress_tracker.update(
            "orchestrator",
            "system",
            ProgressStatus.IN_PROGRESS,
            30.0,
            "Execution plan created"
        )
        
        # Display the plan
        print("\n✅ Execution Plan Created!")
        print("=" * 80)
        print(f"\n📊 Plan Overview:")
        print(f"   Phases: {len(execution_plan.phases)}")
        print(f"   Agents Required: {len(execution_plan.agents)}")
        print(f"   Estimated Duration: {execution_plan.estimated_duration} minutes")
        print(f"   Dependencies: {len(execution_plan.dependencies)}")
        
        # Show phases
        print(f"\n📋 Execution Phases:")
        print("=" * 80)
        for i, phase in enumerate(execution_plan.phases, 1):
            phase_dict = phase if isinstance(phase, dict) else phase.__dict__
            print(f"\n{i}. {phase_dict.get('phase_name', 'Unnamed Phase')}")
            print(f"   Description: {phase_dict.get('description', 'No description')}")
            print(f"   Agent Role: {phase_dict.get('required_role', 'Unknown')}")
            print(f"   Duration: {phase_dict.get('estimated_duration', 'Unknown')} minutes")
            print(f"   Parallel: {'Yes' if phase_dict.get('parallel_possible', False) else 'No'}")
            
            # Show deliverables
            deliverables = phase_dict.get('deliverables', [])
            if deliverables:
                print(f"   Deliverables:")
                for deliverable in deliverables:
                    print(f"     • {deliverable}")
        
        # Show agent team
        print(f"\n👥 Agent Team:")
        print("=" * 80)
        for agent_spec in execution_plan.agents:
            spec_dict = agent_spec if isinstance(agent_spec, dict) else agent_spec.__dict__
            print(f"\n• {spec_dict.get('role', 'Unknown').upper()} Agent")
            print(f"  System Prompt: {spec_dict.get('system_prompt', 'N/A')[:100]}...")
            tools = spec_dict.get('tools', [])
            if tools:
                print(f"  Tools: {', '.join(tools[:5])}")
        
        await progress_tracker.update(
            "orchestrator",
            "system",
            ProgressStatus.COMPLETED,
            100.0,
            "Demo execution completed"
        )
        
        # Show summary
        print("\n" + "=" * 80)
        progress_tracker.display_summary()
        
        print("✨ Demo Complete!")
        print("\n💡 In full mode, the platform would now:")
        print("   1. Spawn E2B sandboxes for each agent")
        print("   2. Execute phases in parallel where possible")
        print("   3. Coordinate agent communication via Redis")
        print("   4. Build tools autonomously as needed")
        print("   5. Handle errors with autonomous recovery")
        print("   6. Learn from successful executions")
        print("   7. Deliver production-ready results")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        await progress_tracker.update(
            "orchestrator",
            "system",
            ProgressStatus.FAILED,
            0.0,
            f"Failed: {str(e)}"
        )


if __name__ == "__main__":
    asyncio.run(demo_execution())
