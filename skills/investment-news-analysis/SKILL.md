---
name: investment-news-analysis
description: 持仓监控与量化调仓建议系统。面向多持仓组合，收集新闻、生成每日日报、验证预测并输出组合级建议。适用于：分析整体持仓情况、收集市场新闻、生成日报、跟踪组合强弱。❗ 单个持仓逻辑校验与具体调仓建议请使用 single-holding-adjustment SKILL；单基金深度研究请使用 fund-deep-research SKILL。
---

> ⚠️ **免责声明**：本工具仅供个人学习和信息整理使用，所有分析内容均不构成任何投资建议。投资有风险，入市需谨慎，请依据自身判断做出投资决策。

> 📌 **书写规范**：所有报告、预测、验证表格中提及基金时，必须写成"基金名称(代码)"。禁止只写代码，禁止把代码写在名称前面。

> 🚫 **事实纪律（最高优先级，不得违反）**：
> 1. 只能引用实际搜索、抓取或归档到本地的信息。
> 2. 缺失数据必须明确写缺口，不能用估算值或猜测补齐。
> 3. 不得虚构盘中涨跌、第三方观点、个股层行情跟踪、成交量数据。
> 4. 不能把没有确认的数据混入日报主结论。
> 5. 每个预测或建议都必须同时交代支持证据、风险、信息边界。

# 投资新闻收集与预测分析

## 核心定位

这是一个面向**当前持仓组合 / 多持仓基金**的日报与建议系统，负责四件事：

1. 先围绕政策、市场行情与量级、宏观建立当天判断框架，再按需补充基金本身信息。
2. 基于前一交易日确认数据生成每日 summary。
3. 生成当日投资建议 HTML 归档页面。

> ❗ **边界说明**：本 SKILL 不做单基金深度研究，不负责输出成体系的深度研究框架、建仓打分和长篇情景推演。如需深度研究单只基金，请使用 `fund-deep-research` SKILL。
>
> 单个持仓的逻辑正确性校验、单持仓调仓建议、单持仓独立报告，请使用 `single-holding-adjustment` SKILL。

## 三份主规范

执行本 skill 时，以下三份文档是唯一主规范：

1. [reference/daily-summary-template.md](reference/daily-summary-template.md)
日报结构、时间视角、章节职责、Markdown 骨架。

2. [reference/prediction-verification.md](reference/prediction-verification.md)
信息充分性检查的规则来源。

3. [reference/investment-advice-report-20260517-guide.md](reference/investment-advice-report-20260517-guide.md) + `reference/investment-advice-report-20260517-template.html`
HTML 投资建议报告的唯一结构规范与唯一页面骨架。两者必须一起使用，禁止脱离模板文件另写一套 HTML 结构或样式。

其他参考文档只提供补充流程或实现细节，不再单独定义另一套日报或建议结构。

## 执行协议

> 🚫 **主流程禁止委派子 agent（最高优先执行约束）**：从"执行开始"到交付的全部主流程步骤——画像约束读取、定量脚本运行、历史数据读取、新闻归档与搜索、信息充分性检查、每日 summary 编写、HTML 建议报告编写与交付校验、index.json 更新——**一律由主 agent 亲自完成，禁止用 delegate_task / 子 agent 代写或代跑**。原因：完整报告需要主 agent 全程持有数据与上下文，且能完整走查交付；两轮子 agent 委托均已因超时/上下文切断而失败。
> 子 agent 仅限、且必须严格按本 skill 要求用于**搜索阶段的网络新闻采集补充**。即使子 agent 用于搜索，其返回结果仍不得覆盖 `market_momentum` 脚本数据；脚本数据是唯一可信基准。

