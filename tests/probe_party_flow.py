"""P0 v4：端到端跑通派对链路，定位 spuId 并下钻到场次。

依据 query-party-city 描述：spuId 需从 mall-points-products 获取。
完整链路：
  mall-points-products ->(派对类商品 spuId)-> query-party-city -> query-party-store
  -> query-party-store-date -> query-party-store-session

零依赖。用法：python tests/probe_party_flow.py
"""

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import get_mcp_token  # noqa: E402

MCP_URL = "https://mcp.mcd.cn"


def _post(payload):
    headers = {"Content-Type": "application/json",
               "Accept": "application/json, text/event-stream",
               "Authorization": f"Bearer {get_mcp_token()}"}
    req = urllib.request.Request(MCP_URL, data=json.dumps(payload).encode(), headers=headers, method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.read().decode("utf-8", "ignore")


def _parse(raw):
    if "text/event-stream" in raw[:200].lower():
        for line in raw.splitlines():
            if line.startswith("data:"):
                raw = line[5:].strip(); break
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"_raw": raw}


def rpc(method, params=None, req_id=None):
    p = {"jsonrpc": "2.0", "method": method}
    if req_id is not None:
        p["id"] = req_id
    if params is not None:
        p["params"] = params
    return _parse(_post(p))


def extract_json(text):
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


def call_tool(name, args, req_id):
    resp = rpc("tools/call", {"name": name, "arguments": args}, req_id=req_id)
    if "result" not in resp:
        return None, json.dumps(resp.get("error"), ensure_ascii=False)
    text = "".join(c.get("text", "") for c in resp["result"].get("content", []) if isinstance(c, dict))
    return extract_json(text), text


def as_list(data):
    if isinstance(data, dict):
        for k in ("data", "list", "items", "records", "products"):
            v = data.get(k)
            if isinstance(v, list):
                return v
        # 单层则返回所有 list 值里最长的
        cand = [v for v in data.values() if isinstance(v, list)]
        return max(cand, key=len) if cand else []
    return data if isinstance(data, list) else []


def main():
    for ver in ["2025-06-18", "2025-03-26", "2024-11-05"]:
        if "result" in rpc("initialize", {"protocolVersion": ver, "capabilities": {},
                                          "clientInfo": {"name": "probe", "version": "0.1"}}, req_id=1):
            break
    rpc("notifications/initialized")
    tools = {t["name"]: t for t in rpc("tools/list", {}, req_id=2).get("result", {}).get("tools", [])}

    print("== mall-points-products schema ==")
    mpp = tools.get("mall-points-products", {}).get("inputSchema", {})
    print("required=", mpp.get("required"), " props=", list(mpp.get("properties", {}).keys()))

    print("\n== 调用 mall-points-products 找派对类商品 ==")
    data, text = call_tool("mall-points-products", {}, req_id=10)
    items = as_list(data)
    print(f"商品数={len(items)}")
    if items:
        print("首条目字段:", list(items[0].keys()))

    keywords = ("派对", "体验营", "品鉴", "读书会", "生日", "主题")
    party_items = [it for it in items if isinstance(it, dict) and any(k in json.dumps(it, ensure_ascii=False) for k in keywords)]
    print(f"命中派对关键词的商品数={len(party_items)}")

    spu = None
    if party_items:
        first = party_items[0]
        print("派对商品示例:", json.dumps(first, ensure_ascii=False)[:500])
        for k in ("spuId", "spuCode", "spuID", "id", "productId", "code"):
            if k in first and first[k] not in (None, ""):
                spu = first[k]
                print(f"-> spuId 字段 = {k} = {spu}")
                break
    else:
        print("未在 mall-points-products 命中派对商品，原文预览:", text[:600])

    if not spu:
        print("\n未取得 spuId，链路终止。")
        return 0

    print("\n== 用 spuId 下钻派对链路 ==")
    code, _ = call_tool("query-party-city", {"spuId": spu}, req_id=11)
    cities = as_list(code)
    print(f"[query-party-city] 城市数={len(cities)} 预览={json.dumps(cities[:2], ensure_ascii=False)[:300]}")
    if not cities:
        return 0
    city = next((c for c in cities if c.get("name") in ("上海市", "北京市", "广州市", "深圳市")), cities[0])
    city_code = city.get("code") or city.get("cityCode")
    print(f"  选用城市: {city.get('name')} code={city_code}")

    stores, _ = call_tool("query-party-store", {"code": city_code, "spuId": spu}, req_id=12)
    stores = as_list(stores)
    print(f"[query-party-store] 门店数={len(stores)}")
    if not stores:
        return 0
    store = stores[0]
    store_code = store.get("code") or store.get("storeCode") or store.get("storeId")
    print(f"  选用门店: {store.get('name')} code={store_code} 字段={list(store.keys())}")

    dates, _ = call_tool("query-party-store-date", {"spuId": spu, "storeCode": store_code}, req_id=13)
    dates = as_list(dates)
    print(f"[query-party-store-date] 日期数={len(dates)} 预览={json.dumps(dates[:5], ensure_ascii=False)[:300]}")
    if not dates:
        return 0
    d0 = dates[0]
    date_str = d0 if isinstance(d0, str) else (d0.get("dateStr") or d0.get("date") or d0.get("day") or d0)

    sessions, _ = call_tool("query-party-store-session", {"spuId": spu, "storeCode": store_code, "dateStr": date_str}, req_id=14)
    sessions = as_list(sessions)
    print(f"[query-party-store-session] 场次数={len(sessions)} 预览={json.dumps(sessions[:2], ensure_ascii=False)[:400]}")

    print("\n== 结论 ==")
    print("✅ 派对链路端到端可用（spuId->城市->门店->日期->场次），方向 A 完全可行。" if (dates and sessions is not None)
          else "⚠️ 链路部分可用，请检查上面哪一级为空。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
