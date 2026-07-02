# 仓位诊断与调仓建议 HTML 模板说明

这个模板服务的是**组合前置诊断页面**，不是替代单持仓报告本体。

适用场景：

1. 用户不喜欢 Markdown，希望把“当前仓位诊断 -> 逐基金是否适合当前仓位 -> 最终调仓/换产品结论”交付成正式 HTML 页面。
2. 需要先把组合层诊断单独展示，再进入后续单持仓研究。
3. 希望沿用当前仓位分析与建议体系的视觉语言，但页面结构比多持仓日报更聚焦。

对应模板：`reference/position-diagnosis-report-template.html`

建议输出路径：

`投资者行动/持仓分析与建议/仓位诊断与调仓建议_YYYYMMDD.html`

## 页面结构

模板固定四段：

1. Hero：一句话总诊断 + 三张信号卡 + 四个关键指标。
2. 当前仓位诊断：结构调仓指令区、三个动作步骤、当前/目标双环图、画像约束、结构问题。
3. 逐基金判断：先给动作总览卡，再按“优先处理 / 停止追加 / 结构保留 / 待补判断”四组展示基金。
4. 直接执行：只保留“需要调仓 / 待补数据 / 要用钱先出 / 有新钱先去”四块；其中需要调仓必须直接给出仓位金额参考，最后落到最短结论。

这个顺序要保持不变，因为用户想先知道“组合哪里不对、先动什么”，再看“单只基金怎么处理”。

第一章现在默认使用 ECharts 做可视化增强，适合静态 HTML 归档页，不需要额外构建流程。

## 必填占位符

最少需要填这些字段：

1. `{{hero_title}}`
2. `{{hero_lede}}`
3. `{{report_date}}`
4. `{{holdings_count}}`
5. `{{portfolio_diagnosis}}`
6. `{{priority_action}}`
7. `{{signal_1_title}}` / `{{signal_1_body}}`
8. `{{signal_2_title}}` / `{{signal_2_body}}`
9. `{{signal_3_title}}` / `{{signal_3_body}}`
10. `{{allocation_gap_badges_html}}`
11. `{{profile_constraints_html}}`
12. `{{structure_findings_html}}`
13. `{{current_pie_title}}` / `{{current_pie_lede}}` / `{{current_pie_center}}`
14. `{{target_pie_title}}` / `{{target_pie_lede}}` / `{{target_pie_center}}`
15. `{{current_allocation_json}}`
16. `{{target_allocation_json}}`
17. `{{action_summary_cards_html}}`
18. `{{priority_group_title}}` / `{{priority_group_lede}}` / `{{priority_fund_cards_html}}`
19. `{{control_group_title}}` / `{{control_group_lede}}` / `{{control_fund_cards_html}}`
20. `{{keep_group_title}}` / `{{keep_group_lede}}` / `{{keep_list_html}}`
21. `{{pending_group_title}}` / `{{pending_group_lede}}` / `{{pending_fund_cards_html}}`
22. `{{rebalance_reference_html}}`
23. `{{pending_names}}`
24. `{{liquidity_order_names}}`
25. `{{add_funds_order_names}}`
26. `{{bottom_line_html}}`

其中两段 JSON 需要直接输出合法 JSON 数组，供第一章双环图和外侧图例读取：

1. `{{current_allocation_json}}`：每个资产层至少包含 `name`、`value`、`amount`、`color`。
2. `{{target_allocation_json}}`：每个资产层至少包含 `name`、`value`、`amount`、`color`。

目录相关：

1. 左侧目录固定指向 `动作总览 / 优先处理 / 停止追加 / 结构保留 / 待补判断` 五个锚点，不再按每只基金展开。
2. 动作总览卡里的数量，必须和各动作分组里的基金卡片数或列表项数一致。

## 基金卡片写法

每张卡片建议沿用这套语法：

1. 当前建议
2. 什么时候动作
3. 判断理由
4. 事实依据
5. 信息边界

第二章现在不建议再把所有基金先做成一张重表。更合适的做法是：

