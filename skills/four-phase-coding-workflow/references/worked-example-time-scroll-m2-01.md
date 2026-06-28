# Worked Example: 4-Phase Correction on time-scroll M2-01 (ProjectRepository 扩展)

**Session**: 当前 session (2026-06-16, minimax-cn provider)
**Base docs** (用户通过 clarify 选定"所有"):
- `docs/02_设计文档/GYC_DES_数据库设计_v2.0_20260527.md` (Agent A)
- `docs/03_技术文档/GYC_TECH_技术方案_v2.0_20260527.md` (Agent B)
- `docs/03_技术文档/GYC_TECH_API文档_v2.0_20260527.md` (Agent C)
- `harmonyos-docs` skill + 现有代码 `entry/src/main/ets/repository/BaseRepository.ets` (Agent D)
**Target implementation doc**: `docs/04_计划文档/实施计划_v1.0_20260602.md` M2-01 段(行 301-314)
**Skill**: `four-phase-coding-workflow`

## ⚠️ 启动前就埋雷 — 父 agent 自查清单不足

**用户在 /four-phase-coding-workflow 触发后,父 agent 做了**:

1. ✅ 用 clarify 跟用户确认 base doc 范围(用户选"所有",4 份)
2. ✅ 列出 todo 6 项
3. ✅ 启动 4 个并行子 agent,任务描述里**没**写"目标文件 ProjectRepository.ets 可能已存在,先 search_files 验证"
4. ❌ **未亲自 search_files/git log 确认目标文件存在状态**

**结果**:子 agent D 在 4 个并行子 agent 中独立 read_file 验证,发现 `ProjectRepository.ets` 已存在(138 行,M1-05 commit `3bf93a2` 作为 BaseRepository 演示子类提交),但 D 把这个发现**写进了"建议"段**,没有重写"目标对象"段。其余 3 个子 agent(A/B/C)只读实施 doc,完全不知道文件已存在,继续按"新建 138 行"思路给建议。

**阶段 1 报告合并后,4 份子 agent 输出风格不一致**:
- A/B/C 写"实施 doc 偏离 base doc" → 实施 doc 段校正建议
- D 写"实施 doc 偏离 base doc + 现状与目标混合" → 混杂建议

**这就是"目标已存在陷阱"的典型症状**。

## 阶段 1 报告真实内容(亲自分类,不是子 agent 转述)

### A. 实施 doc 段需校正(共 10 项)

| # | 严重度 | 项 | 校正内容 |
|---|---|---|---|
| A1 | 高 | 返回类型 | 行 309-312 全部改为 `Promise<Result<...>>`(对齐 M1-05 验收第 173 行) |
| A2 | 高 | softDelete 描述 | 改为"复用基类实现,无需重写" |
| A3 | 高 | restore 越权 | 拆双层:Repository 写 deleted_at=NULL;Service 跨表+30 天校验(M3) |
| A4 | 中 | 缺失 togglePause | API §2.6 要求,实施 doc 遗漏 |
| A5 | 中 | mapToEntity 描述 | 注明 `protected abstract` + 需同时实现 `getTableName` |
| A6 | 中 | 字段映射表 | 8 对映射,特别 is_paused 0/1↔boolean |
| A7 | 中 | 错误脱敏约定 | 整段补 hilog.error + error(DB_ERROR) |
| A8 | 低 | 索引策略 | 引用数据库设计 3.3 |
| A9 | 低 | 时间戳语义 | deleted_at = Date.now() Unix ms |
| A10 | 低 | 文件路径 | 注明 `entry/src/main/ets/repository/ProjectRepository.ets` |

### B. 代码现状(编码阶段前必须告知子 agent,子 agent D 已经部分发现)

1. `ProjectRepository.ets` **已存在**(138 行,M1-05 commit `3bf93a2`),仅含 3 个抽象方法
2. `BaseRepository.ets` 已提供 6 个 CRUD,**全部返回 `Promise<Result<T>>`**
3. `ProjectRepository.test.ets` **是旧残留**(222 行,测 queryAll/updateName 等不存在的方法)

### C. 关键决策(必须 clarify 拍板)

