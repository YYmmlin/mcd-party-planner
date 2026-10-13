# 报名提交指南 + Issue 文案（已按官方仓库规则校正）

> 官方活动仓库：**https://github.com/M-China/mcd-developer-innovation-challenge**
> （注意：报名 Issue 提交到**这个仓库**，不是 `mcd-mcp-server`；后者只是 MCP 使用说明仓库）
> 截止：2026-10-25 23:59（北京时间）；以 2026-10-26 00:00 采集的 Star 数据定榜；奖品兑换截止 11-14。

---

## 一、⚠️ 上一次报名失败复盘（#591）

- Issue：#591「【参赛提交】麦麦派对策划师 mcd-party-planner」
- 机器人回复（2026-10-13 02:59）：
  > 您的作品未通过审核，失败原因：您的GitHub项目无法访问，您可以公开项目，或检查issue是否符合标准格式，并重新issue。
- 排查结论：
  1. **仓库本身没问题** —— `YYmmlin/mcd-party-planner` 为 `public`，GitHub API 可正常读取，非私有、非删除。
  2. **真正原因 = Issue 格式不合规**。机器人用 `项目地址：<url>` 单行规则提取仓库地址；#591 正文写成了 `## 项目地址` + 换行 + 裸链接，提取失败 → 被判"项目无法访问"。
  3. 附带问题：`CONTEST_DECLARATION.md` 用了自写版本，而官方要求**文件名与内容均不可改动**。

---

## 二、官方硬性要求（原文摘要）

| 序号 | 文件 | 要求 |
|---|---|---|
| 1 | `README.md` | 项目介绍/安装/示例/目标用户。**必须，文件名不可改动** |
| 2 | `CONTEST_DECLARATION.md` | 官方模板，**文件名及内容均不可改动** |
| 3 | `MCP_INTEGRATION.md` | 实际使用的 MCP Server / Tool / 调用流程 / 业务价值。必须 |
| 4 | 源代码 | 项目主体代码，形式不限。必须 |
| 5 | `workbuddy.md` | WorkBuddy 开发对话存档。非必须，但**参加 WorkBuddy 专项奖（前 100 名 3,000 积分）必须提交** |

**Issue 格式（严格）：**

```
Issue 标题：自定义报名标题
Issue 正文：
【参赛申请】
项目名称：{项目名称}
项目地址：{项目 GitHub 仓库地址}
项目简介：{项目简介}
```

> ⚠️ 官方警告：报名 Issue 的【标签】与【内容】之间**不要使用换行符**；项目地址**不要用 Markdown 格式**。

---

## 三、✅ 正确 Issue 文案（照抄，勿加空行 / 勿加 markdown）

**标题：**

```
【参赛申请】麦麦派对策划师（mcd-party-planner）
```

**正文（整体复制，注意：全文 4 行，行内不要换行，行间不要空行）：**

```
【参赛申请】
项目名称：麦麦派对策划师（mcd-party-planner）
项目地址：https://github.com/YYmmlin/mcd-party-planner
项目简介：麦当劳派对一站式策划 Skill（WorkBuddy 开发，纯 Python 标准库零依赖）。官方把派对能力开放成 5 个原子工具却没串成用户闭环，本项目补上这一环：从积分商城目录取派对商品（拿到 spuId）→ 默认城市广州、可切全国 280+ 城市按距离选门店 → 查真实可约日期 → 看场次（时段 / 成团人数 / 价格 / 余位）→ 一键生成主题化可分享方案卡（生日类 / 主题类 / 品鉴会 / 读书会 / 麦麦体验营各配专属配色）。下单设安全闸：仅在用户明确确认后才调用 party-order-create，缺 skuId 拒单，绝不自动扣款。
```

---

## 四、重新报名的操作步骤

1. **先把仓库两个改动推上去**（本次已改好）：
   - `CONTEST_DECLARATION.md` → 已替换为官方原文（内容零改动）
   - `SUBMISSION.md` → 本文档
2. **关闭旧 Issue #591**（或保留不管），**新开一个 Issue**：到
   https://github.com/M-China/mcd-developer-innovation-challenge/issues/new
   标题、正文照抄上面第三节。
3. 等机器人回复。成功会在 Issue 下回复成功通知。
4. 成功后开始拉票 → 排行榜只展示 **Star > 0** 的项目。

---

## 五、提交前自查

- [x] 仓库为 **Public**（已核，GitHub API `private:false`）
- [x] `.env` 未被提交（`git ls-files | grep -c "^\.env$"` = 0）
- [x] `.env.example` 仅占位符 `YOUR_MCP_TOKEN`
- [x] `README.md` / `CONTEST_DECLARATION.md` / `MCP_INTEGRATION.md` / `workbuddy.md` / `SKILL.md` 均在仓库内
- [x] `CONTEST_DECLARATION.md` 内容与官方一致
- [ ] 新 Issue 已按第三节格式重新提交
- [ ] Star 数已拉起来（当前 2 ★，榜单门槛约 6 ★）
