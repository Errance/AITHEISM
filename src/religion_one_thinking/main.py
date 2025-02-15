import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from .discussion.orchestrator import DiscussionOrchestrator
from .utils.logger import DiscussionLogger
from .utils.discussion_manager import DiscussionManager
import shutil

async def main():
    """Main entry point"""
    # Load environment variables
    load_dotenv()
    
    # Initialize logger
    logger = DiscussionLogger()
    
    try:
        # 清理讨论文件，但保留目录
        discussions_dir = "discussions"
        for f in os.listdir(discussions_dir):
            if f != '.gitkeep':
                os.remove(os.path.join(discussions_dir, f))
        
        # Read initial question
        with open("src/religion_one_thinking/thesis.txt", "r") as f:
            initial_question = f.read().strip()
            
        # Create orchestrator
        orchestrator = DiscussionManager.get_orchestrator()
        await orchestrator.initialize(initial_question)
        
        # Start discussion
        await orchestrator.run_discussion()
        
    except Exception as e:
        logger.log_error(f"Main process error: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 