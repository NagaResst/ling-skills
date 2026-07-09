# 跨文档概念对齐与数据库设计交叉验证

本文档覆盖 `document-spec-compliance` skill 的独有内容，补充 `doc-lifecycle` Phase 2b（交叉一致性）在跨文档对齐和 DB 设计验证方面的能力。

## 跨文档概念对齐（Cross-Document Conceptual Alignment）

当用户要求检查下游文档（功能规格、设计文档、技术文档）是否符合上游权威文档（PRD、产品规格）时，这不是格式/结构合规检查，而是**概念对齐审计** —— 两个文档描述的是同一个产品吗？

### 确定权威文档

"source of truth" 是用户指定的参考文档。典型层级：PRD > 功能规格 > 设计文档 > 技术文档。

### 比较类别

| 类别 | 检查什么 | 不匹配严重度 |
|------|---------|------------|
| 核心逻辑 | 基本机制描述一致？（如"计时器自动累计" vs "仅外部导入"） | 🔴 Critical |
| 交互设计 | UI 入口、按钮行为、页面流程匹配？ | 🔴 Critical |
| 术语 | 相同概念用相同术语？无废弃术语？ | 🟡 Medium |
| 数据模型 | 字段定义、存储策略（持久化 vs 运行时计算）、实体关系匹配？ | 🟡 Medium |
| 范围/优先级 | 功能优先级（P0/P1/P2）和 MVP 范围匹配？ | 🟡 Medium |
| 边界条件 | 目标达成行为、错误处理、状态转换匹配？ | 🟡 Medium |

### 系统方法

1. **先完整阅读两份文档**，不要逐节即时比较。
2. **构建 forbidden/required term 自动扫描**：
   - **Forbidden terms**: 废弃术语，必须不出现。任何非零计数为 FAIL。
   - **Required terms**: 必须出现的概念。任何零计数为 FAIL。
   - 用 `search_files(path=..., pattern=..., output_mode="count")` 优于 `execute_code` + `read_file`。
   - 呈现为 PASS/FAIL 表格。
3. **手动比较核心逻辑** —— 无法全自动化的部分。
4. **按严重度分组报告**。

### 下游文档常见 stale 模式

- **缺失 UX 重设计**：PRD 重构了交互但下游文档仍描述旧入口
- **范围收窄未反映**：PRD 扩展了功能适用范围但下游仍有旧约束
- **已删除概念仍被引用**：PRD 删除的概念（表、字段）下游仍在用
- **存储策略演变**：字段从持久化改为运行时计算（或反之），下游描述旧策略
- **优先级变更**：PRD 降级/升级功能但下游仍用旧标签

### 多路交叉验证（PRD + Spec + Design）

三份以上文档形成层级时，仅验证相邻父子对（PRD↔Spec, Spec↔Design）会遗漏 PRD↔Design 的直接矛盾。应同时对**所有**上游权威文档运行扫描。

### 全文重写 vs 增量 patch 决策

**重写条件**（任一）：
- 5+ 个核心架构元素变更
- 下游文档缺少权威文档定义的整个页面/章节
- 术语变更普遍（10+ 处）
- 下游文档描述了根本不同的产品交互

**Patch 条件**：
- 变更局限于特定章节
- 整体架构和交互模型相同
- 仅术语、字段名、优先级标签需更新

## 数据库设计交叉验证

验证 **数据库设计文档** 对齐 PRD/Spec 数据模型定义时，标准 forbidden/required term scan 不够。需要**逐字段结构对比**。

### 检查清单

对权威文档中定义的每张表：

1. **表存在性**：权威文档中的每张表在 DB 文档中都有对应章节
2. **字段存在性**：权威文档中每个字段在 DB 文档中出现
3. **字段类型对齐**：`TEXT`、`INTEGER`、`BOOLEAN` → `INTEGER (0/1)` 映射有文档
4. **枚举值**：`source IN ('timer','manual')` 等确切值必须匹配
5. **存储策略**：权威文档标注"运行时计算/不持久化"的字段不能出现在 DB 表定义中
6. **已删除表**：权威文档已删除的表不能在 DB 文档中有活跃表定义（迁移章节中的历史引用可接受）
7. **软删除一致性**：如果权威文档在某些表定义了 `deleted_at`，DB 文档应在所有记录表上添加

### Service→SQL 映射表

