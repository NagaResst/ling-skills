# Stage 4 反查清单 (Stage 4 Verification Checklist)

**用途**: four-phase-coding-workflow 阶段 4 — 亲自反查阶段 3 报告,不信任子 agent 转述。
**来源**: M2-01 阶段 4 实战验证,14 项反查 7/7 真实,7/7 子 agent H 报告属实。

## 核心原则

- **不信任阶段 3 报告** — 它说"无偏离"≠ 真的无偏离,亲自 grep/read_file/git log 验证
- **必须超出子 agent 报告** — 阶段 3 子 agent 报告里**没**提到的项,自己主动查(关键的:实际 commit 存在、关键 grep 通过、子类设计合法)
- **每条反查标记** ✅ 确认属实 / ❌ 失实 / ⚠️ 部分属实,然后才能进修复建议
- **核查 agent ≠ 父 agent 自验**（2026-06-24 用户纪律）— 派出去的核查子 agent **不**读改造 agent 的 self-report,**不**读父 agent 中间 grep 结果,只给原 spec + 文件路径 + "从头重做"。父 agent 用自己的 grep 作中间信号可以,但**不能**取代派核查 agent。

## 反查项分类(共 14 项)

### 类别 A: Commit 真实存在性 (必做)

```bash
# 1. 所有 commit 真实存在
git log --oneline <base>..HEAD
# 2. 每个 commit 实际改了哪些文件(不能光看 message)
git show --stat HEAD
git show --stat HEAD~1
git show --stat HEAD~2
```

### 类别 B: 代码覆盖率反查 (核心防护)

```bash
# 3. 子类不重写基类已有方法(防止覆盖基类逻辑)
grep -n "softDelete" <子 Repository.ets> || echo "PASS: 未重写,继承基类"

# 4. 新方法签名 + 返回类型覆盖
grep -nE "async (method1|method2|method3)\(" <子 Repository.ets>

# 5. 错误脱敏统一(每方法都走 hilog + 中文消息,无 errMsg 透传)
grep -nE "hilog\.error.*<子 Repository>" <子 Repository.ets>
grep -nE "return error\(ErrorCodes\.DB_ERROR" <子 Repository.ets>
# 反向: 确认没有 errMsg(err) 出现在 Result.message 里
grep -nE "errMsg\(err\)" <子 Repository.ets>  # 应只在 hilog 调用里

# 6. 跨表语义越权终极 grep
# 子 agent 报告"未越权"时,亲自 grep 关键词,应该只在 JSDoc 注释出现
grep -nE "(关联表\.|关联 Service|跨表|30 天)" <子 Repository.ets>
```

### 类别 C: 测试覆盖率反查 (核心防护)

```bash
# 7. 测试用例数(子 agent 可能虚报)
grep -cE "^\s+it\(" <测试文件.ets>

# 8. 测试无 any 滥用
grep -nE "(\bas any\b|: any\b|<any>)" <测试文件.ets> || echo "PASS"

# 9. 测试 import 路径真实存在
grep -E "from '\.\./\.\./main/ets" <测试文件.ets>
# 验证每个 import 路径 ls -la 能找到

# 10. 测试文件行数 + describe 块数
wc -l <测试文件.ets>
grep -cE "^\s+describe\(" <测试文件.ets>
```

### 类别 D: 类型与设计反查 (子 agent 主动简化防护)

```bash
# 11. 子 agent 主动简化的类型/接口替换,验证等价性
# 例: 字面量联合 → 类型别名
cat <常量定义文件>  # 确认别名与字面量联合类型等价
```

### 类别 E: 实施 doc 与代码一致性反查 (防止"doc 与 code 漂移")

```bash
# 12. 实施 doc 关键段 + 代码片段对比
sed -n '<段起>,<段止>p' <实施 doc>
sed -n '<行起>,<行止>p' <代码文件>
# 人工核对方法签名/字段映射/错误码

# 13. 抽象方法实现完整(子类不实现 abstract 方法则编译失败)
grep -nE "protected (getTableName|mapToEntity|mapToValues)\(" <子 Repository.ets>
```

### 类别 F: 测试子类设计反查 (ArkTS 严格模式)

```bash
# 14. TestableRepository / StubExplodingRepository 真实存在 + 实现合法
grep -nE "class (Testable\w+|StubExploding\w+)" <测试文件.ets>
# 验证 protected→public 用包装模式(合法)而非 override 改可见性(可能非法)
sed -n '<行>,<行>p' <测试文件.ets>
```

### 类别 G: API 导出形式反查 (防止 function/class static 漂移)

