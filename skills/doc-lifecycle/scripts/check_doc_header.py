#!/usr/bin/env python3
"""
check_doc_header.py — 检查 .md 文档是否带 8 字段头部

8 字段：项目名称 / 文档类型 / 创建日期 / 创建人 / 审核人 / 版本号 / 状态

用法:
  python3 check_doc_header.py docs/**/*.md

退出码:
  0 — 全部合规
  1 — 有文档缺字段
  2 — 参数错误
"""

import re
import sys
import glob
from pathlib import Path


REQUIRED_FIELDS = [
    ("项目名称", r"\*\*项目名称\*\*\s*[:：]"),
    ("文档类型", r"\*\*文档类型\*\*\s*[:：]"),
    ("创建日期", r"\*\*创建日期\*\*\s*[:：]\s*\d{4}-\d{2}-\d{2}"),
    ("创建人", r"\*\*创建人\*\*\s*[:：]"),
    ("审核人", r"\*\*审核人\*\*\s*[:：]"),
    ("版本号", r"\*\*版本号\*\*\s*[:：]\s*v\d+\.\d+"),
    ("状态", r"\*\*状态\*\*\s*[:：]"),
]


def check_file(path: Path) -> int:
    """检查单个文档，返回缺失字段数。"""
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"❌ 无法读取 {path}: {e}")
        return -1

    # 仅检查前 30 行（头部在文档开头）
    head = "\n".join(content.splitlines()[:30])
    missing = []

    for name, pat in REQUIRED_FIELDS:
        if not re.search(pat, head):
            missing.append(name)

    if missing:
        print(f"❌ {path}: 缺字段 {missing}")
        return len(missing)
    else:
        print(f"✅ {path}: 8 字段头部完整")
        return 0


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)

    paths = []
    for arg in sys.argv[1:]:
        matched = glob.glob(arg, recursive=True)
        if matched:
            paths.extend(Path(p) for p in matched)
        else:
            paths.append(Path(arg))

    paths = [p for p in paths if p.is_file()]
    if not paths:
        print("❌ 没有找到任何文件")
        sys.exit(2)

    total_missing = 0
    for path in paths:
        total_missing += check_file(path)

    print(f"\n{'='*60}")
    if total_missing == 0:
        print(f"✅ 全部 {len(paths)} 个文档头部合规")
        sys.exit(0)
    else:
        print(f"❌ 共 {total_missing} 处字段缺失")
        sys.exit(1)


if __name__ == "__main__":
    main()