合并 A2+A3 出现"Repository/Service 分层边界"冲突,4 份报告浓缩成 4 个建议项,父 agent 写了一份"我的最佳建议"长答案,用户反馈"最佳建议是什么"——**意思是想要我给判断 + 风险**。我的回答用 4 个表格(每项 2-3 行优劣对比)给"采 / 不采",而非简单选 ABCD。

**注意**:本会话是 4 阶段工作流第一次出现"阶段 1 报告后 → 决策评审 → 阶段 2"模式,既不是"父 agent 替用户拍板"也不是"逐项 confirm"。

## 阶段 4 反查门救命(关键)

父 agent 在写阶段 2 编码子 agent 任务描述前,亲自做了:
- `ls -la entry/src/main/ets/repository/` → 确认 `ProjectRepository.ets` 4265 字节
- `git log --oneline -- 'entry/src/main/ets/repository/ProjectRepository.ets'` → commit `3bf93a2` (M1-05 演示)
- `read_file ProjectRepository.ets` → 138 行,只含 3 个抽象方法 + 4 个 asString/asNumber/asNumberOrNull/asProjectType 辅助
- `read_file BaseRepository.ets` → 285 行,6 个 CRUD 全部 `Promise<Result<T>>`,无 restore 方法,softDelete 写 `deleted_at = Date.now()`
- `read_file ProjectRepository.test.ets` → 222 行,确实是旧残留,测 queryAll/updateName 等不存在的方法

**这 5 步反查确认了 3 件事**:
1. 编码目标**不是"新建 138 行"**而是"为已存在的 138 行骨架 + 4 个新方法"
2. softDelete 复用基类(B 选项),restore 拆双层(A 选项),togglePause 限于字段更新(C 选项)
3. 测试必须**全量重写**(D 选项),不是修补

**如果跳过阶段 4 反查,直接让子 agent 按"新建 ProjectRepository.ets"执行**,会:
- 与 M1-05 commit `3bf93a2` 的 138 行代码产生冲突
- 丢掉 `asString/asNumber/asNumberOrNull/asProjectType` 4 个辅助方法
- 实现一个不存在的 `restore` 双层语义

## 阶段 2 / 3 / 4 执行情况

**阶段 2** (尚未执行):规划 3 个串行子 agent(① 实施 doc 校正 ② ProjectRepository 扩展方法 + 重写测试 ③ 兼容性回归)。

**阶段 3** (尚未执行):独立子 agent 对照 base doc 校验 diff。

**阶段 4** (部分执行):本文件就是"真实施记录"——不是阶段 3 报告的复述,而是父 agent 亲自分类 + 反查 + 决策评审的输出。

## 关键教训(已 patch 进 SKILL.md Pitfalls)

1. **阶段 1 启动前父 agent 自查清单必须包含 "目标文件/类是否已存在"**——这是本会话新发现的元方法论缺陷
2. **阶段 1 任务描述模板需补一条**:每个子 agent 必须先 `search_files` + `git log -- <target>` 验证目标存在状态,再决定输出方向("新建"还是"补全")
3. **阶段 1 → 决策评审 → 阶段 2 模式**:当 4 份子 agent 报告出现 N 个互斥方案,父 agent 浓缩成 N 个"建议项"喂给 clarify,而非"父 agent 替用户拍板"或"逐项 confirm"
4. **决策评审回答格式**:每项用 2-3 行表格给"采 / 不采 + 风险",**不是**简单列 ABCD 选项——用户用"最佳建议是什么"反馈明确表达了这个偏好

## 重用备忘

- **何时加载本 worked-example**:用户提到"以 X 为基础,校正 Y,然后改代码" + base doc 涉及 3+ 个 + 目标代码/类可能在早期阶段已存在
- **rate-limit 备注**:本会话没出现 HTTP 429(只 4 个并行子 agent,均在 minimax-cn 预算内),但 M1-05 worked-example 里的"2-3 并行"经验仍适用
- **本次决策未拍板前不要进阶段 2** —— ABC+D 是 4 个**互锁决策**,不能 A+C 然后回头改 B
