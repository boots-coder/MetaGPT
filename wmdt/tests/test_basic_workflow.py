#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WMDT 基础工作流测试

验证核心组件是否正常工作
"""

import asyncio
from pathlib import Path

from metagpt.team import Team
from metagpt.logs import logger

from wmdt.roles.product_managers import StrictPM
from wmdt.roles.simple_developer import SimpleDeveloper
from wmdt.core.belief_state import BeliefState


SIMPLE_REQUIREMENT = """
Build a simple movie database with:
- Movie title
- Rating (1-5 stars)
"""


async def test_strict_pm_generates_belief():
    """
    测试 1: StrictPM 能否生成 BeliefState
    """
    logger.info("=" * 60)
    logger.info("TEST 1: StrictPM BeliefState Generation")
    logger.info("=" * 60)

    team = Team(use_mgx=False)  # 使用普通 Environment，不需要 TeamLeader
    pm = StrictPM()
    team.hire([pm])

    team.invest(investment=1.0)
    team.run_project(SIMPLE_REQUIREMENT)

    await team.run(n_round=1)

    # 检查是否生成了 BeliefState
    beliefs = pm.get_belief_trajectory()

    logger.info(f"Generated {len(beliefs)} BeliefState(s)")

    if len(beliefs) > 0:
        belief = beliefs[0]
        logger.info(f"✅ TEST PASSED: BeliefState generated")
        logger.info(f"   - Role: {belief.role_name}")
        logger.info(f"   - Goal: {belief.current_goal[:60]}...")
        logger.info(f"   - Identified Risks: {belief.identified_risks}")

        # 验证 StrictPM 应该识别出风险
        if len(belief.identified_risks) > 0:
            logger.info(f"✅ StrictPM identified {len(belief.identified_risks)} risk(s) as expected")
        else:
            logger.warning(f"⚠️ StrictPM didn't identify any risks (may need prompt tuning)")

        return True
    else:
        logger.error(f"❌ TEST FAILED: No BeliefState generated")
        return False


async def test_full_workflow():
    """
    测试 2: 完整的 PM + Dev 工作流
    """
    logger.info("=" * 60)
    logger.info("TEST 2: Full PM + Developer Workflow")
    logger.info("=" * 60)

    team = Team(use_mgx=False)  # 使用普通 Environment
    pm = StrictPM()
    dev = SimpleDeveloper()
    team.hire([pm, dev])

    team.invest(investment=2.0)
    team.run_project(SIMPLE_REQUIREMENT)

    await team.run(n_round=2)

    pm_beliefs = pm.get_belief_trajectory()
    dev_beliefs = dev.get_belief_trajectory()

    logger.info(f"PM generated {len(pm_beliefs)} BeliefState(s)")
    logger.info(f"Dev generated {len(dev_beliefs)} BeliefState(s)")

    if len(pm_beliefs) > 0 and len(dev_beliefs) > 0:
        logger.info(f"✅ TEST PASSED: Both roles generated BeliefStates")

        # 显示 Dev 的 BeliefState
        dev_belief = dev_beliefs[0]
        logger.info(f"   Dev's Goal: {dev_belief.current_goal[:60]}...")
        logger.info(f"   Dev's Identified Risks: {dev_belief.identified_risks}")

        return True
    else:
        logger.error(f"❌ TEST FAILED: Missing BeliefStates")
        return False


async def test_belief_state_serialization():
    """
    测试 3: BeliefState 序列化与反序列化
    """
    logger.info("=" * 60)
    logger.info("TEST 3: BeliefState Serialization")
    logger.info("=" * 60)

    # 创建一个测试 BeliefState
    test_belief = BeliefState(
        step=1,
        role_name="TestPM",
        role_profile="Product Manager",
        global_state="Project starting",
        current_goal="Write PRD",
        teammate_model={"Developer": "Waiting for PRD"},
        identified_risks=["Data type not specified", "Missing validation"]
    )

    # 保存到文件
    output_dir = Path("wmdt/data/test")
    output_dir.mkdir(parents=True, exist_ok=True)
    test_file = output_dir / "test_belief.json"

    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_belief.to_json())

    # 重新加载
    loaded_belief = BeliefState.from_json(open(test_file).read())

    # 验证
    if (loaded_belief.role_name == test_belief.role_name and
        loaded_belief.identified_risks == test_belief.identified_risks):
        logger.info(f"✅ TEST PASSED: Serialization/Deserialization works")
        return True
    else:
        logger.error(f"❌ TEST FAILED: Data mismatch after deserialization")
        return False


async def run_all_tests():
    """
    运行所有测试
    """
    logger.info("""
╔═══════════════════════════════════════════════════════════╗
║              WMDT Basic Workflow Tests                   ║
╚═══════════════════════════════════════════════════════════╝
""")

    results = []

    # Test 1
    result1 = await test_strict_pm_generates_belief()
    results.append(("StrictPM BeliefState Generation", result1))

    # Test 2
    result2 = await test_full_workflow()
    results.append(("Full PM + Developer Workflow", result2))

    # Test 3
    result3 = await test_belief_state_serialization()
    results.append(("BeliefState Serialization", result3))

    # 汇总
    logger.info("=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} - {name}")

    logger.info(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        logger.info("🎉 All tests passed!")
    else:
        logger.warning(f"⚠️ {total - passed} test(s) failed")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)
