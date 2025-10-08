#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DivergenceJudge: 分歧评估器

通过 LLM 评估两个 BeliefState 之间的认知分歧程度
"""

import json
import re
from typing import Dict, List, Tuple, Optional
from pydantic import BaseModel, Field

from metagpt.llm import LLM
from metagpt.logs import logger

from wmdt.core.belief_state import BeliefState, BeliefTrajectory
from wmdt.core.prompts import DIVERGENCE_JUDGE_PROMPT


class DivergenceScore(BaseModel):
    """分歧评分结果"""
    step: int = Field(description="步骤编号")
    role_name: str = Field(description="角色名称")

    global_divergence: float = Field(ge=0.0, le=1.0, description="全局状态分歧")
    goal_divergence: float = Field(ge=0.0, le=1.0, description="目标分歧")
    teammate_divergence: float = Field(ge=0.0, le=1.0, description="队友模型分歧")
    risk_divergence: float = Field(ge=0.0, le=1.0, description="风险识别分歧（关键指标）")
    overall_divergence: float = Field(ge=0.0, le=1.0, description="总体分歧")

    explanation: str = Field(description="分歧解释")

    def is_high_divergence(self, threshold: float = 0.5) -> bool:
        """判断是否为高分歧"""
        return self.overall_divergence >= threshold

    def is_risk_spike(self, threshold: float = 0.6) -> bool:
        """判断是否为风险分歧飙升（PCI 的潜在信号）"""
        return self.risk_divergence >= threshold


class DivergenceJudge:
    """
    分歧评估器

    对比参考轨迹和失败轨迹，逐步评估 BeliefState 的分歧，
    找到 risk_divergence 飙升的点（PCI 候选点）
    """

    def __init__(self, llm: Optional[LLM] = None):
        self.llm = llm or LLM()
        self.divergence_scores: List[DivergenceScore] = []

    async def evaluate_divergence(
        self,
        reference_belief: BeliefState,
        failed_belief: BeliefState
    ) -> Optional[DivergenceScore]:
        """
        评估两个 BeliefState 之间的分歧

        Args:
            reference_belief: 参考轨迹的 BeliefState（成功路径）
            failed_belief: 失败轨迹的 BeliefState

        Returns:
            DivergenceScore 对象，包含各维度的分歧评分
        """
        try:
            # 构造评估 Prompt
            prompt = DIVERGENCE_JUDGE_PROMPT.format(
                reference_belief=reference_belief.to_json(indent=2),
                failed_belief=failed_belief.to_json(indent=2)
            )

            logger.info(
                f"Evaluating divergence: {reference_belief.role_name} "
                f"Step {reference_belief.step}"
            )

            # 调用 LLM 评估
            response = await self.llm.aask(prompt)

            # 解析 JSON
            score_data = self._parse_divergence_json(response)
            if not score_data:
                logger.warning("Failed to parse divergence score JSON")
                return None

            # 构造 DivergenceScore
            score = DivergenceScore(
                step=reference_belief.step,
                role_name=reference_belief.role_name,
                global_divergence=score_data.get("global_divergence", 0.0),
                goal_divergence=score_data.get("goal_divergence", 0.0),
                teammate_divergence=score_data.get("teammate_divergence", 0.0),
                risk_divergence=score_data.get("risk_divergence", 0.0),
                overall_divergence=score_data.get("overall_divergence", 0.0),
                explanation=score_data.get("explanation", "")
            )

            logger.info(
                f"Divergence: overall={score.overall_divergence:.2f}, "
                f"risk={score.risk_divergence:.2f}"
            )

            self.divergence_scores.append(score)
            return score

        except Exception as e:
            logger.error(f"Error evaluating divergence: {e}")
            return None

    def _parse_divergence_json(self, response: str) -> Optional[dict]:
        """解析 LLM 返回的 JSON（复用 observable_role 的逻辑）"""
        try:
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

    async def evaluate_trajectories(
        self,
        reference_trajectory: BeliefTrajectory,
        failed_trajectory: BeliefTrajectory
    ) -> List[DivergenceScore]:
        """
        评估两条完整轨迹的分歧

        按步骤和角色对齐，逐对评估 BeliefState

        Returns:
            所有评估的 DivergenceScore 列表
        """
        logger.info(
            f"Evaluating trajectories: "
            f"Reference={len(reference_trajectory.belief_states)} states, "
            f"Failed={len(failed_trajectory.belief_states)} states"
        )

        # 按 (step, role_name) 对齐两条轨迹
        aligned_pairs = self._align_trajectories(
            reference_trajectory.belief_states,
            failed_trajectory.belief_states
        )

        scores = []
        for ref_belief, failed_belief in aligned_pairs:
            score = await self.evaluate_divergence(ref_belief, failed_belief)
            if score:
                scores.append(score)

        return scores

    def _align_trajectories(
        self,
        ref_beliefs: List[BeliefState],
        failed_beliefs: List[BeliefState]
    ) -> List[Tuple[BeliefState, BeliefState]]:
        """
        对齐两条轨迹的 BeliefState

        按 (step, role_name) 配对

        Returns:
            [(参考belief, 失败belief), ...] 列表
        """
        pairs = []

        # 创建索引：(step, role_name) -> BeliefState
        ref_index = {(b.step, b.role_name): b for b in ref_beliefs}
        failed_index = {(b.step, b.role_name): b for b in failed_beliefs}

        # 找到公共的 (step, role_name) 键
        common_keys = set(ref_index.keys()) & set(failed_index.keys())

        for key in sorted(common_keys):
            pairs.append((ref_index[key], failed_index[key]))

        logger.info(f"Aligned {len(pairs)} BeliefState pairs")
        return pairs

    def find_pci(self, risk_threshold: float = 0.6) -> Optional[DivergenceScore]:
        """
        查找 PCI (Point of Causal Inevitability)

        定义：risk_divergence 首次显著飙升的点

        Args:
            risk_threshold: risk_divergence 阈值

        Returns:
            PCI 对应的 DivergenceScore，如果未找到则返回 None
        """
        for score in self.divergence_scores:
            if score.is_risk_spike(risk_threshold):
                logger.info(
                    f"🎯 PCI Found: Step {score.step}, Role {score.role_name}, "
                    f"risk_divergence={score.risk_divergence:.2f}"
                )
                return score

        logger.warning("No PCI found (no risk_divergence spike detected)")
        return None

    def save_results(self, filepath: str):
        """保存分歧评估结果"""
        data = {
            "divergence_scores": [score.model_dump() for score in self.divergence_scores],
            "pci": self.find_pci().model_dump() if self.find_pci() else None
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(self.divergence_scores)} divergence scores to {filepath}")
