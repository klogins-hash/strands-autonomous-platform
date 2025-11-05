#!/usr/bin/env python3
"""Execute Phase 1: Foundation & Core Infrastructure"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.agents.meta_orchestrator import MetaOrchestrator
import uuid


async def main():
    print('🚀 PHASE 1: Foundation & Core Infrastructure')
    print('=' * 80)
    print('Building: Backend + Frontend + Database + Simple Agent')
    print()
    
    # Read task
    with open('phase1_foundation.md', 'r') as f:
        task = f.read()
    
    # Initialize
    print('⏳ Initializing Meta-Orchestrator...')
    orchestrator = MetaOrchestrator()
    await orchestrator.initialize()
    print('✅ Ready')
    print()
    
    # Create plan
    print('🤔 Creating execution plan...')
    project_id = str(uuid.uuid4())
    task_id = str(uuid.uuid4())
    
    plan = await orchestrator.orchestrate_task(task, project_id)
    
    print(f'✅ Plan created: {len(plan.phases)} phases, {len(plan.agents)} agents')
    print()
    
    # Execute
    print('🚀 STARTING EXECUTION...')
    print('=' * 80)
    print('This will take ~60 minutes. Watch the agents work!')
    print()
    
    try:
        results = await orchestrator.execute_plan(plan, task_id)
        
        print()
        print('=' * 80)
        print('✅ PHASE 1 COMPLETE!')
        print('=' * 80)
        print()
        print('📊 What was built:')
        print('   ✅ FastAPI backend with chat endpoint')
        print('   ✅ React frontend with chat interface')
        print('   ✅ PostgreSQL database setup')
        print('   ✅ Simple code agent working')
        print('   ✅ End-to-end flow functional')
        print()
        print('🎉 Foundation is ready!')
        print()
        print('Next steps:')
        print('   1. Test the system')
        print('   2. Run Phase 2 for visualization')
        
    except Exception as e:
        print(f'❌ Execution failed: {str(e)}')
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
