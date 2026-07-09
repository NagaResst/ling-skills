---
name: doc-lifecycle
version: "1.0.0"
author: Hermes Agent
license: MIT
description: |
  文档全生命周期管理 — 4 场景入口 → 验证 → 评分 → 进化。
  适用：新建项目文档体系、外部仓库研读转研读笔记、文档版本升级重写、批量独立评分。
  触发：建文档、写文档、研究仓库、研读仓库、文档对齐、交叉一致性检查、打分、评分、
  v1.x→v2.x、重写升级、校对齐、改文档、文档落伍、文档没跟上、文档 lint。
  不适用：单文件修一个 typo（直接 patch）、PR 级代码审查（用 requesting-code-review）。
metadata:
  hermes:
    tags: [documentation, lifecycle, validation, scoring, version-rewrite, research-notes]
    related_skills: [wiki, plan, requesting-code-review, simplify-code]
---

# Document Lifecycle — 文档全生命周期管理

## Overview

把 4 个相互关联但入口不同的文档工作流（新建 / 研读 / 升级 / 评分）合并为一个端到端生命周期。
流程骨架写在 SKILL.md，具体规范和方法下沉到 `references/` 和 `scripts/`，可脚本化的固定规则一律脚本化。

核心设计原则：
- **4 场景规范物理分区**：每个场景有自己的命名/格式/结构规范，绝不混用
- **4 阶段路由驱动**：根据入口判断 Phase 2 跑哪些步骤、跳过哪些
- **人机协同决策链**：Phase 3 与 Phase 4 之间必有用户拍板停顿，目标是对齐用户想法
- **固定规则脚本化**：可机械检查的内容一律进 `scripts/`，不进 SKILL.md/references/

## When to Use

**适用（按 4 个场景入口）**：

| 场景 | 触发词 | 起点 |
|------|--------|------|
| 1. 新建项目文档体系 | 建文档、写文档、写 PRD、写 SPEC、写技术方案 | Phase 1（场景 1 方法） |
| 2. 外部仓库研读 | 研究仓库、研读仓库、把 README 读完、给一份研究文档、document this repo | Phase 1（场景 2 方法） |
| 3. 现有文档升级 | 重写 v2.0、升级到 v2.x、校对齐、文档没跟上、把 v1.0 改成 v2.0 | Phase 1（场景 3 方法） |
| 4. 批量独立评分 | 给文档打分、文档独立评分、per-doc scorecard | **跳过 Phase 1**，直接 Phase 3 |

**不适用**：
- 单文件改一个 typo / 一句话 → 直接 `patch`
- PR 级代码审查 → `requesting-code-review`
- 单条 skill 编排计划 → `plan`

---

## 路由决策树

```
                    用户说什么?
                        │
       ┌────────────────┼────────────────┬─────────────────┐
       ▼                ▼                ▼                 ▼
   "建文档/写PRD"   "研究仓库"     "重写v2.0/升级"    "给文档打分"
       │                │                │                 │
   场景 1             场景 2          场景 3            场景 4
   scene-create      scene-research  scene-rewrite     scene-audit
       │                │                │                 │
       ▼                ▼                ▼                 │
    Phase 1          Phase 1          Phase 1             │
    (方法 A)         (方法 B)         (方法 C)            │
       │                │                │                 │
       └────────────────┴────────────────┘                 │
                        │                                  │
                        ▼                                  │
                   Phase 2 路由                           │
              (按入口判断跑哪些步骤)                       │
                        │                                  │
                        ▼                                  ▼
                   Phase 3 评分  ←─────────────────────┘
                        │
                        ▼
                【停顿 · 用户拍板】
                        │
                        ▼
                   Phase 4 进化（用户授权后）
```

---

## 适用场景规范（4 套独立规范，物理分区）

每个场景有自己的产出规范。**绝不能混用**（场景 1 的 8 字段头部不能套到场景 2 的研读笔记上，反之亦然）。

