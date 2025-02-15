import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import json
from ..thinkers.base_thinker import BaseThinker
from rich.console import Console
from ..config import load_config
from ..utils.logger import DiscussionLogger
from ..utils.memory_agent import MemoryAgent
from .discussion_chain import DiscussionChain
from .discussion_point import DiscussionPoint
import logging
from ..thinkers.context_processor import ContextProcessor
from ..thinkers import GPTThinker, ClaudeThinker, GeminiThinker, DeepSeekThinker, QwenThinker
import os
from ..utils.key_manager import KeyManager
from ..utils.discussion_manager import DiscussionManager
from ..utils.file_utils import read_round_data

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DiscussionOrchestrator:
    """
    Orchestrates the multi-AI discussion process.
    
    This class manages:
    - Discussion initialization and flow
    - AI response coordination
    - State saving and recovery
    - Error handling and logging
    
    Attributes:
        thinkers (List[BaseThinker]): List of AI participants
        max_rounds (int): Maximum discussion rounds
        save_path (Path): Path for saving discussion states
    """

    def __init__(self):
        # 从 key_manager 获取一个 key
        key_manager = DiscussionManager.get_key_manager()  # 使用 DiscussionManager
        api_key = key_manager.get_current_key()

        self.thinkers = [
            GPTThinker(api_key=api_key),
            ClaudeThinker(api_key=api_key),
            GeminiThinker(api_key=api_key),
            DeepSeekThinker(api_key=api_key),
            QwenThinker(api_key=api_key)
        ]
        self.discussion_chain = None
        self.logger = DiscussionLogger()
        self.current_round = 0
        self.round_start_time = None
        self.round_duration = 180  # 3 minutes
        self.config = load_config()
        self.max_rounds = self.config["discussion"]["max_rounds"]
        self.initial_question = None
        self.context_processor = ContextProcessor(api_key=api_key)
        self.discussion_dir = "discussions"  # 确保这个路径是正确的
        
    async def initialize(self, initial_question: str):
        """Initialize discussion with question"""
        self.initial_question = initial_question
        self.discussion_chain = DiscussionChain(initial_question)
        self.round_start_time = datetime.utcnow()
        self.current_round = 1
        logger.info(f"Initialized orchestrator with current_round: {self.current_round}")
        
    async def get_current_state(self) -> dict:
        """Get current discussion state"""
        try:
            # 获取当前活跃的讨论点
            active_points = self.discussion_chain.get_active_points() if self.discussion_chain else []
            
            # 获取当前轮次的所有消息
            messages = []
            for point in self.discussion_chain.points:  # 从所有点中获取消息
                if point.round_num == self.current_round:  # 只获取当前轮次的消息
                    for response in point.agreements + point.disagreements:
                        messages.append({
                            "model": response["author"],
                            "content": response["content"],
                            "timestamp": datetime.utcnow()
                        })
            
            # 添加调试信息
            print(f"Current round: {self.current_round}")
            print(f"Number of messages: {len(messages)}")
            print(f"Active points: {[p.content for p in active_points]}")
            
            return {
                "status": "ongoing" if self.discussion_chain else "not_started",
                "messages": messages,
                "round": self.current_round,
                "remaining_time": 0  # 移除时间计算，因为不再需要
            }
        except Exception as e:
            print(f"Error in get_current_state: {str(e)}")  # 添加错误日志
            raise Exception(f"Error getting current state: {str(e)}")
        
    def _get_current_messages(self) -> List[dict]:
        """Get messages from current round"""
        messages = []
        for point in self.discussion_chain.get_active_points():
            if point.round_num == self.current_round:
                for response in point.agreements + point.disagreements:
                    messages.append({
                        "model": response["author"],
                        "content": response["content"],
                        "timestamp": datetime.utcnow()
                    })
        return messages

    async def _safe_think(self, thinker: BaseThinker, point: str, round_num: int) -> Dict[str, str]:
        """Safely execute a thinker's response"""
        try:
            response = await thinker.think(point, round_num)
            if response and isinstance(response, dict):
                return response
            
        except Exception as e:
            error_msg = f"Error with {thinker.name}: {str(e)}"
            self.logger.log_error(error_msg)
            self.console.print(f"[red]{error_msg}[/]")
            return None

    async def _discuss_point(self, point: str, round_num: int) -> List[Dict[str, str]]:
        """Discuss a single point"""
        responses = []
        for thinker in self.thinkers:
            self.console.print(f"\n[bold blue]🤖 {thinker.name} discussing: {point}[/]")
            response = await self._safe_think(thinker, point, round_num)
            if response:
                responses.append(response)
                # Save to memory
                self.memory_agent.add_memory(
                    content=response["content"],
                    author=response["author"],
                    round_num=round_num
                )
                # Add short delay to avoid API rate limits
                await asyncio.sleep(0.5)
        return responses

    async def conduct_round(self, round_num: int) -> List[Dict[str, str]]:
        """Conduct one round of discussion"""
        all_responses = []
        active_points = self.discussion_chain.get_active_points()
        
        for point in active_points:
            responses = await self._discuss_point(point, round_num)
            all_responses.extend(responses)
            
        # Update discussion chain
        self.discussion_chain.analyze_round(round_num, all_responses)
        
        # Save discussion chain
        self.discussion_chain.save_chain(f"discussions/chain_{round_num}.json")
        
        # Print current discussion status
        self._print_discussion_status(round_num)
        
        return all_responses

    def _enhance_prompt(self, original_prompt: str, discussion_state: Dict[str, Any]) -> str:
        """增强提示，引导讨论方向"""
        enhanced = f"{original_prompt}\n\n"
        
        if discussion_state["resolved_points"]:
            enhanced += "\nResolved points (no need to discuss further):\n"
            for point, conclusion in discussion_state["resolved_points"].items():
                enhanced += f"- {point}\n"
        
        if discussion_state["unresolved_points"]:
            enhanced += "\nPoints that need further discussion:\n"
            for point in discussion_state["unresolved_points"]:
                enhanced += f"- {point}\n"
            
        if discussion_state["suggested_focus"]:
            enhanced += f"\nSuggested focus for this round:\n{discussion_state['suggested_focus']}"
        
        return enhanced

    async def conduct_discussion(self):
        """Conduct the discussion process"""
        try:
            self.console.print("\n[bold cyan]╔══ Starting AI Religion Discussion ══╗[/]")
            current_topic = self.initial_question
            
            for round_num in range(self.max_rounds):
                self.logger.log_round_start(round_num)
                round_start_time = datetime.now()
                
                # Display round status
                self.console.print(f"\n[bold green]Round {round_num + 1}[/]")
                self.console.print(f"\n[cyan]Current Topic:[/]\n{current_topic}\n")
                
                # Collect responses from thinkers
                responses = []
                for thinker in self.thinkers:
                    self.console.print(f"\n[bold blue]🤖 {thinker.name} is thinking...[/]")
                    response = await self._safe_think(thinker, current_topic, round_num)
                    if response:
                        responses.append(response)
                        self.logger.log_thinker_response(
                            thinker.name, 
                            response["content"]
                        )
                
                # Process responses and update topic for next round
                if responses:
                    discussion_points = [r["content"] for r in responses]
                    round_summary = await self.context_processor.summarize_discussion(
                        discussion_points
                    )
                    self.logger.log_summary(round_num, round_summary)
                    
                    # Update topic for next round
                    current_topic = (
                        f"Based on the previous discussion:\n{round_summary}\n\n"
                        "Please continue the discussion, focusing on the key points raised "
                        "and developing the ideas further."
                    )
                
                # Save progress
                self._save_round_progress(round_num, responses)
                
                # Display round results
                self._print_round_results(round_num, round_start_time)
            
            self.console.print("\n[bold cyan]╚══ Discussion Complete ══╝[/]")
            
        except Exception as e:
            error_msg = f"Discussion error: {str(e)}"
            self.logger.log_error(error_msg)
            self.console.print(f"[red]{error_msg}[/]")
            raise
        
    async def load_thesis(self) -> str:
        """Load the discussion thesis."""
        thesis_path = Path("src/religion_one_thinking/thesis.txt")
        return thesis_path.read_text(encoding="utf-8")
        
    async def load_description(self) -> str:
        """Load the discussion description."""
        desc_path = Path("src/religion_one_thinking/description.txt")
        return desc_path.read_text(encoding="utf-8")

    def save_discussion_state(self, round_num: int, responses: List[Dict[str, str]]):
        """
        Save the current discussion state.
        
        Args:
            round_num: Current round number
            responses: List of AI responses
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        save_file = self.save_path / f"discussion_round_{round_num}_{timestamp}.json"
        
        state = {
            "round": round_num,
            "timestamp": timestamp,
            "responses": responses,
            "discussion_summary": self.discussion_chain.get_discussion_summary()
        }
        
        with open(save_file, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
            
        self.console.print(f"[blue]Discussion state saved to {save_file}[/]")

    def _print_discussion_status(self, round_num: int):
        """Print current discussion status"""
        active_points = self.discussion_chain.get_active_points()
        concluded_points = [p for p in self.discussion_chain.points 
                           if p.status == "concluded"]
        
        self.console.print(f"\n[bold]===== Round {round_num} Status =====[/]")
        
        if concluded_points:
            self.console.print("\n[green]Concluded Points:[/]")
            for point in concluded_points:
                self.console.print(f"✓ {point.content}")
        
        if active_points:
            self.console.print("\n[yellow]Active Points for Discussion:[/]")
            for point in active_points:
                self.console.print(f"• {point}")
        
        self.console.print("\n" + "=" * 50 + "\n")

    def _print_round_status(self, round_num: int, points: List[Any]):
        """Display the current round status"""
        self.console.print(f"\n[bold green]Round {round_num + 1}[/]")
        self.console.print("\n[cyan]Discussion Points:[/]")
        for point in points:
            self.console.print(f"• {point.content[:100]}...")

    def _print_round_results(self, round_num: int, start_time: datetime):
        """Display the results of a discussion round"""
        duration = datetime.now() - start_time
        self.console.print(f"\n[green]Round {round_num + 1} completed in {duration.total_seconds():.2f}s[/]")
        
        # Show conclusions if any
        concluded_points = self.discussion_chain.get_concluded_points()
        if concluded_points:
            self.console.print("\n[yellow]Conclusions reached:[/]")
            for point in concluded_points:
                if point.conclusion:
                    self.console.print(f"✓ {point.conclusion[:100]}...")

    # 建议添加：
    # - 异常处理机制
    # - 讨论进度保存功能
    # - 可配置的轮次控制 

    async def run_discussion(self):
        """Run the discussion process"""
        try:
            for round_num in range(self.max_rounds):
                self.current_round = round_num + 1
                self.logger.log_round_start(self.current_round)
                print(f"\n=== Round {self.current_round} ===\n")
                
                # 获取当前讨论点
                if self.current_round == 1:
                    current_points = [self.initial_question]
                else:
                    previous_responses = self._get_previous_round_responses()
                    current_points = await self._generate_next_round_points(previous_responses)
                    print("\nNew discussion points for this round:")
                    for i, point in enumerate(current_points, 1):
                        print(f"{i}. {point.strip('1234567890. ')}")  # 移除编号
                    print("\n")
                
                # 为每个 AI 分配一个讨论点
                for i, thinker in enumerate(self.thinkers):
                    point = current_points[i % len(current_points)]  # 循环分配
                    try:
                        print(f"🤖 {thinker.name} discussing: {point}")
                        response = await thinker.think(point, self.current_round)
                        
                        if isinstance(response, dict) and "content" in response:
                            print(f"Response: {response['content']}\n")
                            self.discussion_chain.add_response(point, response)
                            self.logger.log_response(thinker.name, point, response["content"])
                        else:
                            print("Error: Invalid response format\n")
                    except Exception as e:
                        error_msg = f"Error occurred: {str(e)}"
                        print(error_msg)
                        self.logger.log_error(error_msg)
                
                # 保存本轮进度
                self._save_round_progress(self.current_round)
                
                # 显示本轮状态
                print(f"\n===== Round {self.current_round} Status =====\n")
                print("Active Points for Discussion:")
                active_points = self.discussion_chain.get_active_points()
                for point in active_points:
                    print(f"• {point.content}")
                print("\n" + "=" * 50 + "\n")
                
                # 更新轮次开始时间
                self.round_start_time = datetime.utcnow()
                
                # 等待一小段时间再进入下一轮
                await asyncio.sleep(2)

        except Exception as e:
            error_msg = f"Error occurred: {str(e)}"
            print(error_msg)
            self.logger.log_error(error_msg)

    def _get_previous_round_responses(self) -> List[str]:
        """获取上一轮的所有回复"""
        responses = []
        for point in self.discussion_chain.points:
            if point.round_num == self.current_round - 1:
                for response in point.agreements + point.disagreements:
                    responses.append(response["content"])
        return responses

    async def _generate_next_round_points(self, previous_responses: List[str]) -> List[str]:
        """根据上一轮的回复生成新的讨论点"""
        try:
            # 生成总结
            summary = await self.context_processor.summarize_discussion(previous_responses)
            
            # 基于总结生成新的讨论点
            follow_up_prompt = (
                f"Based on this summary:\n{summary}\n\n"
                "Generate 2-3 specific questions that will help deepen the discussion "
                "and explore the most interesting or controversial points raised."
            )
            
            # 生成新的讨论点
            questions = await self.context_processor.analyze_patterns([follow_up_prompt])
            if questions:
                # 提取问题（包含问号的句子），并确保是新的问题
                new_points = [q.strip() for q in questions.split('\n') if '?' in q]
                # 只返回最新的2-3个问题
                return new_points[:3]
            
            return [self.initial_question]
        
        except Exception as e:
            self.logger.log_error(f"Error generating next round points: {str(e)}")
            return [self.initial_question]

    def _save_round_progress(self, round_num: int):
        """Save the current round's progress"""
        try:
            save_dir = Path("discussions")
            save_dir.mkdir(exist_ok=True)
            
            class DateTimeEncoder(json.JSONEncoder):
                def default(self, obj):
                    if isinstance(obj, datetime):
                        return obj.isoformat()
                    return super().default(obj)
                
            data = {
                "round_num": round_num,
                "timestamp": datetime.utcnow(),
                "points": [
                    {
                        "id": point.id,
                        "content": point.content,
                        "round_num": point.round_num,
                        "status": point.status,
                        "agreements": point.agreements,
                        "disagreements": point.disagreements,
                        "participants": list(point.participants)
                    }
                    for point in self.discussion_chain.points
                ],
                "responses": self._get_current_messages(),
                "current_round": self.current_round,
                "status": "completed" if round_num < self.current_round else "ongoing"
            }
            
            save_file = save_dir / f"round_{round_num}.json"
            with open(save_file, "w", encoding="utf-8") as f:
                json.dump(data, f, cls=DateTimeEncoder, ensure_ascii=False, indent=2)
            
            print(f"Progress saved to {save_file}")
            
        except Exception as e:
            error_msg = f"Error saving progress: {str(e)}"
            print(error_msg)
            self.logger.log_error(error_msg) 

    def get_remaining_time(self) -> int:
        """获取当前轮次剩余时间（秒）"""
        if not self.round_start_time:
            return 0
        
        elapsed = (datetime.utcnow() - self.round_start_time).total_seconds()
        remaining = max(0, self.round_duration - elapsed)
        return int(remaining) 

    def get_discussion_points(self, round_num: int = None) -> List[DiscussionPoint]:
        """获取指定轮次的讨论点"""
        try:
            if round_num is None:
                round_num = self.current_round
            logger.info(f"Getting discussion points for round {round_num}, current_round is {self.current_round}")
            
            # 检查 discussion_dir 是否存在
            if not os.path.exists(self.discussion_dir):
                logger.error(f"Discussion directory not found: {self.discussion_dir}")
                return []
            
            # 获取目录下所有文件
            files = os.listdir(self.discussion_dir)
            logger.info(f"Found files in discussion dir: {files}")
            
            round_file = os.path.join(self.discussion_dir, f"round_{round_num}.json")
            logger.info(f"Reading file: {round_file}")
            
            if not os.path.exists(round_file):
                logger.warning(f"Round file not found: {round_file}")
                return []
            
            with open(round_file, 'r', encoding='utf-8') as f:
                round_data = json.load(f)
                logger.info(f"Round data loaded: {round_data.keys()}")
                logger.info(f"Number of points in round data: {len(round_data.get('points', []))}")
            
            points = []
            for point_data in round_data.get("points", []):
                try:
                    logger.info(f"Processing point: {point_data['id']}")
                    point = DiscussionPoint(
                        content=point_data["content"],
                        round_num=round_num,
                        timestamp=datetime.fromisoformat(point_data["timestamp"] if "timestamp" in point_data else round_data["timestamp"]),
                        agreements=point_data.get("agreements", []),
                        disagreements=point_data.get("disagreements", []),
                        participants=point_data.get("participants", [])
                    )
                    points.append(point)
                except Exception as e:
                    logger.error(f"Error processing point {point_data.get('id')}: {str(e)}")
                    continue
            
            logger.info(f"Processed {len(points)} points for round {round_num}")
            return points
        except Exception as e:
            logger.error(f"Error getting discussion points for round {round_num}: {str(e)}")
            logger.error(f"Current working directory: {os.getcwd()}")
            return [] 

    async def start_next_round(self):
        """Start the next discussion round"""
        try:
            config = load_config()
            logger.info("Loaded config successfully")
            
            if "models" not in config:
                logger.error("Missing 'models' configuration in config")
                raise ValueError("Missing 'models' configuration")
            
            logger.info("Creating context processor")
            key_manager = DiscussionManager.get_key_manager()
            api_key = key_manager.get_current_key()
            context_processor = ContextProcessor(api_key=api_key)
            
            logger.info(f"Summarizing discussion for round {self.current_round}")
            # 直接传递轮次号
            summary = await context_processor.summarize_discussion(self.current_round)
            
            logger.info("Generating next points")
            next_points = await context_processor.generate_next_points(summary)
            if not next_points:
                logger.error("No next points generated")
                raise ValueError("No next points generated")
            
            # 更新轮次
            self.current_round += 1
            logger.info(f"Updated current round to {self.current_round}")
            
            # 保存新的讨论点
            await self.save_discussion_points(next_points)
            logger.info("Saved new discussion points")
            
            return next_points
        except Exception as e:
            logger.error(f"Error starting next round: {str(e)}", exc_info=True)
            raise 