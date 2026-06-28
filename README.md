# ling-skill

个人 Hermes Agent 自定义 skill 仓库。集中存放非官方、非内置的 skill，统一走 git 版本控制。

## 与 Hermes 的关系

本仓内的 skill 通过 `~/.hermes/config.yaml` 的 `skills.external_dirs` 字段挂载到 Hermes skill 加载器。

```yaml
skills:
  external_dirs:
    - ~/SourceCode/ling-skill/skills/
```

挂载后，本仓 skill 与 `~/.hermes/skills/` 下 skill 等价：
- 同样出现在 `hermes skills list` 输出中
- 同样受 `skills.disabled` 配置控制启用/禁用
- 同样受 `skills.guard_agent_created` 策略控制
- metadata 写入 `~/.hermes/skills/.usage.json`

## 目录结构

```
ling-skill/
├── README.md
├── .gitignore
└── skills/
    ├── _template/                 # 新 skill 的复制起点
    │   ├── README.md
    │   └── SKILL.md.example       # (可选) frontmatter 模板
    ├── devops/                    # 镜像 Hermes 类别
    │   └── <skill-name>/
    │       └── SKILL.md
    ├── github/
    ├── research/
    ├── software-development/
    ├── productivity/
    └── ...
```

## 类别选择

参考 Hermes 官方类别（在 `~/.hermes/hermes-agent/skills/` 下可见）：
`autonomous-ai-agents`, `creative`, `data-science`, `devops`, `email`, `gaming`, `github`, `media`, `mlops`, `note-taking`, `productivity`, `research`, `smart-home`, `social-media`, `software-development`, `workflow`

不要凭空发明新类别。新 skill 在最接近的现有类别下创建。

## 新增 skill 流程

1. `cp -r skills/_template skills/<category>/<skill-name>/`
2. 编辑 `SKILL.md`，按 `hermes-agent-skill-authoring` skill 的规则写 frontmatter + body
3. 写完后跑 hermes 自带 validator：
   ```bash
   python3 -c "import yaml,re; from pathlib import Path; \
     t = Path('skills/<category>/<skill-name>/SKILL.md').read_text(); \
     assert t.startswith('---'); \
     m = re.search(r'\\n---\\s*\\n', t[3:]); \
     fm = yaml.safe_load(t[3:m.start()+3]); \
     assert 'name' in fm and 'description' in fm; \
     assert len(str(fm['description'])) <= 1024; \
     assert len(t) <= 100000; \
     print('PASS')"
   ```
4. `git add skills/<category>/<skill-name>/ && git commit`

## 维护纪律

- **skill 命名**：小写 + 连字符，≤64 字符，描述 trigger 必须以 "Use when ..." 开头
- **frontmatter**：name + description 是硬要求（Hermes validator 强制）；version / author / license / metadata.hermes 是 peer 约定，强烈建议加上
- **description 长度**：≤1024 字符
- **总文件大小**：≤100 KB（超过应拆 `references/`）
- **body 结构**：必备 `## Overview` + `## When to Use` + `## Common Pitfalls` + `## Verification Checklist`

## 与 make-little-money/skills/ 的区别

| 仓 | 用途 |
|------|------|
| `~/SourceCode/ling-skill/` | 通用 skill（devops、github、research 等），跨项目可用 |
| `~/SourceCode/make-little-money/skills/` | 项目专属 skill（基金/金融），跟随 `make-little-money` 业务仓 |

不要把通用 skill 放进 `make-little-money/skills/`，避免业务仓臃肿。