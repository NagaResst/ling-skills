---
name: china-mobile-web-archiving
topic: wechat-archive-session-2026-06-27
version: 1.0.0
created: 2026-06-27
source: 2026-06-27 实际 session（任务 t_4ae317ae）
status: archived   # 内容已沉淀，session 本身不再演进
---

# Wechat Archive Session 2026-06-27 — 案例参考

> 本文档记录一次典型的"用户给微信 URL，要求抓取 + 总结 + 入 wiki"会话
> 的完整链路、坑点、最终结果。供未来同类任务对照。

## 任务输入

```
URL: https://mp.weixin.qq.com/s/ZzoqPLYNSAZQB9kfakqQIQ
用户原话: "把这个通过看板发给 read buddy，让他帮我总结一下，
放到我的 wiki 里边。"
```

## 实际链路

```
T+0:00  用户在微信端发指令
T+0:30  发包方（主对话 hermes）确认 read_buddy 是 kanban assignee
T+0:35  发包方写出 task body（缺 fallback、缺回报强制）
T+0:35  hermes kanban create → t_4ae317ae, assignee=reader_buddy
T+0:35  reader_buddy worker spawn (pid 794192, ~5 秒内 claim)
T+0:35  worker browser_navigate URL
T+1:00  worker 撞腾讯天御 CAPTCHA → 自己尝试用 news.hsw.cn / sohu 转载源
T+5:00  worker 抓到华商网 1938413 + 搜狐 1039307152_121443915 转载
T+8:00  worker 整理 500 字摘要 + 关键要点
T+10:00 worker 写 wiki concepts/wechat-xian-518-te-da-chuan-xiao-an-2026-06-27.md
T+11:00 worker git add + git commit (commit 74aad03)
T+13:00 worker exit 0, **没调 kanban_complete 或 kanban_comment**
T+13:00 dispatcher 收 result_len=0 → protocol_violation → gave_up
T+13:00 自动重试 spawn run #2
T+14:25 run #2 完成 85 秒空跑 → completed (result_len=0)
T+14:25 archived
T+14:25 **用户发现"完全失败"**

发包方（主对话 hermes）从未 poll 进度 → 14 分钟内没发现实际产物已写入
```

## 实际产物

commit `74aad03` 写了：
- `concepts/wechat-xian-518-te-da-chuan-xiao-an-2026-06-27.md`（57 行，concept）
- `index.md`（Concepts 区 +1 行 + Total pages 30→31 + 时间戳）

**产物内容审计**：

| 维度 | 评级 | 说明 |
|---|---|---|
| 内容真实性 | ✓ | 没用 LLM 编造，三源转载交叉印证 |
| confidence 标注 | ✓ | frontmatter 标 `confidence: medium`，正文第 47 行解释原因 |
| 多源印证明示 | ✓ | 第 18 行明示"微信原页面被腾讯天御 CAPTCHA 拦截"，列 3 转载源 |
| frontmatter 字段名 | ✓ | `sources:` 复数用对了，6 字段齐 |
| 抓取挑战记录 | ✓ | 第 56 行明记 CAPTCHA 详情 + slug 来源 |
| wiki 合规 | 略低 | 加了 `confidence` / `updated`（允许但非必填） |

**结论**：产物实际**不差**，是诚实的 fallback 实施。但**发包方没及时发现 = 用户
以为失败**。

## 复盘：本任务失败点不在产物，在协议

| 失败点 | 根因 | 修正路径 |
|---|---|---|
| 发包方没 poll | 习惯放羊 | 走 hermes-kanban-dispatch-architecture §12.4 poll 纪律 |
| task body 没强制回报 | 默认信任 worker 自发完成 | §12.2 双步锁（comment + complete） |
| task body 没 fallback | 默认信任 worker 自发 fallback | §12.3 fallback 决策树必含 |
| 没设 max-runtime | 没意识到 worker 会僵死 | §12.1 五条款必含 |
| worker 没调 kanban_complete | 没意识到 dispatcher 把这当 protocol violation | §12.2 写入任务模板 |
| worker 没在 comment 回报 | 同上 | §12.1 必含 comment 必填字段 |

## lesson → skill 沉淀

| lesson | 沉淀到 |
|---|---|
| 发包方 5 条款 | hermes-kanban-dispatch-architecture §12.1 |
| protocol violation 实际案例 | hermes-kanban-dispatch-architecture §12.5 |
| poll 监控纪律 | hermes-kanban-dispatch-architecture §12.4 |
| 多源交叉印证 fallback | china-mobile-web-archiving §3 |
| frontmatter 字段名易错 | wiki references/frontmatter-field-name-gotchas.md |
| confidence 评估规则 | china-mobile-web-archiving §6 |
| 微信 metadata 即使 CAPTCHA 也可读 | china-mobile-web-archiving §8 |

## 后续建议

1. **永久**：发包方发 kanban 任务前**复制 §4 task body 模板**，不要手写
2. **永久**：发包方发任务后**立刻起 2 min 间隔 poll**，建议用 cronjob
3. **永久**：wiki 产物审计必须跑 verify_wiki_pages.py
4. **可选**：在 `hermes-kanban-dispatch-architecture` 加一个
   `templates/kanban-task-body-template.md` 提供 copy-paste 模板
5. **可选**：写一个 `china-mobile-web-archiving` 的脚本自动探测
   平台 + 触发 fallback（避免每次手动判断）

## 本 session 任务处理建议（用户当前问的事）

产物 commit `74aad03` 已经写入（worker 写完 → commit → 没用 kanban_complete）
但有 3 个 action item 待用户决定：

1. **保留产物但修 frontmatter** —— `confidence` 移到标准字段，
   加 `source_url` 字段（合并 raw/articles 标准）
2. **保留产物 + 完整重写** —— 删 worker 写的，agent 重新写一遍合规版本
3. **删除整个产物** —— `git revert 74aad03` + kanban task unlink

**建议方案 1**（最低破坏路径）。