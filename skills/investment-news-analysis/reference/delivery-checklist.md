# 交付前自检查清单

> 每次生成 summary + item_summaries + HTML 后，必须逐项执行以下检查。任何一项未通过都不得宣布交付。

## 一、持仓集合一致性

从 `持仓情况.md` 提取 `份数 > 0` 的基金作为 active_holdings（唯一基准名单），以下所有区域必须从这一份名单派生：

| 检查区域 | 校验内容 | 方法 |
|----------|---------|------|
| 目录子链接 | 数量 = 持仓数，名称 = 全称 | `re.findall(r'class="toc-sub"[^>]*>(.*?)</a>', html)` |
| 第四章决策卡 | 数量 = 持仓数，h3 包含完整"基金名称(代码)" | `re.findall(r'<article[^>]*class="decision-item"', html)` |
| 第七章摘要表 | 行数 = 持仓数，第一列 = 全称 | `re.findall(r'<tr><td>(.*?)</td>', html)` |
| fund_cards_json | 条数 = 持仓数，full 字段 = 全称 | 从 HTML 源码解析 JSON |
| summary 核心指标表 | 行数 = 持仓数，基金名称(代码) 全称 | 人工或脚本校验 |

**判定**：以上五处的基金名称集合必须完全一致，且无重复。`all_name_sets_match != true` 则不得交付。

**顺序校验**：如果 HTML 按决策优先级排序而非持仓文件原始顺序，用决策顺序数组做对账，不要拿 active_holdings 原始遍历顺序去校验。

## 二、裸代码零容忍

所有交付物（summary、item_summaries、HTML）正文中提及基金时必须写成"基金名称(代码)"全称格式。禁止只写代码、只写简称、或把代码写在名称前面。

### 扫描方法

用 execute_code 运行以下脚本，扫描全部交付物：

```python
import re, os

# 1. 从持仓情况.md 提取基金代码列表
with open("投资者行动/持仓情况.md") as f:
    holdings_text = f.read()
codes = re.findall(r'代码:\s*(\d{6})', holdings_text)

# 2. 定义扫描函数
def scan_file(filepath, codes, is_html=False):
    with open(filepath) as f:
        text = f.read()
    violations = []
    for code in codes:
        for m in re.finditer(re.escape(code), text):
            pos = m.start()
            # 豁免1: 在 "名称(代码)" 格式中（前一个是"("，后一个是")"）
            if pos > 0 and text[pos-1] == '(' and text[pos+len(code):pos+len(code)+1] == ')':
                continue
            # 豁免2: HTML 专属（code-badge / href / JSON code 字段）
            if is_html:
                before = text[max(0, pos-80):pos]
                if 'code-badge' in before[-60:] or 'href="#fund-' in before[-30:] or '"code"' in before[-40:]:
                    continue
            # 豁免3: 反引号内（文件路径）
            if text[:pos].count('`') % 2 == 1:
                continue
            violations.append((code, pos, text[max(0,pos-50):pos+len(code)+50]))
    return violations

# 3. 扫描全部交付物
date = "2026-07-09"  # 替换为当日日期
files = [
    (f"投资新闻归档/2026-07/{date}/summary_{date}.md", False),
    (f"投资者行动/持仓分析与建议/投资建议报告_{date.replace('-','')}.html", True),
]
# 加上 item_summaries
item_dir = f"投资新闻归档/2026-07/{date}/item_summaries"
if os.path.isdir(item_dir):
    for fname in sorted(os.listdir(item_dir)):
        if fname.endswith('.md'):
            files.append((os.path.join(item_dir, fname), False))

# 4. 输出结果
total = 0
for filepath, is_html in files:
    v = scan_file(filepath, codes, is_html)
    if v:
        print(f"\n❌ {filepath}: {len(v)} violations")
        for code, pos, ctx in v:
            print(f"  {code}: ...{ctx}...")
        total += len(v)
    else:
        print(f"✅ {filepath}: clean")

print(f"\n{'='*40}")
print(f"Total violations: {total}")
if total > 0:
    print("⛔ 禁止交付，必须逐处替换为'基金名称(代码)'全称后重新扫描")
else:
    print("✅ 全部通过，可交付")
