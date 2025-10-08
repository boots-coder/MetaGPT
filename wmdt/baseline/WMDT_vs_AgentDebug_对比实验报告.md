# WMDT vs AgentDebug: 对比实验报告
## 电影评分系统失败轨迹分析对比

---

**实验日期**: 2025-10-08
**场景**: 电影评分数据库系统设计
**失败原因**: PRD 未明确指定 rating 字段的数据类型

---

## 一、实验背景

### 1.1 实验目的

对比两种多智能体系统故障分析方法：
- **WMDT (World Model Divergence Tracking)**: 基于 BeliefState 分歧的 PCI 定位
- **AgentDebug**: 基于执行轨迹错误分类的关键错误检测

通过同一失败场景的分析，验证两种方法的：
1. 定位准确性
2. 根因解释深度
3. 方法论差异
4. 互补性

### 1.2 实验场景

**任务需求**:
```
Build a movie rating database system with the following features:
1. Store movie information (title, director, year, rating)
2. Allow users to rate movies
3. Calculate average ratings

Key requirement: The system should track user ratings for movies.
```

**设计陷阱**:
- 需求中 `rating` 字段未指定数据类型
- 测试 PM 是否能识别技术风险
- 测试 Developer 在信息不足时的决策

**实验设计**:
- **参考轨迹**: StrictPM (严谨PM) + SimpleDeveloper
  - StrictPM 主动识别技术风险，明确数据类型
- **失败轨迹**: VaguePM (模糊PM) + SimpleDeveloper
  - VaguePM 只关注业务需求，忽视技术细节

---

## 二、WMDT 分析结果

### 2.1 方法概述

**核心机制**:
1. 提取每个智能体在每个步骤的 **BeliefState**
2. 对比参考轨迹与失败轨迹的 BeliefState **分歧**
3. 使用 `risk_divergence` 定位 **PCI (Point of Causal Inevitability)**

**BeliefState 结构**:
```python
{
    "global_state": str,        # 对全局状态的理解
    "current_goal": str,        # 当前目标
    "teammate_model": dict,     # 对队友的认知
    "identified_risks": list    # 识别的风险（核心）
}
```

### 2.2 分析过程

#### **Step 0: Alice (PM)**

| 维度 | 参考轨迹 (StrictPM) | 失败轨迹 (VaguePM) |
|------|-------------------|------------------|
| **identified_risks** | • "Potential for ambiguity in **data types and validation rules**"<br>• "Risk of overlooking **implementation pitfalls**" | • "Potential misalignment on **feature specifications**"<br>• "Lack of clarity on **user interface requirements**" |
| **current_goal** | "Write a detailed PRD that **explicitly specifies all technical details**" | "Write a **concise and user-friendly** PRD" |
| **teammate_model** | Bob "may **require clear specifications** to avoid misinterpretation" | Bob "Alice trusts Bob's **technical expertise** to implement" |

**分歧评估**:
- `risk_divergence`: **0.80** ⚠️ (超过阈值 0.5)
- `teammate_divergence`: 0.70
- `goal_divergence`: 0.50
- `overall_divergence`: 0.62

#### **Step 0: Bob (Developer)**

| 维度 | 参考轨迹 | 失败轨迹 |
|------|---------|---------|
| **identified_risks** | "Potential **lack of clarity** on data types" | "The PRD may **lack specific data type specifications**" |

**分歧评估**:
- `risk_divergence`: **0.30** (低于阈值)
- `overall_divergence`: 0.20

### 2.3 WMDT 定位结果

```json
{
  "pci": {
    "step": 0,
    "role_name": "Alice",
    "role_profile": "Product Manager",
    "risk_divergence": 0.80,
    "overall_divergence": 0.62,
    "explanation": "Most critically, the identified risks differ substantially, with the failed state missing key risks related to ambiguity and implementation pitfalls."
  }
}
```

