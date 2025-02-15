from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from pathlib import Path
import json

class DiscussionPoint:
    """讨论点节点"""
    def __init__(self, content: str, round_num: int, parent_id: Optional[str] = None):
        self.id = f"point_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        self.content = content
        self.round_num = round_num
        self.parent_id = parent_id
        self.status = "ongoing"
        self.conclusion = None
        self.agreements = []
        self.disagreements = []
        self.consensus_score = 0.0
        self.participants = set()
        
    def add_response(self, response: Dict[str, Any]):
        """添加 AI 的回复"""
        try:
            author = response["author"]
            content = response["content"]
            self.participants.add(author)
            
            # 分析回复类型
            if self._is_agreement(content):
                self.agreements.append({
                    "author": author,
                    "content": content,
                    "timestamp": datetime.utcnow().isoformat()
                })
            else:
                self.disagreements.append({
                    "author": author,
                    "content": content,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
            # 更新共识状态
            self._update_consensus()
            
        except Exception as e:
            print(f"Error adding response to point: {str(e)}")
            raise
            
    def _is_agreement(self, content: str) -> bool:
        """检查是否为赞同回复"""
        agreement_markers = [
            "I agree", "I propose", "I suggest", "I consider",
            "I observe", "Indeed", "Exactly", "True"
        ]
        return any(marker.lower() in content.lower() for marker in agreement_markers)
        
    def _update_consensus(self):
        """更新共识状态"""
        if not self.participants:
            return
            
        # 计算共识分数
        total_responses = len(self.agreements) + len(self.disagreements)
        if total_responses > 0:
            agreement_ratio = len(self.agreements) / total_responses
            self.consensus_score = agreement_ratio
            
            # 如果达到一定共识，标记为已结束
            if len(self.participants) >= 3 and agreement_ratio > 0.7:
                self.status = "concluded"
                self._generate_conclusion()
                
    def _generate_conclusion(self):
        """生成结论"""
        if self.agreements:
            # 使用最后一个赞同回复作为结论
            self.conclusion = self.agreements[-1]["content"]

class DiscussionChain:
    """管理讨论链"""
    def __init__(self, initial_question: str):
        # 初始问题是第一轮的讨论点
        self.points = [DiscussionPoint(initial_question, round_num=1)]

    def get_active_points(self) -> List[DiscussionPoint]:
        """获取仍在讨论中的点"""
        return [p for p in self.points if p.status == "ongoing"]

    def get_concluded_points(self) -> List[DiscussionPoint]:
        """获取已达成结论的点"""
        return [p for p in self.points if p.status == "concluded"]

    def add_response(self, point: Union[str, DiscussionPoint], response: dict):
        """添加回复到讨论点"""
        try:
            if isinstance(point, str):
                existing_point = next(
                    (p for p in self.points if p.content == point), 
                    None
                )
                if existing_point:
                    point = existing_point
                else:
                    point = DiscussionPoint(
                        content=point,
                        round_num=response.get("round_num", 1)
                    )
                    self.points.append(point)
            
            # 添加响应并更新状态
            point.add_response(response)
            
        except Exception as e:
            print(f"Error adding response: {str(e)}")
            raise

    async def analyze_round(self, round_num: int, responses: List[Dict[str, str]]):
        """分析一轮讨论"""
        try:
            # 更新现有讨论点
            for point in self.get_active_points():
                relevant_responses = [
                    r for r in responses 
                    if self._is_response_relevant(point.content, r["content"])
                ]
                for response in relevant_responses:
                    point.add_response(response)
            
            # 提取新的讨论点
            new_points = self._extract_new_points(responses, round_num)
            self.points.extend(new_points)
            
        except Exception as e:
            print(f"Error analyzing round: {str(e)}")
            raise

    def _is_response_relevant(self, point_content: str, response_content: str) -> bool:
        """检查回复是否与讨论点相关"""
        # 提取关键词（去除常见停用词）
        keywords = set(point_content.lower().split()) - {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for"
        }
        return any(keyword in response_content.lower() for keyword in keywords)

    def _extract_new_points(self, responses: List[Dict[str, str]], round_num: int) -> List[DiscussionPoint]:
        """从回复中提取新的讨论点"""
        new_points = []
        for response in responses:
            # 寻找问题句（以问号结尾的句子）
            content = response["content"]
            questions = [s.strip() + "?" for s in content.split("?") if s.strip()]
            
            for question in questions:
                if not any(p.content == question for p in self.points):
                    new_points.append(DiscussionPoint(question, round_num=round_num))
                    
        return new_points

    def save_chain(self, path: str = "discussion_chain.json"):
        """保存讨论链"""
        chain_data = {
            "points": [point.to_dict() for point in self.points]
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(chain_data, f, ensure_ascii=False, indent=2)

    def get_discussion_summary(self) -> Dict[str, Any]:
        """获取讨论总结"""
        return {
            "total_points": len(self.points),
            "concluded_points": len(self.get_concluded_points()),
            "active_points": len([p for p in self.points if p.status == "ongoing"]),
            "latest_conclusions": [
                {
                    "point": p.content,
                    "conclusion": p.conclusion
                }
                for p in self.get_concluded_points()[-3:]  # 最近3个结论
            ]
        } 