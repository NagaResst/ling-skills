# HTML 生成工作流

> 本文只负责 **如何生成 HTML**，不负责交付前是否合格。交付判定一律以 `delivery-checklist.md` 为准。

## 适用时机

在以下情况进入本文：

1. 已完成当日 summary 和 item_summaries，准备生成 `投资建议报告_YYYYMMDD.html`
2. 模板需要扩展到 10+ 只基金
3. 悬浮卡片 / `fund_cards_json` / 占位符替换出现异常
4. 需要批量修补已生成 HTML 的字段结构或交互逻辑

## 生成原则

**推荐直接在 `execute_code` 中完成全流程，不委托子智能体。**

原因：模板填充本质是文本替换。委托子智能体容易出现 TOC 只填部分、裸代码残留、单花括号未替换、卡片数不一致等错误。

## 标准工作流

1. 在 `execute_code` 中完成所有数据准备：解析 `market_momentum` JSON、计算持仓金额/占比、构建 `fund_cards_json` 数组。
2. 在同一个 `execute_code` 中直接读取模板文件、做字符串替换、写入输出 HTML。
3. 替换完成后检查残留占位符。
4. 再执行 `delivery-checklist.md` 中的全部交付前检查。

## 占位符替换纪律

模板使用两种占位符：

- `{{double_brace}}`：用于大部分公共字段
- `{single_brace}`：用于 per-fund 字段（如 `fund_name_1`, `fund_1_action`）

### 必查项

替换完成后，以下两类残留都必须为 0：

```python
re.findall(r'\{\{[^}]+\}\}', html)
re.findall(r'\{fund_', html)
```

## 模板扩展（9 → 10+ 只基金）

模板默认 9 个 fund slot（`fund-1..fund-8 + fund-n`）。持仓增长到 10+ 时，必须先程序化扩展模板，再做填充。

### 扩展步骤

1. **CSS**：插入 `:nth-child(N)` 规则
2. **TOC**：在 `fund-n` 前插入新的 `<a class="toc-sub" href="#fund-N">{{fund_name_N}}</a>`
3. **decision-item**：在 `fund-n` 前插入完整的 `<article id="fund-N" class="decision-item">` 块
4. **Summary table**：在 `fund-n` 行前插入新的 `<tr>`

### 最低验证

```python
template.count('class="decision-item"') == 目标基金数
```

## 悬浮卡片与 `fund_cards_json`

### 生成纪律

以下区域必须从同一份 `active_holdings` 数据结构派生，禁止分别手写：

- 目录子链接
- 第四章决策卡
- 第七章摘要表
- `fund_cards_json`
- 当前持仓数量文案

### `fund_cards_json` 最低字段

每个基金对象至少应包含：

- `full`
- `code`
- `nav`
- `amount`
- `weight_pct`

### 批量字段修补

当模板字段结构变更时（如新增 `nav` 字段），不仅要更新模板和指南，已生成 HTML 也应同步更新。可用 `execute_code` 做：

1. 从 HTML 中 regex 提取 JSON
2. patch 每个基金对象
3. 写回 HTML
4. 如有需要同步更新 JS injection 逻辑
5. 再执行 checklist 校验

## 悬浮卡片异常处理

### DOM 校验时避免误算标题

如果页面启用了 `.fund-ref` / `.fund-card`：

1. 不要直接对整个 `h3` 取 `textContent.trim()`，因为 hover 卡片文本会被一起算进去。
2. 优先读取标题里的第一层文本节点，或显式读取 `.decision-item-hdr h3` 的可见标题文本。
3. `fundRefCount` / `fundCardCount` 大于 0 只能证明悬浮层已生成；标题、目录、摘要表的一致性仍要用独立选择器校验。
4. 不要假设 `fund_cards_json` 会以全局变量形式暴露在 `window` 上；应用 DOM 计数、结构计数或直接解析 HTML 源码。

### 正则转义与 false positive

已知正确的基金名正则转义：

```js
fund.full.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
```

如果转义序列断了，页面肉眼可能正常，但所有 hover 节点注入会静默失败。

检查裸代码残留时，要注意 hover 卡片里的 `代码 005851` 会造成 false positive。

### 交互完整性

- Chart init 和 hover init 各自独立 `try/catch`
- Hover wrappers 不能侵入 `.mini-card h4`、`.action-column h3`、`.toc`、`.table-wrap`
- 第四章 `#sec-4 .decision-item-hdr h3 .fund-ref` 应与决策卡数量一致；第七章 `#sec-7 .fund-ref === 0`
- Fund matching 不能只匹配 `fund.full`；还要兼容第四章标题里的纯 `fund.name`，并按长串优先匹配
- 悬浮卡片显隐不能只依赖 CSS `:hover`；模板必须提供 JS 显式切换 `.is-open` 作为兜底，至少覆盖 `mouseenter` / `mouseleave` / `focus` / `blur` / `Escape` / outside click

