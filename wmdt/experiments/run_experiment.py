#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
运行 WMDT 实验

对比参考轨迹（StrictPM）和失败轨迹（VaguePM）
"""

import asyncio
from pathlib import Path

from metagpt.team import Team
from metagpt.schema import Message
from metagpt.actions import UserRequirement
from metagpt.logs import logger

from wmdt.roles.product_managers import StrictPM, VaguePM
from wmdt.roles.simple_developer import SimpleDeveloper
from wmdt.core.belief_state import BeliefTrajectory
from wmdt.core.divergence_judge import DivergenceJudge


# 实验需求：电影评分系统（包含 rating 字段，故意不指定类型）
EXPERIMENT_REQUIREMENT = """
Build a movie rating database system with the following features:

1. Store movie information (title, director, year, rating)
2. Allow users to rate movies
3. Calculate average ratings

Key requirement: The system should track user ratings for movies.
"""


async def run_reference_trajectory():
    """
    运行参考轨迹（成功路径）

    使用 StrictPM，会明确定义 rating 的数据类型
    """
    logger.info("=" * 60)
    logger.info("🟢 Running REFERENCE Trajectory (StrictPM + Developer)")
    logger.info("=" * 60)

    team = Team(use_mgx=False)  # 使用普通 Environment
    team.hire([
        StrictPM(),
        SimpleDeveloper()
    ])

    team.invest(investment=3.0)
    team.run_project(EXPERIMENT_REQUIREMENT)

    # 运行 2 轮：PM 写 PRD -> Dev 写 Schema
    await team.run(n_round=2)

    # 提取 BeliefTrajectory
    pm = team.env.get_role("Alice")
    dev = team.env.get_role("Bob")

    reference_trajectory = BeliefTrajectory(
        trajectory_id="reference",
        description="Reference trajectory with StrictPM"
    )

    # 收集所有 BeliefState
    for belief in pm.get_belief_trajectory():
        reference_trajectory.add_belief_state(belief)
    for belief in dev.get_belief_trajectory():
        reference_trajectory.add_belief_state(belief)

    # 保存轨迹
    output_dir = Path("wmdt/data")
    output_dir.mkdir(parents=True, exist_ok=True)
    reference_trajectory.save(str(output_dir / "reference_trajectory.json"))

    logger.info(f"✅ Reference trajectory saved: {len(reference_trajectory.belief_states)} BeliefStates")

    return reference_trajectory


async def run_failed_trajectory():
    """
    运行失败轨迹（问题路径）

    使用 VaguePM，不会明确定义 rating 的数据类型
    """
    logger.info("=" * 60)
    logger.info("🔴 Running FAILED Trajectory (VaguePM + Developer)")
    logger.info("=" * 60)

    # team = Team()
    team = Team(use_mgx=False)
    team.hire([
        VaguePM(),
        SimpleDeveloper()
    ])

    team.invest(investment=3.0)
    team.run_project(EXPERIMENT_REQUIREMENT)

    await team.run(n_round=2)

    pm = team.env.get_role("Alice")
    dev = team.env.get_role("Bob")

    failed_trajectory = BeliefTrajectory(
        trajectory_id="failed",
        description="Failed trajectory with VaguePM"
    )

    for belief in pm.get_belief_trajectory():
        failed_trajectory.add_belief_state(belief)
    for belief in dev.get_belief_trajectory():
        failed_trajectory.add_belief_state(belief)

    output_dir = Path("wmdt/data")
    failed_trajectory.save(str(output_dir / "failed_trajectory.json"))

    logger.info(f"✅ Failed trajectory saved: {len(failed_trajectory.belief_states)} BeliefStates")

    return failed_trajectory


async def analyze_divergence(reference_trajectory, failed_trajectory):
    """
    分析两条轨迹的分歧，定位 PCI
    """
    logger.info("=" * 60)
    logger.info("🔍 Analyzing Divergence & Locating PCI")
    logger.info("=" * 60)

    judge = DivergenceJudge()
    scores = await judge.evaluate_trajectories(reference_trajectory, failed_trajectory)

    logger.info(f"Evaluated {len(scores)} divergence scores")

    # 查找 PCI
    pci = judge.find_pci(risk_threshold=0.5)

    if pci:
        logger.info(f"""
╔═══════════════════════════════════════════════════════════╗
║                    🎯 PCI FOUND!                         ║
╠═══════════════════════════════════════════════════════════╣
║ Step:              {pci.step:<40} ║
║ Role:              {pci.role_name:<40} ║
║ Risk Divergence:   {pci.risk_divergence:.2f}                                        ║
║ Overall Divergence: {pci.overall_divergence:.2f}                                        ║
║ Explanation:       {pci.explanation[:38]:<38} ║
╚═══════════════════════════════════════════════════════════╝
""")
    else:
        logger.warning("❌ No PCI detected (no significant risk_divergence spike)")

    # 保存结果
    output_dir = Path("wmdt/data")
    judge.save_results(str(output_dir / "divergence_analysis.json"))

    return scores, pci


async def main():
    """
    完整实验流程
    """
    logger.info("""
╔═══════════════════════════════════════════════════════════╗
║      WMDT Experiment: Movie Rating System                ║
║      Comparing Strict PM vs. Vague PM                     ║
╚═══════════════════════════════════════════════════════════╝
""")

    # 1. 运行参考轨迹
    reference_trajectory = await run_reference_trajectory()

    # 2. 运行失败轨迹
    failed_trajectory = await run_failed_trajectory()

    # 3. 分析分歧
    scores, pci = await analyze_divergence(reference_trajectory, failed_trajectory)

    logger.info("=" * 60)
    logger.info("✅ Experiment Complete!")
    logger.info(f"📁 Results saved to: wmdt/data/")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
