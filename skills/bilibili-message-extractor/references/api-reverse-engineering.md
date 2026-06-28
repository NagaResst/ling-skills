# Bilibili Message API — Reverse Engineering Notes

本技能的所有 API 端点均**从 Bilibili 前端 JS bundle 逆向获得**，
非官方文档。B 站前端改版频繁，以下记录可加速下一次 API 漂移排查。

## 信息来源

- 消息中心 SPA: `https://message.bilibili.com`
- 核心 JS bundle: 从首页 `process.env.STATIC_URL` 加载的 `message/index.js`
  （通常位于 `https://s1.hdslb.com/bfs/seed/...`）

## 2026-06 发现记录

### 废弃端点（返回 404 HTML）

| 旧端点 | 新端点 |
|---|---|
| `api.vc.bilibili.com/.../unread_tot` | `api.bilibili.com/x/msgfeed/unread` |
| `api.bilibili.com/x/v2/reply/mine` | `api.bilibili.com/x/msgfeed/reply` |
| `api.vc.bilibili.com/.../get_session_msg` | `api.vc.bilibili.com/svr_sync/v1/svr_sync/fetch_session_msgs` |

### 私信 API 两个版本

| 端点 | 用途 | 消息格式 |
|---|---|---|
| `api.vc.bilibili.com/svr_sync/v1/svr_sync/fetch_session_msgs` | **用户间私信** | 旧平面格式：`{content: "...", msg_type: 1}` |
| `api.bilibili.com/x/custom/session_svr/v1/fetch_sess_msg` | 客服消息（IM V2） | 新格式（含 msg_source 等扩展字段） |

判定方法：在 JS bundle 中搜索 `fetch_session_msgs` 和 `fetch_sess_msg`，
查看其 base URL 类型（svr_sync → vc 域名，custom → api 域名）。

### 消息内容格式

**旧格式**（`fetch_session_msgs` 返回）：
```json
{
  "sender_uid": 1095342058,
  "receiver_id": 282bfb...,
  "msg_type": 1,
  "content": "{\"content\":\"你好\"}",
  "timestamp": 1688000000,
  "msg_seqno": 12345,
  "msg_key": 67890
}
```

msg_type: 1=text, 2=image, 3=voice, 6=sticker

**新格式**（`fetch_sess_msg` 返回，客服消息）：
```json
{
  "sender_uid": ...,
  "msg_source": { ... },
  "content": "{\"content\":\"...\"}",
  "msg_type": 1
}
```

### 消息内容 JSON 解析

所有 `content` 字段都是**内嵌 JSON 字符串**，需要 `json.loads()` 两次：
- 文本：`json.loads(content).get("content", "")`
- 图片：`json.loads(content).get("url", "")`

### 认证头

API 调用需要同时携带：
- `Cookie: SESSDATA=...; bili_jct=...; buvid3=...`
- `User-Agent: Mozilla/5.0 (Chrome 124)` 或更新的 UA
- `Referer: https://www.bilibili.com/`

缺失 `buvid3` 会导致部分 API 返回 412。
纯 `requests`（无 `curl_cffi`）的 TLS 指纹可能被限流/412。

**注意：非所有 API 都需要 Cookie。** `x/web-interface/view`（视频信息）只带 UA 即可；`x/v2/reply`（视频评论）必须全 Cookie。

### 视频评论 API（2026-06 发现）

用于获取视频的高赞评论。与 `x/msgfeed/reply`（自己收到的回复）是两套不同的系统。

```http
GET https://api.bilibili.com/x/v2/reply?oid={aid}&type=1&pn=1&ps=20&sort=2
Cookie: full auth trio
```

| 参数 | 说明 |
|---|---|
| `oid` | 视频 AID（数字型），**不是 BVID**。需先从 `x/web-interface/view?bvid=xxx` 获取 |
| `type` | 1=视频，12=专栏/文章 |
| `pn` | 页码（1-based） |
| `ps` | 每页条数（1-50，默认 20） |
| `sort` | 2=时间倒序，1=时间正序。**都不是按赞排序** |

返回结构关键字段：
```json
{
  "code": 0,
  "data": {
    "page": { "acount": 73, "count": 20, "num": 1, "size": 20 },
    "replies": [
      {
        "rpid": 123456789,
        "mid": 395922059,
        "like": 23,
        "rcount": 6,
        "ctime": 1688000000,
        "member": { "uname": "S_Autumn", "mid": 395922059 },
        "content": { "message": "评论正文..." },
        "replies": [
          { /* sub-reply, same structure */ }
        ]
      }
    ],
    "top_replies": [],   // UP 主置顶
    "upper": { "mid": 395922059 }
  }
}
```

**最佳实践**（经测试验证）：
1. 先调 `x/web-interface/view?bvid=BVxxx` 获取 `aid`（无需 Cookie）
2. 用得到的 `aid` 调 `x/v2/reply`（需要 Cookie）
3. 翻 2-3 页，收集所有 replies
4. 按 `like` 降序排序，取 Top N
5. 每条 comment 的 `replies[]` 内嵌子回复（最多 3 条），`s_Autumn` 字段指向子回复的作者

## 逆向流程（下次 API 漂移时复用）

```bash
# 1. 下载消息页面 HTML，找 JS bundle URL
curl -sSL -o /tmp/bili_page.html \
  -H "User-Agent: Mozilla/5.0 Chrome/124" \
  "https://message.bilibili.com"
grep -oP 'src="[^"]+message/[^"]*"' /tmp/bili_page.html

# 2. 下载 JS bundle
curl -sS -o /tmp/bundle.js \
  "https://s1.hdslb.com/bfs/seed/.../message/index.js"

# 3. 搜索 API 路径
grep -oP '.{50}(fetch_sess|get_sessions|session_svr|unread_tot|msgfeed).{50}' /tmp/bundle.js

# 4. 确认 base URL（是 api. 还是 vc. 还是 proxy）
grep -oP '["'\'']https?://[^"'\'']+custom[^"'\'']*["'\'']' /tmp/bundle.js | sort -u
```

## 核心原则

- `api.bilibili.com/x/msgfeed/*` — 回复/at/未读
- `api.vc.bilibili.com/session_svr/*` — 会话列表
- `api.vc.bilibili.com/svr_sync/*` — 私信消息详情（**P2P 私信**）
- `api.bilibili.com/x/custom/*` — 客服/IM V2（**不是** P2P 私信）
