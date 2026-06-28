---
name: four-phase-coding-workflow
description: 4 阶段校正工作流（阶段 1 校验实施文档 → 阶段 2 编码 → 阶段 3 再校验 → 阶段 4 父 agent 反查总结）。用于“以上游文档为依据，先校正实施文档，再按校正后的实施文档修改代码”的高审计任务。职责是忠实执行设计而非自由发挥；发现冲突时优先反馈。base doc 启动前确认；阶段间严格串行；阶段 4 不信任子 agent 报告，必须亲自反查。
when_to_use: 当任务要求“以上游文档/设计文档为依据，先校正实施文档，再按校正后的实施文档修改代码”，且目标是忠实执行设计而非自由发挥，并要求阶段化验证、子 agent 编排、最终父 agent 反查时使用。
version: 1.2.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
effort: high
metadata:
  hermes:
    tags: [coding, four-phase, doc-coding, anti-hallucination, parallel-then-serial]
    related_skills: [parallel-task-decomposition, hermes-agent]
---

# 4 阶段校正工作流

## Overview

这是一个高审计、强约束的工程 workflow：

1. 先以 **base doc / 上游设计** 为真理源校验实施文档
2. 再按 **校正后的实施文档** 去编码
3. 再对照文档和代码进行二次校验
4. 最后由父 agent **亲自反查** 阶段 3 的报告，并只给真实结论与修复建议

它不是用来发挥创意、优化架构或顺手重构的。它的职责是：**忠实执行设计；发现问题时尽早反馈；在任何不确定处优先停下并报告，而不是自由发挥。**

## 适用场景

适用于以下任务：
- “以 X 为基础，校正 Y，然后改代码”
- “按技术文档 / 数据库设计 / API 文档，校正实施计划，再实现”
- “先校验 doc，再按校正后的 doc 实现”
- 文档、设计、代码三层必须严格对齐的高风险任务

典型触发词：
- “以 X 为基础，校正 Y，然后改代码”
- “4 阶段”
- “校验 doc 然后改代码”
- “按 X 文档，校正 Y 设计，然后实现”

## 不适用场景

不要用于：
- 单纯改代码（优先用 `subagent-driven-development`）
- 单纯文档校验（用专门的文档校验 skill）
- 单纯研究 / 摸底（用 `parallel-task-decomposition`）
- 需要探索性设计、试验性实现、快速原型的任务

## 工作流定位

- **忠实执行设计优先于创意发挥**：本 workflow 的职责不是优化、重构、二次设计或“顺手改进”，而是严格以上游文档为真理源执行。
- **发现冲突优先反馈**：如果 base doc、实施文档、代码现状三者冲突，优先反馈，不擅自发明方案。
- **校正后的实施文档是阶段 2 的直接输入**：阶段 2 不直接根据“记忆中的阶段 1 结论”编码，而是根据已经被父 agent 整理过的校正结果编码。
- **阶段 4 才是最终判决门**：阶段 3 的报告不是结论，只是待反查 claim。

## 核心原则

1. **base doc 不写死**：阶段 1 启动前必须确认哪些文档是上游真理源。
2. **阶段间严格串行**：上一阶段的输出是下一阶段的输入，绝不并行启动下一阶段。
3. **阶段内按依赖决定并行**：只有真正独立的任务才允许并行。
4. **反幻觉门**：阶段 3 报告“代码有问题”时，阶段 4 必须亲自 `grep` / `read_file` / `git log` / 终端反查，确认属实后才给修复建议。
5. **实施文档硬约束必须传播**：阶段 1 得出的“实施文档应该改成什么”，必须显式传给阶段 2 编码子 agent。
6. **先反馈再修复**：除非用户明确批准，阶段 4 只给结论和建议，不直接修代码。

## 父 agent 角色边界

父 agent 默认只负责：
- `clarify` 确认 base doc、范围、决策点
- 阶段编排与子 agent 任务描述构造
- 阶段交接压缩（handoff compaction）
- `search_files` / `read_file` / `terminal` / `git log` / `grep` 反查
- 阶段 4 最终结论与修复建议

