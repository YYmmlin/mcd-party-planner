"""P0 可行性验证 v2：麦当劳 MCP 派对工具逐级下钻。

在 v1 基础上修正：
- 派对工具真实名为 query-party-store-date / query-party-store-session
  （README 表误写为 query-partystore-date/session）。
- 从 tools/list 的 inputSchema 读取每个工具的准确参数名。
- 从工具返回文本中提取真正的 JSON 数据（去掉字段说明前缀）。
- 按 城市 -> 门店 -> 日期 -> 场次 逐级下钻，验证当前是否有可预约活动。
- 不再调用 party-order-create（避免任何误下单风险）。

零第三方依赖。用法：python tests/live_probe.py
"""

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import get_mcp_token  # noqa: E402

MCP_URL = "https://mcp.mcd.cn"
PROTOCOL_VERSIONS = ["2025-06-18", "2025-03-26", "2024-11-05"]
PARTY_TOOLS = [
    "query-party-city",
    "query-party-store",
    "query-party-store-date",
    "query-party-store-session",
]


def _post(session_id, payload):
    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Authorization": f"Bearer {get_mcp_token()}",
    }
    if session_id:
        headers["Mcp-Session-Id"] = session_id
    req = urllib.request.Request(MCP_URL, data=body, headers=headers, method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return resp.headers, resp.getcode(), resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.headers, e.code, e.read().decode("utf-8", "ignore")


def _parse(raw, content_type):
    if "text/event-stream" in (content_type or "").lower():
        for line in raw.splitlines():
            if line.startswith("data:"):
                raw = line[5:].strip()
                break
    raw = raw.strip()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"_raw": raw}


def rpc(session_id, method, params=None, req_id=None):
    payload = {"jsonrpc": "2.0", "method": method}
    if req_id is not None:
        payload["id"] = req_id
    if params is not None:
        payload["params"] = params
    headers, code, body = _post(session_id, payload)
    return code, _parse(body, headers.get("Content-Type"))


def _result_text(resp):
    return "".join(c.get("text", "") for c in resp.get("result", {}).get("content", []) if isinstance(c, dict))


def extract_json(text):
    """从工具返回文本中提取真正的 JSON 数据（字段说明是 markdown 无花括号）。"""
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i + 1])
                except json.JSONDecodeError:
                    return None
    return None


def call_tool(session_id, name, args, req_id):
    code, resp = rpc(session_id, "tools/call", {"name": name, "arguments": args}, req_id=req_id)
    if resp and "result" in resp:
        return code, extract_json(_result_text(resp)), _result_text(resp)
    return code, None, json.dumps((resp or {}).get("error"), ensure_ascii=False)


def main():
    print("== P0 v2 派对工具逐级下钻 ==\n")
    session_id, inited = None, False
    for ver in PROTOCOL_VERSIONS:
        code, resp = rpc(None, "initialize", {
            "protocolVersion": ver, "capabilities": {},
            "clientInfo": {"name": "mcd-party-planner", "version": "0.1.0"},
        }, req_id=1)
        if resp and "result" in resp:
            inited = True
            print(f"[initialize] OK protocol={ver} server={resp['result'].get('serverInfo')}")
            break
    if not inited:
        print("初始化失败"); return 1

    rpc(session_id, "notifications/initialized")

    _, resp = rpc(session_id, "tools/list", {}, req_id=2)
    tools = {t["name"]: t for t in (resp or {}).get("result", {}).get("tools", [])}
    print(f"[tools/list] 共 {len(tools)} 个工具\n")

    print("== 派对工具参数 Schema ==")
    for name in PARTY_TOOLS:
        t = tools.get(name)
        if not t:
            print(f"[{name}] 不存在"); continue
        schema = t.get("inputSchema", {})
        props = list(schema.get("properties", {}).keys())
        print(f"[{name}] required={schema.get('required')} props={props}")

    # ---- 下钻 1：城市 ----
    print("\n== 下钻：城市 ==")
    code, data, _ = call_tool(session_id, "query-party-city", {}, req_id=10)
    cities = (data or {}).get("data", []) if isinstance(data, dict) else []
    print(f"[query-party-city] http={code} 城市数={len(cities)}")
    if not cities:
        print("  无城市数据，派对方向当前可能无在档活动。"); return 0
    pick = next((c for c in cities if c.get("name") in ("上海市", "北京市", "广州市", "深圳市")), cities[0])
    city_code = pick.get("code")
    print(f"  选用城市：{pick.get('name')} code={city_code}")

    # ---- 下钻 2：门店（参数名从 schema 推断）----
    print("\n== 下钻：门店 ==")
    store_props = tools.get("query-party-store", {}).get("inputSchema", {}).get("properties", {})
    city_key = next((k for k in store_props if "city" in k.lower()), "city")
    code, data, _ = call_tool(session_id, "query-party-store", {city_key: city_code}, req_id=11)
    stores = (data or {}).get("data", []) if isinstance(data, dict) else []
    print(f"[query-party-store] http={code} 参数={{{city_key}:{city_code}}} 门店数={len(stores)}")
    if not stores:
        print("  无门店数据。"); return 0
    store = stores[0]
    store_code = store.get("code") or store.get("storeCode") or store.get("storeId")
    print(f"  选用门店：{store.get('name')} code字段={store_code}")

    # ---- 下钻 3：可预约日期 ----
    print("\n== 下钻：可预约日期 ==")
    date_props = tools.get("query-party-store-date", {}).get("inputSchema", {}).get("properties", {})
    date_args = {}
    for k, v in date_props.items():
        kl = k.lower()
        if "city" in kl:
            date_args[k] = city_code
        elif "store" in kl:
            date_args[k] = store_code
    code, data, _ = call_tool(session_id, "query-party-store-date", date_args, req_id=12)
    dates = (data or {}).get("data", []) if isinstance(data, dict) else []
    print(f"[query-party-store-date] http={code} 参数={date_args} 日期数={len(dates)}")
    if not dates:
        print("  无可预约日期。"); return 0
    first_date = dates[0]
    date_val = first_date if isinstance(first_date, str) else (first_date.get("date") or first_date.get("day") or first_date)
    print(f"  首日期：{date_val}")

    # ---- 下钻 4：场次 ----
    print("\n== 下钻：场次 ==")
    sess_props = tools.get("query-party-store-session", {}).get("inputSchema", {}).get("properties", {})
    sess_args = dict(date_args)
    for k, v in sess_props.items():
        kl = k.lower()
        if "date" in kl or "day" in kl:
            sess_args[k] = date_val
        elif "city" in kl:
            sess_args[k] = city_code
        elif "store" in kl:
            sess_args[k] = store_code
    code, data, _ = call_tool(session_id, "query-party-store-session", sess_args, req_id=13)
    sessions = (data or {}).get("data", []) if isinstance(data, dict) else []
    print(f"[query-party-store-session] http={code} 参数={sess_args} 场次数={len(sessions)}")
    if sessions:
        print(f"  首场次示例：{json.dumps(sessions[0], ensure_ascii=False)[:300]}")

    print("\n== 结论 ==")
    if dates:
        print("✅ 派对工具链路可用（城市->门店->日期->场次 均有数据），方向 A 可行，进入 P1。")
    else:
        print("⚠️ 派对工具在线但当前无可预约日期，需评估是否切方向 B。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
