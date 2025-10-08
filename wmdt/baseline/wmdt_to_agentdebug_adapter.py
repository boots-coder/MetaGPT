#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WMDT 轨迹格式转换器
将 WMDT 的轨迹数据转换为 AgentDebug 可分析的格式
"""

import json
from pathlib import Path
from typing import Dict, List, Any


class WMDTToAgentDebugAdapter:
    """将 WMDT 轨迹转换为 AgentDebug 格式"""

    def __init__(self, wmdt_data_dir: str):
        self.wmdt_data_dir = Path(wmdt_data_dir)

    def convert_trajectory(self, trajectory_type: str = "failed") -> Dict[str, Any]:
        """
        转换轨迹数据

        Args:
            trajectory_type: "reference" 或 "failed"

        Returns:
            AgentDebug 格式的轨迹数据
        """
        # 加载 WMDT 轨迹
        trajectory_file = self.wmdt_data_dir / f"{trajectory_type}_trajectory.json"
        with open(trajectory_file, 'r', encoding='utf-8') as f:
            wmdt_trajectory = json.load(f)

        # 构建 AgentDebug 格式
        agentdebug_format = {
            "metadata": {
                "task_id": f"wmdt_movie_rating_{trajectory_type}",
                "success": (trajectory_type == "reference"),
                "environment": "metagpt",
                "source": "WMDT"
            },
            "messages": []
        }

        # 提取 BeliefState 数据
        belief_states = wmdt_trajectory.get("belief_states", [])

        # 构建任务描述（用户消息）
        task_description = """
Build a movie rating database system with the following features:
1. Store movie information (title, director, year, rating)
2. Allow users to rate movies
3. Calculate average ratings

