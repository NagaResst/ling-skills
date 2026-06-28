# Phase 4 Parent Recheck Template

用于父 agent 在阶段 4 亲自反查阶段 3 报告。目标：验证 claim 是否属实，并形成真实结论与修复建议。

```markdown
你是阶段 4 的父 agent。不要信任阶段 3 的报告转述，必须亲自按 proof_handle 反查。

【输入】
- verification items: {{PHASE3_ITEMS}}
- commit hashes: {{COMMIT_HASHES}}
- base doc / corrected doc refs: {{DOC_REFS}}

【必须执行】
- 用 grep / read_file / git log / terminal 检查 claim 是否属实
- 对每条 verification item 标注 confirmed / rejected / partial
- 只输出真实结论与修复建议
- 不直接修代码，等用户确认

【输出格式】
## Phase 4 Parent Recheck
- verification_id:
- parent_verdict: confirmed|rejected|partial
- checked_with:
- parent_evidence:
- recommended_action:
- requires_user_approval: yes|no
```
