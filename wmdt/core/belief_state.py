#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BeliefState: 智能体在某个时间点的内部认知状态

这是 WMDT 追踪的核心数据结构，代表智能体的"内心想法"
"""

import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BeliefState(BaseModel):
    """
    智能体的信念状态

    Attributes:
        step: 当前步骤编号
        role_name: 角色名称
        role_profile: 角色类型（如 ProductManager, Developer）
        global_state: 对全局项目状态的理解
        current_goal: 当前要完成的目标
        teammate_model: 对队友能力/状态的认知模型
        identified_risks: 已识别的风险列表（PCI 定位的关键）
        timestamp: 生成时间戳（可选）
    """
    step: int = Field(description="当前步骤编号")
    role_name: str = Field(description="角色名称，如 Alice")
    role_profile: str = Field(description="角色类型，如 ProductManager")

    global_state: str = Field(
        description="对全局项目状态的理解，如'项目刚启动，需求已明确'"
    )
    current_goal: str = Field(
        description="当前要完成的目标，如'编写清晰的PRD文档'"
    )
    teammate_model: Dict[str, str] = Field(
        default_factory=dict,
        description="对队友的认知模型，如 {'Developer': '依赖PRD进行开发'}"
    )
    identified_risks: List[str] = Field(
        default_factory=list,
        description="已识别的风险列表，如 ['rating字段类型未定义']"
    )

    timestamp: Optional[str] = Field(default=None, description="生成时间")
    raw_response: Optional[str] = Field(default=None, description="LLM原始输出（调试用）")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return self.model_dump()

    def to_json(self, indent: int = 2) -> str:
        """转换为格式化的JSON字符串"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BeliefState":
        """从字典创建BeliefState"""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> "BeliefState":
        """从JSON字符串创建BeliefState"""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def get_risk_count(self) -> int:
        """获取识别的风险数量"""
        return len(self.identified_risks)

    def has_risk(self, risk_keyword: str) -> bool:
        """检查是否识别了包含特定关键词的风险"""
        return any(risk_keyword.lower() in risk.lower() for risk in self.identified_risks)


class BeliefTrajectory(BaseModel):
    """
    信念轨迹：一条执行路径上所有智能体的 BeliefState 序列

    用于对比参考轨迹（成功）和失败轨迹的差异
    """
    trajectory_id: str = Field(description="轨迹ID，如 'reference' 或 'failed'")
    description: str = Field(description="轨迹描述")
    belief_states: List[BeliefState] = Field(
        default_factory=list,
        description="按时间顺序排列的BeliefState列表"
    )

    def add_belief_state(self, belief: BeliefState):
        """添加一个BeliefState"""
        self.belief_states.append(belief)

    def get_by_role(self, role_name: str) -> List[BeliefState]:
        """获取特定角色的所有BeliefState"""
        return [bs for bs in self.belief_states if bs.role_name == role_name]

    def get_by_step(self, step: int) -> List[BeliefState]:
        """获取特定步骤的所有BeliefState"""
        return [bs for bs in self.belief_states if bs.step == step]

    def save(self, filepath: str):
        """保存到JSON文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(json.dumps(self.model_dump(), indent=2, ensure_ascii=False))

    @classmethod
    def load(cls, filepath: str) -> "BeliefTrajectory":
        """从JSON文件加载"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(**data)
