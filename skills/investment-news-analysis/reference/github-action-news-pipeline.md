# GitHub Action 新闻采集流水线

## 文件位置

`.github/workflows/news-collection.yml`（在 make-little-money 仓库根目录）

## 运行机制

- **触发**：每天北京时间 01:00（UTC 17:00 前一天）定时 + 手动 workflow_dispatch
- **运行环境**：ubuntu-latest, Python 3.12
- **脚本来源**：从 `https://github.com/NagaResst/ling-skills.git` 克隆 `cn_finance_news.py`（不依赖 make-little-money 仓库内的 scripts/ 目录）

## 核心逻辑链

### 1. 查找最新归档日期

扫描 `投资新闻归档/` 下所有 `finance_news.json` 文件，用 sed 从路径提取日期：

```bash
LATEST_ARCHIVE=$(find "投资新闻归档" -name "finance_news.json" -type f 2>/dev/null | \
                 sed -n 's|.*/\([0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}\)/raw_data/finance_news.json|\1|p' | \
                 sort -r | head -n 1)
```

**历史 bug（2026-06-30 修复）**：原逻辑扫描 `summary_*.md` 文件名提取日期，导致某天只有 finance_news.json 但没写 summary 时，下次 Action 会重复采集并覆盖已有数据。修复后改为扫描 `finance_news.json`。

### 2. 计算采集天数

```bash
DIFF_DAYS=$(( (TODAY_SECONDS - LAST_SECONDS) / 86400 ))
DAYS=$(( DIFF_DAYS + 1 ))  # +1 包含归档当天
```

### 3. 执行采集

```bash
python3 ling-skills/skills/investment-news-analysis/scripts/cn_finance_news.py --days $DAYS
```

脚本输出到 `~/finance_news_latest.json`。

### 4. 复制到归档目录

```bash
TARGET_DIR="投资新闻归档/${YEAR_MONTH}/${CURRENT_DATE}/raw_data"
cp ~/finance_news_latest.json "${TARGET_DIR}/finance_news.json"
```

### 5. Commit + Push

自动 commit 消息格式：`📰 自动采集投资新闻 (YYYY-MM-DD)`

## 常见故障排查

| 现象 | 可能原因 | 排查步骤 |
|------|---------|---------|
| 当日目录无 finance_news.json | Action 未触发 / push 失败 | 检查 GitHub Actions 运行记录 |
| finance_news.json 内容与前一天完全相同 | 归档日期查找逻辑错误（旧 bug） | 确认 workflow 已更新为检查 finance_news.json |
| 采集天数过多导致重复新闻 | 最新归档日期识别错误 | 手动验证 `find` 命令在归档目录上的输出 |
| cn_finance_news.py 脚本报错 | ling-skills 仓库脚本被修改 | 克隆 ling-skills 仓库本地运行脚本测试 |

## 验证方法

在 make-little-money 仓库根目录运行：

```bash
# 验证归档日期查找逻辑
find "投资新闻归档" -name "finance_news.json" -type f 2>/dev/null | \
  sed -n 's|.*/\([0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}\)/raw_data/finance_news.json|\1|p' | \
  sort -r | head -n 1

# 应输出最新已有 finance_news.json 的日期，而非最新 summary 的日期
```
