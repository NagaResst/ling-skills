# nav-cycle-analysis

基金净值周期分析与中期趋势预测 Skill。

## 核心能力

- **周期识别**：从5年历史净值中识别完整涨跌周期，统计平均时长/振幅/回撤
- **阶段定位**：判断当前净值处于周期的哪个阶段（筑底/初涨/加速/高位/下跌）
- **政策映射**：建立政策事件与净值变化的因果关系库，量化不同政策类型的历史影响
- **市场关联**：整合 ETF 申赎、北向资金、板块强弱、融资余额等市场活动信号
- **中期预测**：基于三维信号合成，输出4–12周方向预测（基准/乐观/悲观三情景）

## 与其他 Skill 的区别

| Skill | 预测周期 | 核心方法 | 主要用途 |
|-------|---------|---------|---------|
| investment-news-analysis | 1–4 周 | 新闻 + 情绪 | 每日日报、短期催化 |
| **nav-cycle-analysis** | **4–12 周** | **统计周期 + 事件回测** | **中期方向判断** |
| fund-deep-research | 长期 | 基本面研究 | 选基、建仓决策 |

## 文件结构

```
nav-cycle-analysis/
├── SKILL.md                        # 主流程（从这里开始读）
├── README.md                       # 本文件
└── reference/
    ├── data-collection.md          # 净值数据采集规范
    ├── cycle-detection.md          # 周期识别算法
    ├── policy-event-mapping.md     # 政策事件影响量化
    └── prediction-engine.md        # 三维信号合成 → 预测结论
```

## 归档路径

```
净值周期分析/
├── index.json
└── {基金代码}/
    ├── nav_history.json
    ├── policy_events.json
    └── reports/
        └── cycle_report_YYYY-MM-DD.md
```
