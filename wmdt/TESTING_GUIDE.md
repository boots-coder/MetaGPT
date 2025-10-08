# WMDT 测试指南

## 🎯 测试目标

验证 WMDT 框架能够：
1. 提取智能体的 BeliefState（内部认知状态）
2. 对比参考轨迹和失败轨迹的分歧
3. 定位 PCI（Point of Causal Inevitability）

---

## 📋 测试准备

### 1. 确认环境

```bash
conda activate wmdt
cd /home/haoxuan004/MetaGPT
```

### 2. 检查配置

确认 `config/config2.yaml` 已正确配置 OpenRouter API key：

```bash
cat config/config2.yaml | grep api_key
```

应显示：
```yaml
api_key: "sk-or-v1-..."
```

---

## 🧪 测试步骤

### 阶段 1: 基础功能测试（预计 3-5 分钟）

运行基础测试验证核心组件：

```bash
python -m wmdt.tests.test_basic_workflow
```

或使用快捷脚本：

```bash
./wmdt/run_quick_test.sh
```

#### 预期输出

```
╔═══════════════════════════════════════════════════════════╗
║              WMDT Basic Workflow Tests                   ║
╚═══════════════════════════════════════════════════════════╝

===========================================================
TEST 1: StrictPM BeliefState Generation
===========================================================
...
✅ TEST PASSED: BeliefState generated
   - Role: Alice
   - Goal: Write a clear and complete PRD...
   - Identified Risks: ['rating data type not specified', ...]

===========================================================
TEST 2: Full PM + Developer Workflow
===========================================================
...
✅ TEST PASSED: Both roles generated BeliefStates
   Dev's Goal: Write database schema based on PRD...

===========================================================
TEST 3: BeliefState Serialization
===========================================================
✅ TEST PASSED: Serialization/Deserialization works

===========================================================
TEST SUMMARY
===========================================================
✅ PASS - StrictPM BeliefState Generation
✅ PASS - Full PM + Developer Workflow
✅ PASS - BeliefState Serialization

Overall: 3/3 tests passed
🎉 All tests passed!
```

#### 如果测试失败

**症状 1: "Failed to parse BeliefState JSON"**
- **原因**: LLM 返回格式不正确
- **检查**: 查看日志中的 `raw_response`
- **解决**: 可能需要调整模型（从 `claude-3.5-sonnet` 换到 `gpt-4`）

**症状 2: "No BeliefState generated"**
- **原因**: LLM 调用失败或超时
- **检查**:
  ```bash
  curl -H "Authorization: Bearer YOUR_API_KEY" https://openrouter.ai/api/v1/models
  ```
- **解决**: 检查网络连接和 API key 有效性

**症状 3: "StrictPM didn't identify any risks"**
- **原因**: Prompt 未能引导 LLM 识别风险
- **影响**: 不影响流程，但 PCI 定位可能失败
- **记录**: 将 `identified_risks` 字段的内容发送给 Claude 分析

---

### 阶段 2: 完整实验（预计 10-15 分钟）

运行完整的对比实验：

```bash
python -m wmdt.experiments.run_experiment
```

#### 预期输出

```
╔═══════════════════════════════════════════════════════════╗
║      WMDT Experiment: Movie Rating System                ║
║      Comparing Strict PM vs. Vague PM                     ║
╚═══════════════════════════════════════════════════════════╝

===========================================================
🟢 Running REFERENCE Trajectory (StrictPM + Developer)
===========================================================
...
✅ Reference trajectory saved: 2 BeliefStates

===========================================================
🔴 Running FAILED Trajectory (VaguePM + Developer)
===========================================================
...
✅ Failed trajectory saved: 2 BeliefStates

===========================================================
🔍 Analyzing Divergence & Locating PCI
===========================================================
Aligned 2 BeliefState pairs
Evaluated 2 divergence scores

╔═══════════════════════════════════════════════════════════╗
║                    🎯 PCI FOUND!                         ║
╠═══════════════════════════════════════════════════════════╣
║ Step:              0                                      ║
║ Role:              Alice                                  ║
║ Risk Divergence:   0.85                                   ║
║ Overall Divergence: 0.72                                  ║
║ Explanation:       Reference PM identified rating type   ║
║                    risk; Failed PM did not               ║
╚═══════════════════════════════════════════════════════════╝

===========================================================
✅ Experiment Complete!
📁 Results saved to: wmdt/data/
===========================================================
```

---