父 agent 默认**不负责**：
- 编写业务代码
- 编写测试
- 修改大段实现文件
- 替子 agent 做整文件编码收尾

允许的例外：
- 1~2 行机械性修正
- 用户明确要求父 agent 亲自修改

原则：**保持父会话上下文干净，把编码工作尽量委托给 fresh subagent。**

## 决策矩阵

### 硬规则

- 两个任务触及同一文件路径 → **必须串行**
- 任务 A 的输出是任务 B 的输入 → **必须串行**
- 阶段 3 → **只读不写**
- 阶段 4 → **只总结与反查，不写代码**
- 父 agent → **默认不参与业务编码**
- 阶段 1 出现互斥设计建议 → **必须进入决策评审门**
- 阶段 4 确认真实问题 → **只给修复建议，待用户确认后才修**

### 推荐规则

| 场景 | 推荐模式 | 原因 |
|---|---|---|
| base doc 固定、任务连续、数量多 | 单子 agent 全量串行校验 | 降低重复读文档与 429 风险 |
| 多个 base doc 视角独立 | 多子 agent 并行校验 | 更快发现不同偏离类型 |
| 多个不同文件、互不依赖 | 并行编码 | 降低总耗时 |
| 高耦合模块 / 接口联动强 | 串行编码 | 降低 sibling 冲突和语义漂移 |
| 出现互斥建议 | 父 agent 汇总后 clarify | 保持真理源单一 |
| 子 agent 限流风险高 / token 压力大 | 单子 agent 串行优先 | 更稳、更省上下文成本 |

## 阶段交接规则（Handoff Compaction）

阶段之间传递信息时：
- **不传全文报告**
- **不传长篇推理过程**
- **不传冗长子 agent 自述**
- 只传下一阶段真正需要的最小信息集合

### Phase 1 → Phase 2 只传
- `finding_id`
- 受影响文件 / 模块
- 受影响 doc 章节
- 校正后的硬约束
- 是否需要用户拍板
- 必要证明句柄

### Phase 2 → Phase 3 只传
- `task_id`
- `related_finding_ids`
- `commit_hash`
- `files_touched`
- `tests_run`
- 必要 `grep` / `read_file` 句柄
- 偏离说明（如有）

### Phase 3 → Phase 4 只传
- `verification_id`
- `claim`
- 对应文件
- 对应 `commit_hash`
- 对应 `doc_clause`
- 必要证明句柄

目标不是减少严谨性，而是减少父会话被中间噪声侵蚀。

## 证明句柄规则

任何关键 finding / claim / 结论，都必须附带 **父 agent 可低成本复查的证明句柄**。

### 文档类证明句柄
- 文件路径
- 章节标识
- 行号范围或 `grep` pattern
- 一句话 claim

### 代码类证明句柄
- 文件路径
- `commit_hash`
- 行号范围或 `grep` pattern
- 一句话 claim

### 测试类证明句柄
- 测试文件路径
- 测试名或 `grep` pattern
- 运行命令
- 一句话结论

阶段 4 父 agent 不需要吃完整分析过程，只按句柄反查关键 claim。

## 偏离类型（Mismatch Taxonomy）

阶段 1 的 `mismatch_type` 统一使用以下枚举：
- `naming_drift` — 命名风格偏离
- `api_shape_drift` — API 形式偏离（函数 / static / class / 参数签名）
- `value_mismatch` — 常量、枚举值、数字约束不一致
- `acceptance_gap` — 验收项缺失
- `responsibility_bleed` — 职责污染或边界不清
- `reference_breakage` — 跨文档引用断裂 / 版本不一致
- `existence_misclassification` — “新建”与“扩展”判断错误
- `test_gap` — 测试覆盖缺口
- `error_handling_drift` — 错误处理形式偏离

## 四阶段快速对照

