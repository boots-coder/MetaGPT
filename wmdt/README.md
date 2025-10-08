# WMDT (World Model Divergence Tracking) 实验框架

## 📖 项目简介

WMDT 是一个用于验证"通过追踪智能体内部 BeliefState 分歧来定位 PCI (Point of Causal Inevitability)"假设的实验框架。

### 核心概念

- **BeliefState**: 智能体在某个时间点的内部认知状态，包含对全局状态、当前目标、队友模型和已识别风险的理解
- **PCI (Point of Causal Inevitability)**: 在认知层面上，某个信念（或信念缺失）使得后续失败变得不可避免的最早时间点
- **ObservableRole**: 封装 MetaGPT 的 Role，自动提取并记录 BeliefState
- **DivergenceJudge**: 评估两条轨迹之间的 BeliefState 分歧

## 🏗️ 项目结构

```
wmdt/
├── core/                       # 核心组件
│   ├── belief_state.py         # BeliefState 数据模型
│   ├── observable_role.py      # ObservableRole 基类
│   ├── divergence_judge.py     # 分歧评估器
│   └── prompts.py              # Prompt 模板
├── roles/                      # 具体角色实现
│   ├── product_managers.py     # StrictPM & VaguePM
│   └── simple_developer.py     # SimpleDeveloper
├── experiments/                # 实验脚本
│   └── run_experiment.py       # 完整实验流程
├── tests/                      # 测试代码
│   └── test_basic_workflow.py  # 基础工作流测试
└── data/                       # 实验数据输出（自动生成）
```

## 🚀 快速开始

### 前置要求

1. 已安装并配置 MetaGPT
2. 已激活 `wmdt` conda 环境
3. 已配置 OpenRouter API key（在 `/home/haoxuan004/MetaGPT/config/config2.yaml`）

### 运行基础测试

验证所有组件是否正常工作：

```bash
cd /home/haoxuan004/MetaGPT
conda activate wmdt
python -m wmdt.tests.test_basic_workflow
```

**预期输出：**
- ✅ TEST 1: StrictPM 生成 BeliefState
- ✅ TEST 2: PM + Developer 完整工作流
- ✅ TEST 3: BeliefState 序列化

### 运行完整实验

对比 StrictPM 和 VaguePM 的分歧：

```bash
cd /home/haoxuan004/MetaGPT
conda activate wmdt
python -m wmdt.experiments.run_experiment
```

**实验流程：**
1. **参考轨迹**：StrictPM (明确定义数据类型) + Developer
2. **失败轨迹**：VaguePM (模糊需求) + Developer
3. **分歧分析**：逐步对比 BeliefState，定位 PCI

**预期结果文件：**
```
wmdt/data/
├── reference_trajectory.json   # 参考轨迹的 BeliefState 序列
├── failed_trajectory.json      # 失败轨迹的 BeliefState 序列
└── divergence_analysis.json    # 分歧评估结果 + PCI 定位
```

## 📊 实验验证标准

### 成功标准

1. **BeliefState 提取成功**
   - StrictPM 的 `identified_risks` 字段应包含 "rating 类型未定义" 或类似风险
   - VaguePM 的 `identified_risks` 字段应为空或缺少关键风险

2. **分歧评估成功**
   - `risk_divergence` 在 PM 步骤应显著高于 0.5
   - PCI 应定位到 PM 角色的第一步

3. **PCI 定位成功**
   - 输出类似：
     ```
     🎯 PCI FOUND!
     Step: 0
     Role: Alice (PM)
     Risk Divergence: 0.85
     ```

### 失败情况处理

如果测试失败，可能的原因：

1. **LLM 返回格式错误**
   - 检查 `wmdt/data/*_trajectory.json` 中的 `raw_response` 字段
   - 可能需要调整 `BELIEF_STATE_PROMPT` 的措辞

2. **BeliefState 为空**
   - 增加 `investment` 预算（默认 3.0）
   - 检查 OpenRouter API 是否正常

3. **分歧评分过低**
   - VaguePM 和 StrictPM 的行为可能过于相似
   - 需要强化 `VAGUE_PM_SYSTEM_PROMPT` 的"模糊性"

## 🔬 实验设计说明

### 实验场景

**需求**：构建电影评分数据库，包含 `rating` 字段

**关键设计**：
- 需求故意**不指定 rating 的数据类型**
- StrictPM 会主动识别并明确（如 `INTEGER 1-5`）
- VaguePM 会忽略此细节，导致 Developer 做出错误假设

### 预期的认知分歧

| 维度 | StrictPM (参考) | VaguePM (失败) |
|------|----------------|---------------|
| `identified_risks` | `["rating数据类型未定义", ...]` | `[]` 或缺少关键风险 |
| PRD 输出 | 明确：`rating: INTEGER (1-5)` | 模糊：`rating` |
| Developer 实现 | 正确：`INTEGER` | 错误：可能用 `TEXT` |

## 📝 手动测试检查清单

运行实验后，请检查以下内容并报告给 Claude：

### 1. BeliefState 质量检查

```bash
cat wmdt/data/reference_trajectory.json | grep -A 5 "identified_risks"
cat wmdt/data/failed_trajectory.json | grep -A 5 "identified_risks"
```

**报告内容：**
- StrictPM 识别的风险列表
- VaguePM 识别的风险列表
- 两者差异

### 2. 分歧评分检查

```bash
cat wmdt/data/divergence_analysis.json
```

**报告内容：**
- `risk_divergence` 的值
- `overall_divergence` 的值
- PCI 是否成功定位

### 3. 角色输出检查

查看控制台日志中：
- StrictPM 生成的 PRD 是否明确定义了数据类型
- VaguePM 生成的 PRD 是否缺少技术细节
- Developer 的 Schema 是否反映了 PM 的差异

## 🐛 调试建议

### 启用详细日志

在代码顶部添加：

```python
from metagpt.logs import logger
logger.setLevel("DEBUG")
```

### 检查中间输出

所有 BeliefState 的 `raw_response` 字段保存了 LLM 的原始输出，可用于调试：

```python
import json
data = json.load(open("wmdt/data/reference_trajectory.json"))
for bs in data["belief_states"]:
    print(f"Step {bs['step']}, Role {bs['role_name']}")
    print(f"Raw: {bs['raw_response'][:200]}...")
```

## 📚 下一步扩展

1. **添加 QA 角色**：测试失败时才能体现完整的因果链
2. **多轮实验**：运行 10 次取平均值，评估稳定性
3. **对比传统方法**：实现事后日志分析，对比定位准确性

## 🤝 贡献

这是一个研究原型，欢迎提出改进建议！

## 📄 许可证

本项目遵循 MetaGPT 的许可证
