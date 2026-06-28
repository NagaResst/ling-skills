#!/usr/bin/env python3
"""
check_doc_v2_residue.py — 通用版 v2.0 文档残留检测

扫描 v2.x 文档中的 11 类 v1.x 比对残留模式 + 用户自定义旧术语。

用法:
  # 仅扫描 11 类通用模式
  python3 check_doc_v2_residue.py <path/to/v2.0-doc.md> [...]

  # 注入项目特定旧术语（推荐）
  python3 check_doc_v2_residue.py --old-terms timing_record,crash_recovery,auto_checkout doc.md

  # 支持 glob
  python3 check_doc_v2_residue.py 'docs/**/*.md'

退出码:
  0 — 全部清零，文档可作为依据使用
  1 — 还有残留，需进一步清理
  2 — 文件不存在或参数错误
"""

import re
import sys
import glob
import argparse
from pathlib import Path


# 11 类通用残留模式
GENERIC_RESIDUE_PATTERNS = [
    ("多列对照表 v1.0 表述/v2.0 校对后", r"\|[^|]*v1\.0\s*表述[^|]*\|[^|]*v2\.0\s*校对后[^|]*\|"),
    ("X → Y 全量替换/迁移/修正", r"[→\-]+\s*(?:全量替换|全量迁移|全量修正|迁移|修正)"),
    ("校对变更 blockquote", r"^\s*>\s*校对(?:关键)?变更"),
    ("v1.0 仅... 反向引用", r"v1\.0\s*仅"),
    ("v1.0 不再... 反向引用", r"v1\.0\s*不再"),
    ("v1.0 → v2.0 标题残留", r"v1\.0\s*[→\-]\s*v2\.0"),
    ("替代 X 术语表条目", r"(?:替代|取代)\s+\S"),
    ("修订记录 ① 多项变更", r"修订内容[^|]*[①⑴]"),
    ("v1.0 表述/v2.0 校对后 章节", r"#+\s*v1\.0\s*表述[^#]*v2\.0\s*校对后"),
    ("由 v1.0 改为 v2.0 叙述", r"(?:由|从)\s*v1\.0\s*改为\s*v2\.0"),
    ("v1.0 不再涉及... 段落", r"v1\.0\s*(?:不再\s*涉及|已经\s*删除|已\s*废弃)"),
]


def build_patterns(old_terms: list[str]) -> list[tuple[str, str]]:
    """构建扫描模式列表（通用 + 用户自定义）"""
    patterns = list(GENERIC_RESIDUE_PATTERNS)

    # 用户自定义旧术语
    for term in old_terms:
        term = term.strip()
        if term:
            patterns.append((f"用户旧术语: {term}", re.escape(term)))

    return patterns


def check_file(path: Path, patterns: list[tuple[str, str]]) -> int:
    """检查单个文件，返回残留总数。"""
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"❌ 无法读取 {path}: {e}")
        return -1

    total = 0
    lines = content.splitlines()

    for label, pat in patterns:
        matches = list(re.finditer(pat, content, re.MULTILINE))
        if matches:
            total += len(matches)
            print(f"  ❌ [{label}]: {len(matches)} 处")
            # 打印前 3 处的行号
            shown = 0
            for i, line in enumerate(lines, 1):
                if re.search(pat, line):
                    print(f"     L{i}: {line.strip()[:100]}")
                    shown += 1
                    if shown >= 3:
                        break

    return total


def main():
    parser = argparse.ArgumentParser(
        description="扫描 v2.0 文档残留的 v1.0 比对模式",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("paths", nargs="+", help="要扫描的文件路径（支持 glob）")
    parser.add_argument(
        "--old-terms",
        default="",
        help="项目特定旧术语，逗号分隔（如 'timing_record,crash_recovery,auto_checkout'）",
    )

    args = parser.parse_args()

    # 解析路径（支持 glob）
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

    # 构建模式
    old_terms = [t for t in args.old_terms.split(",") if t.strip()]
    patterns = build_patterns(old_terms)

    if old_terms:
        print(f"📋 已注入 {len(old_terms)} 个项目旧术语: {', '.join(old_terms)}")
    print(f"📋 共 {len(patterns)} 个扫描模式")
    print()

    grand_total = 0
    for path in paths:
        print(f"=== {path} ===")
        n = check_file(path, patterns)
        if n == 0:
            print("  ✅ 0 处残留")
        elif n > 0:
            grand_total += n

    print(f"\n{'='*60}")
    if grand_total == 0:
        print(f"✅ 全部 {len(paths)} 个文件清零，可作为依据使用")
        sys.exit(0)
    else:
        print(f"❌ 共 {grand_total} 处残留，需进一步清理")
        sys.exit(1)


if __name__ == "__main__":
    main()