| 阶段 | 任务 | 子 agent 模式 | 父 agent 职责 |
|---|---|---|---|
| 1 | 校验实施文档 | 按 base doc 或维度拆分；必要时单子 agent 全量串行 | 确认真理源、回收 finding、决策评审门 |
| 2 | 编码 | 同文件必串；独立文件可并行 | 传递校正结果与硬约束、验证 commit 真实性 |
| 3 | 再校验 | 只读，可并行 | 收集 verification item，不写代码 |
| 4 | 总结 + 反查 | 父 agent 亲自执行 | 按证明句柄反查、输出真实结论与修复建议 |

## 阶段 1：校验实施文档

### 1.1 启动前确认

用一次 `clarify` 收集：
- 哪些是 base doc
- 校验范围（某个里程碑 / 某个模块 / 全量）
- 是否已授权自主推进模式

如果用户需要你给建议，不要只列选项；要同时给：
- 推荐项
- 理由
- 风险 / 代价

### 1.2 阶段 1 输出 schema

```markdown
## Phase 1 Finding
- finding_id:
- severity: high|medium|low
- target_doc:
- target_section:
- base_doc_refs:
- claim:
- mismatch_type:
- exact_fix_recommendation:
- requires_user_decision: yes|no
- proof_handle:
```

### 1.3 阶段 1 子 agent 模板

完整模板见：`references/phase-1-validator-template.md`

### 1.4 阶段 1 回收

父 agent 负责：
- 等待所有子 agent 完成
- 汇总 finding
- 对互斥建议进入决策评审门
- 产出“实施文档改动清单”，供阶段 2 使用

## 阶段 2：编码

### 2.1 阶段 2 输入

必须明确给编码子 agent：
- base doc 指引（只给相关章节）
- 校正后的实施文档版本 / 结论
- 阶段 1 的 `finding_id` 与硬约束
- 任务边界（哪些文件能改，哪些不能改）

### 2.2 阶段 2 输出 schema

```markdown
## Phase 2 Delivery
- task_id:
- related_finding_ids:
- files_touched:
- commit_hash:
- tests_run:
- constraints_applied:
- deviations_from_corrected_doc:
- unresolved_risks:
- proof_handle:
```

### 2.3 阶段 2 子 agent 模板

完整模板见：`references/phase-2-coder-template.md`

### 2.4 阶段 2 回收

父 agent 负责：
- 验证 commit 真实存在
- 验证关键文件确实被改动
- 整理“代码改动清单”供阶段 3 使用

## 阶段 3：再校验

### 3.1 阶段 3 输入

只给：
- 阶段 2 的 commit hash
- 对应文件
- base doc 相关章节
- 校正后的实施文档相关章节

### 3.2 阶段 3 输出 schema

```markdown
## Phase 3 Verification Item
- verification_id:
- related_commit_hash:
- file:
- doc_clause_checked:
- claim:
- verdict: pass|fail|partial|uncertain
- repair_needed: yes|no
- proof_handle:
```

### 3.3 阶段 3 子 agent 模板

完整模板见：`references/phase-3-verifier-template.md`

### 3.4 阶段 3 回收

- 阶段 3 只报告，不修改任何代码
- 输出不是最终结论，而是待阶段 4 反查的 claim 集合

## 阶段 4：父 agent 反查总结

### 4.1 阶段 4 输入

- 阶段 3 的 `verification_id` + claim + proof_handle
- 阶段 2 的 commit hash
- base doc + 实施文档相关章节

### 4.2 阶段 4 核心动作

父 agent 不信任阶段 3 报告，必须亲自反查：
- 它说的文件存在吗？
- 它说的 commit 真的存在吗？
- 它说的代码片段真的在那行吗？
- 它说的文档条款真的是那个意思吗？

### 4.3 阶段 4 输出 schema

```markdown
## Phase 4 Parent Recheck
- verification_id:
- parent_verdict: confirmed|rejected|partial
- checked_with:
- parent_evidence:
- recommended_action:
- requires_user_approval: yes|no
```

### 4.4 阶段 4 模板

完整模板见：`references/phase-4-parent-recheck-template.md`

### 4.5 阶段 4 产出规则

