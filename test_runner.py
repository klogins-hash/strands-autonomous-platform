#!/usr/bin/env python3
"""
Test Runner - Run a specific test project through the platform
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


async def run_test_project():
    """Run the test project"""
    
    print("""
    ╔══════════════════════════════════════════════════════════════════════════════╗
    ║                                                                              ║
    ║              STRANDS PLATFORM - TEST RUN                                     ║
    ║                                                                              ║
    ║              "Testing with a real project"                                   ║
    ║                                                                              ║
    ╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Read test project
    test_file = Path(__file__).parent / "test_project.md"
    if not test_file.exists():
        print("❌ test_project.md not found!")
        return
    
    test_task = test_file.read_text()
    
    # Initialize database
    print("💾 Initializing Database...")
    db_module.db = Database(settings.database_url)
    print("✅ Database ready\n")
    
    # Initialize orchestrator
    print("📋 Initializing Meta-Orchestrator...")
    orchestrator = MetaOrchestrator()
    await orchestrator.initialize()
    print("✅ Meta-Orchestrator ready\n")
    
    print("🎯 Test Project:")
    print("=" * 80)
    print(test_task)
    print("=" * 80)
    
    # Track progress
    await progress_tracker.update(
        "orchestrator",
        "system",
        ProgressStatus.IN_PROGRESS,
        10.0,
        "Analyzing project requirements"
    )
    
    # Create execution plan
    print("\n🗺️  Creating Execution Plan...")
    import uuid
    project_id = str(uuid.uuid4())
    
    try:
        execution_plan = await orchestrator.orchestrate_task(
            task_description=test_task,
            project_id=project_id
        )
        
        await progress_tracker.update(
            "orchestrator",
            "system",
            ProgressStatus.IN_PROGRESS,
            40.0,
            "Execution plan created"
        )
        
        # Display the plan
        print("\n✅ Execution Plan Created!")
        print("=" * 80)
        print(f"\n📊 Plan Overview:")
        print(f"   Project ID: {project_id}")
        print(f"   Phases: {len(execution_plan.phases)}")
        print(f"   Agents Required: {len(execution_plan.agents)}")
        print(f"   Estimated Duration: {execution_plan.estimated_duration} minutes")
        
        # Show phases in detail
        print(f"\n📋 Execution Phases:")
        print("=" * 80)
        for i, phase in enumerate(execution_plan.phases, 1):
            phase_dict = phase if isinstance(phase, dict) else phase.__dict__
            print(f"\n{i}. {phase_dict.get('phase_name', 'Unnamed Phase')}")
            print(f"   Role: {phase_dict.get('required_role', 'Unknown')}")
            print(f"   Duration: {phase_dict.get('estimated_duration', 'Unknown')} min")
            print(f"   Description: {phase_dict.get('description', 'No description')[:100]}...")
            
            # Show deliverables
            deliverables = phase_dict.get('deliverables', [])
            if deliverables:
                print(f"   Deliverables:")
                for deliverable in deliverables[:3]:  # Show first 3
                    print(f"     • {deliverable}")
        
        # Show agent team
        print(f"\n👥 Agent Team Composition:")
        print("=" * 80)
        for agent_spec in execution_plan.agents:
            spec_dict = agent_spec if isinstance(agent_spec, dict) else agent_spec.__dict__
            role = spec_dict.get('role', 'Unknown')
            print(f"\n• {role.upper()} Agent")
            tools = spec_dict.get('tools', [])
            if tools:
                print(f"  Tools: {', '.join(tools[:5])}")
        
        # Show dependencies
        if execution_plan.dependencies:
            print(f"\n🔗 Phase Dependencies:")
            print("=" * 80)
            for dep in execution_plan.dependencies[:5]:  # Show first 5
                dep_dict = dep if isinstance(dep, dict) else dep.__dict__
                print(f"   Phase {dep_dict.get('phase_id', '?')} depends on Phase {dep_dict.get('depends_on', '?')}")
        
        await progress_tracker.update(
            "orchestrator",
            "system",
            ProgressStatus.COMPLETED,
            100.0,
            "Test project analysis completed"
        )
        
        # Show summary
        print("\n" + "=" * 80)
        progress_tracker.display_summary()
        
        print("\n✨ Test Complete!")
        print("\n📝 Summary:")
        print(f"   • The platform successfully analyzed the project")
        print(f"   • Created a {len(execution_plan.phases)}-phase execution plan")
        print(f"   • Assembled a team of {len(execution_plan.agents)} specialized agents")
        print(f"   • Estimated completion time: {execution_plan.estimated_duration} minutes")
        
        print("\n💡 Next Steps:")
        print("   1. Review the execution plan above")
        print("   2. To execute with E2B sandboxes, run: python main.py")
        print("   3. Or modify test_project.md and run this again")
        
        # Save plan to file
        from datetime import datetime
        plan_file = Path(__file__).parent / f"execution_plan_{project_id[:8]}.txt"
        with open(plan_file, 'w') as f:
            f.write(f"EXECUTION PLAN FOR: Task Manager API\n")
            f.write(f"Project ID: {project_id}\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            f.write(f"PHASES ({len(execution_plan.phases)}):\n")
            f.write("=" * 80 + "\n\n")
            for i, phase in enumerate(execution_plan.phases, 1):
                phase_dict = phase if isinstance(phase, dict) else phase.__dict__
                f.write(f"{i}. {phase_dict.get('phase_name', 'Unnamed')}\n")
                f.write(f"   Role: {phase_dict.get('required_role', 'Unknown')}\n")
                f.write(f"   Duration: {phase_dict.get('estimated_duration', 'Unknown')} min\n")
                f.write(f"   Description: {phase_dict.get('description', 'N/A')}\n\n")
        
        print(f"\n💾 Execution plan saved to: {plan_file.name}")
        
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
    asyncio.run(run_test_project())
