# Worked Example: 4-Phase Correction on time-scroll M2-01 + M2-02 (双轮复用)

**Session**: ee86eddfd3f4 (M2-01) + 当前会话 (M2-02) (2026-06-16, minimax-cn provider)
**Base docs** (4 个, 跨两轮):
- `docs/02_设计文档/GYC_DES_数据库设计_v2.0_20260527.md` (§3.2.1 project / §3.2.2 tag / §3.3 索引)
- `docs/03_技术文档/GYC_TECH_技术方案_v2.0_20260527.md` (§4 Repository / §4.1 错误处理 / §4.2 ProjectService)
- `docs/03_技术文档/GYC_TECH_API文档_v2.0_20260527.md` (§2.x / §3.x)
- `harmonyos-docs` skill (ArkTS 限制 + @ohos.data.relationalStore API)

**Target implementation doc**: `docs/04_计划文档/实施计划_v1.0_20260602.md`

## 关键发现: 任务"实现 X"可能 X 已部分存在

### M2-01 现场

- 用户说:"以设计文档和 harmonyos-docs 为基础文档,进行 M2-01 的代码编写"
- 阶段 1 子 agent D 报告:ProjectRepository.ets **已存在 138 行** (commit `3bf93a2` M1-05 阶段的"演示子类")
- 父 agent 亲自验证:`ls -la` + `git log --all --` 确认
- **影响**:M2-01 目标从"新增"变"扩展方法 + 校正 doc"

### 教训 (写入 skill Pitfalls)

阶段 1 启动前(向子 agent 发任务前),**必须亲自校准项目现状**:
```bash
ls -la <目标文件目录>           # 文件大小
wc -c <目标文件>                 # 字节数(0 = 待新建)
git log --oneline --all -- <目标文件>  # 历史 commit
```

如果"现状"与"任务描述"有偏差,在发给子 agent 的任务里**显式标注**"现状 = X,本任务 = Y",子 agent 才知道边界。

## Phase execution trace (M2-01)

### Phase 1 — Document correction (4 parallel sub-agents, 1 base doc each)

| Sub-agent | Base doc | 关键发现 |
|---|---|---|
| A (数据库设计) | GYC_DES_数据库设计 v2.0 | 8 字段完整 / 索引策略 / 软删除语义 / CHECK 约束(8 条问题) |
| B (技术方案) | GYC_TECH_技术方案 v2.0 | 6 方法返回类型 / softDelete 复用 / restore 拆双层(5 条问题) |
| C (API 文档) | GYC_TECH_API 文档 v2.0 | 缺 `togglePause` / `queryByType` 签名 / `softDelete` 缺跨表(8 条问题) |
| D (harmonyos-docs + 现有代码) | skill + BaseRepository.ets | ProjectRepository **已存在 138 行** / mapToEntity 是 protected abstract(6 条问题) |

**关键澄清**:子 agent D 的"现状报告"改变了 M2-01 任务边界。父 agent 亲自 read_file 验证 + 整理改动清单 A1-A10。

### Phase 2 — Code correction (3 串行 sub-agents)

按 ABC+ D1+D2 配置,3 个子 agent 串行(同一项目不能并行写,sibling 冲突):

- **E (实施 doc 校正)**: commit `865cd67`,M2-01 段 14 行 → 63 行
  - **关键校正**:索引名 `idx_project_active` → `idx_project_deleted`(如实引用数据库设计实际命名)
  - **Stage 4 反查 1**:子 agent A 阶段 1 报告的索引名是错的,这里被纠正
- **F (ProjectRepository 扩展方法)**: commit `a10f866`,138 → 249 行,+4 方法
  - **主动简化**:子 agent F 把 `queryByType` 的字面量联合改成 `ProjectType` 别名。父 agent 验证别名定义(`project_type_constants.ets:5`)与字面量联合类型等价,接受。
- **G (测试重写)**: commit `9d4560d`,222 行旧 v0 草稿 → 410 行新测试,5 describe / 39 it
  - **巧妙设计**:`TestableProjectRepository`(包装 protected public) + `StubExplodingProjectRepository`(覆写 getStore 抛错),让 protected 抽象方法可测 + 模拟 DB 异常测脱敏路径
  - **路径修正**:旧测试 `../../main/ets/models/ProjectModel` (错) → `../../main/ets/model/ProjectModel` (对)