1. 先用 `{{action_summary_cards_html}}` 输出四条纵向摘要行，不要再做并排高低不齐的概览卡。每条摘要卡必须包含三个子元素：`<div>` (label+value) + `<div></div>` (spacer) + `<p>` (描述文字)。缺了 spacer `<div></div>` 会导致 `<p>` 被塞进 72px 的第二列，文字极窄。正确结构：`<article class="action-summary-card priority"><div><span class="label">优先处理</span><span class="value">2</span></div><div></div><p>描述文字</p></article>`
2. 再把重心最高的基金放进 `{{priority_fund_cards_html}}`，每只基金占一整行，左侧放身份和判断，右侧放决策理由。
3. 把逻辑仍成立但需要“停止追加”的放进 `{{control_fund_cards_html}}`，保持同样的全宽行动卡结构。
4. 把暂时不动的基金压缩成 `{{keep_list_html}}`，建议直接输出 `<article class="keep-item"><strong class="keep-name">基金名称(代码)</strong><span class="keep-note">一句话保留理由</span></article>`，放进模板内置的 `keep-stack` 容器，不要再复用通用列表样式。
5. 把数据未补齐但方向匹配的基金单列到 `{{pending_fund_cards_html}}`，不要和优先处理组混排。

模板里的 `{{fund_cards_html}}` 建议直接填多张 `<article class="fund-card">...</article>`。

第三章现在只保留真正要执行的内容：

1. `{{rebalance_reference_html}}`：只放需要调仓的基金，并直接写成 `<p class="name-line">基金名称(代码)：当前约 X 元，调仓参考 Y 元</p>`。
2. `{{pending_names}}`：只放“待补数据”的基金名字。
3. `{{liquidity_order_names}}`：只写卖出顺序，用 `->` 串起来。
4. `{{add_funds_order_names}}`：只写新增资金顺序，用 `->` 串起来。
5. 不要再把“暂不加仓”或“先不动”单独放进第三章。
6. 不要解释原因，不要写判断句，不要补背景复述。

最小骨架如下：

```html
<article class="fund-card" id="fund-003984">
  <div class="fund-header">
    <div>
      <h3>嘉实新能源新材料股票A(003984)</h3>
      <span class="fund-role">观察仓</span>
    </div>
  </div>

  <div class="fund-meta">
    <div class="meta-box">
      <span class="label">当前仓位判断</span>
      <span class="value">合适</span>
    </div>
    <div class="meta-box">
      <span class="label">当前建议</span>
      <span class="value">继续观察</span>
    </div>
    <div class="meta-box">
      <span class="label">是否换产品</span>
      <span class="value">否</span>
    </div>
  </div>

  <ul class="decision-list">
    <li><strong>什么时候动作</strong>只有在确认重新转强后再讨论恢复仓位。</li>
    <li><strong>判断理由</strong>当前仓位已压到观察仓级别，不再拖累组合。</li>
    <li><strong>事实依据</strong>最新持仓约占总资产 0.95%，近 1 月与高点回撤仍弱。</li>
    <li><strong>信息边界</strong>没有新增基金直接催化，不支持恢复主动仓。</li>
  </ul>
</article>
```

其中 `{{fund_cards_json}}` 是一个 JSON 数组，用于正文基金名称悬浮卡片自动注入。每个元素必须包含以下字段：

| 字段 | 说明 | 示例 |
|------|------|------|
| `full` | 基金全名(代码)，用于文本匹配 | `"财通新视野灵活配置混合A(005851)"` |
| `name` | 基金简称（悬浮卡片标题） | `"财通新视野灵活配置混合A"` |
| `code` | 6 位代码 | `"005851"` |
| `nav` | 最新净值，格式为「净值 日期」 | `"1.2345 06-30"` |
| `amount` | 当前金额 | `"5,823.41 元"` |
| `weight` | 总资产占比 | `"6.25%"` |
| `action` | 当前建议 | `"继续持有"` |

其中 `nav` 的日期取 market_momentum 或 analysis_snapshot 中 `official_nav` 对应的 `nav_date`（MM-DD 格式）。

## 交付前校验

HTML 交付前至少对这四件事：

1. 当前/目标双环图和两侧金额图例是否共享同一套资产层定义。
2. 动作总览数字、分组基金卡片数/列表项数、左侧目录分组锚点是否一致。
3. 所有基金名称是否统一使用“基金名称(代码)”。
4. “判断理由”和“事实依据”是否分开，没有混写。
5. 第三章是否已经删掉“暂不加仓”和“先不动”两类名单，只保留真正要执行的项目。
6. 需要调仓的基金是否都带了仓位金额参考，而且金额口径和正文同一天数据一致。
7. 第三章的两条资金路径是否和第二章结论一致，没有把“停止追加”组写进新增资金入口。