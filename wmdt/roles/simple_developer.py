#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化的 Developer 角色

用于快速验证实验流程，实现简单的数据库schema生成
"""

from metagpt.actions import Action
from metagpt.schema import Message

from wmdt.core.observable_role import ObservableRole
from wmdt.core.prompts import DEVELOPER_SYSTEM_PROMPT
from wmdt.roles.product_managers import WritePRD


class WriteSchema(Action):
    """根据 PRD 编写数据库 Schema"""

    PROMPT_TEMPLATE: str = """
Based on the PRD below, write a SQLite database schema.

## PRD:
{prd}

## Your Task:
1. Design the database tables based on the requirements
2. Return the CREATE TABLE statements in SQLite syntax
3. Pay attention to data types specified in the PRD

Return only the SQL code, no additional explanation.
"""

    name: str = "WriteSchema"

    async def run(self, prd: str) -> str:
        prompt = self.PROMPT_TEMPLATE.format(prd=prd)
        rsp = await self._aask(prompt)
        return rsp


class SimpleDeveloper(ObservableRole):
    """
    简化的开发者角色

    负责：根据 PRD 生成数据库 Schema
    """

    name: str = "Bob"
    profile: str = "Developer"
    desc: str = DEVELOPER_SYSTEM_PROMPT

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([WriteSchema])
        self._watch([WritePRD])  # 订阅 PM 的输出

    async def _act(self) -> Message:
        """执行 WriteSchema 动作"""
        # ① 手动提取 BeliefState（因为我们重写了 _act）
        belief = await self._extract_belief_state()
        if belief:
            self.belief_trajectory.append(belief)

        # ② 执行业务逻辑
        todo = self.rc.todo
        msg = self.get_memories(k=1)[0]  # 获取 PM 的 PRD

        schema_code = await todo.run(msg.content)

        output_msg = Message(
            content=schema_code,
            role=self.profile,
            cause_by=type(todo)
        )

        # ③ 增加步骤计数
        self.current_step += 1

        return output_msg
