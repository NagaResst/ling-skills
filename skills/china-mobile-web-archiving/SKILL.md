---
name: china-mobile-web-archiving
description: |
  把中国大陆 mobile web 资源（微信公众号 / 头条号 / 网易号 / 移动门户等）抓取、
  总结、归档到本地 wiki 的标准 workflow。当用户给出 mp.weixin.qq.com /
  mp.toutiao.cn / 3g.163.com / 类似 anti-bot 严格的 mobile web URL，
  要求"抓一下"、"总结"、"归档到 wiki"、"入我的知识库"时第一命中。
  覆盖：anti-bot CAPTCHA 拦截识别（腾讯天御 / 头条风控 / 阿里云盾的差异）、
  多源交叉印证 fallback 策略、wiki frontmatter 合规化、kanban worker 派发
  协议（与 hermes-kanban-dispatch-architecture §12 联合）、产物 confidence
  评估、git 提交规范。**不是**通用 web_extract——专攻被 anti-bot 拦截或
  JS 强渲染的中文 mobile web。

  触发词（第一命中）：
  - "抓这个微信文章"、"总结这篇公众号"、"mp.weixin.qq.com"
  - "头条号归档"、"这篇今日头条"、"3g.163.com"
  - "中文 mobile web 抓不到"、"CAPTCHA 拦截"、"抓取被风控"
  - "把这个 URL 总结并入 wiki"、"整理成一篇 wiki"
  - "多源交叉印证"、"转载源"

  不触发：
  - 普通 web 抓取（→ web_extract / browser_navigate 直接读）
  - 海外站点（→ github-raw-fetch 或通用 web 工具）
  - 通用 wiki 创作（→ wiki skill）
  - 通用 kanban 派发（→ hermes-kanban-dispatch-architecture）
metadata:
  hermes:
    tags: [china, mobile-web, wechat, toutiao, anti-bot, captcha, web-archiving, wiki]
    related_skills: [wiki, hermes-kanban-dispatch-architecture, hermes-self-cli-reference, github-raw-fetch]
---

# China Mobile Web Archiving — 微信/头条/移动门户归档 workflow

## 一句话

> **目标 URL 被 anti-bot 拦截是常态，不是异常**——归档这类资源的标准做法
> 不是"硬抓"，而是"探测主源 + 多源交叉印证 + 标注 confidence + 入 wiki"。
> 必须用 kanban 派发，因为抓取 + 总结 + 写 wiki + commit 是 4 步链路，
> 不适合在主对话 context 里一气呵成。

## §1 — Anti-bot 拦截识别矩阵

| 平台 | URL 模式 | 拦截表现 | 拦截方 | 绕过难度 |
|---|---|---|---|---|
| **微信公众号** | `mp.weixin.qq.com/s/<id>` | 重定向到 `mp/wappoc_appmsgcaptcha` 滑动拼图 | 腾讯天御 CAPTCHA | 中（需 session cookie） |
| **头条号** | `mp.toutiao.cn/mp/item/<id>` | JS challenge + 滑块 | 字节跳动风控 | 高 |
| **网易号 / 移动门户** | `3g.163.com/...` / `news.163.com/...` | IP 限频 + UA 黑名单 | 阿里云盾 / 自研 | 中 |
| **搜狐 / 凤凰移动版** | `m.sohu.com/...` / `ishare.ifeng.com/...` | 直接可读（通常） | — | 低 |
| **知乎专栏** | `zhuanlan.zhihu.com/p/<id>` | 登录态要求 | 知乎反爬 | 高（需登录） |
| **百家号** | `baijiahao.baidu.com/...` | 强 JS 渲染 + 限频 | 百度风控 | 中 |

→ **不要"硬抓"作为唯一策略**。每个 URL 第一步先做"可读性探测"。

## §2 — 可读性探测（30 秒内判断）

```bash
# 1. 试直接 curl 看 HTTP 状态码 + 头
curl -sI -L --max-time 10 "https://mp.weixin.qq.com/s/ZzoqPLYNSAZQB9kfakqQIQ" \
  | head -20
# 期望：200 + 真实 HTML / 实际：302 → captcha URL

# 2. 用 browser_navigate + browser_snapshot
# 如果 snapshot 只看到 "请拖动滑块完成验证" → 确认 CAPTCHA 拦截

# 3. 判定
# - 200 + 真实正文 → 直接抓
# - 200 + "请验证" placeholder → 主源失败，走 fallback
# - 403/429/5xx → 等待 / 走 fallback
```

## §3 — 多源交叉印证 fallback（核心策略）

主源失败时**不要**宣布失败——而是**主动搜同主题转载源**：

```bash
# 1. 提取主源关键词（标题 / 关键人名 / 关键数字）
# 例：原 URL 标题包含 "西安 5·18 特大传销案" → 关键词 = "西安 5·18 传销"

# 2. 多搜索引擎找转载
web_search "西安 5·18 传销"  # 看哪些新闻站转载
# 优先选：news.hsw.cn (华商网)、gov.cn (官方)、人民网 / 新华网

# 3. 抓转载页（这些通常 anti-bot 较松）
curl -s "https://news.hsw.cn/system/2026/0622/1938413.shtml" | w3m -dump

# 4. 至少 2 个独立转载源交叉对比关键事实
# 关键事实一致 → confidence: medium（主源未直读）
# 关键事实矛盾 → 标 contested: true，主张并陈两方
# 仅 1 个转载源 → confidence: low
```

