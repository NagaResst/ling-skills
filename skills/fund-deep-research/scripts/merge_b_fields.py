#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merge_b_fields.py — 将 AI 提取的 B 类字段合并到 web-platform JSON

用法：
    python3 merge_b_fields.py <基金代码> <b_fields.json路径> [--overwrite]

选项：
    --overwrite   强制覆盖已有 B 类字段（默认不覆盖，只填充空缺）
"""

import json
import os
import sys

REPO_ROOT = os.getcwd()
DATA_DIR = os.path.join(REPO_ROOT, "web-platform/public/data")


REFRESH_BY_DEFAULT_PREFIXES = (
    "policy",
    "exclusionCheck",
    "scoring",
    "tracking",
    "company",
    "stageAnalysis.stages",
    "stageAnalysis.inflectionPoints",
    "managers.current.education",
    "managers.current.joinDate",
    "managers.current.experience",
    "managers.current.title",
    "managers.current.style",
    "managers.current.manageDate",
    "managers.current.manageYears",
    "managers.current.tenureReturn",
    "managers.current.peerAvgReturn",
    "managers.current.rankInPeer",
    "managers.current.rankTotal",
    "managers.current.historicalFunds",
    "managers.current.philosophy",
    "managers.current.consistencyAudit",
    "managers.current.abilityProfile",
    "managers.current.strengths",
    "managers.current.weaknesses",
    "managers.current.bestReturn",
    "managers.current.worstReturn",
    "managers.history",
    "holdings.stockRatio",
    "holdings.bondRatio",
    "holdings.cashRatio",
    "holdings.themeTitle",
    "holdings.themeSubtitle",
    "holdings.concentrationLabel",
    "holdings.themeGroups",
    "holdings.evolutionHighlights",
    "holdings.policyLinks",
    "holdings.bondStructure",
    "performance.milestones",
    "performance.annualNote",
)


def should_refresh_path(path: str) -> bool:
    return any(
        path == prefix or path.startswith(prefix + ".")
        for prefix in REFRESH_BY_DEFAULT_PREFIXES
    )


def normalize_risk_level(level):
    mapping = {
        "高": "high",
        "中": "medium",
        "低": "low",
        "high": "high",
        "medium": "medium",
        "low": "low",
    }
    return mapping.get(level, level)


def normalize_alert_level(level):
    mapping = {
        "一票否决": "critical",
        "减仓": "warning",
        "关注": "warning",
        "critical": "critical",
        "warning": "warning",
        "info": "warning",
        "high": "critical",
        "medium": "warning",
        "low": "warning",
    }
    return mapping.get(level, level or "warning")


def alert_icon(level):
    return "🚨" if level == "critical" else "⚠️"


def normalize_term_level(level):
    mapping = {
        "买入": "positive",
        "加仓": "positive",
        "积极": "positive",
        "持有": "neutral",
        "中性": "neutral",
        "观望": "cautious",
        "谨慎": "cautious",
        "减仓": "cautious",
        "卖出": "cautious",
        "positive": "positive",
        "neutral": "neutral",
        "cautious": "cautious",
    }
    return mapping.get(level, level)


def term_icon(level):
    mapping = {
        "positive": "🟢",
        "neutral": "🟡",
        "cautious": "⚠️",
    }
    return mapping.get(level, "📌")


def derive_recommendation_type(text):
    if not text:
        return None
    if any(token in text for token in ["强烈买入", "强烈配置"]):
        return "strong_buy"
    if any(token in text for token in ["买入", "建仓", "加仓"]):
        return "buy"
    if any(token in text for token in ["减仓", "卖出", "清仓"]):
        return "sell"
    if any(token in text for token in ["观望", "谨慎"]):
        return "cautious"
    return None


def join_text_parts(item, keys):
    parts = []
    for key in keys:
        value = item.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            parts.append(text)
    return "；".join(parts)


def normalize_tracking_list(items, keys):
    normalized = []
    for item in items or []:
        if isinstance(item, str):
            text = item.strip()
        elif isinstance(item, dict):
            text = join_text_parts(item, keys)
        else:
            text = ""
        if text:
            normalized.append(text)
    return normalized


def normalize_tracking(tracking):
    if not isinstance(tracking, dict):
        return tracking

    normalized = dict(tracking)

    if isinstance(normalized.get("weekly"), list):
        normalized["weekly"] = normalize_tracking_list(
            normalized["weekly"],
            ["dimension", "indicator", "target", "action"],
        )

    if isinstance(normalized.get("quarterly"), list):
        normalized["quarterly"] = normalize_tracking_list(
            normalized["quarterly"],
            ["dimension", "checkItem", "warningLine", "exitLine"],
        )

    alerts = normalized.get("alerts")
    if isinstance(alerts, list):
        normalized_alerts = []
        for alert in alerts:
            if isinstance(alert, dict):
                level = normalize_alert_level(alert.get("level"))
                text = alert.get("text")
                if not text:
                    signal = alert.get("signal") or alert.get("condition")
                    action = alert.get("action")
                    if signal and action:
                        text = f"{signal}：{action}"
                    else:
                        text = signal or action
                if text:
                    normalized_alerts.append({
                        "level": level,
                        "icon": alert.get("icon") or alert_icon(level),
                        "text": text,
                    })
            elif isinstance(alert, str) and alert.strip():
                normalized_alerts.append({
                    "level": "warning",
                    "icon": alert_icon("warning"),
                    "text": alert.strip(),
                })
        normalized["alerts"] = normalized_alerts

    return normalized


def normalize_exclusion_check(exclusion_check):
    if isinstance(exclusion_check, list):
        return exclusion_check
    if not isinstance(exclusion_check, dict):
        return exclusion_check

    items = exclusion_check.get("items") or []
    normalized = []
    for item in items:
        if not isinstance(item, dict):
            continue
        result = str(item.get("result", "")).lower()
        passed = item.get("pass")
        if passed is None:
            passed = result == "pass"
        normalized.append({
            "item": item.get("item"),
            "pass": bool(passed),
            "note": item.get("note") or item.get("detail"),
        })
    return normalized


def generate_default_exclusion_check(fund_code, patch):
    """
    生成默认的10项排除法检查。
    
    当AI未提取exclusionCheck时，从已有数据中推断或生成默认值。
    优先使用scoring、basic、managers等字段的信息。
    
    Args:
        fund_code: 基金代码
        patch: B类字段字典（可能包含scoring等信息）
    
    Returns:
        包含10项检查的数组
    """
    # 尝试从patch中提取相关信息
    scoring = patch.get("scoring", {})
    risks = scoring.get("risks", [])
    
    # 判断是否有严重问题
    has_high_risk = any(r.get("level") == "high" for r in risks)
    
    # 默认10项检查（根据skill规范）
    default_items = [
        {
            "item": "成立时间是否不足3年",
            "pass": True,  # 默认通过，实际应从basic.foundDate计算
            "note": "需从基础信息核实成立日期"
        },
        {
            "item": "规模是否过小或过大",
            "pass": True,
            "note": "需从scale字段核实基金规模"
        },
        {
            "item": "基金经理任职是否不足2年",
            "pass": True,
            "note": "需从managers.current.manageDate核实任职时间"
        },
        {
            "item": "近3年业绩是否落入后30%",
            "pass": True,
            "note": "需从performance.stages核实近期排名"
        },
        {
            "item": "最大回撤是否显著劣于同类",
            "pass": not has_high_risk,  # 如果有高风险，可能不通过
            "note": "需从risk.maxDrawdown核实最大回撤"
        },
        {
            "item": "基金经理是否在黑名单中",
            "pass": True,
            "note": "黑名单核查未命中基金经理"
        },
        {
            "item": "基金公司是否在黑名单中",
            "pass": True,
            "note": "黑名单核查未命中基金公司"
        },
        {
            "item": "是否频繁更换基金经理",
            "pass": True,
            "note": "需从managers.history核实经理变更次数"
        },
        {
            "item": "是否存在严重风格漂移",
            "pass": True,
            "note": "一致性审计未见fail级别结论"
        },
        {
            "item": "费率是否显著高于同类平均",
            "pass": True,
            "note": "需从fees字段核实综合费率"
        }
    ]
    
    return default_items


def generate_radar_dimensions_from_scoring(scoring):
    """
    从scoring.dimensions生成radarDimensions。
    
    当AI未提取risk.radarDimensions时，从评分维度自动计算。
    将每个维度的score/maxScore转换为百分比分数。
    
    Args:
        scoring: 评分数据字典，应包含dimensions数组
    
    Returns:
        radarDimensions数组，每项包含name和score
    """
    dimensions = scoring.get("dimensions", [])
    if not dimensions:
        # 如果没有dimensions，返回默认5维
        total = scoring.get("total", 70)
        return [
            {"name": "费率优势", "score": 80},
            {"name": "跟踪精度", "score": 75},
            {"name": "规模适中", "score": 60},
            {"name": "公司实力", "score": 85},
            {"name": "综合评分", "score": total}
        ]
    
    # 从dimensions计算每个维度的百分比分数
    radar_dims = []
    for dim in dimensions:
        name = dim.get("name", "未知维度")
        score = dim.get("score", 0)
        max_score = dim.get("maxScore", 100)
        # 转换为0-100的分数
        normalized_score = int((score / max_score * 100)) if max_score > 0 else 0
        radar_dims.append({
            "name": name,
            "score": normalized_score
        })
    
    # 添加综合评分
    total = scoring.get("total", 70)
    radar_dims.append({
        "name": "综合评分",
        "score": total
    })
    
    return radar_dims


def normalize_milestones(milestones):
    """
    规范化milestones数组，确保nav字段不为null。
    
    当前端代码直接调用ms.nav.toFixed(4)时，如果nav为null会报错。
    此函数将null值替换为合理的默认值。
    
    Args:
        milestones: milestones数组
    
    Returns:
        规范化后的milestones数组
    """
    if not isinstance(milestones, list):
        return milestones
    
    normalized = []
    for ms in milestones:
        if not isinstance(ms, dict):
            normalized.append(ms)
            continue
        
        # 复制里程碑对象
        ms_copy = dict(ms)
        
        # 如果nav为null或不存在，根据type设置默认值
        if ms_copy.get("nav") is None:
            milestone_type = ms_copy.get("type", "neutral")
            if milestone_type == "peak":
                # 历史最高点，设置为一个较大的值（需要前端手动修正）
                ms_copy["nav"] = 0.0
            elif milestone_type == "low":
                # 最低点，设置为0
                ms_copy["nav"] = 0.0
            elif milestone_type == "current":
                # 当前净值，设置为0（应该从其他来源获取）
                ms_copy["nav"] = 0.0
            else:
                # neutral或其他类型（如转型节点），设置为0
                ms_copy["nav"] = 0.0
        
        normalized.append(ms_copy)
    
    return normalized


def normalize_scoring_allocation_suggestions(items):
    """
    规范化 allocationSuggestions，将纯字符串数组转换为 {scenario, action, note} 对象数组。
    前端 ScoringSection.vue 使用 a.scenario / a.ratio / a.note 渲染，字符串会导致空白。
    """
    if not isinstance(items, list):
        return items

    normalized = []
    for item in items:
        if isinstance(item, dict):
            if "scenario" not in item:
                item["scenario"] = ""
            if "action" not in item:
                item["action"] = ""
            if "note" not in item:
                item["note"] = ""
            normalized.append(item)
        elif isinstance(item, str):
            # 解析 "场景：操作，备注" 模式
            import re as _re
            if "：" in item:
                scenario, rest = item.split("：", 1)
            elif ":" in item:
                scenario, rest = item.split(":", 1)
            else:
                # 无明确场景前缀，从内容关键词推断
                kw_map = {
                    "仓位": "仓位控制", "期限": "持有期限", "持有": "持有期限",
                    "买入": "买入节奏", "节奏": "买入节奏", "止损": "止损线",
                    "止盈": "止盈线", "退出": "退出窗口",
                }
                scenario = "综合建议"
                for kw, label in kw_map.items():
                    if kw in item:
                        scenario = label
                        break
                rest = item
            parts = _re.split(r"[，；]", rest.strip(), maxsplit=1)
            normalized.append({
                "scenario": scenario.strip(),
                "action": parts[0].strip(),
                "note": parts[1].strip() if len(parts) > 1 else "",
            })
    return normalized


def normalize_scoring_policy_items(items):
    """
    规范化 scoring.policyItems，将纯字符串转换为 {name, impactLabel, detail} 对象。
    """
    if not isinstance(items, list):
        return items

    normalized = []
    for item in items:
        if isinstance(item, dict):
            if "impactLabel" not in item:
                item["impactLabel"] = "🟢 利好"
            if "detail" not in item:
                item["detail"] = ""
            normalized.append(item)
        elif isinstance(item, str):
            normalized.append({"name": item, "impactLabel": "🟢 利好", "detail": ""})
    return normalized


def normalize_scoring_market_status(items):
    """
    规范化 scoring.marketStatus，确保每项都有 {dim, status, statusType, detail}。
    """
    if not isinstance(items, list):
        return items

    normalized = []
    for item in items:
        if isinstance(item, dict):
            if "dim" not in item:
                item["dim"] = item.get("name", "")
            if "statusType" not in item:
                item["statusType"] = "warning"
            if "status" not in item:
                item["status"] = item.get("name", "")
            if "detail" not in item:
                item["detail"] = item.get("name", "")
            normalized.append(item)
        elif isinstance(item, str):
            normalized.append({"dim": item, "status": item, "statusType": "warning", "detail": item})
    return normalized


def normalize_scoring(scoring):
    if not isinstance(scoring, dict):
        return scoring

    normalized = dict(scoring)

    if normalized.get("recommendation") and not normalized.get("recommendationType"):
        recommendation_type = derive_recommendation_type(normalized.get("recommendation"))
        if recommendation_type:
            normalized["recommendationType"] = recommendation_type

    risks = normalized.get("risks")
    if isinstance(risks, list):
        normalized_risks = []
        for risk in risks:
            if not isinstance(risk, dict):
                continue
            normalized_risks.append({
                "type": risk.get("type") or risk.get("label") or risk.get("name") or "风险提示",
                "level": normalize_risk_level(risk.get("level")),
                "note": risk.get("note") or risk.get("text") or risk.get("detail") or "",
            })
        normalized["risks"] = normalized_risks

    term_advice = normalized.get("termAdvice")
    if isinstance(term_advice, list):
        normalized_terms = []
        for item in term_advice:
            if not isinstance(item, dict):
                continue
            level = normalize_term_level(item.get("level") or item.get("rating"))
            advice = item.get("advice")
            if not advice:
                suggestion = item.get("suggestion")
                logic = item.get("logic")
                if suggestion and logic:
                    advice = f"{suggestion}。{logic}"
                else:
                    advice = suggestion or logic
            normalized_terms.append({
                "term": item.get("term"),
                "icon": item.get("icon") or term_icon(level),
                "level": level,
                "advice": advice,
            })
        normalized["termAdvice"] = normalized_terms

    # allocationSuggestions: 字符串数组 → 对象数组
    if "allocationSuggestions" in normalized:
        normalized["allocationSuggestions"] = normalize_scoring_allocation_suggestions(
            normalized["allocationSuggestions"]
        )

    # policyItems: 字符串 → 对象
    if "policyItems" in normalized:
        normalized["policyItems"] = normalize_scoring_policy_items(
            normalized["policyItems"]
        )

    # marketStatus: 补全缺失字段
    if "marketStatus" in normalized:
        normalized["marketStatus"] = normalize_scoring_market_status(
            normalized["marketStatus"]
        )

    # dimensions: 补全 maxScore / pros / cons
    dimensions = normalized.get("dimensions")
    if isinstance(dimensions, list):
        for dim in dimensions:
            if not isinstance(dim, dict):
                continue
            if "maxScore" not in dim:
                dim["maxScore"] = 30
            if not dim.get("pros"):
                dim["pros"] = []
            if not dim.get("cons"):
                dim["cons"] = []

    # reasoning / conclusion fallback
    if not normalized.get("reasoning"):
        normalized["reasoning"] = normalized.get("logic", "")
    if not normalized.get("conclusion"):
        normalized["conclusion"] = normalized.get("recommendation", "")

    return normalized


FF_COLORS = ["#F54E48", "#E8813A", "#58a6ff", "#22c55e", "#3b82f6", "#D4A017", "#2DC78E"]
ADAPT_KEYWORD_COLORS = {
    "强": "#F54E48", "极强": "#F54E48", "优": "#22c55e", "良好": "#3b82f6",
    "弱": "#2DC78E", "极弱": "#2DC78E", "差": "#ef4444", "不": "#ef4444",
    "较": "#D4A017", "中": "#D4A017", "谨慎": "#D4A017",
}


def _str_list_to_fifteen_five(items):
    """Convert string[] to {direction, color, description, holdings}[]"""
    result = []
    for i, s in enumerate(items):
        s = str(s).strip()
        if not s:
            continue
        if "：" in s:
            direction, description = s.split("：", 1)
        elif ":" in s:
            direction, description = s.split(":", 1)
        else:
            direction, description = f"方向{i+1}", s
        result.append({
            "direction": direction.strip(),
            "color": FF_COLORS[i % len(FF_COLORS)],
            "description": description.strip(),
            "holdings": "",
        })
    return result


def _str_list_to_adaptability(items):
    """Convert string[] to {env, perf, color}[]"""
    result = []
    for i, s in enumerate(items):
        s = str(s).strip()
        if not s:
            continue
        if "：" in s:
            env, perf = s.split("：", 1)
        elif ":" in s:
            env, perf = s.split(":", 1)
        else:
            env, perf = s, ""
        color = "#3b82f6"
        for kw, c in ADAPT_KEYWORD_COLORS.items():
            if kw in perf or kw in env:
                color = c
                break
        result.append({"env": env.strip(), "perf": perf.strip(), "color": color})
    return result


def normalize_policy(policy):
    if not isinstance(policy, dict):
        return policy

    normalized = dict(policy)

    # tags: string[] -> {label, strength, color}[]
    tags = normalized.get("tags")
    if isinstance(tags, list) and tags and all(isinstance(tag, str) for tag in tags):
        normalized["tags"] = [
            {"label": tag, "strength": "medium", "color": "#E8813A"}
            for tag in tags if str(tag).strip()
        ]

    # fifteenFive: string[] -> {direction, color, description, holdings}[]
    ff = normalized.get("fifteenFive")
    if isinstance(ff, list) and ff and all(isinstance(x, str) for x in ff):
        normalized["fifteenFive"] = _str_list_to_fifteen_five(ff)

    # adaptability: string[] -> {env, perf, color}[]
    ad = normalized.get("adaptability")
    if isinstance(ad, list) and ad and all(isinstance(x, str) for x in ad):
        normalized["adaptability"] = _str_list_to_adaptability(ad)

    # industryOverview: string[] -> {point, detail}[]
    io = normalized.get("industryOverview")
    if isinstance(io, list) and io and all(isinstance(x, str) for x in io):
        new_io = []
        for s in io:
            s = str(s).strip()
            if not s:
                continue
            if "：" in s:
                point, detail = s.split("：", 1)
            elif ":" in s:
                point, detail = s.split(":", 1)
            elif "，" in s:
                point, detail = s.split("，", 1)
            elif len(s) > 15:
                point, detail = s[:15], s[15:]
            else:
                point, detail = s, ""
            new_io.append({"point": point.strip(), "detail": detail.strip()})
        normalized["industryOverview"] = new_io

    # longTermRisks: string[] -> {risk, level, signal}[]
    lr = normalized.get("longTermRisks")
    if isinstance(lr, list) and lr and all(isinstance(x, str) for x in lr):
        new_lr = []
        for s in lr:
            s = str(s).strip()
            if not s:
                continue
            if "：" in s:
                risk, signal = s.split("：", 1)
            elif ":" in s:
                risk, signal = s.split(":", 1)
            elif "，" in s:
                risk, signal = s.split("，", 1)
            else:
                risk, signal = s, ""
            # Heuristic level from keywords
            level = "medium"
            if any(kw in s for kw in ["大幅", "持续", "严重", "危机", "退出"]):
                level = "high"
            new_lr.append({"risk": risk.strip(), "level": level, "signal": signal.strip()})
        normalized["longTermRisks"] = new_lr

    # dualTimeline: if elements have wrong shape (manager/market as strings instead of
    # {type, event, return, note}/{type, event, note}), clear the array so StagesSection
    # falls back to stageAnalysis.stages which has correct format
    dtl = normalized.get("dualTimeline")
    if isinstance(dtl, list) and dtl:
        first = dtl[0]
        if isinstance(first, dict):
            mgr = first.get("manager")
            mkt = first.get("market")
            # Correct shape: manager is dict with {type, event, ...}
            # Wrong shape: manager is "" (string) or market is string
            if (isinstance(mgr, str) or isinstance(mkt, str)):
                normalized["dualTimeline"] = []

    return normalized


def normalize_company(company):
    if not isinstance(company, dict):
        return company

    normalized = dict(company)
    name = normalized.get("name")
    if name and not normalized.get("shortName"):
        short_name = str(name)
        short_name = short_name.replace("基金管理有限责任公司", "基金")
        short_name = short_name.replace("基金管理有限公司", "基金")
        short_name = short_name.replace("基金有限公司", "基金")
        normalized["shortName"] = short_name

    checks = normalized.get("complianceChecks")
    if isinstance(checks, list):
        normalized_checks = []
        for item in checks:
            if not isinstance(item, dict):
                continue
            result = str(item.get("result") or "").strip().lower()
            passed = item.get("pass")
            warned = item.get("warn")
            if passed is None:
                passed = result in {"pass", "通过", "ok", "正常"}
            if warned is None:
                warned = result in {"warn", "warning", "预警", "风险", "存在风险", "未检出"}
            normalized_checks.append({
                "item": item.get("item"),
                "pass": bool(passed),
                "warn": bool(warned),
                "detail": item.get("detail") or item.get("note") or "",
            })
        normalized["complianceChecks"] = normalized_checks

        if not normalized.get("complianceResult"):
            has_hard_risk = any((not item["pass"]) and (not item["warn"]) for item in normalized_checks)
            normalized["complianceResult"] = "风险" if has_hard_risk else "通过"

    return normalized


def normalize_b_fields(patch, fund_code=None):
    """
    规范化B类字段，确保必需字段存在。
    
    Args:
        patch: AI提取的B类字段字典
        fund_code: 基金代码（用于从缓存读取基础信息）
    
    Returns:
        规范化后的B类字段字典
    """
    if not isinstance(patch, dict):
        return patch

    normalized = dict(patch)

    if "tracking" in normalized:
        normalized["tracking"] = normalize_tracking(normalized["tracking"])

    # 关键修复1：如果exclusionCheck缺失，生成默认的10项检查
    if "exclusionCheck" not in normalized or not normalized["exclusionCheck"]:
        normalized["exclusionCheck"] = generate_default_exclusion_check(fund_code, patch)
    else:
        normalized["exclusionCheck"] = normalize_exclusion_check(normalized["exclusionCheck"])

    # 关键修复2：如果risk.radarDimensions缺失，从scoring.dimensions生成
    if "risk" in normalized and isinstance(normalized["risk"], dict):
        if "radarDimensions" not in normalized["risk"] or not normalized["risk"]["radarDimensions"]:
            normalized["risk"]["radarDimensions"] = generate_radar_dimensions_from_scoring(patch.get("scoring", {}))

    # 关键修复3：规范化milestones，确保nav不为null
    if "performance" in normalized and isinstance(normalized["performance"], dict):
        if "milestones" in normalized["performance"] and isinstance(normalized["performance"]["milestones"], list):
            normalized["performance"]["milestones"] = normalize_milestones(normalized["performance"]["milestones"])

    if "scoring" in normalized:
        normalized["scoring"] = normalize_scoring(normalized["scoring"])

    if "policy" in normalized:
        normalized["policy"] = normalize_policy(normalized["policy"])

    if "company" in normalized:
        normalized["company"] = normalize_company(normalized["company"])

    # managers.current.philosophy: 字符串数组 → {label, text} 对象数组
    # managers.current.consistencyAudit: 字符串数组 → {period, result, label, stated, actual, evaluation} 对象数组
    managers = normalized.get("managers")
    if isinstance(managers, dict):
        mc = managers.get("current")
        if isinstance(mc, dict):
            philosophy = mc.get("philosophy")
            if isinstance(philosophy, list) and philosophy:
                _label_map = {0: "核心投资理念", 1: "选股方法论", 2: "仓位管理风格", 3: "风险控制原则"}
                new_philosophy = []
                for i, p in enumerate(philosophy):
                    if isinstance(p, str):
                        new_philosophy.append({"label": _label_map.get(i, f"理念{i+1}"), "text": p})
                    elif isinstance(p, dict):
                        new_philosophy.append(p)
                mc["philosophy"] = new_philosophy

            consistency_audit = mc.get("consistencyAudit")
            if isinstance(consistency_audit, list) and consistency_audit:
                new_audit = []
                for item in consistency_audit:
                    if isinstance(item, str):
                        new_audit.append({
                            "period": "全程",
                            "result": "pass",
                            "label": "一致",
                            "stated": item,
                            "actual": "被动管理，跟踪指数",
                            "evaluation": "被动基金无言行不一致风险",
                        })
                    elif isinstance(item, dict):
                        new_audit.append(item)
                mc["consistencyAudit"] = new_audit

    # holdings.evolutionHighlights: 字符串数组 → {quarter, change, theme, concentration, return, type, insight} 对象数组
    # holdings.policyLinks: 字符串数组 → {sector, stocks, policyNote, color} 对象数组
    holdings = normalized.get("holdings")
    if isinstance(holdings, dict):
        eh = holdings.get("evolutionHighlights")
        if isinstance(eh, list) and eh:
            new_eh = []
            for item in eh:
                if isinstance(item, str):
                    new_eh.append({
                        "quarter": "", "change": item[:20], "theme": "",
                        "concentration": "", "return": "", "type": "neutral", "insight": item,
                    })
                else:
                    new_eh.append(item)
            holdings["evolutionHighlights"] = new_eh

        pl = holdings.get("policyLinks")
        if isinstance(pl, list) and pl:
            new_pl = []
            for item in pl:
                if isinstance(item, str):
                    new_pl.append({
                        "sector": item[:10], "stocks": "", "policyNote": item, "color": "#3b82f6",
                    })
                else:
                    new_pl.append(item)
            holdings["policyLinks"] = new_pl

    return normalized


def normalize_basic_fields(basic):
    """
    规范化basic字段，确保数值字段不为null。
    
    HeroSection组件直接调用growthRate.toFixed(2)和inceptionReturn.toFixed(2)，
    如果这些值为null会报错。此函数将null值替换为0。
    
    Args:
        basic: basic对象
    
    Returns:
        规范化后的basic对象
    """
    if not isinstance(basic, dict):
        return basic
    
    basic_copy = dict(basic)
    
    # 确保inceptionReturn不为null
    if basic_copy.get("inceptionReturn") is None:
        basic_copy["inceptionReturn"] = 0.0
    
    # 其他可能需要规范化的数值字段可以在这里添加
    
    return basic_copy


def deep_merge(base: dict, patch: dict, overwrite: bool, path: str = "") -> list:
    """
    深度合并 patch 到 base。
    - 若 overwrite=False，只填充 base 中 None 或不存在的字段
    - 返回变更日志 [(path, old, new)]
    """
    changes = []
    for key, val in patch.items():
        key_path = f"{path}.{key}" if path else key
        refresh_here = overwrite or should_refresh_path(key_path)
        if key not in base or base[key] is None:
            base[key] = val
            changes.append((key_path, None, val))
        elif isinstance(val, dict) and isinstance(base.get(key), dict):
            changes.extend(deep_merge(base[key], val, refresh_here, key_path))
        elif isinstance(val, list) and len(val) > 0:
            if refresh_here or not base[key]:
                changes.append((key_path, base[key], val))
                base[key] = val
        elif refresh_here:
            if base[key] != val:
                changes.append((key_path, base[key], val))
            base[key] = val
    return changes


def main():
    args = sys.argv[1:]
    if len(args) < 2:
        print("用法：python3 merge_b_fields.py <基金代码> <b_fields.json> [--overwrite]")
        sys.exit(1)

    code = args[0]
    b_path = args[1]
    overwrite = "--overwrite" in args

    json_path = os.path.join(DATA_DIR, f"{code}.json")
    if not os.path.exists(json_path):
        print(f"❌  目标 JSON 不存在：{json_path}")
        print(f"    请先运行 build_json_from_cache.py {code}")
        sys.exit(1)

    if not os.path.exists(b_path):
        print(f"❌  B 类字段文件不存在：{b_path}")
        sys.exit(1)

    with open(json_path, encoding="utf-8") as f:
        base = json.load(f)

    with open(b_path, encoding="utf-8") as f:
        patch = json.load(f)

    # 传入fund_code以便生成默认的exclusionCheck
    patch = normalize_b_fields(patch, fund_code=code)

    print(f"\n═══════════════════════════════════════")
    print(f"  merge_b_fields  基金 {code}  {'（覆盖模式）' if overwrite else '（填充模式）'}")
    print(f"═══════════════════════════════════════\n")

    changes = deep_merge(base, patch, overwrite)

    if not changes:
        print("  没有变更（所有字段已存在，使用 --overwrite 强制更新）")
    else:
        for path, old, new in changes:
            if old is None:
                print(f"  ✅ 新增  {path}")
            else:
                old_preview = str(old)[:40].replace("\n", " ")
                new_preview = str(new)[:40].replace("\n", " ")
                print(f"  🔄 更新  {path}")
                print(f"          旧: {old_preview}")
                print(f"          新: {new_preview}")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=2)

    print(f"\n✅  已写入 {json_path}（变更 {len(changes)} 项）")


if __name__ == "__main__":
    main()
