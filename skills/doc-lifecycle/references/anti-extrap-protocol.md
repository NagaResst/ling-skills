# Anti-Extrapolation Protocol — 防外推协议

**适用**：完成场景 2（外部仓库研读）后，用户可能要求把研究结论应用到宿主项目。**这种外推几乎总是错的**。

---

## 核心纪律

> **研读外部仓库 → 给宿主项目出 P0/P1/P2 优先级 = 经典错误**

刚刚加载了 `free-code` 的研究模式，agent 就开始给 Hermes 提建议："Hermes 也应该有 `model_tools.py`" — **这是错的**。

---

## 为什么这是错的

刚做完研读的 agent 心理状态：
- 手里有刚读到的模式（`commands.ts` + `tools.ts` + `feature()` flag）
- 急于把这些模式"用起来"
- 对宿主项目的实际架构只有**模糊回忆**或**完全没有**

这种状态下产出的建议：
- 基于**合理类比**（"Hermes 也是 Python，应该可以这样"）
- 基于**不准确的回忆**（"Hermes 有个 skill 调度模块"）
- **不基于任何 host 源码验证**

用户会问："这些建议你怎么知道的？" agent 答："呃...我从 free-code 推论的..." **用户立刻识破**："你改的这些有用吗？我怎么感觉都没用啊"

---

## 失败案例（研读 free-code → 给 Hermes 提建议）

研读完 `paoloanzn/free-code`（一个 Claude Code CLI 的 fork）后，用户问"哪些模式可以移植到 Hermes？"

agent 立即产出：
- P0: 改 `model_tools.py` 引入 `feature()` flag
- P1: 拆分 `skill_dispatch.py`
- P2: 重构 SKILL.md schema

**实际情况**：
- Hermes 的 `model_tools.py` **不存在**（agent 编造的文件名）
- Hermes 没有 `skill_dispatch.py`（agent 推断的模块名）
- SKILL.md schema 实际是 YAML frontmatter，agent 提议的"重构"方向与现状完全不符

**用户反应**："你改的这些有用吗？我怎么感觉都没用啊"

---

## 防外推协议（5 步）

当用户从"研究仓库"转向"移植到我的项目"时：

### Step 1 — 重置到探索模式

**不要带着研读 momentum 进入建议模式**。

研读后的 momentum 会让 agent 急于输出建议 — 这就是失败模式的起点。**停下来**。

### Step 2 — 读宿主系统的实际源码

**用 `search_files` / `read_file` / `grep` 真实读**宿主项目相关模块：

```bash
# 示例：用户问"Hermes 能不能用 free-code 的 feature() flag 模式"
search_files(target='content', pattern='feature', path='agent/')
search_files(target='files', pattern='model_tools', path='agent/')
search_files(target='content', pattern='skill_dispatch', path='agent/')
```

**每个外推建议都要 cite host 端的 `path:line`**，不能只 cite free-code。

### Step 3 — 明确陈述差距

```
free-code 用 `feature()` flag 在 `scripts/build.ts:13` 做编译期消除。
我尚未验证 Hermes 是否有类似的编译期消除机制。
要不要我先读 `agent/build_*.py` 和 `agent/cli.py` 再回来？
```

**承认未验证**比硬给建议强。

### Step 4 — 推迟优先级标签（P0/P1/P2）

**优先级标签（P0/P1/P2）必须双侧都验证后才能给**：

- free-code 侧：`free-code:src/build.ts:13-50`
- Hermes 侧：`hermes-agent:agent/build.py:42-78`（假设存在）

**只验证一侧就给 P0/P1/P2 = 虚构**。

### Step 5 — 用户催促时给"处方"不给"诊断"

如果用户坚持要立即建议，不要给 P0/P1/P2 列表，给**处方**：

```
要回答这个问题，需要读：
1. `agent/build_*.py` - 看 Hermes 当前的构建流程
2. `agent/cli.py` - 看 CLI 入口
3. `agent/skills/` 下的 5-10 个文件 - 看 skill 调度现状

读完后我才能给出有根据的建议。
```

---

## 何时这条规则不适用

**反例**：当用户明确说"我要的就是 free-code 模式在 Hermes 的镜像"，这是**复制粘贴**而非外推，可以直接做。

**判定**：如果用户给的是**精确目标**（"在 X 文件加 Y 函数"），可以执行；如果用户给的是**模糊目标**（"free-code 那个模式我们能不能用"），必须先读宿主源码。

---

## 反模式速查

| 反模式 | 症状 | 修复 |
|--------|------|------|
| 凭类比给建议 | "Hermes 也是 Python，所以这样应该可以" | 读 Hermes 实际源码 |
| 虚构文件 | 引用 host 端不存在的文件 | 用 search_files 验证存在 |
| 模糊回忆 | "Hermes 有个 skill 调度模块" | 用 search_files 找确切路径 |
| 单侧优先级 | 只 cite free-code 就给 P0/P1/P2 | 双侧 cite 后再给 |
| 急于交付 | 读完 free-code 立即写推荐 | 重置到探索模式 |

---

## 完成标准

- [ ] 已停止基于 free-code momentum 的输出
- [ ] 已读 host 端实际源码（用 search_files / grep）
- [ ] 已陈述 free-code 和 host 端的差距
- [ ] 优先级标签（P0/P1/P2）有双侧 cite
- [ ] 如未双侧验证，给的是"处方"（"先读这些文件"）而非"诊断"