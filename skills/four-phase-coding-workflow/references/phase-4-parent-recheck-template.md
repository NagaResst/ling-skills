# Phase 4 Parent Recheck Template

用于父 agent 在阶段 4 亲自反查阶段 3 报告。目标：验证 claim 是否属实，并形成真实结论与修复建议。

```markdown
你是阶段 4 的父 agent。不要信任阶段 3 的报告转述，必须亲自按 proof_handle 反查。

【输入】
- verification items: {{PHASE3_ITEMS}}
- commit hashes: {{COMMIT_HASHES}}
- base doc / corrected doc refs: {{DOC_REFS}}
- phase 1 over-engineering findings: {{OVER_ENG_FINDINGS}}（如有）
- phase 2 ponytail_shortcuts: {{PONYTAIL_SHORTCUTS}}（如有）

【必须执行】
- 用 grep / read_file / git log / terminal 检查 claim 是否属实
- 对每条 verification item 标注 confirmed / rejected / partial
- 只输出真实结论与修复建议
- 不直接修代码，等用户确认

【Ponytail 反查 — 条件性，仅当阶段 1/3 产出相关 finding 时触发】

1. Over-engineering finding 反查：
   - 阶段 1 报告的 `over_eng_type`（yagni/stdlib/native/shrink/delete）分类是否属实？
   - 建议的 simpler_alternative 是否真的可行？
   - 验证方式：grep 文档指定内容 + 对比 stdlib/platform API 文档

2. 安全护栏违反反查：
   - 阶段 3 报告安全护栏违反时，grep commit diff 确认：
     - 输入验证是否真的被移除/削弱？
     - 错误处理是否真的被简化掉？
     - 安全措施是否真的被省略？
   - 防止子 agent 误报（把文档没要求的验证当成被砍掉的安全措施）

3. `ponytail:` shortcut 审计：
   - 每个阶段 2 标注的 `ponytail:` 注释是否真的标注了上限和升级路径？
   - 没有升级路径的 shortcut → 标记为 `no-trigger`，这些是静默腐烂风险

【输出格式】

一致性 verification item 反查：

## Phase 4 Parent Recheck
- verification_id:
- parent_verdict: confirmed|rejected|partial
- checked_with:
- parent_evidence:
- recommended_action:
- requires_user_approval: yes|no

Over-engineering / 安全护栏反查：

## Phase 4 Parent Recheck — Ponytail
- verification_id:
- recheck_type: over_engineering | safety_guardrail | shortcut_audit
- parent_verdict: confirmed|rejected|partial
- checked_with:
- parent_evidence:
- recommended_action:
- requires_user_approval: yes|no
```
