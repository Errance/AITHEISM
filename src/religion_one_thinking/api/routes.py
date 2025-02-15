from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
from pydantic import BaseModel, ValidationError
from datetime import datetime
from ..discussion.orchestrator import DiscussionOrchestrator
from ..utils.config import load_config
from .service import APIService
from dotenv import load_dotenv
import os
from ..utils.discussion_manager import DiscussionManager
import json
import logging
from ..utils.file_utils import read_round_data

# 环境变量已经通过 docker-compose 加载
# load_dotenv("src/religion_one_thinking/.env")  # 删除这行

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

# Models
class ChatMessage(BaseModel):
    model: str
    content: str
    createdAt: datetime
    roundNum: int

class ArgumentNode(BaseModel):
    id: int
    argument: str
    size: int
    roundNum: int
    status: str  # "ongoing" or "completed"

class ChatHistory(BaseModel):
    messages: List[ChatMessage]
    hasMore: bool
    nextCursor: str | None
    roundNum: int

class AgoraResponse(BaseModel):
    messages: List[ChatMessage]
    currentRound: int
    roundStatus: str  # "ongoing" or "completed"
    nextRoundStart: Optional[datetime]
    remainingTime: Optional[int]  # seconds until next round

class DiscussRequest(BaseModel):
    question: str

class AgoraMessage(BaseModel):
    type: str  # "get_messages"
    page: int = Query(1, ge=1)
    page_size: int = Query(20, ge=1, le=100)
    round_num: Optional[int] = None

# 创建服务实例
api_service = APIService()

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化 orchestrator
@app.on_event("startup")
async def startup_event():
    """在应用启动时初始化 orchestrator"""
    try:
        orchestrator = DiscussionManager.get_orchestrator()
        # 读取初始问题
        with open("src/religion_one_thinking/thesis.txt", "r") as f:
            initial_question = f.read().strip()
        # 初始化讨论
        await orchestrator.initialize(initial_question)
        print("Orchestrator initialized successfully")
    except Exception as e:
        print(f"Error initializing orchestrator: {e}")
        raise

def read_round_data(round_num: int) -> dict:
    """安全地读取轮次数据"""
    file_path = f"discussions/round_{round_num}.json"
    try:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    content = f.read()
                    print(f"Reading file {file_path}, size: {len(content)} bytes")
                    data = json.loads(content)
                    return data
                except json.JSONDecodeError as e:
                    print(f"JSON decode error in {file_path}: {str(e)}")
                    print(f"Content preview: {content[:100]}...")
                    return {}
        return {}
    except Exception as e:
        print(f"Error reading {file_path}: {str(e)}")
        return {}

class AgoraWebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except WebSocketDisconnect:
                self.disconnect(connection)

agora_manager = AgoraWebSocketManager()

