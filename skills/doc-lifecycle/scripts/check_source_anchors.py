#!/usr/bin/env python3
"""
check_source_anchors.py — 检查研读笔记中源码锚点覆盖率

源码锚点格式：`src/path/file.ext:line` 或 `src/path/file.ext:line-line`

用法:
  python3 check_source_anchors.py <research-dir>/*.md

退出码:
  0 — 全部达标（≥ 80%）
  1 — 有文档不达标
  2 — 参数错误

建议覆盖率阈值:
  --threshold 80 (默认)
"""

import re
import sys
import glob
from pathlib import Path


# 锚点模式
ANCHOR_PATTERNS = [
    re.compile(r"`[\w\-./]+:\d+(?:-\d+)?`"),                          # `src/file.ts:42`
    re.compile(r"`[\w\-./]+:\d+[-–]\d+`"),                            # `src/file.ts:42-78`
    re.compile(r"来源[:：]\s*`?[\w\-./]+:\d+(?:[-–]\d+)?`?"),        # 来源：src/file.ts:42
    re.compile(r"see\s+`[\w\-./]+:\d+(?:[-–]\d+)?`", re.IGNORECASE),  # see `src/file.ts:42`
]

# 应有锚点的"事实性主张"信号词
FACTUAL_CLAIM_SIGNALS = [
    "live", "exists", "function", "class", "method", "import",
    "exports", "interface", "type", "enum", "module", "registry",
    "feature", "gates", "defined", "declared", "lives", "is a",
]


def count_anchors_and_claims(content: str) -> tuple[int, int]:
    """返回 (锚点数, 事实性主张数)。"""
    anchors = 0
    for pat in ANCHOR_PATTERNS:
        anchors += len(pat.findall(content))

    # 简单估算事实性主张数（按句子分割，统计含信号词的句子）
    sentences = re.split(r"[。.!?！？\n]", content)
    claims = 0
    for sent in sentences:
        sent = sent.strip()
        if len(sent) < 10:  # 太短的句子不算
            continue
        for signal in FACTUAL_CLAIM_SIGNALS:
            if signal.lower() in sent.lower():
                claims += 1
                break

    return anchors, claims


def check_file(path: Path, threshold: float) -> int:
    """检查单个文件，返回 0/1。"""
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"❌ 无法读取 {path}: {e}")
        return -1

    anchors, claims = count_anchors_and_claims(content)

    if claims == 0:
        print(f"⚠️ {path}: 未检测到事实性主张（可能无源码引用需求）")
        return 0

    coverage = anchors / claims if claims > 0 else 0
    coverage_pct = coverage * 100

    if coverage_pct >= threshold:
        print(f"✅ {path}: 锚点 {anchors}/{claims} = {coverage_pct:.0f}% (阈值 {threshold}%)")
        return 0
    else:
        print(f"❌ {path}: 锚点 {anchors}/{claims} = {coverage_pct:.0f}% (阈值 {threshold}%)")
        return 1


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)

    threshold = 80.0
    args = sys.argv[1:]
    if args and args[0] == "--threshold":
        threshold = float(args[1])
        args = args[2:]

    paths = []
    for arg in args:
        matched = glob.glob(arg, recursive=True)
        if matched:
            paths.extend(Path(p) for p in matched)
        else:
            paths.append(Path(arg))

    paths = [p for p in paths if p.is_file()]
    if not paths:
        print("❌ 没有找到任何文件")
        sys.exit(2)

    bad = sum(check_file(p, threshold) for p in paths)

    print(f"\n{'='*60}")
    print(f"扫描 {len(paths)} 个文件,阈值 {threshold}%")
    sys.exit(1 if bad > 0 else 0)


if __name__ == "__main__":
    main()