---
name: bilibili-message-extractor
description: "Use when the user wants to fetch/extract their Bilibili messages — 回复 (replies/at-mentions) and/or 私信 (private messages/DMs). Requires the user to provide Bilibili auth cookies (SESSDATA, bili_jct, buvid3/buvid4) via environment variables. Ships a companion Python script at scripts/bilibili_msg.py for actual API calls."
version: 1.3.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [bilibili, api, messages, replies, dms, social-media]
    related_skills: [blogwatcher, china-mobile-web-archiving]
---

# Bilibili Message Extractor

Extract messages from Bilibili — 收到的回复 (replies/at-mentions) and 私信 (private messages).

## Overview

Bilibili's API is accessible only with authenticated cookies. This skill provides:

1. **回复提取** — Fetch your recent received replies (comments on your content, @-mentions, replies to your comments)
2. **私信提取** — List active DM sessions and fetch conversation history
3. **未读检查** — Check unread counts across all channels (reply, @, DM, like)

The companion script `scripts/bilibili_msg.py` implements all API calls with error handling, pagination, and formatted output.

## When to Use

- "看看我 bilibili 有没有新回复"
- "查一下 bilibili 私信"
- "拉取我 B 站的消息"
- "bilibili 未读消息"
- "帮我检查 B 站通知"
- "bilibili 消息提取"

