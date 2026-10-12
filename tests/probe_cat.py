"""P0 v5：发现派对商品的 catRuleIds（类目规则 ID）与 spuId。

mall-points-products 需 catRuleIds 才返回商品，但无"列类目"工具。
这里对 catRuleIds 做小区间只读扫描，找出：
- 哪些类目有商品；
- 哪些类目含派对/体验营/品鉴会/读书会/生日关键词；
- 命中则取其 spuId 并端到端下钻，验证方向 A 可行性。

纯查询，不调用任何下单/抽奖/兑换工具。零依赖。
用法：python tests/probe_cat.py [起始ID] [结束ID]
"""

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import get_mcp_token  # noqa: E402

MCP_URL = "https://mcp.mcd.cn"
KEYWORDS = ("派对", "体验营", "品鉴", "读书会", "生日", "主题")


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
        return None
    text = "".join(c.get("text", "") for c in resp["result"].get("content", []) if isinstance(c, dict))
    return extract_json(text)


def as_list(data):
    if isinstance(data, dict):
        for k in ("data", "list", "items", "products"):
            if isinstance(data.get(k), list):
                return data[k]
        cand = [v for v in data.values() if isinstance(v, list)]
        return max(cand, key=len) if cand else []
    return data if isinstance(data, list) else []


def main():
    lo = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    hi = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    for ver in ["2025-06-18", "2025-03-26", "2024-11-05"]:
        if "result" in rpc("initialize", {"protocolVersion": ver, "capabilities": {},
                                          "clientInfo": {"name": "probe", "version": "0.1"}}, req_id=1):
            break
    rpc("notifications/initialized")

    print(f"== 扫描 catRuleIds {lo}..{hi} ==")
    party_spu = None
    non_empty = 0
    rid = 100
    for cid in range(lo, hi + 1):
        rid += 1
        data = call_tool("mall-points-products", {"catRuleIds": [cid]}, req_id=rid)
        items = as_list(data)
        if not items:
            continue
        non_empty += 1
        names = [str(it.get("spuName", "")) for it in items if isinstance(it, dict)]
        hit = [it for it in items if isinstance(it, dict) and any(k in json.dumps(it, ensure_ascii=False) for k in KEYWORDS)]
        print(f"[catRuleId={cid}] 商品数={len(items)} 派对命中={len(hit)} 样例={names[:3]}")
        if hit and party_spu is None:
            it = hit[0]
            party_spu = it.get("spuId")
            print(f"  >>> 派对商品: {it.get('spuName')} spuId={party_spu} point={it.get('point')}")

    print(f"\n非空类目数={non_empty}；party_spu={party_spu}")

    if party_spu:
        print("\n== 用派对 spuId 端到端下钻 ==")
        cities = as_list(call_tool("query-party-city", {"spuId": party_spu}, req_id=200))
        print(f"[query-party-city] 城市数={len(cities)} 预览={json.dumps(cities[:2], ensure_ascii=False)[:250]}")
        if cities:
            city = next((c for c in cities if c.get("name") in ("上海市", "北京市", "广州市", "深圳市")), cities[0])
            cc = city.get("code") or city.get("cityCode")
            print(f"  城市 {city.get('name')} code={cc}")
            stores = as_list(call_tool("query-party-store", {"code": cc, "spuId": party_spu}, req_id=201))
            print(f"[query-party-store] 门店数={len(stores)}")
            if stores:
                st = stores[0]
                sc = st.get("code") or st.get("storeCode") or st.get("storeId")
                print(f"  门店 {st.get('name')} code={sc} 字段={list(st.keys())}")
                dates = as_list(call_tool("query-party-store-date", {"spuId": party_spu, "storeCode": sc}, req_id=202))
                print(f"[query-party-store-date] 日期数={len(dates)} 预览={json.dumps(dates[:5], ensure_ascii=False)[:250]}")
                if dates:
                    d0 = dates[0]
                    ds = d0 if isinstance(d0, str) else (d0.get("dateStr") or d0.get("date") or d0)
                    sess = as_list(call_tool("query-party-store-session", {"spuId": party_spu, "storeCode": sc, "dateStr": ds}, req_id=203))
                    print(f"[query-party-store-session] 场次数={len(sess)} 预览={json.dumps(sess[:2], ensure_ascii=False)[:350]}")
                    print("\n✅ 方向 A 派对链路端到端可用！" if dates else "\n⚠️ 有日期但场次异常")
    else:
        print("\n⚠️ 未在扫描区间发现派对类目。可扩大区间重试，或评估切换方向 B。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
