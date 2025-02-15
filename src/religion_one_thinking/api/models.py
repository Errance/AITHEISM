from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime

class Response(BaseModel):
    """AI 回应的数据模型"""
    author: str
    content: str
    timestamp: datetime
    point_type: Optional[str] = None

class DiscussionPoint(BaseModel):
    """讨论观点节点的数据模型"""
    id: str
    content: str = Field(..., description="观点的完整内容")
    summary: str = Field(..., description="观点的简短摘要，用于树状显示")
    round_num: int = Field(..., description="讨论轮次")
    parent_id: Optional[str] = Field(None, description="父观点ID")
    point_type: Optional[str] = Field(None, description="观点类型：proposal/agreement/disagreement等")
    status: str = Field(..., description="观点状态：ongoing/concluded")
    consensus_score: float = Field(..., ge=0, le=1, description="共识度分数")
    children: List['DiscussionPoint'] = Field(default_factory=list, description="子观点列表")

class DiscussionHistory(BaseModel):
    """观点的详细讨论历史"""
    point_id: str
    content: str = Field(..., description="观点内容")
    responses: List[Response] = Field(..., description="AI的回应列表")
    consensus_score: float = Field(..., description="共识度")
    participants: List[str] = Field(..., description="参与讨论的AI列表")
    conclusion: Optional[str] = Field(None, description="如果已达成结论，这里是结论内容")
    created_at: datetime
    updated_at: datetime

class ThesisResponse(BaseModel):
    """初始问题的响应模型"""
    thesis: str = Field(..., description="初始讨论问题")
    description: Optional[str] = Field(None, description="问题的详细描述")
    created_at: datetime

class PaginationParams(BaseModel):
    """分页参数"""
    offset: int = Field(0, ge=0, description="起始位置")
    limit: int = Field(10, gt=0, le=50, description="每页数量")
    depth: Optional[int] = Field(None, ge=0, description="加载的深度")

class PageInfo(BaseModel):
    """分页信息"""
    total: int = Field(..., description="总数")
    has_next: bool = Field(..., description="是否有下一页")
    next_offset: Optional[int] = Field(None, description="下一页的起始位置")

class DiscussionTreeResponse(BaseModel):
    """讨论树的响应模型"""
    root: DiscussionPoint
    total_points: int
    concluded_points: int
    active_points: int
    max_depth: int
    page_info: PageInfo
    has_more_children: Dict[str, bool] = Field(
        default_factory=dict, 
        description="每个节点是否还有更多子节点的映射"
    ) 