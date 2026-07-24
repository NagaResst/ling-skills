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
- manifest 文件（全文）— 按语言选：`package.json` / `pyproject.toml` / `Cargo.toml` / `pom.xml` / `go.mod`
- 顶层架构文档（`CLAUDE.md` / `ARCHITECTURE.md` / `docs/architecture.md`，如有）
- **注册表文件** — 按项目类型找（见下表），它们是事实之源

**注册表定位原则**：注册表 = 集中声明"这个项目有哪些可枚举单元"的文件。不同框架的注册表形态不同——关键是**找到那个用声明替代散落定义的地方**，而不是死记文件名。

常见定位参考（按实际仓库结构调整）：

| 项目类型 | 常见注册表位置 | 识别特征 |
|---------|---------------|---------|
| CLI / 开发工具 | `commands.ts` + `tools.ts` | `memoize(() => [...])` 枚举所有命令/工具 |
| 后端 API（FastAPI） | `main.py` / `app.py` | `app.include_router()` 调用集中处 |
| 后端 API（Express） | `app.js` / `server.ts` | `app.use('/path', router)` 调用集中处 |
| 后端 API（Django） | `urls.py`（根 + 各 app） | `urlpatterns` 列表 |
| 后端 API（Spring Boot） | 无中央注册表 | grep `@RestController` / `@RequestMapping` 注解替代 |
| 后端 API（Go: gin/echo） | `router.go` / `main.go` | `r.Group()` + `.GET()/.POST()` 调用链 |
| 前端 SPA（React/Vue） | router 配置 + store 配置 | 路由表 + 状态 slice 声明 |
| 前端 SPA（Next.js） | `app/` 或 `pages/` 目录 | 约定式路由，目录即路由表 |
| Monorepo | 先识别前后端边界，分别定位 | 前后端各走一遍 |

如果找不到注册表，回退到 grep 关键符号（注解、函数名、配置键）来枚举。**找到什么就用什么，不要因为和上表不匹配就跳过**。

把这些保存为"骨架事实"，后续工作就是填缺口。

### Step 3 — 并行扫描子系统目录

**一轮调用多个 `search_files(target='files')`** 并行扫描。

**扫描目标选择规则**：按项目类型选"最可能存在子系统的目录"扫描。以下是常见参考，不是硬性清单——**以实际目录结构为准，发现什么扫什么**：

```python
# CLI / 开发工具项目 — 扫命令/工具/插件/服务
search_files(target='files', path='src/commands')
search_files(target='files', path='src/tools')
search_files(target='files', path='src/plugins')

# 后端 API 项目 — 扫路由/模型/服务/中间件/数据层
search_files(target='files', path='src/routes')        # 或 routers/ / controllers/
search_files(target='files', path='src/models')         # 或 entities/ / domain/
search_files(target='files', path='src/middleware')      # 或 interceptors/ / filters/
search_files(target='files', path='src/db')             # 或 migrations/ / prisma/
search_files(target='files', path='tests')

# 前端 SPA 项目 — 扫组件/页面/状态/HTTP 客户端/hooks
search_files(target='files', path='src/components')
search_files(target='files', path='src/pages')           # 或 views/ / screens/
search_files(target='files', path='src/store')           # 或 state/ / redux/
search_files(target='files', path='src/api')             # 或 services/ / lib/api/
search_files(target='files', path='src/hooks')
```

如果某目录不存在或为空，直接跳过。如果发现实际目录名和上面不同，以实际为准。

**技巧**：返回 `truncated` 时用 `offset=200` 等分页。**不要试图一次读整个清单**。

### Step 4 — 读注册表（关键步骤）

**注册表文件是黄金**：用枚举替代逐个读文件。

**按项目类型读注册表**：

**CLI / 开发工具**：通常包含 `COMMANDS = memoize(() => [addDir, advisor, ...])` 或 `getAllBaseTools()` 之类的枚举。命名导出 + `feature('FLAG') ? require(...) : null` 三元运算给出每个命令/工具 + 它由哪个 feature flag 控制。

**后端 API**：
- FastAPI：读 `main.py` 中所有 `app.include_router()` 调用，拿到路由前缀 → router 模块映射。每个 router 文件就是一组 API 端点的注册表
- Express：读 `app.js` 中所有 `app.use('/path', router)` 调用，同上
- Django：读根 `urls.py` 的 `urlpatterns`，展开各 `include('app.urls')` 拿到 app 级路由表
- Spring Boot：**无中央注册表**。用 `search_files(pattern='@RestController|@RequestMapping|@GetMapping|@PostMapping', target='content')` grep 注解发现所有路由。用 `search_files(pattern='@Configuration|@Bean', target='content')` 发现组件装配
- Go (gin/echo)：读 `router.go` / `main.go` 中 `r.Group()` + `.GET()/.POST()` 调用链

**前端 SPA**：
- React/Vue：读 router 配置文件，拿到路由 → 组件映射表。读 store 配置文件，拿到 state slice → reducer/action 映射
- Next.js：扫描 `app/` 或 `pages/` 目录结构即路由表（约定式路由，不需要读文件内容枚举路由）

**通用原则**：**不要通过目录清单枚举** — **让注册表替你枚举**。如果项目类型无中央注册表（如 Spring Boot），用 grep 注解替代。

### Step 5 — 综合成 8-12 份主题 Markdown

输出到 `~/workspace/<repo-name>-research/`（与仓库平行），**不放在仓库内**。

每份 5-15KB（一份独立可读，8-12 份覆盖所有子系统）。

**子系统划分规则**：00-02 通用（overview/architecture/build），03+ 按项目类型的关注点拆分。**拆分原则是"一个子系统 = 一个可独立阅读的关注点"，不是"一个目录 = 一份文件"**——如果两个目录强耦合，合并成一份；如果一个目录太大，拆成两份。

常见划分参考（按实际仓库结构调整，不强制对齐）：

**CLI / 开发工具**：commands / tools / plugins / services / warnings

**后端 API**：api-routes（路由+端点清单）/ database-layer（schema+migrations+ORM）/ middleware（请求 pipeline）/ service-layer（业务逻辑）/ config / error-handling / security / warnings

**前端 SPA**：routing（路由+守卫+懒加载）/ state-management（store+slice 读写边界）/ component-hierarchy（核心组件树+通信模式）/ api-client（HTTP 封装+拦截器）/ styling / build-system / warnings

**Monorepo**：先识别前后端边界，分别走对应模板。`00-overview.md` 额外记录 monorepo 工具（turborepo/nx/lerna）和包间依赖关系。

**文件数 8-12 份是目标，不是硬限制**——小型项目可能 6 份就够，大型项目可能 14 份。关键是每份独立可读、无跨文件重复。

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