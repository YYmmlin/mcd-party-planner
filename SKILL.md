---
name: mcd-party-planner
description: 麦当劳派对/主题活动规划助手（麦麦派对策划师）。基于麦当劳中国官方 MCP，帮用户按城市筛选可办派对门店、查询可预约日期与场次、生成主题化可分享方案卡。当用户想"办麦当劳派对/生日派对/主题派对/品鉴会/亲子读书会/麦麦体验营"、询问"哪里能办派对/怎么预约/多少钱/有哪些场次"时使用。仅非商业用途；下单必须经用户明确确认后才执行。
---

# 麦麦派对策划师（McParty Planner）

基于麦当劳中国官方 MCP（`https://mcp.mcd.cn`）的派对 / 主题活动规划助手。
2026 麦当劳程序员创意开发大赛参赛作品，使用 WorkBuddy 开发。

## 能力

- **列主题**：从积分商城全量目录取出派对/主题活动商品（生日类派对 / 主题类派对 / 品鉴会 / 读书会 / 麦麦体验营），按类目分组。
- **选城市**：默认**广州市**，可按用户指定城市切换（全国 280+ 城市）。
- **挑门店**：按距离排序返回可办该主题的门店（含地址、距离、营业状态）。
- **约日期**：返回该门店未来可预约日期。
- **看场次**：返回指定日期的场次（时段、成团人数、价格、余位）。
- **出方案卡**：按主题生成不同风格的 HTML 可分享卡片。
- **（可选）代下单**：仅在用户明确确认后调用 `party-order-create`，绝不自动下单。

## 依赖与接入

- 需要麦当劳 MCP Token：`open.mcd.cn/mcp` → 手机号登录 → 控制台 → 激活。
- Token 放仓库根目录 `.env`（已 gitignore），代码经 `config.py` 读取。
- 在 MCP Client（WorkBuddy 等）配置官方 MCP：

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

## 使用方式（给 Agent 的编排指引）

典型流程（均通过 `party_flow.PartyPlanner` 只读方法）：

1. `planner.products_by_category()` → 让用户选主题 / 类目。
2. `planner.compose_plan(product 或 category, city_name="广州市", people=人数)` → 组装方案
   （默认广州、默认取最近门店、默认首个可约日期）。
3. `report.render_plan_card(plan)` → 生成主题化 HTML 方案卡，交予用户。
4. 若用户要下单：先用 `party_flow.submit_party_order(..., confirm=False)` 生成**确认摘要**并展示；
   仅当用户明确回复确认后，才以 `confirm=True` 且补齐 `skuId` 后真正调用。

## 使用的麦当劳 MCP 工具（官方 v1.0.9）

`mall-points-products`、`query-party-city`、`query-party-store`、
`query-party-store-date`、`query-party-store-session`、`party-order-create`（仅确认后）。

## 合规红线

- 仅非商业用途，遵循《麦当劳 MCP 服务规则》《使用条款》。
- Token 不入库；不暗示官方背书；不伪造任何餐品/价格/活动数据（全部实时取自官方接口）。
- **下单必须用户明确确认后才执行**；未确认一律只出方案、不动交易。
- 派对工具真实名为 `query-party-store-date` / `query-party-store-session`（官方 README 表有笔误）。
