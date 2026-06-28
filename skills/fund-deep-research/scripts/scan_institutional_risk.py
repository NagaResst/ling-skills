#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基金经理与基金公司风险扫描脚本
目标：全网搜索合规处罚、负面舆情、离职传闻等风险信号。
"""

import sys
import json
import requests

def search_risk_signals(name, fund_company):
    """
    模拟搜索风险信号（实际执行时 AI 会调用 search_web 工具，此处提供关键词逻辑）
    """
    keywords = [
        f"{name} 违规 处罚",
        f"{fund_company} 监管函",
        f"{name} 离职 传闻",
        f"{fund_company} 内幕交易",
        f"{name} 风格漂移"
    ]
    
    # 在实际 Skill 执行中，AI 会根据这些关键词去 search_web
    # 这里我们返回一个结构化的搜索计划
    return {
        "target_person": name,
        "target_company": fund_company,
        "search_keywords": keywords,
        "risk_level": "pending_ai_search" 
    }

def main():
    if len(sys.argv) < 3:
        print(json.dumps({"error": True, "message": "请提供基金经理姓名和基金公司名称"}, ensure_ascii=False))
        sys.exit(1)

    manager_name = sys.argv[1]
    company_name = sys.argv[2]

    # 解析 --output 和 --fund-code 参数
    output_path = None
    fund_code = None
    raw_args = sys.argv[3:]
    for i, arg in enumerate(raw_args):
        if arg == '--output' and i + 1 < len(raw_args):
            output_path = raw_args[i + 1]
        elif arg == '--fund-code' and i + 1 < len(raw_args):
            fund_code = raw_args[i + 1]

    result = search_risk_signals(manager_name, company_name)
    output_str = json.dumps(result, ensure_ascii=False, indent=2)

    # Auto-write to /tmp cache directory when --fund-code is provided
    if fund_code:
        import os as _os
        raw_dir = f"/tmp/fund_research_{fund_code}/raw"
        _os.makedirs(raw_dir, exist_ok=True)
        auto_path = _os.path.join(raw_dir, "institutional_risk.json")
        with open(auto_path, 'w', encoding='utf-8') as f:
            f.write(output_str)
        print(f"[OK] saved to {auto_path}", file=sys.stderr)
    elif output_path:
        import os
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output_str)
        print(f"[OK] 已保存到 {output_path}", file=sys.stderr)
    else:
        print(output_str)

if __name__ == "__main__":
    main()
