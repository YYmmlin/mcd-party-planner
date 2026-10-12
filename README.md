<div align="center">

# 🎪 麦麦派对策划师 · McParty Planner

### 一句话，办一场麦当劳派对。

基于**麦当劳中国官方 MCP**，把 5 个"派对原子能力"串成用户愿意用的闭环。

`Python 3.8+` · `零第三方依赖` · `MCP · 麦当劳中国` · `2026 麦当劳程序员节参赛作品` · `Made with WorkBuddy`

</div>

---

## 🤔 为什么做这个

麦当劳中国官方把「派对 / 主题活动」能力开放成了 MCP 工具——城市、门店、日期、场次、下单，一应俱全。
但这些原子接口单独拎出来都很"碎"：普通用户面对"选城市 → 挑门店 → 约日期 → 看场次 → 下单"一头雾水。

**麦麦派对策划师**做的就是把这个"总指挥"补上：一句对话走完整条链路，还能按主题生成可直接晒圈的方案卡。

> 官方能力很全，缺的是一个好用的编排层。

## ✨ 亮点

| | |
|---|---|
| 🎪 **蓝海切口** | 全网少有人做「麦当劳派对」场景，覆盖 生日类派对 / 主题类派对 / 品鉴会 / 亲子读书会 / 麦麦体验营 |
| 🗺 **默认广州、全国可达** | 默认城市广州，可切换 280+ 城市，按距离排序推荐可办门店 |
| 🗓 **真实可约** | 日期与场次（时段 / 成团人数 / 价格 / 余位）实时取自官方接口，不缓存、不伪造 |
| 🎨 **主题化方案卡** | 不同派对类目渲染不同配色气质，输出可分享 HTML |
| 🔒 **下单安全闸** | 仅在用户明确确认后才调用 `party-order-create`，缺 `skuId` 拒单，**绝不自动花你的钱** |
| 🪶 **零依赖** | 纯 Python 标准库，克隆即跑，离线可测 |

## 🎨 主题风格一览

不同派对主题 → 不同视觉风格（真实效果见 [`examples/showcase.html`](./examples/showcase.html)）：

| 主题 | 风格 | 主色 |
|---|---|---|
| 🎂 生日类派对 | 节日 · 暖 | 粉 `#FF5C8A` |
| 🎪 主题类派对 | 游乐 · 炫 | 紫 `#7C3AED` |
| 🍷 品鉴会 | 雅致 · 暗金 | 金 `#D4AF37` |
| 📚 亲子读书会 | 文艺 · 清朗 | 青绿 `#0E9F94` |
| 🚀 麦麦体验营 | 活力 · 翠绿 | 绿 `#0E9F6E` |

```bash
python tests/run_party_flow.py        # 默认广州，按类目生成主题方案卡到 examples/
```

## 🚀 快速开始

```bash
git clone <你的仓库> mcd-party-planner && cd mcd-party-planner
cp .env.example .env        # 填入真实 MCD_MCP_TOKEN
python tests/run_party_flow.py
```

## 🔧 接入麦当劳 MCP

1. 申请 Token：<https://open.mcd.cn/mcp> → 手机号登录 → 控制台 → 激活 → 复制。
2. 在 MCP Client（WorkBuddy / Cursor / Cherry Studio 等）配置：

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

踩坑记录与字段口径见 [`MCP_INTEGRATION.md`](./MCP_INTEGRATION.md)。

## 🧭 使用方式（作为 Skill）

```python
from party_flow import PartyPlanner
from report import render_plan_card

p = PartyPlanner(); p.c.initialize()
plan = p.compose_plan(category="生日类派对", city_name="广州市", people=8)  # 默认广州
print(render_plan_card(plan))   # 主题化方案卡 HTML
# 下单走安全闸：未确认只出确认摘要、绝不发送
```

技能描述见 [`SKILL.md`](./SKILL.md)。

## 🗂 项目结构

```
mcd-party-planner/
├── config.py         # Token / 配置加载（零依赖）
├── mcp_client.py     # 麦当劳 MCP 客户端（零依赖 + 健壮 JSON 提取）
├── party_flow.py     # 派对编排层（只读查询 + compose_plan + 下单安全闸）
├── themes.py         # 主题视觉预设（不同类目不同配色）
├── report.py         # 主题化方案卡 HTML 生成
├── SKILL.md          # WorkBuddy 技能描述
├── workbuddy.md      # WorkBuddy 开发存档
├── CONTEST_DECLARATION.md / MCP_INTEGRATION.md / SUBMISSION.md
├── .env.example      # Token 模板（可提交，占位符）
├── .gitignore        # 忽略 .env 等敏感/产物文件
├── examples/         # 生成的示例方案卡（showcase + 各主题单卡）
└── tests/            # 官方 MCP 只读探测 / 端到端实跑
```

## 🧪 测试

- `tests/run_party_flow.py`：端到端实跑 + 主题方案卡生成 + 下单安全闸演示。
- `tests/live_probe.py`、`tests/probe_party_catalog.py` 等：对官方 MCP 的只读探测。
- 全程只读，**不产生任何真实订单**。

## 🔒 安全与合规

- 真实 Token 仅存 `.env`（已被 `.gitignore` 忽略），**绝不入库**；`.env.example` 仅含占位符。
- 下单必须用户明确确认后执行；未确认一律只出方案、不动交易。
- 仅非商业用途，遵循《麦当劳 MCP 服务规则》《使用条款》；不暗示官方背书；数据全部实时取自官方接口。

## 🏆 参赛信息

- 赛事：**2026 麦当劳程序员创意开发大赛**（WorkBuddy × 麦当劳中国）
- 开发工具：**WorkBuddy**（开发存档见 [`workbuddy.md`](./workbuddy.md)）
- 参赛声明：[`CONTEST_DECLARATION.md`](./CONTEST_DECLARATION.md) · 报名文案：[`SUBMISSION.md`](./SUBMISSION.md)

## ⭐ 喜欢就点个 Star

如果这个点子对你有启发，欢迎 **Star / Fork / 提 Issue**。
也欢迎去官方仓库 [`M-China/mcd-mcp-server`](https://github.com/M-China/mcd-mcp-server) 围观麦当劳派对能力。

---

<div align="center"><sub>数据来自麦当劳中国官方 MCP 实时返回，仅供参考，以门店实际为准。本项目非麦当劳官方出品。</sub></div>
