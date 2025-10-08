#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ObservableRole: 可观测的智能体角色

通过封装 MetaGPT 的 Role，在每次 _act() 前后自动提取 BeliefState
遵循"不修改源码，只封装"的设计原则
"""

import json
import re
from datetime import datetime
from typing import Optional, List

from metagpt.roles.role import Role
from metagpt.schema import Message
from metagpt.logs import logger

from wmdt.core.belief_state import BeliefState, BeliefTrajectory
from wmdt.core.prompts import BELIEF_STATE_PROMPT


class ObservableRole(Role):
    """
    可观测角色：在原有 Role 基础上添加 BeliefState 追踪

    关键特性：
    1. 在每次 _act() 前提取 BeliefState
    2. 维护一个 belief_trajectory 列表
    3. 提供 BeliefState 保存/加载功能
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.belief_trajectory: List[BeliefState] = []
        self.current_step: int = 0

    async def _extract_belief_state(self) -> Optional[BeliefState]:
        """
        提取当前的 BeliefState

        通过 LLM 分析当前上下文、记忆和待执行动作，提取智能体的认知状态
        """
        try:
            # 准备上下文信息
            context = self._get_context_summary()
            action_desc = self._get_current_action_description()
            recent_memories = self._get_recent_memories_summary()

            # 构造 BeliefState 提取 Prompt
            prompt = BELIEF_STATE_PROMPT.format(
                role_profile=self.profile,
                role_name=self.name,
                context=context,
                action_description=action_desc,
                recent_memories=recent_memories
            )

            # 调用 LLM 提取
            logger.info(f"[{self.name}] Extracting BeliefState at step {self.current_step}")
            response = await self.llm.aask(prompt)

            # 解析 JSON
            belief_data = self._parse_belief_json(response)
            if not belief_data:
                logger.warning(f"[{self.name}] Failed to parse BeliefState JSON")
                return None

            # 构造 BeliefState 对象
            belief = BeliefState(
                step=self.current_step,
                role_name=self.name,
                role_profile=self.profile,
                global_state=belief_data.get("global_state", ""),
                current_goal=belief_data.get("current_goal", ""),
                teammate_model=belief_data.get("teammate_model", {}),
                identified_risks=belief_data.get("identified_risks", []),
                timestamp=datetime.now().isoformat(),
                raw_response=response
            )

            logger.info(
                f"[{self.name}] BeliefState extracted: "
                f"Risks={len(belief.identified_risks)}, "
                f"Goal={belief.current_goal[:50]}..."
            )

            return belief

        except Exception as e:
            logger.error(f"[{self.name}] Error extracting BeliefState: {e}")
            return None

    def _parse_belief_json(self, response: str) -> Optional[dict]:
        """
        从 LLM 响应中解析 JSON

        支持多种格式：
        - 纯 JSON
        - Markdown 代码块中的 JSON
        - 带有额外文本的 JSON
        """
        try:
            # 尝试直接解析
            return json.loads(response)
        except json.JSONDecodeError:
            # 尝试提取 JSON 代码块
            json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
            match = re.search(json_pattern, response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass

            # 尝试找到第一个完整的 JSON 对象
            json_obj_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            match = re.search(json_obj_pattern, response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass

            return None

    def _get_context_summary(self) -> str:
        """获取当前上下文摘要"""
        if self.rc.env:
            env_desc = self.rc.env.desc or "No environment description"
            all_roles = ", ".join(self.rc.env.role_names())
            return f"Environment: {env_desc}. Team members: {all_roles}"
        return "No environment context available"

    def _get_current_action_description(self) -> str:
        """获取即将执行的动作描述"""
        if self.rc.todo:
            return f"{self.rc.todo.name}: {self.rc.todo.__doc__ or 'No description'}"
        return "No current action"

    def _get_recent_memories_summary(self, k: int = 3) -> str:
        """获取最近的记忆摘要"""
        if not self.rc.memory:
            return "No memory available"

        recent = self.rc.memory.get(k=k)
        if not recent:
            return "No recent memories"

        summary = []
        for msg in recent:
            summary.append(f"- [{msg.role}] {msg.content[:100]}...")
        return "\n".join(summary)

    async def _act(self) -> Message:
        """
        重写 _act() 方法，在执行动作前提取 BeliefState

        这是 ObservableRole 的核心：在不修改原有逻辑的情况下，
        通过钩子机制注入 BeliefState 追踪
        """
        # 提取 BeliefState（动作执行前）
        belief = await self._extract_belief_state()
        if belief:
            self.belief_trajectory.append(belief)

        # 调用父类的 _act() 执行原有逻辑
        result = await super()._act()

        # 增加步骤计数
        self.current_step += 1

        return result

    def get_belief_trajectory(self) -> List[BeliefState]:
        """获取完整的 BeliefState 轨迹"""
        return self.belief_trajectory

    def save_belief_trajectory(self, filepath: str):
        """保存 BeliefState 轨迹到文件"""
        trajectory = BeliefTrajectory(
            trajectory_id=self.name,
            description=f"{self.profile} ({self.name}) belief trajectory",
            belief_states=self.belief_trajectory
        )
        trajectory.save(filepath)
        logger.info(f"[{self.name}] Saved {len(self.belief_trajectory)} BeliefStates to {filepath}")

    def get_latest_belief(self) -> Optional[BeliefState]:
        """获取最新的 BeliefState"""
        return self.belief_trajectory[-1] if self.belief_trajectory else None