| 阶段       | 必读参考                                                                                                                                                                       | 本阶段必须产出                                      |
| -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| 画像约束前    | `投资者行动/投资者画像.md`                                                                                                                                                           | 黑名单、风险偏好、工具边界                                |
| 搜索前      | [reference/archiving.md](reference/archiving.md)                                                                                                                           | 当日归档目录、单条摘要字段、去重规则                           |
| 搜索阶段     | [reference/search-strategy.md](reference/search-strategy.md)                                                                                                               | 以`finance_news.json`为初始轮素材，额外再加上网络搜到的素材归档到本地 |
| 定量数据前    | `scripts/fetch_market_momentum.py`                                                                                                                                         | 前一交易日官方净值、宽基ETF收盘、申万二级行业指数、北向单日、全市场融资余额、全A（沪深京）成交额、持仓快照                  |
| 历史读取前    | [reference/historical-data.md](reference/historical-data.md)                                                                                                               | 历史 summary 提取、最近可比较基准读取、持仓变化对比               |
| 预测前      | [reference/prediction-verification.md](reference/prediction-verification.md)                                                                                               | 信息充分性检查                               |
| HTML 输出前 | [reference/investment-advice-report-20260517-guide.md](reference/investment-advice-report-20260517-guide.md) + `reference/investment-advice-report-20260517-template.html` | 必须基于模板文件填充出的完整 HTML 页面，禁止自定义另一套页面骨架 |

## 阶段零：画像与边界约束

每次开始前必须读取 `投资者行动/投资者画像.md`，确认：

1. 黑名单过滤。
2. 仅推荐场外基金或 ETF 联接基金。
3. 新方向必须有明确政策支持。
4. 用户当前风险偏好和既有套牢经历。

## 阶段一：定量数据与历史上下文

### A. 读取历史数据

搜索前必须读取：

1. `投资新闻归档/index.json`
2. 与当前持仓相关的近期 summary
3. `投资者行动/持仓情况.md`

用途：

- 对比持仓份额变化
- 提取上一轮有效判断与边界

细则见 [reference/historical-data.md](reference/historical-data.md)。

### B. 再跑定量脚本

先完成本小节的**量能前置取数**，再且只运行一次 `scripts/fetch_market_momentum.py`。

#### 量能前置取数（脚本前置，不属于阶段二的政策/市场/宏观新闻搜索）

在分析日当天，主 agent 必须实际访问一篇**前一交易日收评原文**，并记录其原始 URL，作为全A（沪深京）成交额的同日回退输入。原文必须同时明确：

1. 前一交易日日期；
2. `沪深京三市`（或等价的全A沪深京）口径；
3. 成交总额数值与单位。

这一步是定量数据的来源预检，不得等脚本报错后才临时搜索，也不得拿搜索摘要、盘中快讯、当日实时行情或跨市场加总充数。准备好 URL 后，首次且唯一一次脚本运行同时传入它；脚本优先查询 `800004` 历史日线，只有主源不可用时才解析该原文，并在**正文自身**的日期、口径、金额三项均匹配时接受。

若两条同日路径都不可验证，脚本会中止；**不得省略量能字段、不得第二次运行脚本补参数、不得生成日报或 HTML**。这保证交付物不会带着“数据缺失”继续流转，而不是虚构“网络一定不会失败”。

统一口径：

- `--date YYYY-MM-DD` 代表生成这一天的日报。
- 日报中的基金净值、ETF、北向单日、全市场融资余额，一律截到**前一交易日**。
- 北向近 7 天窗口保留，但窗口终点同样是前一交易日。
- 不使用估值，不使用分析日当天 ETF spot，不使用当天北向单日数据。

推荐调用方式：

```bash
python3 .github/skills/investment-news-analysis/scripts/fetch_market_momentum.py \
	--date YYYY-MM-DD \
	--holdings-file 投资者行动/持仓情况.md \
	--market-turnover-report-url "已实际访问并验证的前一交易日收评原文URL" \
	--output 投资新闻归档/YYYY-MM/YYYY-MM-DD/raw_data/market_momentum_YYYY-MM-DD.json
```

