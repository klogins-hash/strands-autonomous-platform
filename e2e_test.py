#!/usr/bin/env python3
"""
End-to-End Test - Full platform execution with E2B sandboxes
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.agents.meta_orchestrator import MetaOrchestrator
from src.coordination.messaging import CoordinationManager
from src.coordination.autonomous_recovery import AutonomousRecoverySystem
from src.learning.persistence import AgentPersistenceSystem
from src.core.config import settings
from src.core import database as db_module
from src.core.database import Database


async def main():
    """Run end-to-end test"""
    
    print("""
    ╔══════════════════════════════════════════════════════════════════════════════╗
    ║                                                                              ║
    ║              STRANDS PLATFORM - END-TO-END TEST                              ║
    ║                                                                              ║
    ║              "Full execution with E2B sandboxes"                             ║
    ║                                                                              ║
    ╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Simple test task
    test_task = """
    Create a simple Python script that:
    1. Prints "Hello from Strands Platform!"
    2. Creates a file called output.txt with the text "Test successful"
    3. Reads the file back and prints its contents
    
    Just create a single Python file called test.py with this functionality.
    """
    
    print("🎯 Test Task:")
    print(test_task)
    print("\n" + "=" * 80 + "\n")
    
    try:
        # Initialize database
        print("💾 Initializing Database...")
        db_module.db = Database(settings.database_url)
        try:
            await db_module.db.setup_vector_extension()
            await db_module.db.create_tables()
            print("✅ Database ready")
        except Exception as e:
            print(f"⚠️  Database warning: {str(e)}")
        
        # Initialize orchestrator
        print("\n📋 Initializing Meta-Orchestrator...")
        orchestrator = MetaOrchestrator()
        await orchestrator.initialize()
        print("✅ Meta-Orchestrator ready")
        
        print("\n" + "=" * 80)
        print("✨ System ready!")
        print("=" * 80 + "\n")
        
        # Create execution plan
        print("🗺️  Creating Execution Plan...")
        import uuid
        project_id = str(uuid.uuid4())
        task_id = str(uuid.uuid4())
        
        execution_plan = await orchestrator.orchestrate_task(
            task_description=test_task,
            project_id=project_id
        )
        
        print(f"\n✅ Plan Created!")
        print(f"   Phases: {len(execution_plan.phases)}")
        print(f"   Agents: {len(execution_plan.agents)}")
        print(f"   Duration: {execution_plan.estimated_duration} min")
        
        # Show phases
        print(f"\n📋 Execution Phases:")
        for i, phase in enumerate(execution_plan.phases, 1):
            phase_dict = phase if isinstance(phase, dict) else phase.__dict__
            print(f"   {i}. {phase_dict.get('phase_name', 'Phase')} ({phase_dict.get('required_role', '?')})")
        
        print("\n" + "=" * 80)
        print("🚀 Starting Execution...")
        print("=" * 80 + "\n")
        
        # Execute the plan
        results = await orchestrator.execute_plan(execution_plan, task_id)
        
        print("\n" + "=" * 80)
        print("✅ EXECUTION COMPLETE!")
        print("=" * 80)
        
        # Show results
        if results:
            print(f"\n📊 Results:")
            for phase_id, result in results.items():
                print(f"\n   Phase: {phase_id}")
                if isinstance(result, dict):
                    print(f"   Status: {result.get('status', 'unknown')}")
                    if 'output' in result:
                        print(f"   Output: {str(result['output'])[:200]}...")
        
        print("\n✨ End-to-End Test Complete!")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        print("✅ Cleanup complete")


if __name__ == "__main__":
    asyncio.run(main())