**核心发现**:
1. ✅ PCI 位于 **PM 阶段**（Step 0, Alice）
2. ✅ 根因是 PM 的**风险识别能力缺陷**
3. ✅ VaguePM 只识别了业务风险，遗漏了技术风险
4. ✅ Developer 在两种情况下都识别到了数据类型问题，说明 Developer 不是根源

---

## 三、AgentDebug 分析结果

### 3.1 方法概述

**核心机制**:
1. **Phase 1**: 逐步骤、逐模块进行错误检测
   - Memory, Reflection, Planning, Action 四个模块
   - 基于错误分类法（Error Taxonomy）
2. **Phase 2**: 识别关键错误点（Critical Error）
   - 分析错误的级联效应
   - 定位最早的关键失败点

**错误分类法**:
- **Memory**: hallucination, over_simplification, memory_retrieval_failure
- **Reflection**: progress_misjudge, outcome_misinterpretation, causal_misattribution
- **Planning**: constraint_ignorance, impossible_action, inefficient_plan
- **Action**: format_error, parameter_error, misalignment

### 3.2 Phase 1: Fine-Grained Analysis

#### **Step 1: Alice (VaguePM)**

| 模块 | 错误检测 | 错误类型 | 证据 |
|------|---------|---------|------|
| **Memory** | ⚠️ 有错误 | `over_simplification` | "Agent simplifies the project to just 'creating a movie rating database with specific features'" |
| **Reflection** | ⚠️ 有错误 | `progress_misjudge` | "Overly optimistic view of progress, does not account for potential misalignment on feature specifications" |
| **Planning** | ✅ 无错误 | `no_error` | "The planning output aligns with the task requirements" |
| **Action** | ✅ 无错误 | `no_error` | "The action 'WritePRD()' aligns with the plan" |

#### **Step 2: Bob (Developer)**

| 模块 | 错误检测 | 错误类型 | 证据 |
|------|---------|---------|------|
| **Memory** | ⚠️ 有错误 | `over_simplification` | "Agent simplifies the project to just creating a database schema" |
| **Reflection** | ⚠️ 有错误 | `progress_misjudge` | "Overly optimistic, does not acknowledge that the task has already been completed" |
| **Planning** | ✅ 无错误 | `no_error` | "The planning output logically follows the requirements" |
| **Action** | ✅ 无错误 | `no_error` | "The action 'WriteSchema()' aligns with the plan" |

### 3.3 Phase 2: Critical Error Detection

```json
{
  "critical_step": 1,
  "critical_module": "planning",
  "error_type": "constraint_ignorance",
  "root_cause": "The agent's plan did not adequately consider the complexity of the project, particularly the need for clear feature specifications and user interface requirements. This oversight led to a lack of alignment between the PRD and the actual implementation.",
  "evidence": "The agent simplifies the project to just creating a database schema for a Movie Rating system based on the provided PRD.",
  "correction_guidance": "The agent should have conducted a thorough analysis of the PRD, ensuring that all aspects, including user needs, business value, and feature specifications, were clearly understood.",
  "cascading_effects": [
    {
      "step": 2,
      "effect": "Bob's understanding was based on an incomplete plan, leading to misjudgment of progress and potential issues in schema design."
    }
  ],
  "confidence": 0.90
}
```

**核心发现**:
1. ✅ Critical Error 位于 **Step 1 (PM)**
2. ⚠️ 定位的模块是 **Planning**（而非风险识别）
3. ⚠️ 错误类型是 `constraint_ignorance`（约束忽视）
4. ⚠️ 根因描述强调了"功能规格"和"用户界面需求"，而非技术细节（如数据类型）

---

## 四、方法对比分析

### 4.1 定位结果对比