**Do NOT use for:** Downloading videos, uploading content, searching Bilibili (that's a different use case), or modifying account settings.

## Authentication

### Required Cookies

Extract these from your browser after logging into `bilibili.com`:

| Cookie | How to get |
|---|---|
| `SESSDATA` | Browser DevTools → Application → Cookies → bilibili.com |
| `bili_jct` | Same place (CSRF token) |
| `buvid3` | Device ID — browser cookies |
| `buvid4` | Device ID — browser cookies (optional but helps) |

### Where to find them

1. Open `https://www.bilibili.com` in Chrome/Edge and log in
2. Press F12 → Application → Cookies → `https://www.bilibili.com`
3. Copy values for `SESSDATA`, `bili_jct`, `buvid3` (and `buvid4` if present)

### How to provide to the script

Set these environment variables before running:

```bash
export BILIBILI_SESSDATA=your_sessdata_here
export BILIBILI_BILI_JCT=your_bili_jct_here
export BILIBILI_BUVID3=your_buvid3_here
export BILIBILI_BUVID4=your_buvid4_here    # optional but recommended

# Then run
python3 scripts/bilibili_msg.py --action unread
```

Or in one line:

```bash
BILIBILI_SESSDATA=... BILIBILI_BILI_JCT=... BILIBILI_BUVID3=... \
  python3 scripts/bilibili_msg.py --action unread
```

## Script Location & Usage

The companion script lives at `scripts/bilibili_msg.py` within this skill directory.

### Basic usage

```bash
cd ~/.hermes/skills/research/bilibili-message-extractor
python3 scripts/bilibili_msg.py --action replies --limit 10
python3 scripts/bilibili_msg.py --action sessions
python3 scripts/bilibili_msg.py --action unread
python3 scripts/bilibili_msg.py --action messages --session-id 1095342058 --limit 20
```

### All options

| Flag | Description |
|---|---|
| `--action` | Required: `replies`, `sessions`, `messages`, `unread` |
| `--limit` | Max items per page (1-50, default: 20) |
| `--session-id` | Talker UID (required for `messages` action) |
| `--format` | `text` (default) or `json` |

### Quick verification

```bash
# 1. Check unread counts (fastest — validates credentials)
python3 scripts/bilibili_msg.py --action unread

# 2. List active DM sessions
python3 scripts/bilibili_msg.py --action sessions

# 3. Fetch messages from a specific session
python3 scripts/bilibili_msg.py --action messages --session-id <UID> --limit 5
```

## API Endpoints Used

All endpoints were reverse-engineered from Bilibili's current (2026) web SPA (`message.bilibili.com`).

### Unread

```
GET https://api.bilibili.com/x/msgfeed/unread?build=0&mobi_app=web
Cookies: auth trio
→ { "code": 0, "data": { "reply": N, "at": M, "chat": K, "like": L, ... } }
```

### Replies (收到的回复)

```
GET https://api.bilibili.com/x/msgfeed/reply?build=0&mobi_app=web
Cookies: auth trio
→ { "data": { "items": [...], "cursor": { "is_end": bool, "id": N, "time": N } } }
```

Cursor-based pagination: pass `cursor_id` and `cursor_time` from the previous response to get the next page.

Each item includes:
- `user.nickname` — replier's display name
- `user.mid` — replier's UID
- `item.root_reply_content` — what they said
- `item.source_content` — what they replied to
- `item.business` — content type (评论/视频 etc.)
- `item.title` — original video/article title
- `item.uri` — deep-link URL
- `reply_time` — unix timestamp

### @-mentions

```
GET https://api.bilibili.com/x/msgfeed/at?build=0&mobi_app=web
Cookies: auth trio
→ { "data": { "items": [...], "cursor": {...} } }
```

### Session List (私信会话列表)

```
GET https://api.vc.bilibili.com/session_svr/v1/session_svr/get_sessions
  ?session_type=1&group_fold=1&unfollow_fold=0&sort_rule=2
Cookies: auth trio
→ { "data": { "session_list": [...], "has_more": N } }
```

Each session includes:
- `talker_id` — the other user's UID
- `unread_count` — unread messages
- `last_msg.sender_uid` — who sent the last message
- `last_msg.msg_type` — 1=text, 2=image, 3=voice, 6=sticker
- `last_msg.content` — JSON-encoded content
- `last_msg.timestamp` — unix timestamp

### Session Messages (私信消息详情)

```
GET https://api.vc.bilibili.com/svr_sync/v1/svr_sync/fetch_session_msgs
  ?session_type=1&talker_id={uid}&begin_seqno=0&size={limit}
  &sender_device_id=1&build=0&mobi_app=web
Cookies: auth trio
→ { "data": { "messages": [...], "has_more": N } }
```

Each message uses the old-format flat structure:
- `sender_uid` — sender's UID
- `receiver_id` — receiver's UID
- `msg_type` — 1=text, 2=image, 3=voice
- `content` — JSON string ({"content":"..."} for text, {"url":"..."} for image)
- `timestamp` — unix timestamp
- `msg_seqno` / `msg_key` — message identifiers

Note: Bilibili also has a newer `fetch_sess_msg` endpoint at `api.bilibili.com/x/custom/session_svr/v1/fetch_sess_msg` which only returns customer service (IM V2) messages. The svr_sync endpoint is the one for peer-to-peer DMs.

## Video Comments (高质量评论)

The `bilibili_video_summary.py` script fetches video comments and filters for **high-quality content** (not just by likes):

```http
GET https://api.bilibili.com/x/v2/reply?oid={aid}&type=1&pn={page}&ps=20&sort=2
Cookies: full auth trio (SESSDATA + bili_jct + buvid3)
```

**Quality filtering strategy:** The script fetches up to 3 pages (60 replies), sorts by likes descending, then applies `_is_low_quality_comment()` to filter out:
- Comments shorter than 15 characters
- Spam patterns: `@username` + 发我邮箱 / 记笔记 / 整理笔记 etc.
- Pure emoji / gibberish

Only substantive comments survive — meaningful technical discussions, experience sharing, thoughtful questions. The default target is 5 quality comments. The section heading in wiki output is "高质量评论", not "高赞评论".

**Key differences from video info API:**

| API | Requires auth | Returns | Key param |
|---|---|---|---|
| `x/web-interface/view` | No (UA only) | Video metadata | `bvid` |
| `x/v2/reply` | Yes (full cookies) | User comments | `oid` (AID, not BVID) |

**Pagination & sorting:**  
- `sort=2` = time order (newest), `sort=1` = chronological. Neither is like-order — the script fetches 2-3 pages (60 replies max), then sorts all by `like` descending and applies `_is_low_quality_comment()` filtering to get high-quality entries.
- Each page has 20 replies; the response includes `page.acount` (total count).
- Each reply object includes: `rpid`, `mid`, `like`, `rcount` (sub-reply count), `content.message`, `member.uname`, `member.mid`, `ctime`, and a `replies[]` array with embedded sub-replies.

**Error codes:**
- `-352`: Missing or invalid auth cookies (video info works without them, comments don't)
- `-403`: WBI signature required (add `w_rid` + `wts` params, or use the older `x/v2/reply` path without `/wbi/`)

**Sub-replies:** Each top-level reply has a `replies[]` field with up to 3 embedded sub-replies (same structure).

**Question-thread sub-reply fetching:** When `--comments > 0`, `fetch_quality_comments()` also calls `fetch_comment_replies()` for comments that look like questions (contain `？`/`?` or start with `请问`/`想请教`/`请教`/`大佬，`/`up主，`/`up up`/`有个问题`/`有没有什么好的`/`该如何`/`怎么`/`adr是什么`). It fetches up to 2 pages (40 replies) via:

```http
GET https://api.bilibili.com/x/v2/reply/reply?oid={aid}&type=1&root={rpid}&ps=20&pn={page}
Cookies: full auth trio
```

Results are sorted by likes descending and capped at `min(rcount, 6)` entries. Sub-replies are included in the output as a `sub_replies` array on each comment dict; wiki format renders them as a blockquoted 💬 thread under the parent comment.

## Video Summary Extraction

A companion script `scripts/bilibili_video_summary.py` implements the end-to-end workflow of extracting an AI bot's video summary from your Bilibili DMs and producing wiki-ready output.

### Workflow

1. User asks an AI bot (on Bilibili) to watch a video and summarize
2. AI sends text + images to the user's Bilibili DMs
3. This script takes the video URL, finds the matching summary, and outputs structured content

### Usage

```bash
# Basic
python3 scripts/bilibili_video_summary.py --video-url "https://www.bilibili.com/video/BV1xx..." --ai-uid 1095342058

# If BILIBILI_AI_UID env var is set (recommended)
export BILIBILI_AI_UID=<AI_bot_UID>
python3 scripts/bilibili_video_summary.py --video-url "https://www.bilibili.com/video/BV1xx..." --format text

# Wiki-ready output (with frontmatter)
python3 scripts/bilibili_video_summary.py --video-url "https://www.bilibili.com/video/BV1xx..." --format wiki

# With high-quality comments (default: 5, auto-filters spam)
python3 scripts/bilibili_video_summary.py --video-url "https://www.bilibili.com/video/BV1xx..." --format wiki --comments 5

# Skip comments
python3 scripts/bilibili_video_summary.py --video-url "https://www.bilibili.com/video/BV1xx..." --format wiki --comments 0

# JSON output (for programmatic use)
python3 scripts/bilibili_video_summary.py --video-url "https://www.bilibili.com/video/BV1xx..." --format json
```

### Options

| Flag | Description |
|---|---|
| `--video-url` | Required. Bilibili video URL (full URL, BV id, or BV string) |
| `--ai-uid` | AI bot's Bilibili UID (can also set `BILIBILI_AI_UID` env var) |
| `--limit` | Max DMs to fetch (default: 50, increase for older summaries) |
| `--comments` | Number of high-quality comments to fetch (default: 5, 0 to skip; filters out spam/@-requests/short) |
| `--format` | Output format: `text` (default), `json`, or `wiki` |

### How It Works

1. **Extract BVID** — Parses any Bilibili URL format (full link, short link, bare BV)
2. **Fetch video info** — Calls `api.bilibili.com/x/web-interface/view` for title, author, etc.
3. **Fetch DMs** — Calls `api.vc.bilibili.com/svr_sync/v1/svr_sync/fetch_session_msgs` for the AI user's recent messages
4. **Match summary** — Searches DM text for the video title (in `《》` quotes, BV号, or keyword overlap)
5. **Collect burst** — Gathers all messages from the same sender within a 5-minute time window (captures text + images from the same summary burst). **Critical**: text fragments must be collected as `(timestamp, text)` tuples and sorted ascending (API returns newest-first), then merged at 500-char truncation boundaries. Images are collected separately and also timestamp-sorted.
6. **Output** — Formats as human-readable text, JSON, or wiki-ready markdown with frontmatter
7. **高质量评论** — Fetches comments from `x/v2/reply` API (3 pages, ~60 replies), sorts by likes, filters out low-quality content (spam/@-requests/short), retains substantive comments only; for question-type comments also fetches sub-replies via `x/v2/reply/reply`

### Matching Strategy

| Method | Priority | Confidence | Description |
|---|---|---|---|
| BVID in message | Highest | 100% | BV号 directly in DM text |
| Title quote `《》` | High | 95% | Video title found in `《》` in DM (AI's standard format) |
| Keyword overlap | Medium | 50-90% | Multiple title keywords found across DM text |

### Wiki Output Format

When `--format wiki` is used, the output includes:

- **Frontmatter**: title, created/updated timestamps (ISO 8601), type=summary, tags
- **Video link**: Original Bilibili URL in the body
- **AI summary text**: Full extracted summary content
- **Images**: Markdown image links for each image in the summary burst
- **高质量评论** (when `--comments > 0`): Numbered list of quality-filtered comments, with username, like count, full text, reply count, and timestamp. Low-quality entries (@-request spam, too short, gibberish) are filtered out automatically.
- **Metadata**: Video title, URL, UP主 info, AI UID, match method, confidence

The output is designed to be written directly to the wiki's `summaries/` directory.

### Additional Pitfalls for Video Summary

1. **BVIDs are case-sensitive.** The `BV` prefix is always uppercase, but the rest uses base58 encoding with mixed case. Do not uppercase/lowercase the entire BVID.

2. **Summary split across multiple messages.** The AI often sends text + multiple images as separate messages. The script groups them by sender + 5-minute time window (time-based burst detection, not index-based window).

3. **Timestamp-based burst detection.** The script uses a 5-minute window from the anchor message's timestamp to group related messages (images + additional text). This prevents older summaries from being mixed in.

4. **Long text messages split at Bilibili's 500-char DM limit.** Bilibili DMs cap content at ~500 characters. Very long summaries are automatically split into multiple consecutive text messages by the server. The script detects this: after sorting all text fragments by timestamp ascending, it merges adjacent fragments where the previous one is ≥480 chars (near the truncation boundary). This fixes artifacts like `"撰写S" + "pec决策文档"` → `"撰写Spec决策文档"` and `"第四阶" + "段"` → `"第四阶段"`. The merge happens in `match_summary()` after `text_fragments.sort()` — do NOT reorder these steps.

5. **API returns messages newest-first; burst collection must sort by timestamp.** The `fetch_session_msgs` API returns messages from newest to oldest. When the script collects a summary burst (anchor + related messages within ±5 min), it must sort text and image fragments by timestamp ascending — otherwise the output reads in reverse order. Always use `(timestamp, text)` tuples with sort before assembling the final result.

## Common Pitfalls

1. **SESSDATA expired.** Bilibili SESSDATA typically lasts 30 days. If you get 412 or 403 errors, re-login and refresh the cookies.

2. **Missing buvid3.** Some API endpoints won't respond without `buvid3`. Always set at least SESSDATA + bili_jct + buvid3 via env vars.

3. **Rate limiting.** Bilibili rate-limits at ~30 req/min for authenticated users. The script includes a built-in 0.5-second delay between paginated pages.

4. **Reply content has `<em>` tags.** Bilibili wrap at-mentions and bold text in `<em class="font-bold">@name</em>`. The script strips these automatically.

5. **Private message content is JSON-encoded.** The `content` field of a DM is a JSON string: `{"content":"hello","msg_type":1,...}`. The script parses it.

6. **Session list returns limited history.** Bilibili's session API returns only recent sessions (typically last 50). For older conversations, use the message-level pagination.

7. **curl_cffi not installed.** The script falls back to `requests` automatically, but Bilibili may deny `requests` due to TLS fingerprint. Install curl_cffi if you see SSL/connection errors:
   ```bash
   pip3 install curl_cffi
   ```

8. **Env vars not propagated to cron/scheduled tasks.** If using this script in a cron job, export the env vars in the cron command or source a `.env` file before the script call.

9. **Message API endpoints changed (2026).** The old `x/v2/reply/mine`, `get_session_msg` and `unread_tot` endpoints are deprecated. Use the msgfeed APIs listed above.

10. **Peer-to-peer DMs vs customer service.** User-to-user DMs use the `svr_sync/v1/svr_sync/fetch_session_msgs` endpoint, NOT the `fetch_sess_msg` endpoint (which returns CS bot messages).

11. **Video comment API requires full auth.** Unlike `x/web-interface/view` (which works with just User-Agent), `x/v2/reply` needs the full Cookie trio. If you get `-352` or `-403`, auth headers are missing or expired.

12. **Comment API uses AID, not BVID.** You must call `x/web-interface/view` to get the AID first, then use it as `oid` for the reply API.

13. **Hot comments ≠ quality comments.** Neither `sort=1` nor `sort=2` returns by like count. Always fetch 2-3 pages, sort by `like` descending, AND apply `_is_low_quality_comment()` filtering (removes spam, @-requests for notes, <15 chars) client-side. The section in wiki output is titled "高质量评论" not "高赞评论".

## Reference Files

- `references/api-reverse-engineering.md` — Full API endpoint map, JS bundle reverse engineering procedure, JSON content format details, auth header requirements. Read this first when Bilibili API endpoints change again.

## Verification Checklist

- [ ] Env vars `BILIBILI_SESSDATA`, `BILIBILI_BILI_JCT`, `BILIBILI_BUVID3` are set
- [ ] `python3 scripts/bilibili_msg.py --action unread` returns counts (may be 0)
- [ ] `python3 scripts/bilibili_msg.py --action sessions` lists active DM sessions
- [ ] `python3 scripts/bilibili_msg.py --action messages --session-id <UID> --limit 5` returns DM history
