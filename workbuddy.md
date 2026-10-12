# workbuddy.md — 「麦麦派对策划师」开发对话存档

> 本作品使用 **WorkBuddy** 完成全部开发。本文档为开发过程存档，用于赛事"使用 WorkBuddy 开发"专项奖励核验。

## 一、项目与工具
- 项目：麦麦派对策划师（mcd-party-planner）
- 开发助手：**WorkBuddy**
- 底层能力：麦当劳中国官方 MCP 服务（https://mcp.mcd.cn）
- 技术栈：Python 标准库（零第三方依赖）

## 二、开发过程（时间线）

### 调研与定方向
- 读取赛事公众号文章、官方 MCP 仓库 README 与社区 issues，确认玩法：基于麦当劳 MCP 用 WorkBuddy 做 Agent Skill，公开仓库 + 报名 Issue，按 Star 排名。
- 竞品扫描：省钱比价 / 营养热量 / 多人订餐已是红海；**派对 / 主题活动**方向（官方 5 个工具）几乎无人使用 → 定为蓝海主方向。

### P0 可行性验证（由 WorkBuddy 编写零依赖探针，边测边修正）
1. 握手成功：`initialize` 返回 mcd-mcp v1.0.0；服务端**无状态**（不要求 session id）。
2. 工具清单纠错：`tools/list` 实际返回 **35** 个工具（官方 README 表写 33，社区 issue #16 亦有反馈）。
3. 派对工具真名纠错：真实名为 `query-party-store-date` / `query-party-store-session`（README 表误写为 `query-partystore-*`）。
4. 定位 spuId 入口：派对工具均需 `spuId`；从 `query-party-city` 描述得知"spuId 从 `mall-points-products` 获取"；再实测确认**不传 `catRuleIds` 时该工具返回全量目录**（派对商品 `shopId=5`，含生日类派对 / 主题类派对 / 品鉴会 / 读书会）。
5. 踩坑与修复：工具返回文本内含 `{data[].xxx}` 字段说明占位符，早期"取第一个 `{}`"提取 JSON 会被占位符卡住、误判空数据 → 改为"遍历每个 `{` 配平解析，取第一个含 `data`/`success` 的字典"。

### P1 核心开发
- 沉淀 `mcp_client.py`（零依赖客户端 + 健壮 JSON 提取）、`party_flow.py`（只读编排层 + `compose_plan` + 下单安全闸）。
- 按需求实现**默认城市广州**与**主题化方案卡**：`themes.py` 为每个类目定义配色气质，`report.py` 渲染自包含 HTML。
- 实跑（广州）：生日类派对 spuId=8516（¥138 / 5~12 人）、主题类派对 spuId=11308（¥118）、读书会 spuId=1830（¥45），均返回真实门店 / 日期 / 场次。
- **下单安全闸**：`submit_party_order(confirm=False)` 仅生成确认摘要、绝不发送；缺 skuId 拒单。实测拦截生效，全程未产生任何真实订单。

### 展示页配色修复
- 发现 showcase 页把多张完整 HTML 文档直接嵌入外层页面，各卡 `<style>` 互相覆盖导致配色失效 → 改用 `<iframe srcdoc>` 隔离渲染修复。

## 三、合规自查
- 全程仅只读查询，未调用任何下单 / 抽奖 / 兑换。
- 真实 Token 存于 `.env`（已被 `.gitignore` 忽略），未提交；`.env.example` 仅含占位符。
- 不暗示官方背书；数据全部实时取自官方接口，不缓存、不伪造。