| 维度 | WMDT | AgentDebug |
|------|------|-----------|
| **关键步骤** | Step 0, Alice | Step 1, Alice |
| **关键模块/维度** | **风险识别 (identified_risks)** | **Planning** |
| **核心指标** | `risk_divergence = 0.80` | `confidence = 0.90` |
| **错误类型** | 风险识别缺陷（遗漏技术风险） | `constraint_ignorance`（约束忽视） |
| **根因描述** | "VaguePM 只识别了业务风险，遗漏了数据类型等技术风险" | "PM 的计划未充分考虑项目复杂性，特别是功能规格和UI需求" |

**一致性**:
- ✅ 两种方法都定位到了 **PM 阶段**
- ✅ 都认为 PM 存在问题，而非 Developer
- ✅ 都识别出 PM 忽视了某些重要因素

**差异性**:
- ❌ WMDT 定位到**风险识别维度**，AgentDebug 定位到 **Planning 模块**
- ❌ WMDT 强调"遗漏**技术风险**"，AgentDebug 强调"忽视**功能规格**"
- ❌ WMDT 通过分歧对比定位，AgentDebug 通过单轨迹错误分类定位

### 4.2 分析粒度对比

#### **WMDT 的分析粒度**:

```
Role (Alice) → BeliefState 维度 → 分歧评估
                    ↓
    • global_state (理解)
    • current_goal (目标)
    • teammate_model (队友认知)
    • identified_risks (风险识别) ← 关键维度
```

**优势**:
- 直接捕捉到 PM 的**认知模式**（"技术细节应由开发者决定"）
- 通过对比揭示**认知差异**（业务风险 vs 技术风险）
- 定位到**风险识别能力**这一深层认知缺陷

#### **AgentDebug 的分析粒度**:

```
Step → Module → Error Type
         ↓
    • Memory (记忆)
    • Reflection (反思)
    • Planning (规划) ← Critical Error 定位
    • Action (行动)
```

**优势**:
- 系统化的错误分类（覆盖 20+ 种错误类型）
- 级联效应追踪（Step 1 → Step 2）
- 独立分析（无需参考轨迹）

**局限**:
- Planning 模块的错误检测主要基于行为输出，难以捕捉**认知模式**
- 将问题描述为"未考虑项目复杂性"，不如 WMDT 的"遗漏技术风险"精准

### 4.3 根因解释对比

#### **WMDT 的根因解释**:

> **VaguePM 只识别了业务风险（"功能规格对齐"、"UI需求"），完全遗漏了技术风险（"数据类型"、"验证规则"），导致 PRD 缺失关键技术细节。**

**关键证据**:
- VaguePM 的 identified_risks: ❌ 无技术风险
- StrictPM 的 identified_risks: ✅ 明确技术风险
- Developer 的 identified_risks: ✅ 两者都识别到数据类型问题

**结论**: PM 的风险识别能力是根因，Developer 是受害者。

---

#### **AgentDebug 的根因解释**:

> **PM 的计划未充分考虑项目复杂性，特别是需要明确的功能规格和用户界面需求，导致 PRD 与实现不对齐。**

**关键证据**:
- Step 1 Memory: `over_simplification`
- Step 1 Reflection: `progress_misjudge`
- Step 1 Planning: `constraint_ignorance` ← Critical Error

**结论**: PM 的规划不够全面，导致后续问题。

---

### 4.4 评判性对比

#### **WMDT 的优势**:

1. ✅ **认知深度**: 直接访问智能体的内部认知状态（BeliefState）
   - 捕捉到 VaguePM 的认知模式："相信开发者会做出正确选择"
   - 揭示了隐含假设的问题

2. ✅ **精准定位**: 通过 `risk_divergence = 0.80` 明确指出风险识别是问题所在
   - 不是"规划不够全面"，而是"风险识别类型错误"

3. ✅ **责任归属**: 清晰地证明 Developer 不是根源
   - 两个 Developer 的 risk_divergence 仅 0.30
   - 两者都识别到了数据类型问题

#### **WMDT 的局限**:

1. ❌ **依赖参考轨迹**: 需要一条成功的参考轨迹
   - 在真实场景中，可能没有明确的"成功轨迹"
   - 需要提前设计对比实验

