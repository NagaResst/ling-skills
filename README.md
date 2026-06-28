# ling-skills

个人 Hermes Agent 自定义 skill 仓库。集中存放非官方、非内置的 skill，统一走 git 版本控制。

## 与 Hermes 的关系

本仓内的 skill 通过 `~/.hermes/config.yaml` 的 `skills.external_dirs` 字段挂载到 Hermes skill 加载器。

```yaml
skills:
  external_dirs:
    - ~/SourceCode/ling-skills/skills/
```

挂载后行为：
- 出现在 `hermes skills list` 输出中
- 受 `skills.disabled` 配置控制启用/禁用
- 受 `skills.guard_agent_created` 策略控制
- metadata 写入 `~/.hermes/skills/.usage.json`

⚠️ **local 优先于 external_dirs**（同名的 skill，`~/.hermes/skills/` 覆盖本仓）。迁入新 skill 后**必须删除 `~/.hermes/skills/` 下同名副本**，否则启用的是旧版而不是本仓最新版。

## 目录结构

```
ling-skills/
├── README.md          # 本文件
├── .gitignore
└── skills/            # 扁平布局（无 category 子目录）
    ├── _template/     # 新 skill 的复制起点（占位 README）
    └── <skill-name>/  # 一个 skill 一个目录
        ├── SKILL.md   # 必填，含 frontmatter + body
        ├── references/ # (可选) 引用文档
        └── scripts/    # (可选) 伴随脚本
```

## 当前 skill 清单（9 个）

### 💰 金融研究（4 个，从 make-little-money 迁出）

| Skill | 用途 |
|-------|------|
| `holding-adjustment` | 组合仓位调整统一入口（前置诊断 + 4 档再平衡 + 单只基金操作）；处理该不该继续拿、整体调档、按波动率换债基、补 AI 算力链暴露 |
| `investment-news-analysis` | 持仓监控 + 量化调仓建议系统（多持仓组合的新闻收集、日报生成、预测验证、组合级建议） |
| `fund-deep-research` | 基金深度研究助手（akshare 抓数据 + 联网搜索补全 + 风险指标 + 完整研究报告生成）；**脚本数据缺失时必须联网搜索补全** |
| `nav-cycle-analysis` | 基金净值周期分析与 4–12 周趋势预测（顶/底识别 + 政策红利映射 + 市场信号关联 + 多维度预测报告） |

### 🔬 研究（2 个，从 ~/.hermes/skills 迁出）

| Skill | 用途 |
|-------|------|
| `bilibili-message-extractor` | 抓取 Bilibili 回复 / @ / 私信（用 SESSDATA / bili_jct / buvid3 环境变量） |
| `china-mobile-web-archiving` | 抓取中国大陆 mobile web 资源（微信公众号 / 头条号 / 网易号 / 移动门户），归档到本地 |

### 📝 生产力（1 个）

| Skill | 用途 |
|-------|------|
| `doc-lifecycle` | 文档全生命周期管理（4 场景入口 → 验证 → 评分 → 进化；新建体系、研读升级、批量评分、版本重写） |

### 🧑‍🎨 内容创作（1 个）

| Skill | 用途 |
|-------|------|
| `character-building-guide` | LLM 人设构建方法论（核心心法：只演不想、画面感、官方设定优先；附「阮·梅」崩坏：星穹铁道示例角色） |

### 🛠 软件开发（1 个）

| Skill | 用途 |
|-------|------|
| `four-phase-coding-workflow` | 4 阶段校正工作流（校验实施文档 → 编码 → 再校验 → 父 agent 反查总结）；用于「以上游文档为依据」的高审计任务，**忠实执行不自由发挥** |

## 新增 skill 流程

1. `cp -r skills/_template skills/<skill-name>/`
2. 编辑 `SKILL.md`，按 `hermes-agent-skill-authoring` skill 的规则写 frontmatter + body
3. 写完后跑 hermes 自带 validator：
   ```bash
   python3 -c "
   import re, yaml
   from pathlib import Path
   t = Path('skills/<skill-name>/SKILL.md').read_text()
   assert t.startswith('---')
   m = re.search(r'\n---\s*\n', t[3:])
   fm = yaml.safe_load(t[3:m.start()+3])
   assert 'name' in fm and 'description' in fm
   assert len(str(fm['description'])) <= 1024
   assert len(t) <= 100000
   print('PASS')
   "
   ```
4. `git add skills/<skill-name>/ && git commit && git push`

⚠️ **frontmatter 中 `description` 是必填字段**——它会被 hermes 用来自动匹配何时加载这个 skill。**trigger 写法**：英文 skill 以 "Use when ..." 开头，中文 skill 用适用/不适用 + 触发词列表。

## 维护纪律

- **skill 命名**：小写 + 连字符，≤64 字符
- **frontmatter 硬要求**：`name` + `description`（hermes validator 强制）
- **frontmatter 建议字段**：`version` / `author` / `license` / `metadata.hermes.tags`
- **description 长度**：≤1024 字符
- **总文件大小**：≤100 KB（超过应拆 `references/`）
- **body 结构**：建议 `## Overview` + `## When to Use` + `## Common Pitfalls` + `## Verification Checklist`

## 迁移历史

| 日期 | 来源 | 迁入 skill |
|------|------|----------|
| 2026-06-28 | `make-little-money/skills/` (submodule) | `holding-adjustment`, `investment-news-analysis`, `fund-deep-research`, `nav-cycle-analysis` |
| 2026-06-28 | `~/.hermes/skills/` (本地副本) | `bilibili-message-extractor`, `china-mobile-web-archiving`, `doc-lifecycle`, `character-building-guide`, `four-phase-coding-workflow` |

迁入后必须删除源仓库 / `~/.hermes/skills/` 下的同名副本（详见顶部「与 Hermes 的关系」警告）。