### Phase 3 — Re-validation (1 sub-agent)

子 agent H 报告"未发现偏离"。

### Phase 4 — Summary (反查门)

父 agent 亲自做 14 项反查(见 `stage-4-verification-checklist.md`),7+7 = 14/14 全部通过 ✅。放行。

## Phase execution trace (M2-02 — 复用模式)

M2-02 完整复用 M2-01 模式,只换 base doc 章节 + 实施 doc 段。

### Phase 1 (跳过 clarify)

- **关键决策**:base doc 列表不变(4 个,与 M2-01 完全一致)→ **跳过 clarify 节省一轮**
- 4 个子 agent 同样并行校验 M2-02 段
- 阶段 1 子 agent 报告 10+ 项问题,与 M2-01 问题模式**高度相似**(返回类型 / 抽象方法 / 字段映射 / 索引策略 / 错误约定)

### 阶段 1 现状快照(校准教训应用)

```bash
# M2-02 启动前
ls -la entry/src/main/ets/repository/TagRepository.ets
# → 0 字节(全新实现,与 M2-01 不同)
# → 决定:这次是"新建 + 校正 doc",不是"扩展"
```

### Phase 2 (3 串行 sub-agents,待执行)

- 实施 doc 校正(M2-02 段 16 行 → 60+ 行,模板对齐 M2-01 校正后版本)
- TagRepository.ets 实现(0 → ~350 行,7 方法)
- TagRepository.test.ets 重写(旧 v0 草稿 → ~400 行新测试)

### Phase 3 + Phase 4 (复用 14 项反查清单)

## 双轮对比学习

| 维度 | M2-01 | M2-02 |
|---|---|---|
| 任务类型 | 扩展已有方法 + 校正 doc | 新建 + 校正 doc |
| 阶段 1 校准 | 子 agent D 报"已存在 138 行" | 父 agent 主动 `ls -la` 看到 0 字节 |
| 阶段 1 子 agent 数 | 4(并行) | 4(并行,跳过 clarify) |
| 阶段 2 子 agent 数 | 3(串行) | 3(串行) |
| 子 agent 主动简化 | `queryByType` 字面量联合 → 别名 | (待观察) |
| 阶段 4 反查 | 7 项 + 额外 7 项 = 14 | 14 项复用 |
| commit 数 | 3 | 3(预期) |

## Reuse decision tree

```
M2-N 任务到来
  ↓
Q1: base doc 列表是否与上一轮一致?
  → 是: 跳过 clarify,直接进阶段 1
  → 否: clarify 确认 base doc
  ↓
Q2: 目标文件已部分实现吗?
  → 是: 子 agent 任务里显式标注"现状 = X,本任务 = Y"
  → 否: 全新实现
  ↓
Q3: 实施 doc 段结构模板与上一轮一致吗?
  → 是: 子 agent 任务里直接引用上一轮 commit hash 作为模板
  → 否: 先用 plain-text 描述期望结构
  ↓
Q4: 测试模式(子 agent G 的 Testable/Stub 模式)适用吗?
  → 是: 子 agent 任务里直接说"沿用 ProjectRepository.test.ets 模式"
  → 否: 给新模板
  ↓
阶段 2: 串行 3 sub-agents
  ↓
阶段 3 + 阶段 4: 反查清单复用
```

## Commits (M2-01 实际产出)

```
9d4560d test(repository): M2-01 ProjectRepository 测试重写       (410 行测试)
a10f866 feat(repository): M2-01 ProjectRepository 扩展方法       (代码 +114 -3)
865cd67 docs(实施计划): M2-01 校正,A1-A10 全部落实                (文档 +55 -7)
```

工作区领先 origin/main 3 个 commit(待 push)。

## 待观察项 (M2-02 完成后补全)

- 子 agent 是否又会"主动简化"(子 agent F 的别名替换习惯)
- 事务 API(createTransaction + commit/rollBack)实现是否正确
- TagRepository.test.ets 复用 Testable/Stub 模式是否成功