2. ❌ **BeliefState 提取成本**: 每个角色的每个步骤都需要 LLM 调用
   - 本实验：4 个 BeliefState + 2 个分歧评估 = 6 次 API 调用
   - 大规模系统成本会快速上升

3. ❌ **BeliefState 真实性**: 依赖 LLM 的自省能力
   - 可能存在"事后合理化"风险
   - 提取的 BeliefState 可能不完全真实

---

#### **AgentDebug 的优势**:

1. ✅ **独立分析**: 只需要失败轨迹，无需参考轨迹
   - 更灵活，适用于单次失败诊断

2. ✅ **系统化分类**: 基于 Error Taxonomy 的 20+ 种错误类型
   - 覆盖面广（Memory, Reflection, Planning, Action, System）
   - 可解释性强（每种错误都有定义和示例）

3. ✅ **级联效应追踪**: 明确展示错误如何传播
   - Step 1 的 Planning 错误 → Step 2 的理解偏差

#### **AgentDebug 的局限**:

1. ❌ **分析层次**: 主要基于行为输出，难以捕捉深层认知缺陷
   - 将问题归类为 `constraint_ignorance`（约束忽视）
   - 但未指出具体遗漏了**哪些约束**（技术风险 vs 业务风险）

2. ❌ **根因精度**: 根因描述相对模糊
   - "未充分考虑项目复杂性" vs WMDT 的"遗漏技术风险"
   - 未明确指出 PM 的认知模式缺陷

3. ❌ **Phase 1 噪音**: Memory 和 Reflection 也检测到错误
   - Step 1 Memory: `over_simplification`
   - Step 1 Reflection: `progress_misjudge`
   - 这些可能是误报，因为 PM 的 Memory 和 Reflection 本身没有明显问题

---

## 五、互补性分析

### 5.1 两种方法的互补关系

```
┌─────────────────────────────────────────────────────────┐
│                    故障分析全景图                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  认知层 (Cognitive Layer)                                │
│  ┌─────────────────────────────────────────┐           │
│  │  WMDT: BeliefState Divergence           │           │
│  │  • identified_risks 分歧                │           │
│  │  • teammate_model 差异                  │           │
│  │  • 认知模式缺陷                          │           │
│  └─────────────────────────────────────────┘           │
│             ↓ (认知 → 行为)                              │
│                                                         │
│  行为层 (Behavioral Layer)                               │
│  ┌─────────────────────────────────────────┐           │
│  │  AgentDebug: Module Error Detection     │           │
│  │  • Planning: constraint_ignorance       │           │
│  │  • Memory: over_simplification          │           │
│  │  • Reflection: progress_misjudge        │           │
│  └─────────────────────────────────────────┘           │
│             ↓ (行为 → 结果)                              │
│                                                         │
│  结果层 (Outcome Layer)                                  │
│  ┌─────────────────────────────────────────┐           │
│  │  传统调试: Execution Failure             │           │
│  │  • 数据类型选择错误                       │           │
│  │  • Schema 不符合需求                     │           │
│  └─────────────────────────────────────────┘           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 5.2 理想的组合流程

**Step 1**: 使用 **AgentDebug** 进行快速诊断
- 目的：快速定位到可疑的步骤和模块
- 优势：无需参考轨迹，成本低
- 输出：Critical Error (Step 1, Planning, constraint_ignorance)

**Step 2**: 使用 **WMDT** 进行根因分析
- 目的：深入分析认知层的缺陷
- 优势：揭示深层认知模式问题
- 输出：PCI (Step 0, Alice, risk_divergence=0.80, 遗漏技术风险)

**Step 3**: 综合诊断
- **AgentDebug 结论**: PM 的 Planning 忽视了约束
- **WMDT 结论**: PM 的风险识别能力缺陷，遗漏了技术风险
- **综合诊断**: PM 在规划时未识别技术风险（数据类型、验证规则），导致 PRD 缺失关键约束

---

## 六、案例验证：数据类型问题

### 6.1 失败的完整链条

```
VaguePM (Step 0)
   ↓
