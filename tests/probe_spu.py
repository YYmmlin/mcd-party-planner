"""P0 v3：定位派对主题活动的 spuId 来源。

派对工具都需要 spuId（主题活动商品 ID），但工具列表无"列出派对商品"的工具。
本脚本排查 spuId 的可能来源：
1. 打印全部工具名 + 描述，找 spu / party / campaign 相关工具。
2. 调用 campaign-calendar，看活动日历是否带出派对活动及 spuId。
3. 若日历含 spuId，则演示：用该 spuId 走通 query-party-city。

零依赖。用法：python tests/probe_spu.py
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
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Authorization": f"Bearer {get_mcp_token()}",
    }
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
    payload = {"jsonrpc": "2.0", "method": method}
    if req_id is not None:
        payload["id"] = req_id
    if params is not None:
        payload["params"] = params
    return _parse(_post(payload))


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
    text = "".join(c.get("text", "") for c in resp.get("result", {}).get("content", []) if isinstance(c, dict))
    return extract_json(text), text


def main():
    for ver in ["2025-06-18", "2025-03-26", "2024-11-05"]:
        r = rpc("initialize", {"protocolVersion": ver, "capabilities": {},
                               "clientInfo": {"name": "probe", "version": "0.1"}}, req_id=1)
        if "result" in r:
            break
    rpc("notifications/initialized")

    tools = rpc("tools/list", {}, req_id=2).get("result", {}).get("tools", [])
    print(f"== 全部 {len(tools)} 工具（名 + 描述前 60 字）==")
    for t in tools:
        d = (t.get("description") or "").replace("\n", " ")[:60]
        print(f"  {t['name']:<28} {d}")

    print("\n== campaign-calendar 活动日历 ==")
    data, text = call_tool("campaign-calendar", {}, req_id=10)
    if data:
        print("提取到 JSON，keys:", list(data.keys()))
        items = data.get("data")
        print("data 类型:", type(items).__name__, "长度:", len(items) if hasattr(items, '__len__') else "?")
        print("预览:", json.dumps(data, ensure_ascii=False)[:1200])
    else:
        print("未提取到 JSON，原文预览:", text[:800])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