### 转载源优先级

| 来源类型 | 优先级 | 理由 |
|---|---|---|
| 政府官网 / 公安通稿 | ★★★★★ | 权威、anti-bot 弱、可信度最高 |
| 央媒（人民网 / 新华网） | ★★★★ | 权威但转载滞后 |
| 地方都市报（华商报 / 新京报） | ★★★★ | 时效好，通常 anti-bot 弱 |
| 商业门户（搜狐 / 凤凰 / 网易） | ★★★ | 时效好，但有编辑加工 |
| 自媒体 / 内容农场 | ★ | 仅作辅证，不作主源 |

## §4 — Kanban 派发协议（必走）

按 `hermes-kanban-dispatch-architecture` §12 协议发任务，task body **必含**：

```bash
hermes kanban create \
  --body "URL: <目标 URL>

任务目标：
1. 先做可读性探测（§2 三步），明确主源是否可直读
2. 主源可读 → 直接抓全文 + 总结 + 入 wiki
3. 主源被 CAPTCHA 拦截 → 走 §3 多源交叉印证 fallback
4. 写入 ~/SourceCode/wiki/concepts/，命名 wechat-{slug}-{YYYY-MM-DD}.md
5. frontmatter 必须满足 wiki skill §2.1 6 必填字段（title/created/updated/type/tags/sources）
6. confidence 必填：high（主源直读）/ medium（多源印证）/ low（单转载源）

约束：
- 完成后必须先 'hermes kanban comment <id> --body <回报>'，再 'hermes kanban complete <id>'
- 回报必须含：文件绝对路径 / commit hash (short 7) / 文章原始标题 /
  抓取路径（直读 / CAPTCHA + 多源 / 仅单转载）/ confidence 等级
- max-runtime 限制：20 分钟（CAPTCHA 探测很耗时）

返回格式（在 comment 里）：
- 文件绝对路径
- commit hash (short 7 chars)
- 文章原始标题
- 抓取路径：直读 | CAPTCHA + 多源 | 仅单转载
- confidence 等级
- 文章核心 3 条要点" \
  --assignee reader_buddy \
  --priority 5 \
  --max-runtime 1200
```

## §5 — Wiki 产物 frontmatter 模板

```yaml
---
title: <文章原始标题>
created: <ISO 8601 with seconds + timezone>
updated: <ISO 8601 with seconds + timezone>
type: concept
tags: [subsystem, deep-dive, controversy]   # 按文章主题选 tags
sources:
  - <主源 URL，即便未直读也保留>
  - <转载源 1 URL>
  - <转载源 2 URL>
confidence: high | medium | low
contested: true   # 仅当多源矛盾时
---

# <文章标题>

> 来源微信公众号：<公众号名>，原文标题《<原标题>》（<发布日期> 推送）。
> <抓取路径说明：直读 / 被天御 CAPTCHA 拦截后多源印证>

## 1. <500 字摘要>

## 2. 关键要点

- **<维度 1>**：<事实>
- **<维度 2>**：<事实>
- **<维度 3>**：<事实>

## 3. 来源与可靠性

- **原始 <平台>**：<URL>。<可读性说明>
- **<转载源 1>**：<URL>。<内容定位>
- **<转载源 2>**：<URL>。<内容定位>

confidence 标 <level> 的原因：<具体说明>

## 4. 关联页面

- [[<相关 wiki 页>]] —— <关联理由>
```

## §6 — Confidence 评估规则

| 情形 | confidence | frontmatter 必含 |
|---|---|---|
| 主源直读 + 单源 | high | `confidence: high` |
| 主源直读 + 至少 1 个转载交叉印证 | high | `confidence: high` + `sources: [主源, 转载]` |
| 主源 CAPTCHA + ≥2 转载交叉一致 | medium | `confidence: medium` + 来源说明 |
| 主源 CAPTCHA + 仅 1 个转载 | low | `confidence: low` + 主源未读警示 |
| 主源 CAPTCHA + 无转载 | **不入 wiki** | comment 报"无法归档"，不写产物 |
| 多转载源关键事实矛盾 | contested | `contested: true` + 两方主张并陈 |

## §7 — Slug 命名规范

文件名 slug 必须英文化（ascii），避免 CJK：

```python
import re
def slugify_zh_title(title: str) -> str:
    # 例: '西安 5·18 特大传销案破了' → 'xian-518-te-da-chuan-xiao-an'
    # 不能 pinyin 全自动（缺词库），手动从 desc / 标题提取关键词后人工/半自动 slug 化
    pass
```

约定：
- 取主源 title / desc 字段前 5 个关键词
- 中文人名 → 拼音（保留姓 + 名首字母）
- 数字直接保留（5·18 → 518）
- 用 `-` 连接，全小写
- 例：`wechat-xian-518-te-da-chuan-xiao-an-2026-06-27.md`

