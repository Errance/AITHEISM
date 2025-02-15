from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional
from ..utils.discussion_manager import DiscussionManager
from .service import APIService

app = FastAPI(
    title="AI Religion Discussion API",
    description="API for accessing AI religion discussion data",
    version="1.0.0"
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建 API 服务实例
api_service = APIService()

@app.get("/api/discussion/current")
async def get_current_discussion(page: int = 1, page_size: int = 20):
    """获取当前讨论状态
    
    Args:
        page: Page number for messages (1-based)
        page_size: Number of messages per page
    """
    try:
        return await api_service.get_current_discussion(page=page, page_size=page_size)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/discussion/round/{round_num}")
async def get_round_discussion(round_num: int, page: int = 1, page_size: int = 20):
    """获取特定轮次的讨论
    
    Args:
        round_num: Round number to get discussion for
        page: Page number for messages (1-based)
        page_size: Number of messages per page
    """
    try:
        return await api_service.get_current_discussion(round_num=round_num, page=page, page_size=page_size)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/discussion/messages")
async def get_more_messages(page: int = 1, page_size: int = 20):
    """获取更多消息用于无限滚动
    
    Args:
        page: Page number (1-based)
        page_size: Number of messages per page
    """
    try:
        return await api_service.get_more_messages(page=page, page_size=page_size)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/discussion/nodes")
async def get_discussion_nodes():
    """获取所有讨论节点"""
    try:
        return await api_service.get_discussion_nodes()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/discussion/node/{node_id}/history")
async def get_node_history(node_id: int, cursor: Optional[str] = None):
    """获取特定节点的历史"""
    try:
        return await api_service.get_node_history(node_id, cursor)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 