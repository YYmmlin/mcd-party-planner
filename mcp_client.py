"""麦当劳 MCP 客户端（零第三方依赖，仅标准库）。

要点（P0 实测确认）：
- 接入地址 https://mcp.mcd.cn，Streamable HTTP + Authorization: Bearer <token>。
- 服务端无状态：不返回也不要求 Mcp-Session-Id。
- tools/list 实际返回 35 个工具（README 表写 33，见 issue #16）。
- 派对工具真实名：query-party-store-date / query-party-store-session
  （README 表误写为 query-partystore-date/session）。
- 派对链路需 spuId；spuId 来自 mall-points-products 的全量商品目录
  （不传 catRuleIds 即返回全部）。
- 工具返回文本 = "字段说明(含 {data[].xxx} 占位符) + Original Response JSON"，
  必须用 extract_json 提取真实 JSON。
"""

import json
import urllib.error
import urllib.request

from config import get_mcp_token

MCP_URL = "https://mcp.mcd.cn"
PROTOCOL_VERSIONS = ["2025-06-18", "2025-03-26", "2024-11-05"]


class MCPError(RuntimeError):
    pass


def extract_json(text):
    """从工具文本中提取真正的 JSON：遍历每个 '{' 配平解析，取第一个含 data/success 的 dict。

    能穿过字段说明里的 {data[].xxx} 模板占位符，定位到末尾的真实响应体。
    """
    if not text:
        return None
    for i, ch in enumerate(text):
        if ch != "{":
            continue
        depth = 0
        for j in range(i, len(text)):
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        obj = json.loads(text[i:j + 1])
                    except json.JSONDecodeError:
                        obj = None
                    if isinstance(obj, dict) and ("data" in obj or "success" in obj):
                        return obj
                    break
    return None


def as_list(data):
    """把工具返回规整为列表：优先取 data/list/items/products/records。"""
    if isinstance(data, dict):
        for k in ("data", "list", "items", "products", "records"):
            v = data.get(k)
            if isinstance(v, list):
                return v
        cand = [v for v in data.values() if isinstance(v, list)]
        return max(cand, key=len) if cand else []
    return data if isinstance(data, list) else []


class McDonaldsMCP:
    def __init__(self, token=None):
        self._token = token
        self._req_id = 0
        self._server_info = None

    def _auth(self):
        return f"Bearer {self._token or get_mcp_token()}"

    def _post(self, payload):
        req = urllib.request.Request(
            MCP_URL, data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json",
                     "Accept": "application/json, text/event-stream",
                     "Authorization": self._auth()},
            method="POST")
        try:
            resp = urllib.request.urlopen(req, timeout=30)
            return resp.getcode(), resp.read().decode("utf-8", "ignore")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", "ignore")

    @staticmethod
    def _unwrap(raw):
        if "text/event-stream" in raw[:200].lower():
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
            return None

    def _rpc(self, method, params=None, with_id=True):
        if with_id:
            self._req_id += 1
        p = {"jsonrpc": "2.0", "method": method}
        if with_id:
            p["id"] = self._req_id
        if params is not None:
            p["params"] = params
        _, raw = self._post(p)
        return self._unwrap(raw)

    def initialize(self):
        for ver in PROTOCOL_VERSIONS:
            r = self._rpc("initialize", {"protocolVersion": ver, "capabilities": {},
                                         "clientInfo": {"name": "mcd-party-planner", "version": "0.1.0"}})
            if r and "result" in r:
                self._server_info = r["result"].get("serverInfo")
                self._rpc("notifications/initialized", with_id=False)
                return r["result"]
        raise MCPError("MCP initialize 失败")

    def list_tools(self):
        r = self._rpc("tools/list", {})
        if not r or "result" not in r:
            raise MCPError(f"tools/list 失败: {r}")
        return {t["name"]: t for t in r["result"].get("tools", [])}

    def call(self, name, arguments=None):
        """调用工具，返回提取后的真实 JSON（可能为 None）。"""
        r = self._rpc("tools/call", {"name": name, "arguments": arguments or {}})
        if not r or "result" not in r:
            raise MCPError(f"tools/call {name} 失败: {json.dumps((r or {}).get('error'), ensure_ascii=False)}")
        text = "".join(c.get("text", "") for c in r["result"].get("content", []) if isinstance(c, dict))
        return extract_json(text)
