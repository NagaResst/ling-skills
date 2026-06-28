# Worked Example: 4-Phase Correction on time-scroll M1-05~08

**Session**: 723bcea0f4fc (2026-06-13, minimax-cn provider)
**Base docs**: `docs/03_技术文档/GYC_TECH_安全设计_v2.0_20260613.md` + `docs/02_设计文档/GYC_DES_数据库设计_v2.0_20260527.md` + `docs/00_规范文档/代码规范_v1.0_20260523.md` + code (entry/src/main/ets/)
**Target implementation doc**: `docs/04_计划文档/实施计划_v1.0_20260602.md`
**Skill**: `four-phase-coding-workflow` (just created)

## Phase execution trace

### Phase 1 — Document correction (parallel within, 4 sub-agents)

Sub-agents assigned (each edits ONE document, parallel):
- 实施计划 (`docs/04_计划文档/实施计划_v1.0_20260602.md`) — base doc = full doc set
- 数据库设计 (`docs/02_设计文档/GYC_DES_数据库设计_v2.0_20260527.md`)
- 技术方案 (`docs/03_技术文档/GYC_TECH_技术方案_v2.0_20260527.md`)
- API 文档 (`docs/03_技术文档/GYC_TECH_API文档_v2.0_20260527.md`)

**Observed failure**: All 4 sub-agents hit HTTP 429 (minimax-cn rate limit) mid-task. 3 of them had already applied patches but never ran `git commit`. 1 (实施计划) had not started.

**Recovery**: Parent agent noticed status showed 3 modified files + 1 untouched. Manually applied the missing 5 patches to 实施计划 (file name normalization, M1-05 acceptance criteria, M1-07 class static note, M1-04 SQL block description, M3-07 cross-reference). Then 4 separate commits, one per file.

**Commits**: `2b299e0` (实施计划) / `73de402` (数据库) / `dc382e6` (技术方案) / `3f7ad17` (API 文档)

### Phase 2 — Code correction (parallel within, 2 sub-agents)

Sub-agents assigned:
- Agent A: `BaseRepository.ets` error message 脱敏 (E3 — security design §3.3.3 violation)
- Agent B: Result/ErrorCodes refactor — extract to `entry/src/main/ets/common/Result.ets` + update import paths (H2/E1)

**Observed success**: Both completed. But careful verification caught a sibling coordination bug — Agent B's import path change to `BaseRepository.ets` got reverted by Agent A's later patch (Agent A's `read_file` snapshotted BaseRepository before B's commit, then A's `patch` wrote back A's old view of import path).

**Recovery**: Parent agent manually re-applied the import path fix (`ba730af`), and verified by `grep -n` that `../common/Result` was the only import (no `../model/StatisticsModel` residual).

**Commits**: `bed1d10` (Agent A) / `9925910` (Agent B) / `ba730af` (recovery)

### Phase 3 — Re-validation

Not explicitly run as a separate phase in this session — instead, parent agent personally grep-verified after Phase 2, and that served as the "stage 3" gate. (Future runs should consider whether to spin up an independent verification sub-agent or have parent verify.)

### Phase 4 — Summary

Not explicitly run as a separate phase in this session — instead, the parent agent's verification IS the summary. (Future runs should consider spinning up an independent audit sub-agent to write the final report.)

## Lessons embedded back into the umbrella skill

1. **base doc 必须不写死** — 本会话起草 skill 时硬编码了 `harmonyos-docs`,用户立刻纠正:"这个不应该写死,可以跟用户确认"。Skill 现在用 `{{BASE_DOC_PATHS}}` 占位符。

2. **patch 工具扩大修改范围** — 本会话出现至少 3 次 patch 吞紧邻章节标题。Skill 现在在 Pitfalls 显式列此条,并要求父 agent + 子 agent 在每个 patch 前亲自 read 全量。

3. **4-Phase template 与 Two-Phase Correction 的关系** — `parallel-task-decomposition` v1.4 已经包含 "Two-Phase Correction Template" (doc→code)。本次创建的 `four-phase-coding-workflow` 是它的**严格化扩展**(增加阶段 3 再校验 + 阶段 4 总结反查门)。两者并存而非合并 — 两阶段模板适用于快速 doc+code 同步,四阶段模板适用于高风险(实施 doc 改动复杂 + 多文件代码 + 验收要严格对齐)。

## Files committed in this session (in order)

```
e1d4f83 fix(repository): BaseRepository.count() 错误脱敏修复
9db7fae feat(pages): M1-09 改造 Index.ets 为 Navigation + Tabs 根容器
be4b41a feat(pages): M1-12 实现 6 个页面占位
af42fd6 feat(router): M1-10 创建 router_map.json + module.json5
59451c6 feat(service): M1-11 实现 NavigationService
f3edb6d docs(实施计划): M1-08 第 3 点注脚补充
18f1678 fix(ability): EntryAbility 错误日志统一 + JSDoc 补充
d8aa2a9 feat(ability): M1-08 修复 EntryAbility
ba730af fix(repository): 修复 BaseRepository import 路径(sibling 协调问题)
bed1d10 fix(repository): BaseRepository 错误信息脱敏
9925910 refactor(common): Result/ErrorCodes/success/error 抽离到 common/Result.ets
3f7ad17 docs(API文档): Result 工厂函数使用约定补充
dc382e6 docs(技术方案): BaseRepository 泛型约束文档化
73de402 docs(数据库设计): focus_mode_preference 表索引补充
2b299e0 docs(实施计划): 同步 M1-05/M1-07 与代码实际形态
0508f91 feat(utils): 实现 DateUtils/DurationUtils/ValidationUtils
3bf93a2 feat(repository): 实现 BaseRepository 通用 CRUD 基类 + ProjectRepository 子类演示
36ef6e8 fix(database): 启用 PRAGMA foreign_keys + 使用 RdbStore.close()
29d00b4 docs(实施计划): 同步 M1-02/M1-04 与代码实际数量
4409f3d docs: 安全设计 v2.0 重写 + 数据库设计 v2.1 附录扩 + 引用清理
d1eb015 feat: M1-01~04 基础设施搭建
```

## Key reuse notes

- **When to load this skill**: user says "以 X 为基础,校正 Y,然后改代码" / "先校验 doc 再改代码" / "4 阶段" / any "doc → code correction chain" with audit demands
- **Rate-limit awareness on minimax-cn**: parallel batches of 4+ sub-agents commonly hit HTTP 429. Either pre-approve budget, or split into smaller waves (2-3 at a time max).
- **Recovery from 429 mid-batch**: don't retry the same agent — finish the patches yourself in main loop, then commit sequentially. The session that 429'd has likely already burned its token budget.
- **Sibling coordination**: never let 2 sub-agents patch the same file in parallel, even if "tasks look unrelated on paper". Sibling import-path conflict in this session was the worst-case manifestation.