identified_risks: ["功能规格对齐", "UI需求不清晰"]
   ↓ (遗漏技术风险)
PRD: 未明确 rating 字段的数据类型
   ↓
Developer (Step 0)
   ↓
identified_risks: ["PRD 可能缺少数据类型规格"]
   ↓ (意识到问题，但仍执行)
Schema: 在缺少信息的情况下选择数据类型
   ↓
Result: 可能与需求不符
```

### 6.2 WMDT 的分析路径

1. **对比 BeliefState**: 发现 VaguePM 的 identified_risks 与 StrictPM 完全不同
2. **计算 risk_divergence**: 0.80（远超阈值）
3. **定位 PCI**: Step 0, Alice
4. **根因**: VaguePM 遗漏了技术风险

### 6.3 AgentDebug 的分析路径

1. **Phase 1 分析**:
   - Memory: over_simplification
   - Reflection: progress_misjudge
   - Planning: constraint_ignorance ← 识别为问题
2. **Phase 2 定位**: Step 1, Planning
3. **根因**: Planning 未充分考虑项目复杂性

### 6.4 哪个更准确？

**WMDT 更精准**:
- ✅ 直接指出"遗漏技术风险（数据类型、验证规则）"
- ✅ 揭示了 VaguePM 的认知模式："相信开发者会做正确选择"
- ✅ 通过对比证明 Developer 不是根源

**AgentDebug 更全面**:
- ✅ 检测到多个维度的问题（Memory, Reflection, Planning）
- ✅ 提供了系统化的错误分类
- ✅ 追踪了级联效应

**最佳实践**: 两者结合
- AgentDebug 快速定位到 Planning 模块有问题
- WMDT 深入分析发现根因是风险识别缺陷

---

## 七、评判性质疑

### 7.1 对 WMDT 的质疑

#### **质疑 1**: BeliefState 是否真实反映了内部认知？

**证据**:
- VaguePM 的 BeliefState 显示她"相信 Bob 的技术专长"
- 这可能是 LLM 的**事后合理化**，而非真实决策依据

**反驳**:
- VaguePM 的行为（生成简洁PRD）与 BeliefState 一致
- 如果 BeliefState 是事后编造的，应该也会提到技术风险

**结论**: BeliefState 有一定真实性，但可能存在偏差。

---

#### **质疑 2**: risk_divergence = 0.80 是否过高？

**证据**:
- VaguePM 识别了 2 个风险（业务层面）
- StrictPM 识别了 2 个风险（技术层面）
- 两者都识别了风险，只是类型不同

**反驳**:
- 关键不是"是否识别风险"，而是"识别了**什么类型**的风险"
- 对于技术项目，遗漏技术风险是致命的
- 0.80 的分歧合理地反映了这一严重性

**结论**: risk_divergence 的高分值合理。

---

### 7.2 对 AgentDebug 的质疑

#### **质疑 1**: 为什么 Planning 被标记为 "no_error" 在 Phase 1，却成为 Critical Error？

**观察**:
- Phase 1: Planning = `no_error`
- Phase 2: Critical Error at Planning = `constraint_ignorance`

**解释**:
- Phase 1 的检测可能不够敏感
- Phase 2 综合了多个步骤的信息后重新评估

**问题**:
- 这种不一致性降低了方法的可信度
- 应该在 Phase 1 就检测到 Planning 的问题

---

#### **质疑 2**: Memory 和 Reflection 的错误是否是误报？

**Phase 1 检测到的错误**:
- Step 1 Memory: `over_simplification`
- Step 1 Reflection: `progress_misjudge`

**质疑**:
- PM 的 Memory 只是回顾任务理解，何来"过度简化"？
- PM 的 Reflection 识别了风险，何来"进展误判"？

**可能的原因**:
- AgentDebug 的 Error Taxonomy 对 PM 角色的适配性不足
- Memory 和 Reflection 错误定义更适合执行型任务（如 ALFWorld）

**结论**: 存在一定的误报率，需要人工判断。

---

### 7.3 对实验设计的质疑

#### **质疑**: 实验是否具有"结果导向"偏见？

**观察**:
- StrictPM 和 VaguePM 的设计就是为了产生对比
- 实验只验证了预设的差异

**反驳**:
- 这是概念验证（Proof of Concept）实验
- 目的是验证 WMDT 能否捕捉到已知的认知差异
- 下一步应该在真实失败案例中验证

**结论**: 实验设计合理，但需要扩展到真实场景。

---

## 八、结论与展望

### 8.1 核心发现总结

1. **两种方法都定位到了 PM 阶段的问题**
   - WMDT: Step 0, risk_divergence = 0.80
   - AgentDebug: Step 1, confidence = 0.90

2. **WMDT 在根因精度上更优**
   - 明确指出"遗漏技术风险"
   - 揭示了 PM 的认知模式缺陷

3. **AgentDebug 在系统化分类上更优**
   - 覆盖 20+ 种错误类型
   - 提供级联效应追踪

4. **两种方法高度互补**
   - AgentDebug 适合快速诊断（执行层）
   - WMDT 适合深度分析（认知层）

### 8.2 方法适用性对比

| 场景 | WMDT | AgentDebug |
|------|------|-----------|
| **单次失败诊断** | ❌ 需要参考轨迹 | ✅ 只需失败轨迹 |
| **根因分析** | ✅ 认知层深度分析 | ⚠️ 行为层分类 |
| **多角色协作** | ✅ 通过分歧定位责任 | ⚠️ 可能误判责任 |
| **成本** | ⚠️ 需要双轨迹 + BeliefState 提取 | ✅ 单轨迹分析 |
| **可解释性** | ✅ 分歧对比直观 | ✅ 错误分类清晰 |

### 8.3 未来工作方向

1. **扩展实验场景**
   - 增加更多领域（API 设计、UI 开发等）
   - 测试更复杂的多角色系统（3+ 角色）

2. **方法融合**
   - 开发集成框架，结合两种方法的优势
   - Phase 1: AgentDebug 快速定位
   - Phase 2: WMDT 深度分析

3. **真实案例验证**
   - 在实际软件开发项目中应用
   - 收集失败案例数据集

4. **方法改进**
   - WMDT: 降低 BeliefState 提取成本
   - AgentDebug: 改进 PM 角色的错误检测

---

## 九、附录

### 9.1 实验数据

- **WMDT 数据**: `/home/haoxuan004/MetaGPT/wmdt/wmdt/data/`
  - `reference_trajectory.json`
  - `failed_trajectory.json`
  - `divergence_analysis.json`

- **AgentDebug 数据**: `/home/haoxuan004/MetaGPT/wmdt/wmdt/agentdebug_format/`
  - `movie_rating_failed.json`
  - `phase1_results.json`
  - `phase2_results.json`

### 9.2 代码仓库

- **WMDT 实现**: `/home/haoxuan004/MetaGPT/wmdt/`
- **AgentDebug**: `/home/haoxuan004/MetaGPT/wmdt/baseline/AgentDebug/`
- **对比实验**: `/home/haoxuan004/MetaGPT/wmdt/baseline/`

### 9.3 关键代码

- WMDT 实验: `wmdt/experiments/run_experiment.py`
- AgentDebug 分析: `baseline/run_agentdebug_analysis.py`
- 轨迹转换: `baseline/wmdt_to_agentdebug_adapter.py`

---

**报告完成日期**: 2025-10-08
**实验执行者**: haoxuan004
**模型**: OpenAI GPT-4o-mini (via OpenRouter)
**报告版本**: v1.0