Key requirement: The system should track user ratings for movies.
"""

        # 初始用户消息
        agentdebug_format["messages"].append({
            "role": "user",
            "content": f"Your task is: {task_description.strip()}"
        })

        # 根据 BeliefState 构建对话历史
        for i, belief in enumerate(belief_states):
            role_name = belief["role_name"]
            role_profile = belief["role_profile"]

            # 构建 agent 输出（assistant 消息）
            # 模拟 agent 的模块化输出（Memory, Reflection, Planning, Action）
            agent_output = self._build_agent_output(belief, i, trajectory_type)

            agentdebug_format["messages"].append({
                "role": "assistant",
                "content": agent_output
            })

            # 构建环境反馈（user 消息）
            env_feedback = self._build_environment_feedback(belief, i, trajectory_type)

            agentdebug_format["messages"].append({
                "role": "user",
                "content": env_feedback
            })

        return agentdebug_format

    def _build_agent_output(self, belief: Dict, step: int, trajectory_type: str) -> str:
        """
        构建 agent 输出，使用 AgentDebug 期望的 XML 标签格式

        AgentDebug 期望的格式包含：
        - <memory>...</memory>
        - <reflection>...</reflection>
        - <plan>...</plan>
        - <action>...</action>
        """
        role_name = belief["role_name"]
        role_profile = belief["role_profile"]
        global_state = belief["global_state"]
        current_goal = belief["current_goal"]
        identified_risks = belief.get("identified_risks", [])
        teammate_model = belief.get("teammate_model", {})

        # 构建模块化输出（使用 XML 标签）
        output = ""

        # Memory 模块
        memory_content = f"I understand that {global_state}"
        output += f"<memory>\n{memory_content}\n</memory>\n\n"

        # Reflection 模块
        reflection_content = f"My current assessment:\n"
        reflection_content += f"- {global_state}\n\n"

        if identified_risks:
            reflection_content += "Identified risks:\n"
            for risk in identified_risks:
                reflection_content += f"- {risk}\n"
        else:
            reflection_content += "No significant risks identified at this point.\n"

        if teammate_model:
            reflection_content += "\nTeammate understanding:\n"
            for teammate, model in teammate_model.items():
                reflection_content += f"- {teammate}: {model}\n"

        output += f"<reflection>\n{reflection_content}\n</reflection>\n\n"

        # Planning 模块
        planning_content = f"Goal: {current_goal}\n\n"
        planning_content += "Plan:\n"

        # 根据角色类型生成具体计划
        if "Product Manager" in role_profile:
            planning_content += "1. Write a comprehensive PRD\n"
            planning_content += "2. Ensure all requirements are clearly specified\n"
            planning_content += "3. Communicate requirements to the development team\n"
        elif "Developer" in role_profile:
            planning_content += "1. Review the PRD carefully\n"
            planning_content += "2. Design the database schema based on requirements\n"
            planning_content += "3. Implement the schema with appropriate data types\n"

        output += f"<plan>\n{planning_content}\n</plan>\n\n"

        # Action 模块
        action_content = ""
        if "Product Manager" in role_profile:
            action_content = "WritePRD()"
        elif "Developer" in role_profile:
            action_content = "WriteSchema()"

        output += f"<action>\n{action_content}\n</action>"

        return output

    def _build_environment_feedback(self, belief: Dict, step: int, trajectory_type: str) -> str:
        """
        构建环境反馈

        在 MetaGPT 中，环境反馈就是下一个角色收到的消息内容
        """
        role_profile = belief["role_profile"]

        feedback = "**Environment Feedback**:\n\n"

        if "Product Manager" in role_profile:
            # PM 的输出是 PRD
            feedback += "PRD has been written and shared with the team.\n"
            feedback += "Developer has received the PRD and will proceed with schema design.\n\n"

            # 根据轨迹类型添加具体的 PRD 特征提示
            if trajectory_type == "reference":
                feedback += "PRD includes detailed technical specifications:\n"
                feedback += "- All field data types are explicitly defined (e.g., rating: INTEGER 1-5)\n"
                feedback += "- Validation rules are clearly stated\n"
                feedback += "- Potential implementation risks are identified\n"
            else:  # failed
                feedback += "PRD focuses on business requirements:\n"
                feedback += "- User needs and business value are clearly stated\n"
                feedback += "- Feature specifications are provided\n"
                feedback += "- Technical implementation details are left for developer judgment\n"

        elif "Developer" in role_profile:
            # Developer 的输出是 Schema
            feedback += "Database schema has been generated.\n"
            feedback += "Schema implementation is complete.\n\n"

            feedback += "Task completed.\n"

        return feedback

    def save_converted_trajectory(self, trajectory_type: str = "failed", output_dir: str = None):
        """
        转换并保存轨迹

        Args:
            trajectory_type: "reference" 或 "failed"
            output_dir: 输出目录，默认为 baseline/agentdebug_format/
        """
        if output_dir is None:
            output_dir = self.wmdt_data_dir.parent / "agentdebug_format"
        else:
            output_dir = Path(output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)

        # 转换轨迹
        converted = self.convert_trajectory(trajectory_type)

        # 保存
        output_file = output_dir / f"movie_rating_{trajectory_type}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(converted, f, indent=2, ensure_ascii=False)

        print(f"✅ Converted {trajectory_type} trajectory saved to: {output_file}")
        return output_file


def main():
    """转换 WMDT 轨迹数据"""

    # WMDT 数据目录
    wmdt_data_dir = "/home/haoxuan004/MetaGPT/wmdt/wmdt/data"

    # 创建适配器
    adapter = WMDTToAgentDebugAdapter(wmdt_data_dir)

    # 转换失败轨迹（这是我们要用 AgentDebug 分析的）
    print("Converting failed trajectory...")
    adapter.save_converted_trajectory("failed")

    # 也转换参考轨迹（用于对比）
    print("\nConverting reference trajectory...")
    adapter.save_converted_trajectory("reference")

    print("\n✅ Conversion complete!")
    print(f"Output directory: {wmdt_data_dir}/../agentdebug_format/")


if __name__ == "__main__":
    main()
