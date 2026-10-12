"""P0 诊断：mall-points-products 不同 catRuleIds 变体的原始返回。
区分"报错/无JSON"与"确实空数据"，并试探 ID 量级与类型。
零依赖。用法：python tests/probe_diag.py
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
        return resp.getcode(), resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")


def rpc(method, params=None, req_id=None):
    p = {"jsonrpc": "2.0", "method": method}
    if req_id is not None:
        p["id"] = req_id
    if params is not None:
        p["params"] = params
    code, raw = _post(p)
    if "text/event-stream" in raw[:200].lower():
        for line in raw.splitlines():
            if line.startswith("data:"):
                raw = line[5:].strip(); break
    raw = raw.strip()
    try:
        return code, json.loads(raw)
    except json.JSONDecodeError:
        return code, {"_raw": raw[:300]}


def tool_text(name, args, req_id):
    code, resp = rpc("tools/call", {"name": name, "arguments": args}, req_id=req_id)
    if "result" not in resp:
        return code, f"ERROR: {json.dumps(resp.get('error'), ensure_ascii=False)}"
    text = "".join(c.get("text", "") for c in resp["result"].get("content", []) if isinstance(c, dict))
    return code, text


def main():
    for ver in ["2025-06-18", "2025-03-26", "2024-11-05"]:
        if "result" in rpc("initialize", {"protocolVersion": ver, "capabilities": {},
                                          "clientInfo": {"name": "probe", "version": "0.1"}}, req_id=1)[1]:
            break
    rpc("notifications/initialized")

    variants = [
        ("omit", {}),
        ("list[1]", {"catRuleIds": [1]}),
        ("str '1'", {"catRuleIds": "1"}),
        ("list[100001]", {"catRuleIds": [100001]}),
        ("list[7]", {"catRuleIds": [7]}),
    ]
    for i, (label, args) in enumerate(variants):
        code, text = tool_text("mall-points-products", args, req_id=300 + i)
        # 找 data 数组长度线索
        has_data = '"data"' in text
        snippet = text[-300:].replace("\n", " ")  # 看结尾，实际数据在结尾
        print(f"[catRuleIds={label}] http={code} 含'data'={has_data}")
        print(f"    结尾预览: {snippet}")
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
