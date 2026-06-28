#!/usr/bin/env python3
"""
Bilibili Video Summary Extractor — fetch video info, then extract the AI's
summary from private messages and produce wiki-ready output.

Workflow:
    User asks AI bot (B站 UID) to watch a video and summarize.
    AI sends text + images to user's Bilibili DMs.
    User gives this script the video URL.
    Script finds the AI's summary in DMs and outputs structured result.

Usage:
    export BILIBILI_SESSDATA=...
    export BILIBILI_BILI_JCT=...
    export BILIBILI_BUVID3=...
    export BILIBILI_AI_UID=1095342058

    python3 bilibili_video_summary.py --video-url "https://b23.tv/xxxxx"
    python3 bilibili_video_summary.py --video-url "BV1xx..." --format wiki
    python3 bilibili_video_summary.py --video-url "BV1xx..." --format json
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone, timedelta

try:
    from curl_cffi import requests as cffi_requests
    SESSION = cffi_requests.Session(impersonate="chrome124")
    HAS_CURL_CFFI = True
except ImportError:
    import requests as std_requests
    SESSION = std_requests.Session()
    HAS_CURL_CFFI = False

# ── Constants ──────────────────────────────────────────────────────────────

API_BILI = "https://api.bilibili.com"
API_VC   = "https://api.vc.bilibili.com"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
LOCAL_TZ = timezone(timedelta(hours=8))  # CST

# ── Auth ───────────────────────────────────────────────────────────────────

def load_credentials() -> dict:
    sessdata = os.environ.get("BILIBILI_SESSDATA")
    bili_jct = os.environ.get("BILIBILI_BILI_JCT")
    buvid3   = os.environ.get("BILIBILI_BUVID3")
    buvid4   = os.environ.get("BILIBILI_BUVID4")
    missing = []
    if not sessdata: missing.append("BILIBILI_SESSDATA")
    if not bili_jct: missing.append("BILIBILI_BILI_JCT")
    if not buvid3:   missing.append("BILIBILI_BUVID3")
    if missing:
        raise SystemExit(
            "Missing: " + ", ".join(missing)
        )
    creds = {"SESSDATA": sessdata, "bili_jct": bili_jct, "buvid3": buvid3}
    if buvid4: creds["buvid4"] = buvid4
    return creds

def build_headers(creds: dict) -> dict:
    parts = [f"SESSDATA={creds['SESSDATA']}", f"bili_jct={creds['bili_jct']}"]
    if "buvid3" in creds: parts.append(f"buvid3={creds['buvid3']}")
    if "buvid4" in creds: parts.append(f"buvid4={creds['buvid4']}")
    return {"User-Agent": USER_AGENT, "Referer": "https://www.bilibili.com/",
            "Cookie": "; ".join(parts)}

def api_get(url: str, headers: dict, params: dict | None = None,
            retries: int = 2) -> dict:
    for attempt in range(retries + 1):
        try:
            resp = SESSION.get(url, headers=headers, params=params, timeout=15)
        except Exception as exc:
            if attempt < retries: time.sleep(2); continue
            raise SystemExit(f"Request failed: {exc}")
        if resp.status_code == 412:
            raise SystemExit("412 — SESSDATA expired or missing buvid3.")
        if resp.status_code == 403:
            raise SystemExit("403 — credentials invalid.")
        if resp.status_code != 200:
            if attempt < retries: time.sleep(2); continue
            raise SystemExit(f"HTTP {resp.status_code}: {resp.text[:200]}")
        try:
            data = resp.json()
        except json.JSONDecodeError:
            if attempt < retries: time.sleep(2); continue
            raise SystemExit(f"Non-JSON: {resp.text[:200]}")
        if data.get("code") != 0:
            raise SystemExit(f"API error ({data.get('code')}): "
                             f"{data.get('message', data.get('msg', '?'))}")
        return data.get("data") or data
    raise SystemExit("Exhausted retries.")

def parse_json_content(raw: str) -> dict:
    if not raw: return {}
    try:
        return json.loads(raw) if isinstance(raw, str) else raw
    except (json.JSONDecodeError, TypeError):
        return {"content": str(raw)}

def fmt_ts(ts: int) -> str:
    dt = datetime.fromtimestamp(ts, tz=LOCAL_TZ)
    return dt.strftime("%Y-%m-%dT%H:%M:%S+08:00")

# ── Video info ─────────────────────────────────────────────────────────────

BVID_RE = re.compile(r'[Bb][Vv][0-9A-Za-z]{10,}')
AID_RE = re.compile(r'av(\d+)', re.IGNORECASE)
BV_RE_STRICT = re.compile(r'^[Bb][Vv][0-9A-Za-z]{10,}$')

def extract_bvid(url_or_bvid: str) -> str:
    """Extract BV id from URL or return as-is if already a BV id."""
    m = BVID_RE.search(url_or_bvid)
    if m:
        return m.group(0)
    m = AID_RE.search(url_or_bvid)
    if m:
        # We could convert aid to bvid via API, but Bilibili now prefers BV
        # We'll handle it in fetch_video_info
        return f"av{m.group(1)}"
    raise SystemExit(f"Could not extract BVID from: {url_or_bvid}")

def fetch_video_info(bvid: str, headers: dict) -> dict:
    """Fetch video metadata from Bilibili API."""
    params = {}
    if bvid.startswith("BV") or bvid.startswith("bv"):
        params["bvid"] = bvid
    elif bvid.startswith("av"):
        params["aid"] = bvid[2:]
    else:
        params["bvid"] = bvid
    data = api_get(f"{API_BILI}/x/web-interface/view",
                   headers=headers, params=params)
    return {
        "title": data.get("title", "?"),
        "author": data.get("owner", {}).get("name", "?"),
        "author_uid": data.get("owner", {}).get("mid", 0),
        "bvid": data.get("bvid", bvid),
        "aid": data.get("aid", 0),
        "pic": data.get("pic", ""),
        "desc": data.get("desc", ""),
        "duration": data.get("duration", 0),
    }

def extract_title_keywords(title: str) -> list[str]:
    """Extract searchable keywords from video title.
    
    Strategy: split by common delimiters, take meaningful chunks.
    """
    # Remove punctuation, split by common delimiters
    cleaned = re.sub(r'[《》「」【】\[\]()（）！？，。、：；""''…· \t\n\r\f\v]', ' ', title)
    parts = [p.strip() for p in cleaned.split() if len(p.strip()) >= 2]
    # Deduplicate while preserving order
    seen = set()
    result = []
    for p in parts:
        if p not in seen:
            seen.add(p)
            result.append(p)
    return result

# ── DM search ──────────────────────────────────────────────────────────────

def fetch_ai_messages(ai_uid: str, headers: dict, fetch_limit: int = 50,
                     page_size: int = 50) -> list[dict]:
    """Fetch messages from the AI user's DM session."""
    params = {
        "session_type": 1,
        "talker_id": ai_uid,
        "begin_seqno": 0,
        "size": page_size,
        "sender_device_id": "1",
        "build": 0,
        "mobi_app": "web",
    }
    data = api_get(
        f"{API_VC}/svr_sync/v1/svr_sync/fetch_session_msgs",
        headers=headers, params=params
    )
    messages = data.get("messages", [])
    has_more = data.get("has_more", 0)

    # If there are more messages and we want more, paginate backward
    all_msgs = list(messages)
    # The API returns from newest to oldest
    # We already have the newest 'page_size' messages

    return all_msgs

