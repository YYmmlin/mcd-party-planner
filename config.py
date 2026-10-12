"""配置 / Token 加载（零第三方依赖）。

安全约定：
- 真实 token 仅存放在仓库根目录的 `.env` 文件，该文件已被 `.gitignore` 忽略，绝不入库。
- `.env.example` 只含占位符，可安全提交。
- 任何源码都不得硬编码 token；统一通过本模块读取。
"""


import os
from pathlib import Path


ENV_FILE = Path(__file__).resolve().parent / ".env"


def _load_dotenv(path: Path) -> None:
    """极简 .env 解析（零依赖），仅填充尚未存在的环境变量。"""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def get_mcp_token() -> str:
    """返回麦当劳 MCP Token；缺失或仍为占位符时抛出明确错误。"""
    _load_dotenv(ENV_FILE)
    token = os.environ.get("MCD_MCP_TOKEN", "").strip()
    if not token or token == "YOUR_MCP_TOKEN":
        raise RuntimeError(
            "未找到可用的 MCD_MCP_TOKEN。请将 .env.example 复制为 .env 并填入真实 Token，"
            "或在运行环境中导出同名环境变量。"
        )
    return token


def get_auth_header() -> str:
    """返回 MCP 请求所需的 Authorization 头值（Bearer <token>）。"""
    return f"Bearer {get_mcp_token()}"