执行上面命令后，脚本会在同一 `raw_data/` 目录**同时写出**：

- `market_momentum_YYYY-MM-DD.json`
- `analysis_snapshot_YYYY-MM-DD.json`

前者是市场与净值主数据，后者是给 `holding-adjustment` 和后续仓位诊断使用的持仓快照补充层；两者必须视为同一次生成链的配套产物。

### C. 准备当天 `finance_news.json`

找到当天目录下已经有：

`投资新闻归档/YYYY-MM/YYYY-MM-DD/raw_data/finance_news.json`

这是前一天由 `scripts/cn_finance_news.py` 自动运行后把结果落到当天 `raw_data/finance_news.json`。
注意：不要自己运行cn_finance_news.py做重复的工作，直接使用已有的 JSON 文件！！！

若出现以下异常，再补读 [reference/github-action-news-pipeline.md](reference/github-action-news-pipeline.md)：

- 当天目录无 `finance_news.json`
- `finance_news.json` 与前一天完全相同
- 归档日期识别错误导致重复采集
- GitHub Action 运行失败或 days 计算异常

## 阶段二：搜索与归档

搜索顺序以 [reference/search-strategy.md](reference/search-strategy.md) 为准。主链路固定为：

1. 先读今天 `raw_data/finance_news.json`对其内容进行筛选（**必须全文读取逐条筛选，禁止关键词/正则检索前置**，详见 search-strategy.md 硬规则）
2. 然后搜政策面
3. 再搜市场行情面和量级新闻
4. 最后搜宏观面

主链路完成后，再按需要补：

1. 基金本身信息
2. 同类基金横向比较
3. 政策新方向雷达

每轮搜索后立即归档：

- 外部信息到 `item_summaries/`
- 脚本输出到 `raw_data/`

基金本身信息搜索放在后面，且只是补充项；没有新增基金直接新闻不影响主链路判断，不必为此扩大搜索范围，也不需要单独归档此事实。

## 阶段三：建议生成前置

做新预测前必须先通过信息充分性检查。

硬规则：

1. 做新预测前必须先通过信息充分性检查。

## 阶段四：建议生成

本阶段目标是把前文信息压缩成**当日动作判断**。

必须按以下顺序完成：

1. 验证上一轮判断是否有效。
2. 复核当前持仓状态。
3. 结合横向比较确认强弱排序。
4. 给出逐基金状态复核与操作建议。
5. 生成今日关注要点。

如需逐基金动作细化，写法以日报模板第八章和 HTML 指南第四章为准，不得另起一套字段体系。日报章节以模板定义的八章为准，不得自行新增。

补充：逐基金动作里的 `触发价格线 / 什么时候动作` 默认按持仓成本锚定；如果成本没变，就写"更接近既有止盈线"，不要把止盈线跟着最新净值一起上调。只有成本变化或明确策略重估时，才允许改线。

## 常见陷阱

### market_momentum 数据结构

`fetch_market_momentum.py` 输出的 JSON 有几个容易踩的字段名坑：

