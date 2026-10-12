# MCP 接入说明（MCP_INTEGRATION）

## 接入信息
| 项 | 值 |
|---|---|
| 服务地址 | `https://mcp.mcd.cn` |
| 传输协议 | Streamable HTTP |
| 鉴权 | 请求头 `Authorization: Bearer <MCP_TOKEN>` |
| 限流 | 600 次/分钟（超限返回 429） |
| Token 申请 | <https://open.mcd.cn/mcp>（手机号登录 → 控制台 → 激活） |

## 客户端配置（JSON）
```json
{
  "mcpServers": {
    "mcd-mcp": {
      "type": "streamablehttp",
      "url": "https://mcp.mcd.cn",
      "headers": { "Authorization": "Bearer YOUR_MCP_TOKEN" }
    }
  }
}
```

## 本项目使用的工具（官方 v1.0.9）
| 工具 | 用途 |
|---|---|
| `mall-points-products` | 拉取派对/主题活动商品全量目录，取 `spuId`（派对商品 `shopId=5`） |
| `query-party-city` | 按 spuId 查可参与城市 |
| `query-party-store` | 按城市查可办门店（含距离/营业状态） |
| `query-party-store-date` | 查门店可预约日期 |
| `query-party-store-session` | 查指定日期场次（时段/人数/价格/余位） |
| `party-order-create` | 下单（仅用户确认后调用） |

## 开发须知（踩坑记录，供复用）
- `tools/list` 实际返回 **35** 个工具（官方 README 表写 33）。
- 派对工具真名为 `query-party-store-date` / `query-party-store-session`（README 表误写为 `query-partystore-*`）。
- **spuId 只能从 `mall-points-products` 全量目录取得**：不传 `catRuleIds` 返回全部；传 `catRuleIds:[id]` 会过滤成空。
- 工具返回文本 = "字段说明（含 `{data[].xxx}` 占位符）+ Original Response JSON"，须用健壮方式提取真实 JSON。
- 服务端**无状态**：不返回也不要求 `Mcp-Session-Id`。
- 错误码：`401` Token 无效/过期；`429` 触发限流。

## 下单字段口径（party-order-create）
必填 `partyType`（1-包场 / 2-拼团）；其余 `code`(城市码) / `storeCode` / `dateStr` / `id`(场次Id) / `count`(人数) / `spuId` / `skuId` / `timeStart` / `timeEnd` / `leftNum` / `partyTimeInfo{...}`。