子 agent 报告"已实现 X"时, 父 agent 必须按 spec 的**导出形式** grep, 不能只 grep 名字验存在:

```bash
# 反模式: 只 grep <name> → 通过但形式不对(如 class static vs export function)
# 正模式: 按 spec 期望的导出形式 grep

# 函数 / 箭头函数
grep -nE "^export (function|const) <name>\(" <file.ets>
# class + static
grep -nE "^export class <name>" <file.ets>
# class static 方法
grep -nE "public static <methodName>\(" <file.ets>

# 实证: M1-07 实施计划写 `getDayStart(timestamp): number`,
# 子 agent 实现成 `class DateUtils { public static getDayStart(...) }`,
# `grep "getDayStart"` 通过, `grep "^export function getDayStart"` 才能抓到漂移。
```

**何时必做**:阶段 2 任务涉及"实现函数/类/方法",且 spec 明确写了导出形式(class vs function)。
**失败信号**:阶段 4 grep 出 0 个匹配但 spec 说应该存在 → 子 agent 用了别的形式,回去修。

### 类别 H: Ponytail 反查 (条件性 — 仅当阶段 1/3 产出 Ponytail 相关 finding 时触发)

```bash
# H1. Over-engineering finding 验证
# 阶段 1 报告文档过度设计时,验证 claim 是否属实
# 例: 阶段 1 说"文档指定了 moment.js 但 stdlib Intl.DateTimeFormat 可替代"
grep -nE "moment|date-fns" <实施文档>         # 确认文档确实指定了该库
grep -nE "Intl\\.DateTimeFormat" <代码文件>   # 确认替代方案可行(或查 stdlib 文档)

# H2. 安全护栏违反验证
# 阶段 3 报告安全护栏违反时,grep commit diff 确认
git diff <commit_hash> -- <file> | grep -E "(validation|sanitize|escape|auth|permission|password|token)"
# 确认被移除的验证是否真的是"不可简化项",而非文档没要求的额外验证

# H3. ponytail: shortcut 审计
# 阶段 2 标注的所有 ponytail: 注释是否都包含了上限和升级路径
grep -rnE "(#|//) ?ponytail:" <代码目录>
# 检查每个 hit: 是否包含升级路径(如 "if throughput matters")
# 没有升级路径的 → 标记 no-trigger,这些是静默腐烂风险

# H4. Ponytail 阶梯误用检查
# 确认子 agent 没有对文档指定项使用 Ponytail 阶梯简化
# 如果阶段 2 报告了 ponytail_shortcuts,逐条核对:
#   - 该 shortcut 是否涉及文档明确指定的 API/库/抽象?
#   - 是 → 违反优先级规则,需要回退
#   - 否 → 合法 shortcut
```

**何时触发**:
- 阶段 1 产出 `over_engineering` 类型的 finding
- 阶段 3 产出 over-engineering verification item 或安全护栏违反项
- 阶段 2 报告 `ponytail_shortcuts` 非 none

**失败信号**:
- H1: 文档没有指定该库/抽象 → over-engineering finding 失实
- H2: 被移除的验证在文档中确实有要求 → 安全护栏违反确认
- H3: shortcut 没有升级路径 → 标记 no-trigger 风险
- H4: shortcut 涉及文档指定项 → 阶段 2 违反优先级规则

## 真实失实案例 (M2-01 阶段 1)

子 agent A 报告:`idx_project_active (type, is_paused, deleted_at) 复合索引` 用于 queryByType
真实情况:数据库设计 §3.3 实际命名为 `idx_tag_deleted` / `idx_project_deleted`,**不是** `idx_project_active`

**教训**:阶段 1 子 agent 报"索引命中"时,必须亲自 grep 数据库设计 §3.3 段确认索引名,不能信子 agent 转述。

## 真实失实案例 (worked example M1-08)

子 agent A 的 import 路径修改被 agent B 的 patch 覆盖(sibling 冲突),需要父 agent 手动 re-apply (`ba730af`)

**教训**:阶段 2 多个子 agent 改同一文件时,即使任务"看起来不冲突"也要串行,parent 必须在所有 commit 后亲自 grep 验证关键 import / 函数名。

## 反查完成标准

- 14 项全部完成(可按需裁剪,但 A/B/C/F 是核心)
- 类别 H 为条件性触发项(仅当阶段 1/3/2 产出 Ponytail 相关 finding 时触发)
- 每项标记 ✅/❌/⚠️
- ❌ 项 → 进入"修复建议",等用户拍板
- ✅ + ⚠️ 项 → 写入"真实施记录"作为可追溯证据