@app.get("/agora")
async def get_agora(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    round_num: Optional[int] = None
):
    """获取当前讨论状态，支持分页"""
    try:
        all_messages = []
        latest_round = 0
        
        if round_num:
            round_data = read_round_data(round_num)
            if round_data and "points" in round_data:
                latest_round = round_num
                for point in round_data["points"]:
                    for response in point.get("agreements", []) + point.get("disagreements", []):
                        all_messages.append({
                            "model": response["author"],
                            "content": response["content"][:8000],  # 增加到 8000 字符
                            "timestamp": response.get("timestamp", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")),
                            "round_num": round_num
                        })
        else:
            for r in range(1, load_config()["discussion"]["max_rounds"] + 1):
                round_data = read_round_data(r)
                if not round_data:
                    break
                latest_round = r
                if "points" in round_data:
                    for point in round_data["points"]:
                        for response in point.get("agreements", []) + point.get("disagreements", []):
                            all_messages.append({
                                "model": response["author"],
                                "content": response["content"][:8000],  # 增加到 8000 字符
                                "timestamp": response.get("timestamp", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")),
                                "round_num": r
                            })
        
        # 按时间正序排序
        all_messages.sort(key=lambda x: x["timestamp"])
        
        # 计算分页
        total_messages = len(all_messages)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_messages = all_messages[start_idx:end_idx]
        
        return {
            "messages": paginated_messages,
            "currentRound": latest_round,
            "roundStatus": "ongoing",
            "pagination": {
                "total": total_messages,
                "page": page,
                "page_size": page_size,
                "total_pages": (total_messages + page_size - 1) // page_size,
                "has_more": end_idx < total_messages
            },
            "debug_info": {
                "messages_per_round": {
                    i: len([m for m in all_messages if m["round_num"] == i])
                    for i in range(1, latest_round + 1)
                },
                "total_messages": total_messages,
                "latest_round": latest_round,
                "files_found": [i for i in range(1, latest_round + 1) if os.path.exists(f"discussions/round_{i}.json")],
                "max_rounds": load_config()["discussion"]["max_rounds"]
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_agora: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/agora")
async def agora_websocket(websocket: WebSocket):
    """WebSocket endpoint for Agora messages with pagination"""
    await agora_manager.connect(websocket)
    try:
        while True:
            try:
                data = await websocket.receive_json()
                try:
                    message = AgoraMessage(**data)
                    if message.type == "get_messages":
                        response = await get_agora(
                            page=message.page,
                            page_size=message.page_size,
                            round_num=message.round_num
                        )
                        await websocket.send_json(response)
                    else:
                        await websocket.send_json({
                            "error": f"Unknown message type: {message.type}"
                        })
                except ValidationError as e:
                    await websocket.send_json({
                        "error": f"Invalid message format: {str(e)}"
                    })
            except Exception as e:
                await websocket.send_json({
                    "error": f"Error processing message: {str(e)}"
                })
    except WebSocketDisconnect:
        agora_manager.disconnect(websocket)

# Get all argument nodes
@app.get("/discussion/nodes")
async def get_discussion_nodes():
    """获取所有讨论节点"""
    try:
        orchestrator = DiscussionManager.get_orchestrator()
        logger.info(f"Current round: {orchestrator.current_round}")
        
        all_nodes = []
        current_round = orchestrator.current_round
        
        for round_num in range(1, current_round + 1):
            round_data = read_round_data(round_num)
            if not round_data or "points" not in round_data:
                continue
                
            for point in round_data["points"]:
                # 使用原始 ID
                point_id = point.get("id")
                if not point_id:  # 如果没有 ID 才生成
                    timestamp = point.get("timestamp")
                    if isinstance(timestamp, datetime):
                        timestamp = timestamp.isoformat()
                    elif not isinstance(timestamp, str):
                        timestamp = datetime.utcnow().isoformat()
                    point_id = f"point_{datetime.fromisoformat(timestamp).strftime('%Y%m%d_%H%M%S')}"
                
                logger.info(f"Using point ID: {point_id}")
                
                all_nodes.append({
                    "id": point_id,
                    "content": point["content"],
                    "round_num": round_num,
                    "status": "concluded" if round_num < current_round else "ongoing",
                    "agreements": point.get("agreements", []),
                    "disagreements": point.get("disagreements", [])
                })
            
        return all_nodes
    except Exception as e:
        logger.error(f"Error in get_discussion_nodes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Get chat history for a specific node
@app.get("/discussion/nodes/{node_id}/history")
async def get_node_history(
    node_id: str,
    page: int = Query(1, ge=1),  # 页码，从1开始
    page_size: int = Query(20, ge=1, le=100)  # 每页消息数，最多100条
):
    """获取特定节点的历史，支持分页"""
    try:
        logger.info(f"Getting history for node: {node_id}, page: {page}, page_size: {page_size}")
        
        # 获取当前轮次
        orchestrator = DiscussionManager.get_orchestrator()
        current_round = orchestrator.current_round
        
        # 遍历轮次查找节点
        for round_num in range(1, current_round + 1):
            round_data = read_round_data(round_num)
            if not round_data:
                continue
                
            if "points" in round_data:
                for point in round_data["points"]:
                    point_id = point.get("id")
                    if not point_id:
                        timestamp = point.get("timestamp")
                        if isinstance(timestamp, datetime):
                            timestamp = timestamp.isoformat()
                        elif not isinstance(timestamp, str):
                            timestamp = datetime.utcnow().isoformat()
                        point_id = f"point_{datetime.fromisoformat(timestamp).strftime('%Y%m%d_%H%M%S')}"
                    
                    if point_id == node_id:
                        messages = []
                        responses = point.get("agreements", []) + point.get("disagreements", [])
                        
                        # 按时间正序排序
                        responses.sort(key=lambda x: x.get("timestamp", ""))
                        
                        # 计算分页
                        start_idx = (page - 1) * page_size
                        end_idx = start_idx + page_size
                        paginated_responses = responses[start_idx:end_idx]
                        
                        for response in paginated_responses:
                            resp_timestamp = response.get("timestamp")
                            if isinstance(resp_timestamp, datetime):
                                resp_timestamp = resp_timestamp.isoformat()
                            messages.append({
                                "model": response["author"],
                                "content": response["content"][:8000],  # 增加到 8000 字符
                                "timestamp": resp_timestamp,
                                "round_num": round_num
                            })
                            
                        return {
                            "messages": messages,
                            "pagination": {
                                "total": len(responses),
                                "page": page,
                                "page_size": page_size,
                                "total_pages": (len(responses) + page_size - 1) // page_size,
                                "has_more": end_idx < len(responses)
                            },
                            "roundNum": round_num
                        }
        
        raise HTTPException(
            status_code=404,
            detail=f"Node {node_id} not found in any round up to {current_round}"
        )
    except Exception as e:
        logger.error(f"Error getting node history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def save_discussion_data(data: dict, file_path: str):
    """Save discussion data with datetime handling"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, cls=DateTimeEncoder, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving progress: {str(e)}")

@app.post("/discuss")
async def discuss(request: DiscussRequest):
    """处理新的讨论请求"""
    try:
        # 获取 orchestrator 实例
        orchestrator = DiscussionManager.get_orchestrator()
        
        # 初始化新的讨论
        await orchestrator.initialize(request.question)
        
        # 返回初始状态
        return {
            "status": "success",
            "message": "Discussion initialized",
            "question": request.question
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 