def search_summary_in_messages(messages: list[dict], video_info: dict) -> dict | None:
    """Search through messages for the summary matching this video.
    
    Returns dict with matched text messages and image URLs, or None.
    """
    bvid = video_info.get("bvid", "").upper()
    title = video_info.get("title", "")
    title_keywords = extract_title_keywords(title)

    # Priority levels for matching:
    # 1. BV号 in message (most reliable)
    # 2. Full title in message (via 《》 quotes from AI format)
    # 3. Keyword overlap (multiple title keywords)
    
    result = {
        "matched": False,
        "text_parts": [],
        "image_urls": [],
        "match_method": "",
        "match_confidence": 0,  # 0-100
        "timestamp": 0,
        "all_messages_before": [],  # messages before the matched summary
    }

    # First pass: find the anchor message (the one that mentions this video)
    anchor_idx = -1

    for i, msg in enumerate(messages):
        msg_type = msg.get("msg_type", 1)
        raw_cont = msg.get("content", "{}")
        cont_obj = parse_json_content(raw_cont)
        text = cont_obj.get("content", cont_obj.get("message", ""))
        
        if not text:
            continue

        # Check for BV号 match
        if bvid and bvid in text.upper():
            anchor_idx = i
            result["match_method"] = "bvid_in_message"
            result["match_confidence"] = 100
            break

        # Check for title in 《》 format
        quote_match = re.search(r'《([^》]+)》', text)
        if quote_match:
            quoted = quote_match.group(1).strip()
            # Fuzzy match: check if significant portion of title is in quoted
            title_short = re.sub(r'[^\u4e00-\u9fff\w]', '', title)
            quoted_short = re.sub(r'[^\u4e00-\u9fff\w]', '', quoted)
            if len(quoted_short) >= 4 and quoted_short in title_short:
                anchor_idx = i
                result["match_method"] = "title_quote"
                result["match_confidence"] = 95
                break

    # Second pass: keyword overlap scoring (if no direct match)
    if anchor_idx == -1 and title_keywords:
        best_score = 0
        best_idx = -1
        for i, msg in enumerate(messages):
            msg_type = msg.get("msg_type", 1)
            if msg_type != 1:
                continue
            raw_cont = msg.get("content", "{}")
            cont_obj = parse_json_content(raw_cont)
            text = cont_obj.get("content", "")
            if not text:
                continue
            
            score = sum(1 for kw in title_keywords if kw in text)
            if score > best_score:
                best_score = score
                best_idx = i
        
        if best_score >= max(2, len(title_keywords) // 2):
            anchor_idx = best_idx
            result["match_method"] = f"keyword_overlap({best_score}/{len(title_keywords)})"
            result["match_confidence"] = min(90, int(best_score / max(1, len(title_keywords)) * 80) + 10)

    if anchor_idx == -1:
        return None

    # Now collect the summary:
    # The AI's summary is the anchor message + subsequent images
    # Messages are newest first. Anchor message IS the summary text.
    # Images before/after it might be part of the summary.
    # Strategy: include anchor message text + nearby images from same sender
    
    anchor_sender = str(messages[anchor_idx].get("sender_uid", ""))

    # Collect text from the anchor message
    raw_cont = messages[anchor_idx].get("content", "{}")
    cont_obj = parse_json_content(raw_cont)
    anchor_text = cont_obj.get("content", cont_obj.get("message", ""))
    result["text_parts"].append(anchor_text)
    result["timestamp"] = messages[anchor_idx].get("timestamp", 0)
    anchor_ts = result["timestamp"]

    # Collect related messages within same time burst (same sender, ±5 min)
    # Bilibili sends each image as a separate message; a summary burst spans seconds.
    BURST_WINDOW = 300  # 5 minutes
    
    # Store text fragments as (timestamp, text) tuples for later sorting
    text_fragments = [(anchor_ts, anchor_text)]
    image_fragments = []

    for i, msg in enumerate(messages):
        if i == anchor_idx:
            continue
        if str(msg.get("sender_uid", "")) != anchor_sender:
            continue
        msg_ts = msg.get("timestamp", 0)
        if abs(msg_ts - anchor_ts) > BURST_WINDOW:
            continue  # Too far in time — belongs to a different summary

        msg_type = msg.get("msg_type", 1)
        raw_cont = msg.get("content", "{}")
        cont_obj = parse_json_content(raw_cont)

        if msg_type == 2:  # Image
            url = cont_obj.get("url", "")
            if url:
                image_fragments.append({
                    "url": url,
                    "timestamp": msg_ts,
                })
        elif msg_type == 1:  # Text — additional notes in the same burst
            text = cont_obj.get("content", "")
            if text and text != anchor_text:
                text_fragments.append((msg_ts, text))

    # Sort text fragments by timestamp ascending (oldest first = proper reading order)
    text_fragments.sort(key=lambda x: x[0])
    sorted_texts = [t[1] for t in text_fragments]

    # Merge fragments that were split at Bilibili's 500-char DM limit
    # A fragment at/near the max length was truncated mid-content by the server.
    DM_MAX_LEN = 500
    merged = [sorted_texts[0]] if sorted_texts else []
    for f in sorted_texts[1:]:
        prev = merged[-1]
        if len(prev) >= DM_MAX_LEN - 20:  # truncated → continuation
            merged[-1] = prev + f
        else:
            merged.append(f)
    result["text_parts"] = merged
    
    # Sort image fragments by timestamp ascending
    image_fragments.sort(key=lambda x: x["timestamp"])
    result["image_urls"] = image_fragments

    # Collect messages before the summary (for context)
    result["all_messages_before"] = messages[anchor_idx+1:] if anchor_idx < len(messages) - 1 else []
    result["matched"] = True

    return result

# ── High-quality comments ────────────────────────────────────────────

def _is_low_quality_comment(msg: str) -> bool:
    """Check if a comment is low-quality (spam, @-requests, too short)."""
    msg = msg.strip()
    if len(msg) < 15:
        return True
    # Check for @-mention + note-request patterns
    has_at = '@' in msg
    request_patterns = ['发我邮箱', '发到我邮箱', '发到我的邮箱', '发给我', 
                        '详细笔记', '整理笔记', '记笔记']
    is_request = any(p in msg for p in request_patterns)
    if has_at and is_request:
        return True
    # Pure emoji / gibberish
    if all(c in '👍👎😊😂🤣❤️🙏💪😍✨🌟⭐🔥💯🎉😄😆😅🤔😌😏🙄😴😪😷🤒🤕🤢🤮🥴'
           or ord(c) < 128 for c in msg.strip()):
        return False  # Keep meaningful short comments
    return False


def fetch_quality_comments(aid: int, headers: dict, target: int = 5) -> list[dict]:
    """Fetch comments and filter for high-quality ones.
    
    Strategy: fetch up to 60 replies (3 pages), sort by likes,
    then filter out low-quality entries (spam, @-requests, too short).
    Returns at most `target` high-quality comments.
    """
    all_replies = []
    for page in range(1, 4):
        params = {
            "oid": aid,
            "type": 1,
            "pn": page,
            "ps": 20,
            "sort": 2,
        }
        data = api_get(f"{API_BILI}/x/v2/reply",
                       headers=headers, params=params)
        replies = data.get("replies", [])
        if not replies:
            break
        all_replies.extend(replies)
        time.sleep(0.3)
    
    # Sort by likes descending
    all_replies.sort(key=lambda x: x.get("like", 0), reverse=True)
    
    comments = []
    for rp in all_replies:
        msg = rp.get("content", {}).get("message", "").strip()
        if not msg:
            continue
        if _is_low_quality_comment(msg):
            continue
        rpid = rp.get("rpid", 0)
        rcount = rp.get("rcount", 0)
        comment = {
            "uname": rp.get("member", {}).get("uname", "?"),
            "mid": rp.get("mid", 0),
            "like": rp.get("like", 0),
            "message": msg,
            "ctime": rp.get("ctime", 0),
            "rcount": rcount,
            "rpid": rpid,
            "sub_replies": [],  # populated below if it's a question with replies
        }
        # Fetch sub-replies if comment looks like a question and has replies
        if rcount > 0 and _is_question_comment(msg):
            try:
                comment["sub_replies"] = fetch_comment_replies(
                    aid, headers, rpid, max_replies=min(rcount, 6)
                )
            except SystemExit:
                pass  # sub-replies non-critical, skip on error
        comments.append(comment)
        if len(comments) >= target:
            break
    return comments


def _is_question_comment(msg: str) -> bool:
    """Check if a comment appears to be asking a question."""
    msg = msg.strip()
    if '？' in msg or '?' in msg:
        return True
    question_starts = ['请问', '想请教', '请教', '大佬，', 'up主，', 'up up', '有个问题',
                       '有没有什么好的', '该如何', '怎么', 'adr是什么']
    for qs in question_starts:
        if msg.startswith(qs):
            return True
    return False


def fetch_comment_replies(aid: int, headers: dict, root_rpid: int,
                          max_replies: int = 6) -> list[dict]:
    """Fetch sub-replies for a specific comment (question thread)."""
    all_srs = []
    for page in range(1, 3):  # up to 2 pages
        data = api_get(
            f"{API_BILI}/x/v2/reply/reply",
            headers=headers,
            params={"oid": aid, "type": 1, "root": root_rpid,
                    "ps": 20, "pn": page},
        )
        replies = data.get("replies", [])
        if not replies:
            break
        all_srs.extend(replies)
        time.sleep(0.3)
    all_srs.sort(key=lambda x: x.get("like", 0), reverse=True)
    
    results = []
    for sr in all_srs[:max_replies]:
        text = sr.get("content", {}).get("message", "").strip()
        if not text:
            continue
        results.append({
            "uname": sr.get("member", {}).get("uname", "?"),
            "like": sr.get("like", 0),
            "message": text,
            "ctime": sr.get("ctime", 0),
        })
    return results

def summarize_comments(comments: list[dict], top_n: int = 3) -> dict:
    """Generate a brief summary of top comments.
    
    Returns {count, top_likes, summary_points, themes}.
    """
    if not comments:
        return {"count": 0, "top_likes": 0, "summary_points": [], "themes": []}
    
    total_likes = sum(c["like"] for c in comments)
    
    return {
        "count": len(comments),
        "top_likes": total_likes,
        "summary_points": [c["message"][:150] for c in comments[:top_n]],
        "themes": [],  # Placeholder for future NLP extraction
    }

# ── Output formatters ──────────────────────────────────────────────────────

def format_wiki(video_info: dict, summary: dict, ai_uid: str,
                comments: list[dict] | None = None) -> str:
    """Generate wiki-ready markdown with proper frontmatter."""
    now = datetime.now(tz=LOCAL_TZ).strftime("%Y-%m-%dT%H:%M:%S+08:00")
    title = video_info["title"]
    bvid = video_info["bvid"]
    video_url = f"https://www.bilibili.com/video/{bvid}"

    # Generate a slug-able file title
    # Remove special characters for filename
    safe_title = re.sub(r'[\\/:*?"<>|]', '', title)[:60]
    
    text_body = "\n\n".join(summary["text_parts"])
    # Build markdown
    md = f"""---
title: "{title}"
created: {now}
updated: {now}
type: summary
tags: [bilibili, video-summary]
sources: []
---

# {title}

> 原视频：[{video_url}]({video_url})
> UP主：{video_info['author']}

---

## AI 总结内容

{text_body}
"""
    if summary["image_urls"]:
        md += "\n\n### 附带图片\n\n"
        for img in summary["image_urls"]:
            md += f"![]({img['url']})\n\n"
    
    # ── High-quality comments section ──
    if comments:
        md += "\n\n---\n\n## 高质量评论\n\n"
        for i, c in enumerate(comments, 1):
            ts_str = fmt_ts(c["ctime"]) if c["ctime"] else ""
            md += f"### {i}. {c['uname']} · 👍 {c['like']}\n\n"
            md += f"{c['message']}\n\n"
            # ── Sub-replies (question → answer thread) ──
            if c.get("sub_replies"):
                md += "> 💬 问答讨论：\n>\n"
                for sr in c["sub_replies"]:
                    sr_name = sr["uname"]
                    sr_like = sr["like"]
                    sr_msg = sr["message"]
                    md += f"> **{sr_name}** (👍{sr_like}) — {sr_msg}\n>\n"
                md += "\n"
            meta_parts = []
            if c["rcount"] > 0:
                meta_parts.append(f"回复数：{c['rcount']}")
            if ts_str:
                meta_parts.append(f"时间：{ts_str}")
            if meta_parts:
                md += "> " + " ｜ ".join(meta_parts) + "\n\n"
            md += "---\n\n"
    
    md += f"""## 元信息

- **视频标题**: {title}
- **视频地址**: {video_url}
- **UP主**: {video_info['author']} (UID {video_info['author_uid']})
- **AI UID**: {ai_uid}
- **匹配方式**: {summary.get('match_method', '?')}
- **匹配置信度**: {summary.get('match_confidence', 0)}%
- **提取时间**: {now}
"""
    return md

def format_text(video_info: dict, summary: dict, ai_uid: str,
                comments: list[dict] | None = None) -> str:
    """Human-readable text output."""
    bvid = video_info["bvid"]
    lines = []
    lines.append(f"=== 视频信息 ===")
    lines.append(f"标题: {video_info['title']}")
    lines.append(f"UP主: {video_info['author']}")
    lines.append(f"链接: https://www.bilibili.com/video/{bvid}")
    lines.append(f"")
    lines.append(f"=== AI 总结内容 (UID {ai_uid}) ===")
    for part in summary["text_parts"]:
        lines.append(part)
        lines.append("")
    if summary["image_urls"]:
        lines.append("---")
        lines.append(f"附带图片 ({len(summary['image_urls'])} 张):")
        for img in summary["image_urls"]:
            lines.append(f"  📷 {img['url']}")
        lines.append("")
    lines.append(f"---")
    lines.append(f"匹配方式: {summary.get('match_method', '?')}")
    lines.append(f"置信度: {summary.get('match_confidence', 0)}%")
    if comments:
        lines.append("")
        lines.append(f"=== 高质量评论 (TOP {len(comments)}) ===")
        for i, c in enumerate(comments, 1):
            lines.append("")
            lines.append(f"#{i} [{c['like']}👍] {c['uname']}:")
            lines.append(f"  {c['message'][:300]}")
            # Sub-replies in text format
            if c.get("sub_replies"):
                for sr in c["sub_replies"]:
                    lines.append(f"  ↳ [{sr['like']}👍] {sr['uname']}: {sr['message'][:200]}")
    return "\n".join(lines)

def format_json(video_info: dict, summary: dict | None, ai_uid: str,
                comments: list[dict] | None = None) -> str:
    """JSON output for programmatic consumption."""
    output = {
        "video": video_info,
        "ai_uid": ai_uid,
        "summary_found": summary["matched"] if summary else False,
    }
    if summary and summary["matched"]:
        output["summary"] = {
            "text_parts": summary["text_parts"],
            "image_urls": summary["image_urls"],
            "match_method": summary.get("match_method", ""),
            "match_confidence": summary.get("match_confidence", 0),
            "timestamp": summary.get("timestamp", 0),
        }
    if comments:
        output["comments"] = comments
    return json.dumps(output, ensure_ascii=False, indent=2)


# ── CLI ────────────────────────────────────────────────────────────────────

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Bilibili Video Summary Extractor"
    )
    p.add_argument("--video-url", required=True,
                   help="Bilibili video URL or BV id")
    p.add_argument("--ai-uid", default=None,
                   help=f"AI bot's Bilibili UID (default: $BILIBILI_AI_UID or {os.environ.get('BILIBILI_AI_UID', 'not set')})")
    p.add_argument("--limit", type=int, default=50,
                   help="Max DMs to fetch (default: 50)")
    p.add_argument("--format", choices=["text", "json", "wiki"], default="text",
                   help="Output format (default: text)")
    p.add_argument("--comments", type=int, default=5,
                   help="Number of top comments to fetch (0 to skip, default: 5)")
    return p.parse_args(argv)