- 只给真实结论与修复建议
- 不直接修代码
- 只有用户确认后才进入修复阶段

## 常见错误门

| 错误 | 症状 | 应对 |
|---|---|---|
| 子 agent 报告失实 | 子 agent 说文件 / commit / 行号有问题，但父 agent 反查不成立 | 阶段 4 反查，不信转述 |
| 同文件并行写竞争 | patch / diff / sibling 冲突 | 同一文件必须串行 |
| 阶段 2 自由发挥 | API 形式 / 命名 / 错误处理偏离校正后的实施文档 | 在任务描述里显式写硬约束 |
| base doc 写死 | skill 只能在某个技术栈复用 | 启动前确认，运行时填占位符 |
| 把阶段 3 报告当最终结论 | 直接进入修复 | 必须先过阶段 4 反查 |
| 目标文件其实已存在，但文档写成“新建” | 子 agent 报告混淆“与现状偏离”和“与上游真理偏离” | 阶段 1 启动前先校准项目现状 |

## Pitfalls

- 跳过 clarify 直接执行：base doc 错位 → 全程返工
- 阶段 1 报告不传给阶段 2：编码 agent 不知道“实施文档怎么改”，会自由发挥
- 阶段 3 报告直接当结论：失实风险高，必须阶段 4 反查
- 阶段 4 直接写修复 commit：跳过用户确认
- base doc 与实施文档混用：必须区分，**base doc 是上游真理，实施文档是待校验对象**
- 阶段 2 子 agent 过多：管理成本和限流风险会迅速上升
- 阶段 1 子 agent 报“无问题”：警惕，它可能没找到 base doc，而不是真的无问题
- 阶段 3 子 agent 写代码：违反硬约束，阶段 3 只读不写
- worked example 的经验没有上升为规则：容易把项目特定经验误当通用规则
- **派子 agent 干长连接/长轮询/网络长会话任务前,先评估超时风险** — 任务描述里出现 `等 X 发生` / `实时` / `watch` / `长连接` / `流` / `订阅` → 默认改主 agent 后台进程 (`terminal background=true, notify_on_complete=true`),**不**派子 agent。子 agent 没有 stop 信号, 容易 600s 跑满仍卡住

## Stage 4 反查清单

阶段 4 反查门的详细清单见：`references/stage-4-verification-checklist.md`

重点早期信号：
1. 子 agent 报“无问题” — 可能没找到 base doc
2. 子 agent 报“目标文件不存在，需要新建” — 可能没校准项目现状
3. 子 agent 报告的索引名 / 函数名与 base doc 不一致 — 可能张冠李戴
4. 多个子 agent 对同一文件给出互斥建议 — 可能是 sibling 冲突前兆

## References

### 阶段模板
- `references/phase-1-validator-template.md` — 阶段 1 校验子 agent 模板
- `references/phase-2-coder-template.md` — 阶段 2 编码子 agent 模板
- `references/phase-3-verifier-template.md` — 阶段 3 再校验子 agent 模板
- `references/phase-4-parent-recheck-template.md` — 阶段 4 父 agent 反查模板

### 检查清单
- `references/stage-4-verification-checklist.md` — 阶段 4 反查门 14 项可复用清单（commit 真实性 / 代码覆盖 / 测试覆盖 / 类型设计 / 文档一致性 / 测试子类设计）

### Worked examples
- `references/worked-example-time-scroll-m1.md` — M1-05~08 实战：HTTP 429 恢复、sibling 冲突、base doc 不写死教训
- `references/worked-example-time-scroll-m2-01.md` — M2-01 实战：目标已存在陷阱、阶段 4 反查门救命
- `references/worked-example-time-scroll-m2-01-02.md` — M2-01 + M2-02 双轮复用：同 base doc 跳过 clarify、模板复用边界

### 与其他 skill 的关系
- `parallel-task-decomposition` 的“两阶段 doc→code 模板”是本 skill 的轻量版，适用于快速同步；本 skill 适用于高风险、多文件、严格审计场景，因为它多了阶段 3 再校验与阶段 4 反查门。