1. **基金净值**：字段是 `official_nav`，不是 `nav`。`fund_official_navs[]` 每个元素含 `code`、`name`、`official_nav`、`nav_date`。
2. **申万二级行业**：数据嵌套在 `sw_l2_industry_daily.industries[]`，不是 `sw_l2_industry_daily` 直接是数组。行业名字段是 `index_name`，不是 `industry_name`。可用字段：`index_code`、`index_name`、`date`、`change_pct`、`pe_ttm`、`pb`、`dividend_yield_pct`、`circulating_market_cap_yi` 等。
3. **北向资金**：`northbound_weekly_summary.daily_net_flow[].net_deal_amt_raw` 单位是万元，需除以 100 换算为亿元。`total_net_in_yi_if_raw_unit_is_million` 字段名虽含 "million" 但实际已换算为亿元。
4. **ETF 数据分两组**：`relevant_etf_daily` 和 `core_industry_etf_daily`，不是 `etf_daily`（该字段为空字典）。
5. **analysis_snapshot vs holding_valuation_snapshot**：做调仓计算时优先使用 `analysis_snapshot`，因为它有 `full` 和 `holding_weight_pct` 等便利字段。
6. **持仓文件解析**：`fetch_market_momentum.py` 要求持仓文件为扁平 `key: value` 格式。购入时间嵌套格式会导致解析器静默截断。始终显式传入 `--holdings-file`。
7. **市场量能总览**：`market_turnover_summary` 字段含全A（沪深京）成交额，主源为东方财富全A(沪深京)指数 `800004` 的前一交易日日线字段（原始单位元，已换算为亿元）；禁止再将上交所与深交所不同日期的统计数据相加。分析脚本只在**分析当天**对历史 `800004` 源发起一次请求；**不得依赖前一交易日收盘任务或重试**。首次脚本运行前，主 agent 必须已实际访问并传入一篇前一交易日收评原文 URL；主源不可用时，脚本只在原文正文自身同时匹配目标日期、`沪深京三市` 和成交总额时接受该数据，禁止使用搜索摘要、盘中实时值或跨市场拼接。两条同日路径均未取得可验证数值时，脚本必须中止，禁止生成含“数据缺失”的日报。`northbound_daily_raw` 必须读取东财 `006` 北向汇总行的 `NET_DEAL_AMT`；仅在 `006` 缺失时以 `002+004` 同日相加，禁止读取没有净流入字段的 `005` 行。`hs_margin_summary` 字段含全市场融资融券余额，来自 `stock_margin_account_info`（含沪深+北交所，单位亿元）；该字段同时输出 `margin_balance_change_yi`（与前一交易日融资余额变动，单位亿元）和 `margin_balance_change_pct`（变动百分比），用于日报和 HTML 报告中"对比昨日"备注列。与 `northbound_daily_raw` 三者搭配可评估市场整体量能。日报和 HTML 报告中均需展示这三项指标的对比表。
8. **item_summaries 归档边界**：北向资金、融资余额、成交额等脚本定量数据不创建 item_summary。这些数据已在 `raw_data/market_momentum_YYYY-MM-DD.json` 中，在日报第四章展示即可。把它们当作"新闻条目"归档会挤占真正新闻的位置。

### 网络搜索补充的可靠性

用 delegate_task 子智能体搜索 A 股行情时，返回的涨跌方向和幅度可能与脚本实际数据严重矛盾（例如子智能体声称"三大指数收跌"，实际是大反弹日）。**脚本抓取的 market_momentum 数据为唯一可信基准**，子智能体网络搜索结果只能用于补充新闻叙事和政策信息，不得用于替代或覆盖脚本数据。

### macOS 路径与 TCC 权限

项目根目录为 `~/handbook/make-little-money/`。`~/Documents/work/handbook/` 旧路径受 macOS TCC Full Disk Access 限制，脚本输出和文件读写均不可用。所有路径必须指向 `~/handbook/`。

## 每日 Summary 输出要求

每日 summary 的标准结构、章节职责、模板骨架统一见：

- [reference/daily-summary-template.md](reference/daily-summary-template.md)

执行时直接按模板落章。日报采用“精简可审计版”：完整证据链和人读决策解释由同日 HTML 承载；日报保留历史对比与审计所需的核心表、状态快照和可回溯索引，禁止将 HTML 大段内容重复复制进 Markdown。

最低要求：

