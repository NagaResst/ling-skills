# 历史数据引用规范

## 核心目标

历史数据读取的用途只有三个：

1. 找到上一轮 summary 的有效判断、风险边界和观察重点。
2. 对比最近可比较 summary 与最新 `持仓情况.md`，判断是否发生份额变化。
3. 为本轮动作判断提供最近可比较基准。

## 读取顺序

每次分析开始前，按以下顺序读取：

1. `投资新闻归档/index.json`
2. 与当前持仓相关的近 1-4 周 summary
3. `投资者行动/持仓情况.md`

## 重点读取什么

### 从 `index.json` 读取

至少提取：

- `date`
- `file_path`
- `funds_mentioned`
- `item_count`

目的：

1. 找到可验证的历史 summary。
2. 过滤出与当前持仓相关的文件。

### 从历史 summary 读取

优先提取以下章节：

1. `一、核心指标速览与横向对比`
2. `五、复盘与风险雷达`
3. `六、逐基金状态复核与操作建议`
4. `七、今日关注要点`
5. `八、数据附录`

不要再假设历史日报一定带有旧版量化表和第三方观点章节。

### 从 `持仓情况.md` 读取

提取：

1. 基金名称
2. 基金代码
3. 份数
4. 持仓成本

## 历史读取的标准产物

读取完成后，当前轮次至少应形成以下上下文：

1. 最近一个可比较历史 summary 的日期。
2. 当前持仓与最近可比较 summary 的份额差异。
3. 上一轮哪些判断仍有效，哪些需要复核。

## 示例：读取历史 summary

```python
import json

def load_recent_summaries(index_path, target_funds):
    with open(index_path, "r", encoding="utf-8") as file:
        index = json.load(file)

    result = []
    for item in index.get("summaries", []):
        mentioned = set(item.get("funds_mentioned", []))
        if mentioned.intersection(target_funds):
            result.append(item)
    return result
```

## 读取时的处理原则

1. 读取不到历史文件时，明确写"无历史数据可供参考"。
2. 章节缺失时，标注缺失，不要反推内容。
3. 中间某天没有日报归档时，可以向前选择最近可比较基准，但必须写明原因。
4. 优先读取最近、且确实提到当前持仓的 summary。

## 不再作为默认读取目标的旧字段

以下字段不再作为历史读取的默认主目标：

- 旧版情绪打分字段
- 旧版资金汇总表
- 第三方评级变化表
- 个股层跟踪章节

如果历史文件中恰好存在这些信息，可作为补充背景，但不能再依赖它们定义当前日报结构。