def main(argv: list[str] | None = None):
    args = parse_args(argv)

    ai_uid = args.ai_uid or os.environ.get("BILIBILI_AI_UID")
    if not ai_uid:
        raise SystemExit(
            "AI UID not set. Pass --ai-uid or set BILIBILI_AI_UID env var."
        )

    creds = load_credentials()
    headers = build_headers(creds)

    print(f"[info] {'curl_cffi' if HAS_CURL_CFFI else 'requests'} auth OK",
          file=sys.stderr)

    # Step 1: Extract BVID
    bvid = extract_bvid(args.video_url)
    print(f"[info] BVID: {bvid}", file=sys.stderr)

    # Step 2: Fetch video info
    video_info = fetch_video_info(bvid, headers)
    print(f"[info] Title: {video_info['title'][:80]}", file=sys.stderr)
    print(f"[info] Author: {video_info['author']}", file=sys.stderr)
    print(f"[info] AID: {video_info['aid']}", file=sys.stderr)

    # Step 3: Fetch top comments (optional)
    comments = None
    if args.comments > 0:
        print(f"[info] Fetching top {args.comments} comments...", file=sys.stderr)
        try:
            comments = fetch_quality_comments(video_info['aid'], headers, target=args.comments)
            print(f"[info] Got {len(comments)} comments", file=sys.stderr)
        except SystemExit as e:
            print(f"[warn] Comments unavailable: {e}", file=sys.stderr)
    
    # Step 4: Fetch AI's DMs
    print(f"[info] Fetching DMs from AI (UID {ai_uid})...", file=sys.stderr)
    messages = fetch_ai_messages(ai_uid, headers, fetch_limit=args.limit)
    print(f"[info] Got {len(messages)} messages", file=sys.stderr)

    # Step 4: Search for matching summary
    print(f"[info] Searching for summary matching \"{video_info['title'][:50]}...\"",
          file=sys.stderr)
    matched = search_summary_in_messages(messages, video_info)

    # Step 5: Output
    if not matched or not matched["matched"]:
        # Try keyword matching with individual title words
        print("[warn] No direct match found, trying keyword search...",
              file=sys.stderr)
        # Already done in search_summary_in_messages
        if args.format == "json":
            print(format_json(video_info, None, ai_uid))
        else:
            print(f"\n❌ 未在 AI (UID {ai_uid}) 的最近 {len(messages)} 条私信中"
                  f"找到与视频《{video_info['title']}》匹配的总结。")
            print(f"\n可能原因：")
            print(f"  1. AI 还没发总结")
            print(f"  2. 总结在更早的消息里（尝试增大 --limit）")
            print(f"  3. AI UID 不对")
        return

    if args.format == "wiki":
        output = format_wiki(video_info, matched, ai_uid, comments=comments)
    elif args.format == "json":
        output = format_json(video_info, matched, ai_uid, comments=comments)
    else:
        output = format_text(video_info, matched, ai_uid, comments=comments)

    print(output)

if __name__ == "__main__":
    main()
