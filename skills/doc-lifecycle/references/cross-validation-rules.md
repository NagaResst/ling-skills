# Phase 2b 完整规则 — 交叉一致性

**适用**：检查一批文档之间是否一致，自动修复不一致模式。

---

## 核心方法（3 步）

### Step 1 — 加载所有文档

```python
import os

base = "<project>/docs"
docs = {}
for root, dirs, files in os.walk(base):
    for f in sorted(files):
        if f.endswith('.md'):
            docs[f] = open(os.path.join(root, f)).read()
```

### Step 2 — 定义检查规则

规则格式：

```python
[(doc_list, pattern, check_name, positive)]
```

- `positive=True`：必须匹配（声明存在性检查）
- `positive=False`：必须不匹配（残留检查）

辅助函数：

```python
def has(t, p): return bool(re.search(p, t, re.IGNORECASE))
def lacks(t, p): return not has(t, p)
```

### Step 3 — 逐条执行并分类

对每条规则执行并输出 `✅/❌`。

| 类型 | 处理方式 |
|------|---------|
| False positive（误判） | 特定文档性质决定的不适用项，记录说明即可 |
| Real issue（真正不一致） | 用 `patch` 工具修复 |
| 可接受缺失 | API 文档 / 安全设计 / 数据库设计等可不声明产品约束 |

---

## 规则定义（用户自定义，按项目调整）

**这些规则是示例，不是通用规则**。每个项目应根据自身基线（PRD + 功能规格）定义自己的规则集。

规则集模板：

```python
RULES = [
    # 残留类（positive=False）
    ("all_docs", r"\bis_deleted\b", "is_deleted 残留", False),
    ("all_docs", r"\bis_timing\b", "is_timing 残留", False),
    ("except_prd", r"\b归因\b", "归因残留", False),

    # 声明类（positive=True）
    ("functional_spec", r"完全独立|互不混用", "三种模式独立", True),
    ("functional_spec", r"1:1|一一对应", "项目与标签 1:1 绑定", True),
    ("all_docs", r"deleted_at", "软删除 deleted_at", True),

    # 字段级
    ("db_design", r"accumulated_duration DEFAULT 0", "字段默认值", True),
    ("functional_spec", r"≥ ?60.?秒|MIN_TIMING_DURATION", "最小计时时长", True),

    # 代码规范
    ("ui_files", r"@Builder\s+private\s+\w+\([^)]+\):\s*void", "@Builder 带参数", False),
]
```

**自定义规则的方法**：
1. 读项目 PRD + 功能规格作为基线
2. 提取基线声明（关键术语、字段名、约束值）
3. 把"声明"转 positive=True 规则，把"废弃"转 positive=False 规则

---

## 自动化脚本

通用版 → `scripts/check_residual_patterns.py`（接受自定义规则 JSON）

---

## Patch 工具使用纪律

1. **用 `repr()` 读取原文件确认精确内容**（含换行符 `\n` 而非 `\r\n`）
2. `old_string` 需足够长以确保唯一（若多个匹配，扩大上下文）
3. 用**完整 section 内容作为锚点**最可靠

```python
patch(mode="replace",
      old_string="完整的前后几行内容，包含要替换的段落",
      new_string="新内容",
      path="文档路径")
```

---

## 已验证的误判规则（示例）

这些规则需人工判断，工具误判是常见陷阱：

| 现象 | 误判原因 | 正确判断 |
|------|---------|---------|
| `is_timing` 出现在说明句中（如"is_timing 状态通过此判断"） | 不是字段名而是概念描述 | ✅ 误判 |
| 安全设计不声明"三种模式完全独立" | 文档性质决定 | ✅ 误判 |
| API 文档不声明产品 1:1 绑定 | 文档性质决定 | ✅ 误判 |
| 修订记录中保留"修正归因时机"历史条目 | 历史版本演进记录 | ✅ 不应删除 |

---

## 字段级一致性检查（额外流程）

当验证实施文档与数据库设计文档时，做字段级对比：

| 检查项 | 基线文档 | 实施文档 | 修正方式 |
|--------|---------|---------|---------|
| 字段默认值 | `accumulated_duration DEFAULT 0` | 缺默认值 | 补充 `= 0` |
| 可空字段业务层约束 | `target_duration` 数据库可 NULL | 未说明 | 补充"数据库可 null，业务层校验>0" |
| sort_order 默认值 | 未声明，默认0 | 缺默认值 | 补充"≥ 0，默认0" |
| 最小计时时长 | `MIN_TIMING_DURATION_SECONDS = 60` | `> 0` | 修正为 `≥ 60秒` |
| 时间戳类型 | 统一毫秒 | 未强调 | 统一补充"毫秒时间戳" |
| note 字段长度 | ≤200字符 | 未定义 | 补充"≤200字符" |

---

## 测试用例职责边界（项目特定规则示例）

当项目有实施文档中的测试用例章节时：

- Repository 层测试：仅验证数据 CRUD，不验证跨表同步
- Service 层测试：验证跨层同步逻辑
- 禁止在 Repository 测试中写跨层验证（那是上层 Service 的职责）

---

## Pitfalls

### 工具误判需人工判断

检查规则本身是否有漏洞（如某条残留规则会命中概念描述词）。

### 修订记录中的历史条目保留

`re.sub(r'修订记录.*', '', text, flags=re.DOTALL)` 排除修订记录区域后再做负面检查。

### 多列对照表 vs 单列描述

Phase 2b 检查时，**如果发现某文档含多列对照表（如"v1.0 表述/v2.0 校对后"）**，这是 Phase 4 残留模式，不是 Phase 2b 范畴，**转入 Phase 4 重写**。

### 代码规范 vs 代码错误

代码规范检查（如"@Builder 方法无参数"）属于代码 lint，不属于文档交叉验证。**用 Phase 4 重写场景不应把代码规范问题混入**。

---

## 完成标准

- [ ] 规则集已按项目基线定义（不是通用规则直接套用）
- [ ] 每条规则执行 ✅/❌，❌ 项已分类（false positive / real issue）
- [ ] real issue 已用 patch 工具逐条修复
- [ ] 修复后重新扫描，残留 = 0
- [ ] 误判项已人工确认并记录理由