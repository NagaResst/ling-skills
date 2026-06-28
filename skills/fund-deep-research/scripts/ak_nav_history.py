#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用AKShare获取基金日度净值历史
替代原 fetch_nav_daily.py
"""

import sys
import json
import os
from akshare_data_fetcher import AKShareFundFetcher


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": True, "message": "请提供基金代码"}, ensure_ascii=False))
        sys.exit(1)
    
    fund_code = sys.argv[1]
    fetcher = AKShareFundFetcher(fund_code)
    
    # 获取净值历史
    nav_df = fetcher._fetch_nav_history()
    
    # 格式化日期为 YYYY-MM-DD 字符串（去掉 pandas Timestamp 的时间戳部分）
    nav_df['date'] = nav_df['date'].dt.strftime('%Y-%m-%d')

    result = {
        "fund_code": fund_code,
        "nav_count": len(nav_df),
        "date_range": f"{nav_df['date'].iloc[0]} to {nav_df['date'].iloc[-1]}" if not nav_df.empty else "",
        "latest_nav": float(nav_df.iloc[-1]['nav']) if not nav_df.empty else None,
        "data_source": "akshare",
        "nav_data": nav_df.to_dict('records') if not nav_df.empty else []
    }
    output_str = json.dumps(result, ensure_ascii=False, indent=2, default=str)

    # Auto-write to /tmp cache directory
    raw_dir = f"/tmp/fund_research_{fund_code}/raw"
    os.makedirs(raw_dir, exist_ok=True)
    output_path = os.path.join(raw_dir, "nav_daily.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output_str)
    print(f"[OK] saved to {output_path}", file=sys.stderr)

    print(output_str)


if __name__ == "__main__":
    main()
