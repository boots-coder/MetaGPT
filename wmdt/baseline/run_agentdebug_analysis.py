#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
运行 AgentDebug 分析 WMDT 轨迹
"""

import sys
import os
import asyncio
import json
from pathlib import Path

# 将 AgentDebug 的 detector 模块添加到路径
detector_path = str(Path(__file__).parent / "AgentDebug" / "detector")
sys.path.insert(0, detector_path)

from fine_grained_analysis import ErrorTypeDetector
from critical_error_detection import CriticalErrorAnalyzer


async def analyze_wmdt_trajectory():
    """使用 AgentDebug 分析 WMDT 的失败轨迹"""

    # 加载 API 配置
    config_path = "/home/haoxuan004/MetaGPT/config/config2.yaml"

    # 读取配置文件
    import yaml
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # 构建 API 配置
    # OpenRouter 需要完整的 endpoint URL
    base_url = config['llm']['base_url']
    if not base_url.endswith('/chat/completions'):
        base_url = base_url.rstrip('/') + '/chat/completions'

    api_config = {
        "api_key": config['llm']['api_key'],
        "base_url": base_url,
        "model": config['llm']['model'],
        "temperature": 0.0,
        "max_retries": 3,
        "timeout": 120
    }

    print("=" * 60)
    print("AgentDebug Analysis of WMDT Failed Trajectory")
    print("=" * 60)
    print(f"Using model: {api_config['model']}")
    print()

    # 轨迹文件路径
    trajectory_path = "/home/haoxuan004/MetaGPT/wmdt/wmdt/agentdebug_format/movie_rating_failed.json"

    # Phase 1: Fine-Grained Analysis
    print("Phase 1: Fine-Grained Analysis")
    print("-" * 60)

    detector = ErrorTypeDetector(api_config)

    try:
        # 解析轨迹
        trajectory_data = detector.parse_trajectory(trajectory_path)
        print(f"✅ Loaded trajectory with {len(trajectory_data.get('steps', []))} steps")
        print(f"Task: {trajectory_data.get('task_description', 'N/A')[:100]}...")
        print()

        # 分析每个步骤
        step_analyses = []

        for step_data in trajectory_data['steps']:
            step_num = step_data['step']
            print(f"\nAnalyzing Step {step_num}...")

            step_result = {
                'step': step_num,
                'errors': {}
            }

            # 使用 AgentDebug 的方法提取模块
            extracted_modules = detector.extract_modules_from_content(
                step_data['content'],
                trajectory_data['environment']
            )

            # 分析每个模块
            modules = ['memory', 'reflection', 'planning', 'action']

            for module in modules:
                module_content = extracted_modules.get(module, '')

                if not module_content:
                    print(f"  {module}: [empty]")
                    continue

                print(f"  Analyzing {module}...")

                # 调用 AgentDebug 的错误检测
                try:
                    error = await detector.detect_module_errors(
                        module_name=module,
                        module_content=module_content,
                        step_num=step_num,
                        step_data=step_data,
                        task_description=trajectory_data['task_description'],
                        env_response=step_data.get('env_response', ''),
                        previous_steps=trajectory_data['steps'][:step_num-1] if step_num > 1 else [],
                        current_step_input=step_data.get('current_input', ''),
                        task_success=trajectory_data['success'],
                        environment=trajectory_data['environment']
                    )

                    step_result['errors'][module] = {
                        'error_detected': error.error_detected,
                        'error_type': error.error_type,
                        'evidence': error.evidence,
                        'reasoning': error.reasoning
                    }

                    if error.error_detected:
                        print(f"    ⚠️  Error: {error.error_type}")
                        print(f"        Evidence: {error.evidence[:80]}...")
                    else:
                        print(f"    ✅ No error")

                except Exception as e:
                    print(f"    ❌ Error during analysis: {e}")
                    step_result['errors'][module] = None

            step_analyses.append(step_result)

        print("\n" + "=" * 60)
        print("Phase 1 Complete!")
        print("=" * 60)

        # 保存 Phase 1 结果
        phase1_result = {
            'task_description': trajectory_data['task_description'],
            'task_success': trajectory_data['success'],
            'step_analyses': step_analyses
        }

        phase1_output = "/home/haoxuan004/MetaGPT/wmdt/wmdt/agentdebug_format/phase1_results.json"
        with open(phase1_output, 'w', encoding='utf-8') as f:
            json.dump(phase1_result, f, indent=2, ensure_ascii=False)

        print(f"Phase 1 results saved to: {phase1_output}")

        # Phase 2: Critical Error Detection
        print("\n" + "=" * 60)
        print("Phase 2: Critical Error Detection")
        print("-" * 60)

        analyzer = CriticalErrorAnalyzer(api_config)

        # 加载原始轨迹
        original_trajectory = analyzer.load_original_trajectory(trajectory_path)

        # 识别关键错误
        print("Identifying critical error...")
        critical_error = await analyzer.identify_critical_error(
            phase1_results=phase1_result,
            original_trajectory=original_trajectory
        )

        if critical_error:
            print("\n" + "╔" + "═" * 58 + "╗")
            print("║" + " " * 18 + "🎯 CRITICAL ERROR FOUND!" + " " * 17 + "║")
            print("╠" + "═" * 58 + "╣")
            print(f"║ Step:              {critical_error.critical_step:<40} ║")
            print(f"║ Module:            {critical_error.critical_module:<40} ║")
            print(f"║ Error Type:        {critical_error.error_type:<40} ║")
            print(f"║ Confidence:        {critical_error.confidence:.2f}{' ' * 38} ║")
            print("╠" + "═" * 58 + "╣")
            print("║ Root Cause:" + " " * 47 + "║")
            # 分行显示 root_cause
            root_lines = [critical_error.root_cause[i:i+56] for i in range(0, len(critical_error.root_cause), 56)]
            for line in root_lines:
                print(f"║ {line:<56} ║")
            print("╚" + "═" * 58 + "╝")

            # 保存 Phase 2 结果
            phase2_output = "/home/haoxuan004/MetaGPT/wmdt/wmdt/agentdebug_format/phase2_results.json"
            with open(phase2_output, 'w', encoding='utf-8') as f:
                # 手动序列化，因为 dataclass 不能直接 json.dump
                result_dict = {
                    'critical_step': critical_error.critical_step,
                    'critical_module': critical_error.critical_module,
                    'error_type': critical_error.error_type,
                    'root_cause': critical_error.root_cause,
                    'evidence': critical_error.evidence,
                    'correction_guidance': critical_error.correction_guidance,
                    'cascading_effects': critical_error.cascading_effects,
                    'confidence': critical_error.confidence
                }
                json.dump(result_dict, f, indent=2, ensure_ascii=False)

            print(f"\nPhase 2 results saved to: {phase2_output}")
        else:
            print("❌ No critical error identified")

        print("\n" + "=" * 60)
        print("✅ AgentDebug Analysis Complete!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(analyze_wmdt_trajectory())
