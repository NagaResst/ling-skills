#!/usr/bin/env python3
"""
check_doc_naming.py — 检查 .md 文件命名是否符合规范

规范格式：[项目缩写]_[文档类型]_[模块]_[版本号]_[日期].md
例：MyApp_PRD_产品需求_v1.0_20260523.md

用法:
  python3 check_doc_naming.py docs/**/*.md

退出码:
  0 — 全部合规
  1 — 有文件名不规范
  2 — 参数错误
"""

import re
import sys
import glob
from pathlib import Path


# 允许的文档类型（可按项目扩展）
ALLOWED_DOC_TYPES = {
    "PRD", "SPEC", "TECH", "TEST", "API", "DB",
    "DESIGN", "IMPL", "GUIDE", "REF", "MIGRATION",
    "规范", "需求", "设计", "技术", "测试", "API文档",
    "数据库设计", "UI设计", "功能规格", "实施", "代码规范",
}

# 项目缩写：2-6 个大写字母或首字母缩写
PROJECT_ABBR_RE = r"[A-Z][A-Z0-9]{1,5}"

# 模块：可含中文、字母、数字、下划线
MODULE_RE = r"[\w\u4e00-\u9fff]+"

# 版本号：vX.Y 或 vX.Y.Z
VERSION_RE = r"v\d+\.\d+(?:\.\d+)?"

# 日期：YYYYMMDD
DATE_RE = r"\d{8}"

NAMING_PATTERN = re.compile(
    rf"^{PROJECT_ABBR_RE}_([\w\u4e00-\u9fff]+)_({MODULE_RE})_({VERSION_RE})_({DATE_RE})\.md$"
)


def check_file(path: Path) -> tuple[int, str]:
    """检查单个文件名，返回 (不匹配字段数, 错误信息)。"""
    name = path.name
    m = NAMING_PATTERN.match(name)
    if not m:
        return 1, f"不符合命名规范: {name}\n    期望: [项目缩写]_[文档类型]_[模块]_[版本号]_[日期].md"

    doc_type = m.group(1)
    if doc_type not in ALLOWED_DOC_TYPES:
        # 不阻止，只警告
        return 0, f"⚠️ {path}: 文档类型 '{doc_type}' 不在常用清单（{sorted(ALLOWED_DOC_TYPES)[:5]}...），但符合格式"

    return 0, ""


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

    bad = 0
    warnings = 0
    good = 0
    for path in paths:
        n, msg = check_file(path)
        if n > 0:
            bad += n
            print(f"❌ {msg}")
        elif msg:
            warnings += 1
            print(msg)
        else:
            good += 1
            print(f"✅ {path}: 命名规范")

    print(f"\n{'='*60}")
    print(f"扫描 {len(paths)} 个文件: {len(paths) - bad} 合规, {bad} 不规范, {warnings} 警告")
    sys.exit(1 if bad > 0 else 0)


if __name__ == "__main__":
    main()