1. 第一章核心指标表必须包含 `持有份额` 和 `当前持有金额`，并覆盖全部 active holdings。
2. 如检测到份额变化，必须写 `持仓变化检测`；无变化也必须明确写出。
3. 第二章必须列出所有 `item_summaries` 的紧凑索引和归档路径，完整事实与链接以单条归档及 HTML 为准。
4. 第四章必须保留成交额、北向、融资余额三项量能，以及会影响当前持仓状态的市场信号；全量 ETF/行业表放 HTML。
5. `复盘与风险雷达` 必须服务动作判断，只写验证状态、风险变化和动作边界，不能重复前文。
6. 第六章必须是覆盖全部 active holdings 的结构化状态快照，至少有状态/建议、唯一关键信号、成本锚定触发线、置信度及 HTML 卡片路径；完整逐基金推理放 HTML。
7. `今日关注要点` 必须面向分析日当天，默认最多三条，不写成机械的“明日关注”。
8. 数据附录必须写出 `item_summaries_count`、主要 raw_data、最近可比较 summary、同日 HTML 路径、关键缺口和反向证据。

## 投资建议 HTML 输出要求

每次执行分析后，必须生成独立 HTML 页面：

`投资者行动/持仓分析与建议/投资建议报告_YYYYMMDD.html`

HTML 规则以 [reference/investment-advice-report-20260517-guide.md](reference/investment-advice-report-20260517-guide.md) 和 `reference/investment-advice-report-20260517-template.html` 为准，两者缺一不可。

硬约束：每次生成 HTML 时，必须直接复用 `reference/investment-advice-report-20260517-template.html` 作为页面骨架，只允许填充当日内容、数据和 `fund_cards_json`。禁止自行设计另一套 HTML / CSS / 章节结构后再声称"符合模板精神"。

这里只保留最低要求：

1. summary 只生成 Markdown，不生成 HTML。
2. 投资建议正式归档只认 HTML 页面。
3. 第二章必须先解决"今天先看什么"。
4. 第四章必须一只基金一张卡片。
5. 第七章必须保留固定摘要表供后续机器解析。
6. 基金名单只能来自 `投资者行动/持仓情况.md`，不得靠正文手写回忆补全。
7. 交付前必须逐一对账：目录子链接数、第四章基金卡片数、第七章摘要表行数，三者都必须与当前持仓基金数量一致。
8. 交付前必须逐一对账基金名称：目录、第四章卡片标题、第七章摘要表第一列，必须全部使用与持仓文件一致的"基金名称(代码)"全称。
9. 必须使用 `investment-advice-report-20260517-template.html`，并填充 `fund_cards_json`，让正文基金名称自动挂载悬浮卡片；悬浮卡片最少包含净值、总金额、占比三项。交付判断以页面中可见正文基金名称实际能触发悬浮卡片为准，不能只因源码里存在脚本、class 或 `fund_cards_json` 就视为完成。
10. HTML 不是上一日页面的改写版；第二章到第六章必须显式体现当日新增事实，而不是只复述上一日结论。
11. 当数据基准日与上一日报告相同，HTML 必须明确分开写"今天沿用的静态数据"与"今天新增的新闻 / 风险 / 反向证据"，不得混写成连续叙事。
12. 第二章必须落出当日新增 `item_summaries` 的主要锚点；第五章必须写清"今日新增验证样本数"，禁止沿用上一日验证口径冒充今日结果。
13. 若最终 HTML 不是从 `reference/investment-advice-report-20260517-template.html` 直接填充出来，而是另写的一套页面结构，即使内容正确，也视为交付失败。

### HTML 交付前强制校验

HTML 生成完成后，必须执行 [reference/delivery-checklist.md](reference/delivery-checklist.md) 的**全部检查项（一、二、三、四、五节全跑）**；不得自行删减，也不得只挑"四项硬判定"做抽查后就宣布交付——过往曾出现只验证了硬判定、跳过第三节结构校验（news-item 结构/badge 类名等）就交付的情况，属于流程执行不到位，必须每次无差别跑满五节。