| 场景 | 规范文件 | 产物形态 |
|------|---------|---------|
| 1. 新建项目文档 | `references/scene-create.md` | 8 字段头部 + 5 层章节结构 + 命名规范 |
| 2. 外部仓库研读 | `references/scene-research.md` | 00-09 编号主题笔记 + 每条 claim 带 `src/path:line` 锚点 + 待研究标注 |
| 3. 现有文档升级 | `references/scene-rewrite.md` | 仅目标版本状态、禁旧留新、修订记录极简 |
| 4. 批量独立评分 | `references/scene-audit.md` | 5 维评分卡 + 内证纪律 |

---

## Phase 1 · 产出

Phase 1 不是"通用产出方法"，而是**按场景加载对应的方法文件**：

| 场景 | 方法文件 |
|------|---------|
| 1 | `references/method-create.md` |
| 2 | `references/method-research.md` |
| 3 | `references/method-rewrite.md` |
| 4 | **跳过 Phase 1** |

**完成后产出物**：
- 场景 1：`docs/<分类>/<项目缩写>_<文档类型>_<模块>_vX.Y_<YYYYMMDD>.md`
- 场景 2：`<repo>-research/` 目录下 8-12 份主题 .md + README.md 索引
- 场景 3：`<旧文件名>` 重写为 `<新文件名>`，原文件名归档到 `.archive/`
- 场景 4：跳过

**自动化检查**：场景 1 用 `scripts/check_doc_header.py` 校验 8 字段头部；场景 2 用 `scripts/check_source_anchors.py` 校验源码锚点覆盖率。

---

## Phase 2 · 验证

### 前置判断（路由表 — 必读）

**根据 Phase 1 的入口场景，决定跑哪些步骤**：

| 入口来源 | Stage 2a 重构覆盖率 | Stage 2b 交叉一致性 |
|---------|-------------------|-------------------|
| 场景 1（新建） | ❌ 跳过（无"旧版本"概念） | ✅ 跑（与既有基线对齐） |
| 场景 2（研读） | ❌ 跳过（研读笔记自包含） | ❌ 跳过（不在主流程） |
| 场景 3（升级） | ✅ 跑（基线判定决定哪些文件要重写） | ✅ 跑（升级后与未升级文档做差异检查） |
| 场景 4（评分） | ❌ 跳过 | ❌ 跳过 |

> **重要**：跳过不等于省略，而是该步骤对该场景无意义。
> 例如场景 1 跑 2b 是为了"新建文档是否符合项目既有规范"，
> 而场景 2 跑 2b 则是错位（研读笔记是关于外部仓库，不属于本项目文档体系）。

### Stage 2a · 重构覆盖率（如果路由表说要跑）

核心方法（3 步）：
1. **确立基线**：从用户原话或修订记录中提取基线日期 D + 审核人 J + 承诺变更清单
2. **分类**：post-baseline / pre-baseline（caught vocab）/ pre-baseline（vocab-clean）/ pre-baseline（mixed）
3. **优先级排序**：用户行为影响文档 → 高，参考类 → 低

详细规则 → `references/refactor-coverage-rules.md`

### Stage 2b · 交叉一致性（如果路由表说要跑）

核心方法（3 步）：
1. **规则化扫描**：用 regex 检查残留模式（每条规则都有"正面/负面"方向）
2. **分类**：false positive vs real issue，real issue 用 `patch` 修复
3. **字段级对照**：从基线文档（如数据库设计）出发，对比实施文档字段定义

自动化脚本 → `scripts/check_residual_patterns.py`
详细规则 → `references/cross-validation-rules.md`

### Phase 2 完成标准
- 输出"问题清单"（含 false positive 和 real issue 分类）
- real issue 已修复（patch 工具逐条修复 + 重新扫描确认 0 残留）
- 用户已确认 false positive 不需修复

---

## Phase 3 · 评分（独立纪律）

**与 Phase 2 的纪律边界**（重要 — 反义关系）：

| 维度 | Phase 2（验证） | Phase 3（评分） |
|------|---------------|---------------|
| 目的 | 发现文档间的**不一致** | 评估单文档的**质量** |
| 跨文档引用 | ✅ 必须（A→B 的差异） | ❌ **严禁**（"比 X 差"作评分理由） |
| 证据来源 | 文档间行号对比 | 单文档内行号 |
| 输出 | 一致性报告 + 修复 patch | 5 维评分卡 + 决策选项 |

### 5 维评分框架

