#!/usr/bin/env python3
"""
check_residual_patterns.py — 检查文档间残留模式（Phase 2b 通用版）

按用户自定义规则扫描 .md 文档中的残留模式。

规则格式（JSON 文件）:
[
  {
    "doc_filter": "all|except_prd|functional_spec",
    "pattern": "\\\\bis_deleted\\\\b",
    "name": "is_deleted 残留",
    "positive": false
  },
  ...
]

用法:
  python3 check_residual_patterns.py --rules rules.json docs/**/*.md

退出码:
  0 — 全部通过
  1 — 有 real issue（negative 规则不通过 / positive 规则不通过）
  2 — 参数错误
"""

import re
import sys
import glob
import json
import argparse
from pathlib import Path


def apply_filter(doc_filter: str, file_path: Path) -> bool:
    """根据过滤器判断本文件是否应用规则。"""
    if doc_filter == "all":
        return True
    if doc_filter == "all_docs":
        return True

    name = file_path.name.lower()
    if doc_filter == "except_prd":
        return "prd" not in name
    if doc_filter == "functional_spec":
        return "spec" in name or "功能规格" in file_path.name or "func" in name
    if doc_filter == "db_design":
        return "db" in name or "数据库" in file_path.name
    if doc_filter == "ui_files":
        return "ui" in name or "设计" in file_path.name
    if doc_filter == "ui_design":
        return "ui" in name or "设计" in file_path.name

    # 默认应用
    return True


def check_file(path: Path, rules: list) -> tuple[int, list]:
    """检查单个文档，返回 (issue_count, issue_list)。"""
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        return 0, [f"❌ 无法读取 {path}: {e}"]

    issues = []
    for rule in rules:
        if not apply_filter(rule.get("doc_filter", "all"), path):
            continue

        pat = rule["pattern"]
        name = rule["name"]
        positive = rule.get("positive", True)

        matches = re.findall(pat, content, re.IGNORECASE if not positive else 0)

        if positive and not matches:
            # 应该存在但不存在
            issues.append(f"  ❌ [{name}] 应存在但缺失")
        elif not positive and matches:
            # 不应存在但存在
            issues.append(f"  ❌ [{name}] 残留 {len(matches)} 处")

    return len(issues), issues


def main():
    parser = argparse.ArgumentParser(
        description="按自定义规则扫描文档残留模式",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("paths", nargs="+", help="要扫描的 .md 文件路径")
    parser.add_argument("--rules", required=True, help="规则 JSON 文件路径")

    args = parser.parse_args()

    rules_path = Path(args.rules)
    if not rules_path.is_file():
        print(f"❌ 规则文件不存在: {rules_path}")
        sys.exit(2)

    try:
        rules = json.loads(rules_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"❌ 规则文件解析失败: {e}")
        sys.exit(2)

    # 解析路径
    paths = []
    for arg in args.paths:
        matched = glob.glob(arg, recursive=True)
        if matched:
            paths.extend(Path(p) for p in matched)
        else:
            paths.append(Path(arg))

    paths = [p for p in paths if p.is_file()]
    if not paths:
        print("❌ 没有找到任何文件")
        sys.exit(2)

    print(f"📋 加载 {len(rules)} 条规则，扫描 {len(paths)} 个文件\n")

    total_issues = 0
    for path in paths:
        n, issues = check_file(path, rules)
        if issues:
            print(f"=== {path} ===")
            for issue in issues:
                print(issue)
            total_issues += n

    print(f"\n{'='*60}")
    if total_issues == 0:
        print(f"✅ 全部 {len(paths)} 个文件通过所有规则")
        sys.exit(0)
    else:
        print(f"❌ 共 {total_issues} 处 issue")
        sys.exit(1)


if __name__ == "__main__":
    main()