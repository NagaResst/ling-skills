# 4 阶段编码工作流 (Four-Phase Coding Workflow)

> Hermes Agent skill：以上游文档为依据，先校正实施文档，再按校正后的实施文档编码；阶段 4 由父 agent 亲自反查，不信任子 agent 报告转述。

## 这是什么

这是一个用于**高风险、强审计、强对齐**场景的 Hermes skill。

适用任务：
- “以 X 为基础，校正 Y，然后改代码”
- “按技术文档 / 数据库设计 / API 文档，校正实施计划，再实现”
- “先校验 doc，再按校正后的 doc 实现”

它的职责不是发挥创意，而是：
- **忠实执行设计**
- **发现冲突尽早反馈**
- **把阶段 3 报告当作待反查 claim，而不是最终结论**

## 4 阶段

1. **阶段 1：校验实施文档**
2. **阶段 2：编码**
3. **阶段 3：再校验**
4. **阶段 4：父 agent 反查总结**

阶段间严格串行；阶段内是否并行，按文件冲突和依赖关系决定。

## 当前版本的关键特征

- frontmatter 增加 `when_to_use` 与 `effort: high`
- 明确了 **父 agent 不参与业务编码** 的边界
- 增加了 **handoff compaction** 规则
- 增加了 **证明句柄（proof handle）** 规则
- 用统一 schema 规范四阶段输出
- 将 phase 模板下沉到 `references/`
- 将偏离类型收敛成 taxonomy

## 安装

把整个目录复制到你的 Hermes skills 路径：

```bash
# 用户级 skill
mkdir -p ~/.hermes/skills/software-development/
cp -r four-phase-coding-workflow ~/.hermes/skills/software-development/

# 仓库级 skill（项目内，优先级更高）
mkdir -p <your-project>/.hermes/skills/software-development/
cp -r four-phase-coding-workflow <your-project>/.hermes/skills/software-development/
```

重启 Hermes Agent 或 `/new` 进入新 session 后加载。

## 使用

直接对 Hermes 说：
- “以技术文档和数据库设计为基础，校正实施计划，然后实现 M2-01”
- “4 阶段校正：M1-05~08 文档 + 代码 + 再校验 + 总结”
- “按 X 文档，校正 Y 设计，然后改代码”

## 文档结构

```text
four-phase-coding-workflow/
├── SKILL.md
├── README.md
├── LICENSE
└── references/
    ├── phase-1-validator-template.md
    ├── phase-2-coder-template.md
    ├── phase-3-verifier-template.md
    ├── phase-4-parent-recheck-template.md
    ├── stage-4-verification-checklist.md
    ├── worked-example-time-scroll-m1.md
    ├── worked-example-time-scroll-m2-01.md
    └── worked-example-time-scroll-m2-01-02.md
```

## 核心运行哲学

### 1. 父 agent 保持干净
父 agent 默认只做：
- clarify
- 阶段编排
- handoff 压缩
- grep/read_file/git log/terminal 反查
- 阶段 4 最终结论

父 agent 默认**不写业务代码**。

### 2. 设计优先，创意靠后
任何“看起来更好”的实现，如果未被校正后的实施文档允许，都视为偏离，而不是改进。

### 3. 不信任阶段 3 报告
阶段 3 只是生成 verification items；最终是否属实，由阶段 4 父 agent 亲自判定。

## 与其他 skill 的关系

- `parallel-task-decomposition`：其 doc→code 模式是本 skill 的轻量版，适合快速同步
- 本 skill：适用于高风险、多文件、严格审计场景，因为它多了阶段 3 再校验与阶段 4 反查门

## License

MIT — 详见 [LICENSE](LICENSE)
