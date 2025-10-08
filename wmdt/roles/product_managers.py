#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Product Manager 角色

包含两个变体：
- StrictPM: 严谨的PM，明确定义所有技术细节（参考轨迹）
- VaguePM: 模糊的PM，只描述高层需求（失败轨迹）
"""

from metagpt.actions import Action, UserRequirement
from metagpt.schema import Message

from wmdt.core.observable_role import ObservableRole
from wmdt.core.prompts import STRICT_PM_SYSTEM_PROMPT, VAGUE_PM_SYSTEM_PROMPT


class WritePRD(Action):
    """编写产品需求文档 (PRD)"""

    PROMPT_TEMPLATE: str = """
Based on the user requirement, write a Product Requirement Document (PRD).

## User Requirement:
{requirement}

## Your Task:
Write a clear and complete PRD.
{specific_instruction}

Return the PRD in markdown format.
"""

    name: str = "WritePRD"

    async def run(self, requirement: str, specific_instruction: str = "") -> str:
        prompt = self.PROMPT_TEMPLATE.format(
            requirement=requirement,
            specific_instruction=specific_instruction
        )

        rsp = await self._aask(prompt)
        return rsp


class StrictPM(ObservableRole):
    """
    严谨的产品经理 (参考轨迹)

    特点：
    - 明确定义所有字段的数据类型
    - 列出技术实现要点
    - 主动识别潜在风险
    """

    name: str = "Alice"
    profile: str = "Strict Product Manager"
    desc: str = STRICT_PM_SYSTEM_PROMPT

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([WritePRD])
        self._watch([UserRequirement])

    async def _act(self) -> Message:
        """执行 WritePRD 动作"""
        # ① 手动提取 BeliefState（因为我们重写了 _act）
        belief = await self._extract_belief_state()
        if belief:
            self.belief_trajectory.append(belief)

        # ② 执行业务逻辑
        todo = self.rc.todo  # WritePRD Action
        msg = self.get_memories(k=1)[0]  # 用户需求

        # 添加严谨PM的特定指令
        specific_instruction = """
**IMPORTANT Requirements**:
1. Explicitly specify data types for ALL fields (e.g., "rating: integer (1-5)" NOT just "rating")
2. Define validation rules and constraints
3. List potential technical pitfalls
4. Identify risks in a dedicated "Risks" section
"""

        prd_content = await todo.run(msg.content, specific_instruction=specific_instruction)

        output_msg = Message(
            content=prd_content,
            role=self.profile,
            cause_by=type(todo)
        )

        # ③ 增加步骤计数
        self.current_step += 1

        return output_msg


class VaguePM(ObservableRole):
    """
    模糊的产品经理 (失败轨迹)

    特点：
    - 只描述业务需求，不关注技术细节
    - 相信开发者会做出正确选择
    - 不主动识别技术风险
    """

    name: str = "Alice"  # 保持同名以便对比
    profile: str = "Vague Product Manager"
    desc: str = VAGUE_PM_SYSTEM_PROMPT

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([WritePRD])
        self._watch([UserRequirement])

    async def _act(self) -> Message:
        """执行 WritePRD 动作"""
        # ① 手动提取 BeliefState（因为我们重写了 _act）
        belief = await self._extract_belief_state()
        if belief:
            self.belief_trajectory.append(belief)

        # ② 执行业务逻辑
        todo = self.rc.todo
        msg = self.get_memories(k=1)[0]

        # 添加模糊PM的特定指令
        specific_instruction = """
Focus on the business value and user experience.
Keep the PRD concise and high-level.
Technical implementation details can be decided by the development team.
"""

        prd_content = await todo.run(msg.content, specific_instruction=specific_instruction)

        output_msg = Message(
            content=prd_content,
            role=self.profile,
            cause_by=type(todo)
        )

        # ③ 增加步骤计数
        self.current_step += 1

        return output_msg