## 融资余额口径

- 沪市优先用 `akshare.macro_china_market_margin_sh()`
- 深市优先用 `akshare.macro_china_market_margin_sz()`
- `stock_margin_sse()` 不可用作当日沪市汇总口径，它返回的并不是当前交易日最新汇总
- 当北交所程序化数据源未验证时，日报和 HTML 统一展示**沪深两市口径**，并明确“不含北交所”

## 历史 HTML 的使用边界

1. 历史 HTML 只能作为数据来源、验证来源、事实锚点来源
2. 不得把历史 HTML 当作新的页面模板
3. 当前任务必须始终回到 `investment-advice-report-20260517-template.html`

## 常见坑

1. **TOC 扩展必须全量补齐**：模板 TOC 默认只有 fund-1/fund-2/fund-n 三个 `toc-sub` 槽位，`fund-3..fund-8` 在模板里不存在。扩展到 10+ 基金时，必须**补齐 fund-3 到 fund-8 的 toc-sub**，不能只加新基金链接——否则 TOC 子链接数 ≠ 持仓数，交付校验失败。且模板 TOC 占位符是 `{{fund_name_N}}`（双花括号），替换后不能残留花括号包裹（如 `{基金名(代码)}`）。
2. **fund_cards_json 替换坑**：模板中 `const funds = {{fund_cards_json}};`，替换 JSON 数组后不能残留 `{[...]}` 外层花括号——`{[` 会导致 JS 语法错误、悬浮卡片全部静默失效。替换后必须在浏览器验证 `.fund-ref` 数量 > 0 且 hover 后 opacity=1。
3. 只替换 `{{...}}`，漏掉 `{fund_*}`
4. fixed-slot 模板静默丢基金
5. TOC / 卡片 / 摘要表 / `fund_cards_json` 不是从同一份 holdings 派生
6. 子智能体填模板超时或部分覆盖
7. hover CSS 恢复了但忘了 JS injection path
8. 用第一个 `<tbody>` 替换摘要表，误伤 ETF/政策表
7. **sec-2b 新闻条目结构偏离模板**：必须使用模板定义的 `<div class="news-item"><h4>标题</h4><p class="news-meta">来源：XXX | <a href="URL" target="_blank">原始链接</a></p><p>事实摘要</p><p class="muted">判断用途：✅/⚠️/❌ 利好/中性/利空</p></div>` 四段式结构。禁止自造 `news-date`/`news-body`/`news-tag` 等非模板 class，禁止省略来源和链接，禁止把标题/内容/判断压成一行。
8. **市场量能表"亿"重复 bug**：模板中 `{{market_turnover_total}} 亿` 已含"亿"后缀，填充数据值时不能再追加"亿"。正确：`{{market_turnover_total}}` 填 `20,500`，模板自带 ` 亿`。错误：填 `20,500 亿`，结果 `20,500 亿 亿`。同理 `{{northbound_net_flow}}`、`{{margin_balance_total}}` 均不能在数据值中包含"亿"字。
9. **ETF 走向表必须 4 列 + 行类着色**：表头必须是 `ETF(代码) | 来源 | 前一交易日涨跌幅 | 对应持仓/备注`。每行 `<tr>` 必须根据涨跌加 `class="etf-up"`/`class="etf-down"`/`class="etf-flat"`。禁止丢"来源"列、禁止丢行类。来源填 `relevant` 或 `core`。
10. **action-badge 必须用模板定义的类名**：模板只定义了 `hold`/`watch`/`light`/`new` 四种 action-badge 类。禁止自造 `badge-good`/`badge-warn`/`badge-rise`/`badge-hold` 等非模板类名——CSS 无定义，badge 无样式渲染。正确写法：`<span class="action-badge hold">持有不动</span>`。
11. **sec-7 摘要表 badge 必须用模板定义的类名**：同上，`<span class="badge hold">持有不动</span>` 或 `<span class="badge watch">持有观察</span>`。禁止用 `badge-good`/`badge-warn` 等。
12. **sec-5 列表项必须用 `<li>` 包裹**：`<ul>` 和 `<ol>` 内不能直接放纯文本行，每条内容必须用 `<li>…</li>` 包裹。裸文本在 `<ul>` 内会导致浏览器默认样式渲染异常。