DB 设计文档应包含 Service 方法到 SQL 查询的映射表。如果缺失，flag 为 gap。

### 非功能需求对齐

DB 文档应显式回应每个涉及数据库的 PRD 性能目标：
- 写延迟（如 PRD 说 ≤ 50ms — DB 文档应确认 SQLite 可达）
- 运行时计算字段查询延迟
- 加密（PRD 说"本地存储加密"— DB 文档应指名技术）
- 导出格式

### 自动化 DB 验证脚本模式

```python
from hermes_tools import search_files, read_file
import re

AUTHORITY_TABLES = {
    "Project": ["id", "name", "type", "color", "is_paused", "deleted_at", "created_at", "updated_at"],
    "Tag": ["id", "project_id", "name", "sort_order", "deleted_at"],
    # ... etc
}

db_text = read_file(path=db_path, offset=1, limit=500).get("content", "")
db_text += read_file(path=db_path, offset=500, limit=500).get("content", "")

for table, fields in AUTHORITY_TABLES.items():
    for field in fields:
        if field not in db_text:
            issues.append(f"[DB] {table}.{field} missing from database design")
```

**Important**: After recent writes, use `read_file` + Python `in` operator instead of `search_files` to avoid indexing lag false negatives.

## 两遍验证工作流（critical）

自动扫描用 `search_files` 经常报告 false-positive FAIL（搜索模式不匹配实际措辞）。**永远不要把第一遍的 failure 当真，必须验证。**

**Pass 1 — 分类扫描**：按类别运行特定模式检查，产生 PASS/FAIL 记分卡。

**Pass 2 — False-positive 验证**：对每个 FAIL 用更宽/替代模式重新搜索。常见 false positive 原因：

1. **措辞变体**：搜索 `"30 分钟"` 漏掉 `"30/45/60min"`
2. **复合 vs 拆分词**：搜索 `"多行标签栏"` 漏掉分开的 `"多行"` 和 `"标签栏"`
3. **Regex 过度精确**：`"3行限制"` 漏掉 `"3 行"` 不同空格
4. **规则描述包含禁止词**：验证清单本身提到 `无"结束计时"` 会命中
5. **跨行 regex 失败**：`search_files` 单行匹配，跨行模式返回 0
6. **章节标题 vs 内容命名**：搜索过于具体

**只有通过两遍验证的 issue 才需要修复。**

## 架构对比清单

除了术语/数据模型比较，下游文档（尤其是 UI/UX 设计文档）必须检查**结构和架构对齐**。

| 结构元素 | 验证什么 | 典型不匹配 |
|---------|---------|-----------|
| 导航结构 | Tab 名称、Tab 数量、页面组成 | 下游仍有旧 Tab |
| 核心交互机制 | UI 文档是否定义了相同的主要交互？ | 权威定义中央按钮；下游仍用 per-card 按钮 |
| 页面存在性 | 权威文档中的每个页面/屏幕在设计文档中有设计章节 | 缺少页面 |
| 功能主/辅状态 | 哪个是做 X 的主要方式？ | 权威说自动累计是主要，手动是 P1 辅助；下游把手动当平等 |
| UI 状态完整性 | 权威状态机中的每个状态有视觉规格 | 权威定义 5 个按钮状态；下游只有 3 个 |
| 范围扩展 | 功能范围在权威中扩展了 | 权威说专注模式适用于两种类型；下游限制为一种 |
| 新增概念 | 后续 PRD 版本添加的概念 | 权威添加"超额计时"黄色状态；下游没有设计 |

## execute_code 陷阱

### `read_file` dedup 行为

通过 `execute_code` 调用时，`read_file` 可能返回 `{"status": "unchanged"}` 而非内容。key 名也不稳定（`content_returned` / `content` / `False`）。**不要在 `execute_code` 中依赖 `read_file` 做验证。** 用 `terminal(command="cat ...")` 替代。

### `search_files` 索引延迟

`write_file` 或 `patch` 后，`search_files` 可能返回 stale 结果（刚写的内容报 0 hits）。**永远用 `read_file` 直接检查内容来验证 FAIL 结果。**

### `execute_code` 变量作用域

变量在不同 `execute_code` 调用间不持久。如果在一个调用中读文件、在另一个中验证，数据会丢失。**在同一个脚本中读取和验证。**
