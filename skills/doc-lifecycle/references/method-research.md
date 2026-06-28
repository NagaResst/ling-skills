# Phase 1 方法 B — 场景 2 完整流程

**适用**：把不熟悉的第三方仓库读透，产出可跨会话复用的研读笔记库。

---

## 流程（7 步）

### Step 1 — 验证前提（最重要）

**读 2000 个文件之前，先确认仓库到底是什么**。

常见陷阱：
- 名字暗示一回事（如 `free-code` 看起来像 freeCodeCamp 教程，实际是 Claude Code CLI 的 fork）
- README 营销话术需要交叉核对

**必读**（并行）：
1. `README.md`（或 `readme.md`）
2. `CLAUDE.md` / `AGENTS.md`（如有）
3. `FEATURES.md` / `CHANGELOG.md`（如有）
4. `package.json` / `Cargo.toml` / `pyproject.toml`（按语言选）

**记录**：
- 真实身份（upstream vs fork vs clone）
- 版本
- 自述的修改

**如果用户预期和实际不符** — 在第一次回复中**主动指出**，不要在错误前提下深挖几小时。

### Step 2 — 并行批量读顶层文档

**一轮调用多个 `read_file`** 并行读：
- `README.md`（全文）
- `FEATURES.md` / `CHANGELOG.md`（如有）
- `package.json`（全文）
- 顶层架构文档（`CLAUDE.md` / `ARCHITECTURE.md`，如有）
- **两个注册表文件**（commands.ts + tools.ts 之类的） — 它们是事实之源

把这些保存为"骨架事实"，后续工作就是填缺口。

### Step 3 — 并行扫描子系统目录

**一轮调用多个 `search_files(target='files')`** 并行扫描：

```python
# 示例：对 TypeScript 项目
search_files(target='files', path='src/commands')
search_files(target='files', path='src/tools')
search_files(target='files', path='src/skills')
search_files(target='files', path='src/plugins')
search_files(target='files', path='src/services')
search_files(target='files', path='src/bridge')
```

**技巧**：返回 `truncated` 时用 `offset=200` 等分页。**不要试图一次读整个清单**。

### Step 4 — 读注册表（关键步骤）

**两个注册表文件是黄金**：通常包含 `COMMANDS = memoize(() => [addDir, advisor, ...])` 或 `getAllBaseTools()` 之类的枚举。

**全文读这些注册表**（一轮并行），命名导出 + `feature('FLAG') ? require(...) : null` 三元运算给出每个命令/工具 + 它由哪个 feature flag 控制。

**不要通过目录清单枚举** — **让注册表替你枚举**。

### Step 5 — 综合成 8-12 份主题 Markdown

输出到 `~/workspace/<repo-name>-research/`（与仓库平行），**不放在仓库内**。

每份 5-15KB（一份独立可读，8-12 份覆盖所有子系统）。

**每个 claim 必带 `src/path:line` 锚点**：

```markdown
The `feature()` helper (from `bun:bundle`) gates compile-time code elimination — see `scripts/build.ts:13-50`.
```

**不能验证的 claim → 放到末尾的"待研究"**，不要编造。

### Step 6 — 末尾"我还没知道的（待研究）"纪律

每个文件结尾必须包含：

```markdown
## 我还不知道的（待研究）

- [ ] How does `QueryEngine` actually validate input before passing to tools?
- [ ] Whether the build script's `MACRO.NATIVE_PACKAGE_URL = 'undefined'` (string) is intentional
```

**纪律**：
- 具体动词，不要模糊愿望
- 这是**自扩展接口** — 下次会话读到这里就知道该挖哪里

### Step 7 — README 索引

README.md 必须包含：

1. **每个文件的 1 行 "何时读它" 说明**
2. **关键源文件链接 + 角色**
3. **关键统计**：文件数 / 行数 / 命令数 / 工具数（用户能 `ls -la` 和 `wc -l` 自查）
4. **研究时间戳 + 仓库 HEAD SHA**

```markdown
> 研究完成时间：2026-06-28
> 仓库 HEAD SHA：abc1234
```

---

## 完成标准

- [ ] 文件数 8-12 份（不是 1 个超大或 30 个超小）
- [ ] 每份 5-15KB
- [ ] 研读笔记放在仓库**外**的平行目录
- [ ] 每个 claim 带 `src/path:line` 锚点（建议 ≥ 80% 覆盖率）
- [ ] 每个文件末尾有"我还没知道的（待研究）"
- [ ] README 索引含 HEAD SHA 和时间戳
- [ ] **如果用户后续要求"移植 X 到我的项目"** — 严格遵循 `references/anti-extrap-protocol.md`，**不要立即给 P0/P1/P2 优先级**

---

## 完成后 → 进入 Phase 2

按 SKILL.md 的路由表决定跑哪些步骤：
- 场景 2 → 跳过 Stage 2a（无"旧版本"概念）
- 场景 2 → 跳过 Stage 2b（研读笔记不在主流程）