# 报名提交指南 + Issue 文案

> 截止：2026-10-25 23:59（北京时间）；定榜 10-26；奖品兑换截止 11-14。
> GitHub 仓库 / Issue 需用**你本人的 GitHub 账号**操作（涉及个人账号与 Token），这里只提供就绪文案与步骤。

## 一、提交步骤
1. 在 GitHub **新建公开仓库**（建议名 `mcd-party-planner`）。
2. **确认无密钥泄漏**：`.env` 已被 `.gitignore` 忽略（不会提交）；`.env.example` 仅含占位符 `YOUR_MCP_TOKEN`。
3. 提交并推送全部源码，确保包含：`SKILL.md`、`workbuddy.md`、`CONTEST_DECLARATION.md`、`MCP_INTEGRATION.md`、`config.py`、`mcp_client.py`、`party_flow.py`、`themes.py`、`report.py`、`tests/`、`examples/`、`README.md`、`.gitignore`、`.env.example`。
4. 到 <https://github.com/M-China/mcd-mcp-server> → **Issues → New issue**，粘贴下方文案，标题建议：`【参赛提交】麦麦派对策划师 mcd-party-planner`。
5. 提交后拉票求 Star（社交平台 / 社区 / 朋友圈），Star 数决定排名。

## 二、Issue 文案（复制粘贴，替换 <你的账号>）

```markdown
【参赛提交】麦麦派对策划师（mcd-party-planner）

## 项目名称
麦麦派对策划师（mcd-party-planner）

## 项目地址
https://github.com/<你的账号>/mcd-party-planner

## 项目概述
麦麦派对策划师是基于麦当劳中国官方 MCP 能力、使用 WorkBuddy 开发的派对/主题活动规划 Skill。
官方把派对能力开放成了 5 个原子工具，却几乎没人把它们串成用户愿意用的闭环——本项目正是补上这一环：
从积分商城目录取出派对商品（拿 spuId）→ 选城市挑门店 → 查可约日期 → 看场次 → 一键生成主题化可分享方案卡。
纯 Python 标准库实现，零第三方依赖，可被 WorkBuddy 等 MCP 客户端直接调用。

## 功能亮点
- 🎪 蓝海切口：全网少有人做「麦当劳派对」场景，覆盖生日类派对/主题类派对/品鉴会/读书会/麦麦体验营。
- 🗺 默认城市广州、可切换全国 280+ 城市，按距离排序推荐可办门店。
- 🗓 真实可约日期与场次（时段/成团人数/价格/余位）实时取自官方接口。
- 🎨 主题化方案卡：不同派对类目渲染不同配色气质（生日粉/主题紫/品鉴暗金/读书会青绿），输出可分享 HTML。
- 🔒 下单安全闸：仅在用户明确确认后才调用 party-order-create，缺 skuId 拒单，绝不自动下单。
- 🧪 零依赖 + 离线可跑：内置探针/实跑脚本，全部只读查询，不碰任何真实交易。

## 调用的麦当劳 MCP 工具（官方 v1.0.9）
mall-points-products、query-party-city、query-party-store、query-party-store-date、
query-party-store-session、party-order-create（仅用户确认后）。

## 参赛开发工具
WorkBuddy（已使用）。开发对话存档见仓库 workbuddy.md；参赛声明见 CONTEST_DECLARATION.md；接入说明见 MCP_INTEGRATION.md。
```

## 三、提交前自查
- [ ] 仓库设为**公开**
- [ ] `.env` 未被提交（`git ls-files | grep -c "^.env$"` 应为 0）
- [ ] `.env.example` 只有占位符
- [ ] `workbuddy.md` / `CONTEST_DECLARATION.md` / `MCP_INTEGRATION.md` / `SKILL.md` 均在仓库内
- [ ] README 有亮点说明与示例截图（`examples/showcase.html` 可截图作配图）