## §8 — 已知平台的可见元数据技巧

**微信公众号主源即使被 CAPTCHA 拦截，metadata 仍可读**：
- title
- desc（摘要前 200 字，常含事实线索）
- create_time（Unix 秒）
- publish 账号

获取方式：
```bash
# 浏览器抓 HTML 后看 <meta> 标签
curl -s "https://mp.weixin.qq.com/s/ZzoqPLYNSAZQB9kfakqQIQ" \
  | grep -oE '<meta[^>]+>' | head -20
# 或用 browser_console.expression 读 window.__INITIAL_STATE__
```

这些元数据**足以辅助 fallback 搜转载源**，不要因为正文被拦截就放弃。

## §9 — Verification Checklist

派发任务前：
- [ ] 任务 body 含 §4 必含条款
- [ ] 设 `--max-runtime`
- [ ] confidence 评估规则 §6 已写进 body
- [ ] worker poll 计划已定（建议 2 min 间隔）

worker 回报后：
- [ ] commit 存在（git log 看 hash）
- [ ] frontmatter 6 字段齐（wiki skill §2.1）
- [ ] confidence 字段合理
- [ ] index.md 已 patch（wiki skill §3.1）
- [ ] 单独 commit（feat + docs 分开）

## §10 — Pitfalls

1. **不要硬抓 CAPTCHA**——主源失败就走 fallback，不要尝试"换 UA /
   换 IP / 装 cookie"——这是持久战，不在归档 workflow 范围。
2. **不要把"主源未读"的产物标 high**——即便转载源很多，主源没直读
   就降一档，这是诚实标注。
3. **不要用 web_search 替代 web_extract**——搜索引擎给你摘要，**不是
   原文**。要原文必须 `curl` 或 `browser_navigate`。
4. **不要在 wiki 页 frontmatter 里给单数 `source:`**——SCHEMA.md 要求
   `sources:` 复数（详见 wiki skill references/frontmatter-field-name-gotchas.md）。
5. **不要把多转载源当主源**——转载可能有编辑加工，事实细节可能丢，
   关键事实必须多源交叉印证，不能依赖单转载。
6. **不要跳过 §2 可读性探测**——直接发任务让 worker 自由发挥，结果
   不可控。
7. **不要忘了 index.md patch**——wiki skill §3.1C 4 元素必含。
8. **不要忘了 commit 后给 worker 回报路径**——worker 不知道 wiki 提交
   规范，会写出不合规的产物。
9. **worker 搜同关键词找到不相关文章（2026-06-27 实测陷阱）**——
   多源交叉印证 fallback 时，worker 用 `web_search "<关键词>"` 找转载
   可能搜到**主题无关但碰巧含相同关键词**的文章。**实测案例**：
   抓 `mp.weixin.qq.com/s/ZzoqPLYNSAZQB9kfakqQIQ`（达沃斯李强演讲），
   worker 撞 CAPTCHA 后搜 "西安 5·18 传销" 类关键词，找到一篇完全不相关
   的"西安 5·18 特大传销案通报"就当转载源交差。
   **修正**：发包方 task body 必须**显式列出预期文章的独有标识**：
   - 原始标题（精确字符串）
   - 发布账号（公众号名）
   - 发布日期
   - 一两个不可能误中的关键词（如人名、机构名）
   - 期望转载源的发布渠道（"政府官网" / "华商网" / "新华网"）
   worker 在 fallback 阶段必须先**对比这些标识**确认转载源真在讲同一事件，
   关键词重叠不够。**发包方要在 task body 里写**：
   ```
   fallback 阶段对比主源与转载源的以下独有标识，至少 3 项一致才接受：
   - 标题相似度（>70%）
   - 发布日期相近（±3 天）
   - 至少一个具体人名 / 机构名 / 数字一致
   - 事件类型一致（不是同名事件）
   不满足的转载源丢弃，不要凑数。
   ```
   这是 §3 多源交叉印证的**真坑**——关键词命中 ≠ 同一文章。
10. **worker 在 fallback 完成后必须先确认主题相关再写产物**——worker
    写 wiki 文件之前**必须**用 task body 列出的"独有标识"对照一次，
    确认转载源确实在讲同一事件。**实测反例**：worker 整理完西安传销案
    内容后写 frontmatter 时标了 `confidence: medium` 并写"微信原页面被拦截，
    取转载源"——但**完全没核对转载源是否在讲达沃斯李强演讲**。发包方
    在 accept 产物前必须自检："frontmatter 引用的转载源 vs 产物正文讲
    的事件 vs 用户原 URL 标题——三者是否同一件事？"

## §11 — 关联 skill

- `wiki` —— 通用 wiki 创作规范（frontmatter / index.md / commit）
- `hermes-kanban-dispatch-architecture` —— §12 发包方纪律（必走）
- `hermes-self-cli-reference` —— hermes kanban create CLI 精确参数
- `github-raw-fetch` —— GitHub 资源的中国大陆网络绕过（不直接相关，
  但属同类型问题：anti-CDN/anti-bot 资源获取策略）