#!/usr/bin/env python3
"""
Bilibili Message Extractor — fetch replies, @-mentions & private messages.

Usage:
    export BILIBILI_SESSDATA=...
    export BILIBILI_BILI_JCT=...
    export BILIBILI_BUVID3=...
    python3 bilibili_msg.py --action unread
    python3 bilibili_msg.py --action replies --limit 10
    python3 bilibili_msg.py --action sessions
    python3 bilibili_msg.py --action messages --session-id 1095342058 --limit 20

Authentication:
    Environment variables:
        BILIBILI_SESSDATA   — SESSDATA cookie (required)
        BILIBILI_BILI_JCT   — bili_jct cookie (required)
        BILIBILI_BUVID3     — buvid3 cookie (required)
        BILIBILI_BUVID4     — buvid4 cookie (optional)
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime

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

# ── Auth ───────────────────────────────────────────────────────────────────

def load_credentials() -> dict:
    """Load credentials from individual environment variables."""
    sessdata = os.environ.get("BILIBILI_SESSDATA")
    bili_jct = os.environ.get("BILIBILI_BILI_JCT")
    buvid3   = os.environ.get("BILIBILI_BUVID3")
    buvid4   = os.environ.get("BILIBILI_BUVID4")

    missing = []
    if not sessdata:
        missing.append("BILIBILI_SESSDATA")
    if not bili_jct:
        missing.append("BILIBILI_BILI_JCT")
    if not buvid3:
        missing.append("BILIBILI_BUVID3")

    if missing:
        raise SystemExit(
            "Missing required env var(s): " + ", ".join(missing) + "\n"
            "Set them before running:\n"
            "  export BILIBILI_SESSDATA=...\n"
            "  export BILIBILI_BILI_JCT=...\n"
            "  export BILIBILI_BUVID3=...\n"
            "  export BILIBILI_BUVID4=...   (optional but recommended)"
        )

    creds = {"SESSDATA": sessdata, "bili_jct": bili_jct, "buvid3": buvid3}
    if buvid4:
        creds["buvid4"] = buvid4
    return creds


def build_headers(creds: dict) -> dict:
    """Build headers with auth cookies."""
    cookie_parts = [
        f"SESSDATA={creds['SESSDATA']}",
        f"bili_jct={creds['bili_jct']}",
    ]
    if "buvid3" in creds:
        cookie_parts.append(f"buvid3={creds['buvid3']}")
    if "buvid4" in creds:
        cookie_parts.append(f"buvid4={creds['buvid4']}")
    return {
        "User-Agent": USER_AGENT,
        "Referer": "https://www.bilibili.com/",
        "Cookie": "; ".join(cookie_parts),
    }

# ── HTTP helpers ───────────────────────────────────────────────────────────

def api_get(url: str, headers: dict, params: dict | None = None,
            retries: int = 2) -> dict:
    """GET request with retry and error handling."""
    for attempt in range(retries + 1):
        try:
            resp = SESSION.get(url, headers=headers, params=params,
                               timeout=15)
        except Exception as exc:
            if attempt < retries:
                time.sleep(2)
                continue
            raise SystemExit(f"Request failed after {retries} retries: {exc}")

        if resp.status_code == 412:
            raise SystemExit(
                "Bilibili rejected the request (412). Your SESSDATA may be "
                "expired or missing buvid3. Re-login and refresh cookies."
            )
        if resp.status_code == 403:
            raise SystemExit(
                "Bilibili returned 403 Forbidden. Credentials may be invalid "
                "or expired."
            )
        if resp.status_code != 200:
            body_preview = resp.text[:300]
            if attempt < retries:
                time.sleep(2)
                continue
            raise SystemExit(
                f"HTTP {resp.status_code} — unexpected response.\n"
                f"Body: {body_preview}"
            )

        try:
            data = resp.json()
        except json.JSONDecodeError:
            if attempt < retries:
                time.sleep(2)
                continue
            raise SystemExit(
                f"Non-JSON response (HTTP {resp.status_code}): "
                f"{resp.text[:200]}"
            )

        if data.get("code") != 0:
            msg = data.get("message", data.get("msg", "unknown error"))
            raise SystemExit(
                f"API error (code={data.get('code')}): {msg}"
            )
        return data.get("data") or data

    raise SystemExit("Exhausted retries.")


def parse_json_content(raw: str) -> dict:
    """Parse a JSON-encoded content field from a message."""
    if not raw:
        return {}
    try:
        return json.loads(raw) if isinstance(raw, str) else raw
    except (json.JSONDecodeError, TypeError):
        return {"content": str(raw)}


def format_ts(ts: int) -> str:
    """Format unix timestamp to readable local time."""
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


# ── Actions ────────────────────────────────────────────────────────────────

def action_unread(headers: dict, fmt: str):
    """Check unread notification counts."""
    params = {"build": 0, "mobi_app": "web"}
    data = api_get(f"{API_BILI}/x/msgfeed/unread", headers=headers,
                   params=params)

    if fmt == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    reply = data.get("reply", data.get("recv_reply", 0))
    at    = data.get("at", 0)
    chat  = data.get("chat", 0)
    like  = data.get("like", data.get("recv_like", 0))

    print("=== Bilibili 未读消息 ===")
    print(f"  回复 (Replies):   {reply}")
    print(f"  @-提到 (@-mentions): {at}")
    print(f"  私信 (DMs):       {chat}")
    print(f"  点赞 (Likes):     {like}")
    total = reply + at + chat + like
    print(f"  ───────────────")
    print(f"  总计: {total}")


def action_replies(headers: dict, limit: int, fmt: str):
    """Fetch recent reply/at-mention feed (msgfeed API)."""
    collected = []
    cursor_id = None
    cursor_time = None

    while len(collected) < limit:
        params = {"build": 0, "mobi_app": "web"}
        if cursor_id:
            params["cursor_id"] = cursor_id
        if cursor_time:
            params["cursor_time"] = cursor_time

        data = api_get(f"{API_BILI}/x/msgfeed/reply",
                       headers=headers, params=params)
        items = data.get("items", [])
        cursor = data.get("cursor", {})
        is_end = cursor.get("is_end", True)
        cursor_id = cursor.get("id", None)
        cursor_time = cursor.get("time", None)

        if not items:
            break
        collected.extend(items)
        if is_end:
            break
        time.sleep(0.5)

    collected = collected[:limit]

    if fmt == "json":
        print(json.dumps(collected, ensure_ascii=False, indent=2))
        return

    if not collected:
        print("没有找到回复记录。")
        return

    print(f"=== 收到的回复 (共 {len(collected)} 条) ===")
    for i, r in enumerate(collected, 1):
        user = r.get("user", {})
        item = r.get("item", {})
        uname   = user.get("nickname", "?")
        uid     = user.get("mid", "?")
        content = item.get("root_reply_content", "")
        source  = item.get("source_content", "")
        reply_time = format_ts(r.get("reply_time", 0))
        business = item.get("business", "")
        title   = item.get("title", "")
        uri     = item.get("uri", "")
        item_type = item.get("type", "")

        print(f"  [{i}] 💬 {uname} (UID {uid}) 于 {reply_time}")
        print(f"       类型: {business} | 内容: {content[:200]}")
        if source:
            print(f"       回复: {source[:200]}")
        if title:
            print(f"       原文: {title[:100]}")
        if uri:
            print(f"       链接: {uri}")
        print()


def action_sessions(headers: dict, fmt: str):
    """List recent DM sessions."""
    params = {
        "session_type": 1,
        "group_fold": 1,
        "unfollow_fold": 0,
        "sort_rule": 2,
    }
    data = api_get(f"{API_VC}/session_svr/v1/session_svr/get_sessions",
                   headers=headers, params=params)
    session_list = data.get("session_list", [])
    has_more     = data.get("has_more", 0)

    if fmt == "json":
        print(json.dumps(session_list, ensure_ascii=False, indent=2))
        return

    if not session_list:
        print("没有活跃的私信会话。")
        return

    print(f"=== 私信会话列表 (共 {len(session_list)} 个) ===")
    for s in session_list:
        uid      = s.get("talker_id", "?")
        last_msg_raw = s.get("last_msg", {})

        # Extract sender name / preview
        content_raw = last_msg_raw.get("content", "{}")
        cont_obj = parse_json_content(content_raw)
        preview = cont_obj.get("content", cont_obj.get("message", ""))
        msg_type = last_msg_raw.get("msg_type", "?")
        sender_uid = last_msg_raw.get("sender_uid", "?")

        type_label = {1: "文本", 2: "图片", 3: "语音", 6: "表情",
                      10: "系统", 10008: "客服", 10009: "客服"}
        label = type_label.get(msg_type, f"类型{msg_type}")

        msg_time = format_ts(last_msg_raw.get("timestamp", 0))
        unread   = s.get("unread_count", 0)

        print(f"  UID {uid}")
        if unread:
            print(f"       未读: {unread} 条 ⬤")
        if preview:
            print(f"       最后消息 [{label}]: {str(preview)[:120]}")
        elif msg_type == 2:
            print(f"       最后消息: [图片]")
        print(f"       时间: {msg_time}")
        print()

    if has_more:
        print("  ... 还有更多会话")


def action_messages(headers: dict, talker_id: str, limit: int,
                    fmt: str):
    """Fetch messages from a specific DM session.

    Uses the svr_sync endpoint which returns the old-format
    (flat sender_uid/receiver_id) for peer-to-peer DMs.
    """
    params = {
        "session_type": 1,
        "talker_id": talker_id,
        "begin_seqno": 0,
        "size": min(limit, 50),
        "sender_device_id": "1",
        "build": 0,
        "mobi_app": "web",
    }
    data = api_get(
        f"{API_VC}/svr_sync/v1/svr_sync/fetch_session_msgs",
        headers=headers, params=params
    )
    messages = data.get("messages", [])

    if fmt == "json":
        print(json.dumps(messages[:limit], ensure_ascii=False, indent=2))
        return

    if not messages:
        print(f"UID {talker_id} 没有消息记录。")
        return

    # Determine who is "me" from receiver_id of first message, or treat
    # messages where sender_uid == talker_id as "from them"
    my_uid = str(messages[0].get("receiver_id", "")) if messages else ""

    print(f"=== 与 UID {talker_id} 的私信 (显示 {min(len(messages), limit)} 条) ===")

    for m in messages[:limit]:
        sender  = str(m.get("sender_uid", "?"))
        ts      = format_ts(m.get("timestamp", 0))
        msg_type = m.get("msg_type", 1)
        raw_cont = m.get("content", "{}")
        cont_obj = parse_json_content(raw_cont)

        # Determine direction
        if sender == talker_id:
            direction = "← 对方"
        elif sender == my_uid:
            direction = "→ 我"
        else:
            direction = f"← UID {sender}"

        print(f"  {direction} [{ts}]")

        if msg_type == 1:
            text = cont_obj.get("content", "")
            print(f"     {text}")
        elif msg_type == 2:
            image_url = cont_obj.get("url", "")
            print(f"     📷 {image_url}")
        elif msg_type == 3:
            print(f"     🎤 语音消息")
        elif msg_type == 6:
            text = cont_obj.get("content", "")
            print(f"     😀 表情: {text}")
        elif msg_type in (10008, 10009):
            text = cont_obj.get("message", "")
            print(f"     🤖 系统客服: {str(text)[:200]}")
        else:
            text = cont_obj.get("content", cont_obj.get("message", ""))
            print(f"     类型 {msg_type}: {str(text)[:200]}")
        print()

    if data.get("has_more"):
        print(f"  ... 还有更早的消息")


# ── CLI ────────────────────────────────────────────────────────────────────

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Bilibili Message Extractor — fetch replies and DMs",
    )
    p.add_argument("--action", required=True,
                   choices=["unread", "replies", "sessions", "messages"],
                   help="Action to perform")
    p.add_argument("--limit", type=int, default=20,
                   help="Max items (1-50, default: 20)")
    p.add_argument("--session-id", type=str, default="",
                   help="Talker UID for --action messages")
    p.add_argument("--format", choices=["text", "json"], default="text",
                   help="Output format (default: text)")
    return p.parse_args(argv)


def main(argv: list[str] | None = None):
    args = parse_args(argv)

    if args.action == "messages" and not args.session_id:
        raise SystemExit("--session-id is required for --action messages")
    if args.action == "messages" and not args.session_id.isdigit():
        raise SystemExit("--session-id must be a numeric UID")

    args.limit = max(1, min(args.limit, 50))

    creds = load_credentials()
    headers = build_headers(creds)

    print(f"[info] {'curl_cffi' if HAS_CURL_CFFI else 'requests'} "
          f"authenticated as {creds['SESSDATA'][:6]}...",
          file=sys.stderr)

    if args.action == "unread":
        action_unread(headers, args.format)
    elif args.action == "replies":
        action_replies(headers, args.limit, args.format)
    elif args.action == "sessions":
        action_sessions(headers, args.format)
    elif args.action == "messages":
        action_messages(headers, args.session_id, args.limit, args.format)


if __name__ == "__main__":
    main()
