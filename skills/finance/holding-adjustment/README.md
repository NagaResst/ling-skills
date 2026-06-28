# holding-adjustment Skill

> ⚠️ **免责声明**：本工具仅供个人学习和信息整理使用，所有分析内容均不构成任何投资建议。投资有风险，入市需谨慎，请依据自身判断做出投资决策。

组合仓位调整的**统一入口**。三层架构：

- **Layer 1 — 组合前置诊断**（所有动作必经）：画像校准 + 持仓快照 + 仓位变化来源表
- **Layer 2 — 整体再平衡**：4 档框架 + 时代主题修正 + 拆解标的 + 画像补丁
- **Layer 3 — 单只基金操作**：含费成本/止盈止损/置换/去重补缺

## 适用场景

1. 想知道某只基金该不该继续拿 → Layer 1 + Layer 3
2. 想知道整体组合要不要调 4 档比例 → Layer 1 + Layer 2
3. 想按波动率档换债基 → Layer 1 + Layer 3
4. 想按产业链定位基金方向 / 补 AI 算力链某段暴露 → Layer 1 + Layer 3

## 不适用场景

1. 新基金首次研究 → 用 `fund-deep-research`
2. 全组合日报与新闻归档主流程 → 用 `investment-news-analysis`

## 默认输入

1. `投资者行动/投资者画像.md`
2. `投资者行动/持仓情况.md`
3. `投资新闻归档/YYYY-MM/YYYY-MM-DD/raw_data/market_momentum_YYYY-MM-DD.json`
4. `投资新闻归档/YYYY-MM/YYYY-MM-DD/raw_data/analysis_snapshot_YYYY-MM-DD.json`
5. 同一分析日其他必要 `raw_data/*.json`

## 默认输出

| 路径 | 何时使用 |
|------|---------|
| `投资者行动/单持仓分析/基金名称(代码)_YYYY-MM-DD.md` | Layer 3 单基金报告（默认） |
| `投资者行动/持仓分析与建议/调仓建议_YYYYMMDD.md` | Layer 2 整体调仓对账 |
| `投资者行动/持仓分析与建议/仓位诊断与调仓建议_YYYYMMDD.html` | Layer 1 + Layer 2 组合诊断页 |

## 核心原则

**先确认后计算，每步对账，每层闭环。用户是决策者，AI 是计算器和数据收集员。**

进入任何一层之前，**必须先走 Layer 1**（组合前置诊断）。

## 核心建议固定语法（Layer 3 输出）

```markdown
## 核心建议

- 当前建议：
- 什么时候动作：
- 判断理由：
- 事实依据：
- 信息边界：
```

这五项缺一不可。

## 参考文档

- [reference/research-spec.md](reference/research-spec.md) - 强制研究顺序 / 五类必答信号 / 输出结构
- [reference/fee-tiers.md](reference/fee-tiers.md) - A/C 类赎回费档位与含费成本公式
- [reference/ai-computing-chain.md](reference/ai-computing-chain.md) - AI 算力 5 段产业链框架与补缺候选
- [reference/low-wave-bond-funds.md](reference/low-wave-bond-funds.md) - 5% 波动率以内的低波固收+置换档位
- [reference/position-diagnosis-report-guide.md](reference/position-diagnosis-report-guide.md) - HTML 组合诊断模板说明
- [reference/position-diagnosis-report-template.html](reference/position-diagnosis-report-template.html) - HTML 组合诊断页模板

---

**版本**：v2.0 (2026-06-28)  
**维护者**：NagaResst

## 更新日志

- v2.0 (2026-06-28)：吸收 single-holding-adjustment（7 条铁律 + 含费成本公式 + AI 算力链 5 段 + 低波固收+置换表）和 fund-portfolio-rebalancing（4 档框架 + 主题修正 + 板块基分类 + 限购检查 + 画像补丁）。改为三层入口（组合前置诊断 → 整体再平衡 → 单只基金操作）。
- v1.0 (2026-05-26)：首版，建立"以组合前置诊断为前提的单持仓逻辑校验"工作流