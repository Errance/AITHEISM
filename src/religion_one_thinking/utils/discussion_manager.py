import asyncio
from ..utils.key_manager import KeyManager

class DiscussionManager:
    _orchestrator = None
    _key_manager = None
    
    @classmethod
    def get_orchestrator(cls):
        """获取 orchestrator 实例"""
        if cls._orchestrator is None:
            from ..discussion.orchestrator import DiscussionOrchestrator
            cls._orchestrator = DiscussionOrchestrator()
            print(f"Created new orchestrator instance: {id(cls._orchestrator)}")
        else:
            print(f"Using existing orchestrator instance: {id(cls._orchestrator)}")
            
        # 检查 orchestrator 的状态
        if hasattr(cls._orchestrator, 'discussion_chain'):
            print(f"Discussion chain exists: {id(cls._orchestrator.discussion_chain)}")
            if cls._orchestrator.discussion_chain:
                print(f"Number of points: {len(cls._orchestrator.discussion_chain.points)}")
                print(f"Current round: {cls._orchestrator.current_round}")
        else:
            print("Warning: orchestrator has no discussion_chain")
            
        return cls._orchestrator
        
    @classmethod
    def reset(cls):
        """重置 orchestrator 实例（用于测试）"""
        cls._orchestrator = None
        print("Orchestrator instance reset")

    @classmethod
    def get_key_manager(cls):
        if cls._key_manager is None:
            cls._key_manager = KeyManager()
        return cls._key_manager