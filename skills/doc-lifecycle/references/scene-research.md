# 场景 2 规范 — 外部仓库研读

**适用**：把一个不熟悉的第三方/开源仓库读透，产出可跨会话复用的研读笔记库。

**产物形态**：8-12 份主题 .md + README.md 索引，每份 5-15KB，每条 claim 带 `src/path:line` 锚点。

---

## 1. 目录结构

**研读笔记放在仓库外的平行目录**，不放在仓库内：

```
~/workspace/<repo-name>-research/
├── README.md              # 索引 + 结构图
├── 00-overview.md         # 仓库身份 / 版本 / 来源 / 依赖
├── 01-architecture.md     # 顶层布局 + 三大数据流
├── 02-build-system.md     # 构建脚本 / feature flags / 宏
├── 03-<subsystem-A>.md    # 一个子系统一份
├── 04-<subsystem-B>.md
├── ...
└── NN-warnings.md         # 风险 / 未验证声明 / 法律姿态
```

**为什么放仓库外**：
- 仓库可能有 `npm install` / `cargo build` 之类的语义，被散落的 `.md` 文件污染
- 上游仓库被误推东西会污染它
- 重新 clone 时，"研究"和"事实"分离更干净

---

## 2. 文件命名

- `00-overview.md` — 身份/版本/来源
- `01-architecture.md` — 顶层布局 + 数据流
- `02-build-system.md` — 代码如何变成二进制
- `03-NN-<topic>.md` — 一个子系统一份，按依赖顺序

**不要写中文文件名**（避免 URL 编码问题）

---

## 3. 每个文件必须包含的内容

### 3.1 主题清晰的章节结构

- H1：文件标题
- H2：主要章节
- H3：子章节
- **枚举用表格优先于项目符号**

### 3.2 源码锚点（最关键）

**每一条事实性主张必须带 `src/path:line` 锚点**：

```markdown
The `feature()` helper (from `bun:bundle`) gates compile-time code elimination — see `scripts/build.ts:13-50`.

The Bash tool lives at `src/tools/BashTool/BashTool.tsx` (来源：`src/commands.ts:194`)
```

**这是研读笔记的灵魂** — 没了锚点，文档就只是散文，未来无法验证或扩展。

### 3.3 末尾的"我还没知道的（待研究）"

每个文件结尾**必须**包含：

```markdown
## 我还不知道的（待研究）

- [ ] <具体的、可下一步操作的问题，附目标路径>
- [ ] <另一个缺口>
```

**纪律**：
- 项目用具体动词（"How does `QueryEngine` validate input before passing to tools?"）
- 不要写模糊愿望（"More research needed"）
- 这是**自扩展接口** — 下次会话读到这里就知道该挖哪里

---

## 4. README.md（索引）必须包含

1. **每个文件的 1 行 "何时读它" 说明**
2. **关键源文件链接 + 角色**（如 `src/entrypoints/cli.tsx` = CLI 入口）
3. **关键统计**：文件数 / 行数 / 命令数 / 工具数（让用户能 `ls -la` 和 `wc -l` 自查）
4. **研究时间戳 + 仓库 HEAD SHA**（让未来会话知道笔记新鲜度）

```markdown
> 研究完成时间：YYYY-MM-DD
> 仓库 HEAD SHA：<sha>
```

---

## 5. 引用格式约定

**行内引用**：
```markdown
The `feature()` helper ... see `scripts/build.ts:13-50`.
```

**段落引用**：
```markdown
来源：`src/commands.ts:194`
```

**README 引用**：标 README 行号 `README.md:42`

---

## 6. Pitfalls

### 6.1 不要相信 README 的营销话术

Fork 经常声称 "telemetry removed"，但 `package.json` 里 `@opentelemetry/*` 依赖还在（DCE 编译期移除，并未真正删除）。**总要交叉核对 `package.json`、注册表、源代码**。

### 6.2 不要通过读每个文件来枚举子系统

用 `search_files(target='files')` 扫描目录得文件清单，**只读注册表/manifest**（如 `commands.ts` + `tools.ts`）— 它们用 `memoize(() => [...])` 或 `getAllBaseTools()` 枚举了所有项。

### 6.3 不要写 50KB 的超大文档

按关注点拆 8-12 份。未来会话 `read_file` 只需读相关那份。

### 6.4 不要在研究笔记中放入宿主项目的外推结论

**这是最严重的失败模式**：研究完 `free-code` → 给 Hermes 出 P0/P1/P2 优先级列表 — **永远不要**这样。

详见 `references/anti-extrap-protocol.md`。

### 6.5 不要丢失源码路径

当写 "The Bash tool lives at src/tools/BashTool/BashTool.tsx" 时，源路径就是这份文档有用的锚点。没有它，文档只是散文。

### 6.6 不要跨文件重复同一事实

如果构建系统在 `02-build-system.md` 描述，subsystem 文件应该**引用**它，不重写。

---

## 7. 完成后必做

- 用 `scripts/check_source_anchors.py` 校验每个文件的源码锚点覆盖率（建议 ≥ 80% 的事实性主张带锚点）
- 检查文件数 = 8-12 份（不能是 1 个超大或 30 个超小）
- README 含 HEAD SHA 和时间戳