| 维度 | 评估问题 |
|------|---------|
| A. 结构合规性 | 必备字段/章节是否齐全？章节编号是否连贯？ |
| B. 术语一致性 | 关键术语（状态枚举、表名、API 名）在**本文档内**是否前后一致？ |
| C. 完整性 | 是否有空章节、TBD、"待补充"？主题覆盖是否充足？ |
| D. 版本号与修订记录 | 文件名版本号 vs 头部版本号？修订记录是否完整对应实际改动？ |
| E. 代码/可落地性 | 含代码的文档，API 是否现代（非废弃）？代码与文档描述是否一致？ |

每维度 1-5 分。详细评分细则 → `references/scorecard-rubric.md`

### 输出格式

每份文档独立评分卡（自包含）：
```markdown
## <文档名> — <版本号>

| 维度 | 分数 | 内证依据（行号/章节） |
|------|------|--------------------|
| A. 结构 | 4/5 | 8 字段头部完整 (L1-9)；§3.4 跳到 §3.4.2 无 §3.4.1 (L358) |
| B. 术语 | 5/5 | "auto_closed" 全篇一致 (L23, L45, L67) |
| C. 完整 | 3/5 | §5.2 待补充 (L412)，§6 实际为空 (L420-422) |
| D. 版本 | 4/5 | 文件名 v2.0 与头部 v2.0 一致；修订记录缺 v2.0 条目 |
| E. 落地 | 5/5 | ArkTS 代码语法正确 (L89-120) |
| **总分** | **8.2/10** | |
```

**末尾 + 总览表**（这是评分结果的呈现，不是评分依据的交叉引用）。

### Phase 3 完成标准
- 每份文档都有独立评分卡
- 总览表（按总分排序）
- **决策选项**（推荐 1/2/3，下一步建议）→ 等用户拍板

---

## 【停顿 · 用户拍板】

**Phase 3 与 Phase 4 之间必有这个停顿**。

Phase 3 输出三类决策选项：
- **推荐 A：无需修改**（总分 ≥ 8.5，文档已对齐用户想法）
- **推荐 B：小修小补**（6 ≤ 总分 < 8.5，针对低分维度的内文修补，Phase 2 的 patch 流程直接修复）
- **推荐 C：触发 Phase 4 重写**（总分 < 6，或用户明确说"重写"）

**用户拍板后**，才能进入 Phase 4。Phase 3 → Phase 4 不可自动连跑。

**关键纪律**：Phase 4 的目标是"文档与用户想法达成一致"，不是"系统判定的最优"。任何 Phase 4 触发都必须由用户口头/动作明确批准（沿用通用 hermes 变更纪律）。

---

## Phase 4 · 进化（用户授权后）

### 适用场景
- 触发词："重写 v2.0"、"升级到 v2.x"、"校对齐"、"把 v1.0 改成 v2.0"
- 用户在【停顿 · 用户拍板】明确选择推荐 C
- 用户口头/动作明确批准

### 核心方法（3 步）

1. **读取基线**：先读所有上游 v2.x 文档，提取目标版本的术语/表名/API 名（不能凭印象推断）
2. **写新版**：以目标版本为"唯一现实"写新文档，假设旧版本不存在
3. **残留扫描**：用 `scripts/check_doc_v2_residue.py` 扫描 11 类残留模式，逐条 patch 修复

详细残留模式 → `references/version-rewrite-patterns.md`

### Phase 4 完成标准
- 残留扫描脚本退出码 = 0
- 文件名版本号同步更新（不只是头部）
- 修订记录极简（一行："全文重写对齐 [ref docs]"），不写变更清单
- **用户已确认"这一版就是我想要的"**（再次停顿）

### 可选停顿点

Phase 4 过程中可以根据用户反馈多次停顿：
- "读到 §3 突然想改方向" → 暂停重读基线
- "这一段我不太满意" → 局部重写
- "整体差不多了，但 §6 要换写法" → 仅 §6 重写
- "OK 了" → 提交归档

---

## 通用纪律（4 条）