```

### 裸代码高发区

以下位置是裸代码高发区，生成时就必须预防：

- summary 的"持仓变化检测"段落（如"014194 浮盈从…"）
- summary 的"复盘与风险雷达"段落（如"021528暴跌-3.62%/005851跌破成本线"）
- summary 的"今日关注要点"段落（如"观察021528是否修复"）
- item_summaries 的"关联持仓"字段（如"014194/005851/021528芯片方向"）
- HTML 的 hero lede、boundary、review card、watchlist、policy table、ETF trend table
- 任何用斜杠分隔多个基金代码的位置（如"019943/009520/005216"）

### 书写预防

首次出现写"基金名称(代码)"全称，同段后续可用"本基金"指代，禁止用裸代码做缩写。

## 三、HTML 结构校验

| 检查项 | 要求 | 脚本校验 |
|--------|------|---------|
| 占位符残留 | `{{}}` 和 `{}` 两种占位符均为 0 | `re.findall(r'\{\{[^}]+\}\}', html)` + `re.findall(r'\{fund_', html)` |
| 模板来源 | 必须从 `investment-advice-report-20260517-template.html` 填充 | 人工确认 |
| h3 标题格式 | 每个决策卡 h3 包含完整"基金名称(代码)"，不能拆到 code-badge | `re.findall(r'<h3>(.*?)</h3>', html)` |
| 第四章当日新增 | 第二章到第六章必须体现当日新增事实，不是上一日续写 | 人工确认 |
| 单花括号占位符 | 模板有两种占位符 `{{double_brace}}` 和 `{single_brace}`，两种都要替换 | 见上方占位符检查 |

## 四、悬浮卡片校验

若模板启用了 `.fund-ref` / `.fund-card` 悬浮卡片：

1. **h3 标题不能被 hover 包裹侵入**：检查 `h3 .fund-hover-ref` 数量应为 0。hover wrappers 不能出现在 headings 或 card-title 节点下。
2. **DOM 节点已实际生成**：`.fund-ref` 数量 > 0 且 `.fund-card` 数量 > 0。交付标准不是"脚本看起来像对了"，而是浏览器 DOM 中相关节点已实际生成。
3. **false positive 检查**：检查裸代码残留时，hover 卡片里的 `代码 005851` 会造成 false positive。已知好的 hover 正则转义：
   ```js
   fund.full.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
   ```
4. **正则转义断线检测**：如果转义序列断了，页面肉眼正常但所有 hover 节点注入会静默失败。检查 `.fund-ref` 数量是否大于 0 来确认。
5. **try/catch 独立**：Chart init 和 hover init 各自独立 `try/catch`，一个失败不能 disable 整个页面。

## 五、HTML 模板填充工作流

**推荐直接在 `execute_code` 中完成全流程，不委托子智能体。**

1. 在 execute_code 中完成所有数据准备：解析 market_momentum JSON、计算持仓金额/占比、构建 fund_cards_json 数组。
2. 在同一个 execute_code 中直接读取模板文件、做字符串替换、写入输出 HTML。
3. 替换完成后用正则检查残留占位符。
4. 执行交付前强制校验。

> ⚠️ **不推荐委托子智能体填充模板**：模板填充本质是文本替换，子智能体耗时长且可能出错（TOC 只填部分、裸代码满篇等）。

## 六、模板扩展（9 → 10+ 只基金）

模板默认 9 个 fund slot（fund-1..fund-8 + fund-n）。持仓增长到 10+ 时，必须先程序化扩展模板再填充。

扩展步骤（9 → 10，11+ 重复）：

1. **CSS**：在 `:nth-child(8)` 和 `:nth-last-child(1)` 之间插入 `:nth-child(N)` 规则
2. **TOC**：在 `fund-n` 前插入 `<a class="toc-sub" href="#fund-N">{{fund_name_N}}</a>`
3. **decision-item**：在 `fund-n` 的 `<article>` 前插入完整的 `<article id="fund-N" class="decision-item">` 块
4. **Summary table**：在 `fund-n` 行前插入新的 `<tr>`

验证：`template.count('class="decision-item"')` 等于目标基金数。

## 七、份额与快照校验

1. **份数 > 0 才入列表**：`持仓情况.md` 中份数为 0 的历史记录不得进入目录、卡片、摘要表或 fund_cards_json。
2. **份额歧义标注**：若份数字段存在歧义写法（如 `20218.58 - 10109.29`），在报告中显式标注信息边界；未获额外证据前，不能静默按"已减半"改算。
3. **share_change 分类**：每只基金权重变化时分类为 `increased` / `reduced` / `unchanged`（NAV drift），在 prose 中显式区分。
4. **权重分母确认**：确认 `holding_weight_pct` 的分母是 holding-only 还是 total-asset。做调仓计算时优先使用 `analysis_snapshot`（含 `full` 和 `holding_weight_pct` 等便利字段）。
5. **清仓基金处理**：`holdings_change_vs_previous_report.changes[]` 中 `change_type: "cleared"` 的基金不进入活跃持仓列表，但在"持仓变化检测"中写明清仓金额和盈亏。ETF 总览表保留对应行但标注"已清仓"。

## 八、数据降级处理

### 申万二级行业数据缺失

`sw_l2_industry_daily.status` 为 `"empty"` 时：

1. 以 `relevant_etf_daily` 中持仓相关 ETF 涨跌作为板块代理。
2. 以 `core_industry_etf_daily` 中宽基 ETF 作为市场风格参考。
3. 日报第四章用"持仓相关行业代理"表替代申万二级行业涨跌幅排行。
4. 数据附录和 HTML"数据缺口"卡中明确标注。
5. 申万数据缺失不构成预测阻塞项。

### analysis_snapshot 配套产物检查

1. 先检查当天 `raw_data/` 是否存在 `analysis_snapshot_YYYY-MM-DD.json`。
2. 若缺失，优先重跑 `fetch_market_momentum.py`。
3. 若 `share_change_type` 大面积异常（如几乎都变成 `new`），优先检查持仓解析是否兼容当前 HTML 的 `const funds = [...]` 数据结构。
4. 如果用户要求"同一天重新拉取 raw_data 再更新报告"，不要假设只会改动市场字段。必须重新读取最新持仓和 snapshot。
5. 如果重拉后 active holdings 集合/数量/主次结构发生变化，就把 summary 和 HTML 视为"整页重生"。
6. 如果重拉后 `actual_date` 前进了，必须同步删除所有旧的"数据滞后一天"说明。

## 九、交付前校验输出格式

交付前建议用 execute_code 输出以下结构化校验结果：

```
summary_exists: true/false
html_exists: true/false
active_holdings_count: N
toc_sub_links_count: N
decision_cards_count: N
summary_rows_count: N
fund_cards_json_count: N
placeholder_residual: 0
bare_code_violations: 0
toc_matches_active: true/false
cards_matches_active: true/false
summary_matches_active: true/false
fund_cards_matches_active: true/false
all_name_sets_match: true/false
```

只要 `all_name_sets_match != true` 或 `bare_code_violations > 0` 或 `placeholder_residual > 0`，就不得交付。
