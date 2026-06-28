#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
黑名单检查脚本
检查基金公司和基金经理是否在黑名单中
输出JSON格式
"""

import sys
import json
import os


def load_blacklist():
    """
    加载黑名单配置
    
    Returns:
        dict: 黑名单数据
    """
    # 黑名单配置文件路径
    blacklist_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "..",
        "投资者行动",
        "投资者画像.md"
    )
    
    blacklist = {
        "companies": [],
        "managers": []
    }
    
    try:
        with open(blacklist_path, 'r', encoding='utf-8') as f:
            content = f.read()
                        
            # 提取刘彦春
            if "刘彦春" in content:
                blacklist["managers"].append({
                    "name": "刘彦春",
                    "reason": "投资风格过于集中、风控不足，深度套牢近5年"
                })
        
        return blacklist
        
    except Exception as e:
        # 如果无法读取文件，使用硬编码的黑名单
        return {
            "managers": [
                {
                    "name": "刘彦春",
                    "reason": "投资风格过于集中、风控不足"
                }
            ]
        }


def check_blacklist(company_name, manager_name):
    """
    检查是否在黑名单中
    
    Args:
        company_name: 基金公司名称
        manager_name: 基金经理姓名
        
    Returns:
        dict: 检查结果
    """
    blacklist = load_blacklist()
    
    result = {
        "company_check": {
            "name": company_name,
            "in_blacklist": False,
            "reason": ""
        },
        "manager_check": {
            "name": manager_name,
            "in_blacklist": False,
            "reason": ""
        },
        "overall_result": "通过"
    }
    
    # 检查公司
    for item in blacklist["companies"]:
        if item["name"] in company_name:
            result["company_check"]["in_blacklist"] = True
            result["company_check"]["reason"] = item["reason"]
            result["overall_result"] = "不通过"
            break
    
    # 检查经理
    for item in blacklist["managers"]:
        if item["name"] in manager_name:
            result["manager_check"]["in_blacklist"] = True
            result["manager_check"]["reason"] = item["reason"]
            result["overall_result"] = "不通过"
            break
    
    return result


def main():
    if len(sys.argv) < 3:
        print(json.dumps({"error": True, "message": "请提供基金公司和基金经理名称"}, ensure_ascii=False))
        sys.exit(1)
    
    company_name = sys.argv[1]
    manager_name = sys.argv[2]

    # 解析 --fund-code 参数
    fund_code = None
    raw_args = sys.argv[3:]
    for i, arg in enumerate(raw_args):
        if arg == '--fund-code' and i + 1 < len(raw_args):
            fund_code = raw_args[i + 1]
            break

    result = check_blacklist(company_name, manager_name)
    output_str = json.dumps(result, ensure_ascii=False, indent=2)

    # Auto-write to /tmp cache directory when --fund-code is provided
    if fund_code:
        raw_dir = f"/tmp/fund_research_{fund_code}/raw"
        os.makedirs(raw_dir, exist_ok=True)
        output_path = os.path.join(raw_dir, "blacklist.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output_str)
        print(f"[OK] saved to {output_path}", file=sys.stderr)
    else:
        print(output_str)


if __name__ == "__main__":
    main()