1. **场景与规范物理分区**：场景 1/2/3/4 的规范在独立 .md 文件中，禁止在一个文档里同时套用两套规范
2. **Phase 2/3 纪律边界**：验证用 cross-reference，评分用内证，两者不可混淆
3. **Phase 3→Phase 4 人机协同**：不可自动连跑，必须等用户拍板；Phase 4 内部也可多次停顿对齐用户想法
4. **固定规则脚本化**：可机械检查的内容（残留正则、头部字段、源码锚点）一律进 `scripts/`，SKILL.md/references/ 只讲方法论

---

## Common Pitfalls

1. **场景 1 的 8 字段头部套到场景 2 的研读笔记** — 错误！研读笔记不写项目缩写/审核人/版本号头部，每个 claim 带 `src/path:line` 即可
2. **Phase 2 跳步** — 路由表说"跳过"≠"省略"，跳过是因为该步骤无意义；如果场景对不上路由表，说明用户在用错入口
3. **Phase 3 用跨文档引用作评分理由** — 严禁！评分的证据必须来自**本文档内**的行号/章节
4. **Phase 3→Phase 4 自动连跑** — 严禁！必须等用户拍板
5. **Phase 4 写"X→Y 全量替换"实施计划** — 错误！新版只描述目标状态，不写迁移路径
6. **重写后不扫描残留** — 残留模式（v1.0 仅.../v1.0 不再.../校对变更/校对关键变更）容易混入，必须跑脚本
7. **不读基线凭印象推断** — Phase 4 必须先读所有上游 v2.x 文档，不能凭"我猜是这样"
8. **从研读仓库到宿主项目的外推** — 详见 `references/anti-extrap-protocol.md`，研读 free-code → 给 Hermes 出 P0/P1/P2 优先级是经典错误
9. **评分只给总分不给分维度证据** — 每维度必须给行号/章节作内证
10. **修订记录里写 ⑨ 条变更清单** — 一行极简："全文重写对齐 [ref docs]" 即可

---

## Verification Checklist

每次产出文档/完成阶段后自检：

- [ ] SKILL.md 主文件 < 15KB（避免 token 负担）
- [ ] 场景路由判断正确（场景 1/2/3/4 不混用规范）
- [ ] Phase 2 路由表已读并按表执行（未跳步骤）
- [ ] Phase 3 评分卡每维度都有内证行号
- [ ] Phase 3→Phase 4 中间有用户拍板（不是自动连跑）
- [ ] Phase 4 残留扫描脚本退出码 = 0
- [ ] 文件名版本号与头部版本号一致
- [ ] 修订记录极简（一行）
- [ ] 项目特定的硬编码不在主文件（光阴策的"三种模式独立"等 → 案例文档，不是通用规范）

---

## File Layout

```
~/.hermes/skills/productivity/doc-lifecycle/
├── SKILL.md                              # 本文件（流程骨架）
├── references/
│   ├── scene-create.md                   # 场景 1 规范（命名/8字段/5层）
│   ├── scene-research.md                 # 场景 2 规范（00-09 + 锚点）
│   ├── scene-rewrite.md                  # 场景 3 规范（禁旧留新）
│   ├── scene-audit.md                    # 场景 4 规范（5维评分卡）
│   ├── method-create.md                  # Phase 1 场景 1 流程
│   ├── method-research.md                # Phase 1 场景 2 流程
│   ├── method-rewrite.md                 # Phase 1 场景 3 流程
│   ├── refactor-coverage-rules.md        # Phase 2a 完整规则
│   ├── cross-validation-rules.md         # Phase 2b 完整规则
│   ├── scorecard-rubric.md               # Phase 3 5 维评分细则
│   ├── version-rewrite-patterns.md       # Phase 4 11 类残留模式
│   ├── anti-extrap-protocol.md           # 通用教训（防外推）
│   ├── cross-doc-alignment-and-db-validation.md  # 跨文档概念对齐与DB设计交叉验证
└── scripts/
    ├── check_doc_header.py               # 校验 8 字段头部
    ├── check_doc_naming.py               # 校验命名规范
    ├── check_source_anchors.py           # 校验源码锚点覆盖率
    ├── check_residual_patterns.py        # Phase 2b 残留正则扫描
    └── check_doc_v2_residue.py           # Phase 4 残留扫描（参数化旧术语）
```