## 📊 结果分析

### 1. 检查生成的文件

```bash
ls -lh wmdt/data/
```

应包含：
```
reference_trajectory.json     # 参考轨迹
failed_trajectory.json        # 失败轨迹
divergence_analysis.json      # 分歧分析结果
```

### 2. 查看 BeliefState 内容

**StrictPM 的风险识别**（应该包含关键风险）：
```bash
cat wmdt/data/reference_trajectory.json | python -m json.tool | grep -A 10 "identified_risks"
```

**VaguePM 的风险识别**（应该为空或缺少关键风险）：
```bash
cat wmdt/data/failed_trajectory.json | python -m json.tool | grep -A 10 "identified_risks"
```

### 3. 查看分歧评分

```bash
cat wmdt/data/divergence_analysis.json | python -m json.tool | grep -A 5 "divergence"
```

关注以下指标：
- `risk_divergence`: **核心指标**，应在 PM 步骤显著 > 0.5
- `overall_divergence`: 总体分歧
- `explanation`: 分歧原因解释

---

## 📝 报告清单

请将以下信息报告给 Claude 进行分析：

### ✅ 必须报告的内容

1. **基础测试结果**
   ```bash
   # 复制完整的测试输出
   python -m wmdt.tests.test_basic_workflow 2>&1 | tee test_output.log
   cat test_output.log
   ```

2. **BeliefState 对比**
   ```bash
   echo "=== StrictPM Risks ==="
   cat wmdt/data/reference_trajectory.json | python -m json.tool | grep -A 5 "identified_risks"

   echo "=== VaguePM Risks ==="
   cat wmdt/data/failed_trajectory.json | python -m json.tool | grep -A 5 "identified_risks"
   ```

3. **PCI 定位结果**
   ```bash
   cat wmdt/data/divergence_analysis.json | python -m json.tool | grep -A 10 "pci"
   ```

### 🔍 可选但有帮助的内容

4. **完整的轨迹文件**
   ```bash
   cat wmdt/data/reference_trajectory.json
   cat wmdt/data/failed_trajectory.json
   ```

5. **PRD 和 Schema 对比**
   - 在控制台日志中查找 StrictPM 和 VaguePM 生成的 PRD
   - 查找 Developer 生成的 Schema

---

## ✅ 成功标准

实验被认为成功，如果：

1. ✅ **所有基础测试通过**（3/3）
2. ✅ **StrictPM 识别出风险**
   - `identified_risks` 包含 "rating"、"data type"、"type specification" 等关键词
3. ✅ **VaguePM 未识别关键风险**
   - `identified_risks` 为空，或不包含上述关键词
4. ✅ **risk_divergence 显著**
   - PM 步骤的 `risk_divergence` >= 0.5
5. ✅ **PCI 定位到 PM 角色**
   - PCI 的 `role_name` = "Alice"
   - PCI 的 `step` = 0 或 1

---

## 🐛 常见问题

### Q1: 测试运行很慢
**A**: 正常现象。每个 BeliefState 提取需要 1 次 LLM 调用，分歧评估也需要 LLM 调用。
- 基础测试：~3-5 分钟
- 完整实验：~10-15 分钟

### Q2: "risk_divergence" 很低（< 0.3）
**A**: 说明两个 PM 的行为过于相似，需要强化 Prompt 的对比度：
- 检查 `wmdt/core/prompts.py` 中的 `STRICT_PM_SYSTEM_PROMPT` 和 `VAGUE_PM_SYSTEM_PROMPT`
- 可能需要在 `WritePRD` 的 `specific_instruction` 中加强对比

### Q3: PCI 未找到
**A**:
- 检查 `risk_divergence` 是否真的低于阈值
- 尝试降低 PCI 检测阈值：
  ```python
  pci = judge.find_pci(risk_threshold=0.4)  # 默认 0.6
  ```

---

## 📧 提交测试结果

将以下内容整理后发送给 Claude：

1. **环境信息**
   ```
   - OS: Linux/macOS/Windows
   - Python version: 3.10
   - MetaGPT commit: ...
   - LLM model: claude-3.5-sonnet / gpt-4
   ```

2. **基础测试日志**（完整输出）

3. **BeliefState 样本**
   - 至少 1 个 StrictPM 的 BeliefState
   - 至少 1 个 VaguePM 的 BeliefState

4. **PCI 定位结果**（如果找到）

5. **遇到的问题**（如果有）

---

祝测试顺利！🚀