**HTML 增量修改的高危陷阱**：基于已有 HTML（如复用上一轮报告作基座）做局部更新时，**禁止用无差别的全局字符串/正则替换来改日期**（例如 `html.replace("2026-08-13", "2026-08-17")`）。日期字符串会同时出现在"生成日期/标题"和"历史数据表（如北向资金 7 日流水、ETF 多日对比）"两种语境里，全局替换会把历史表里本该保留的原始日期一并篡改，导致数据表乱序/失真且不易发现。正确做法：按 section/字段做定点替换（先用正则截取该 section 的起止边界，只替换该边界内的目标字符串或整体重写该 section 的 innerHTML），对 hero 区的 meta-card、action-board 等"摘要卡片"类内容必须整体重写而非只改标题和一句话导语——曾发生过 hero 区标题/lede 已更新但 meta-card（组合浮盈数值）和 action-board（每日观察重点）仍是上一轮内容，未被替换掉的低级失误。

**交付门槛只有四条硬判定：**

1. `all_name_sets_match == true`
2. `bare_code_violations == 0`
3. `placeholder_residual == 0`
4. 悬浮卡片若在模板中启用，则正文中至少存在可实际触发的基金悬浮卡片，不能只剩静态文本。

任一条件不满足，都不得宣布交付。

HTML 的生成方法、模板扩展、hover 卡片处理等实现细节，统一见 [reference/html-generation-workflow.md](reference/html-generation-workflow.md)。

## 最低交付线

一次完整运行至少应产出：

1. `item_summaries/`
2. `raw_data/`
3. `summary_YYYY-MM-DD.md`
4. `投资建议报告_YYYYMMDD.html`

并满足：

1. 完整 8 持仓日报默认不少于 8 条单条归档。
2. 普通完整日报默认不少于 6 条单条归档。
3. raw_data 中必须存在可回溯单条归档的结构化 JSON。
4. **全部交付物通过裸代码扫描**（违规数 = 0）。

## 参考文档

- [reference/delivery-checklist.md](reference/delivery-checklist.md) - **交付前自检查清单（仅交付检查）**
- [reference/html-generation-workflow.md](reference/html-generation-workflow.md) - HTML 生成、模板扩展、hover 卡片与 `fund_cards_json` 工作流
- [reference/archiving.md](reference/archiving.md) - 归档与单条摘要规则
- [reference/daily-summary-template.md](reference/daily-summary-template.md) - 日报模板
- [reference/historical-data.md](reference/historical-data.md) - 历史读取规范
- [reference/prediction-verification.md](reference/prediction-verification.md) - 信息充分性检查规范
- [reference/search-strategy.md](reference/search-strategy.md) - 搜索层次与范围
- [reference/position-management.md](reference/position-management.md) - 组合内逐基金状态整合
- [reference/nav-analysis.md](reference/nav-analysis.md) - 净值分析与触发线辅助方法
- [reference/directory-structure.md](reference/directory-structure.md) - 目录结构
- [reference/investment-advice-report-20260517-guide.md](reference/investment-advice-report-20260517-guide.md) - HTML 说明
- [reference/investment-advice-report-20260517-template.html](reference/investment-advice-report-20260517-template.html) - HTML 模板文件
- [reference/github-action-news-pipeline.md](reference/github-action-news-pipeline.md) - GitHub Action 新闻采集流水线

## 日常操作顺序

1. 读取投资者画像。
2. 读取历史 summary、最新持仓。
3. 在分析日实际访问并验证前一交易日的沪深京三市收评原文 URL。
4. 带 `--market-turnover-report-url`、`--holdings-file` 运行一次 `fetch_market_momentum.py`；任何必需量能字段未取到即停止。
5. 准备当天 `raw_data/finance_news.json`。
6. 按主链路完成政策、市场行情与量级、宏观搜索，再决定是否补基金本身信息。
7. 分层搜索并即时归档。
8. 执行信息充分性检查。
9. 生成每日 summary。
10. 生成投资建议 HTML 页面。
11. **执行 [delivery-checklist.md](reference/delivery-checklist.md) 全部检查项**，违规数 = 0 方可交付。

---

**版本**：v5.2
**最后更新**：2026-08-17
**维护者**：NagaResst