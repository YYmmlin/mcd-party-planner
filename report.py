"""方案卡 HTML 生成：按派对主题渲染不同风格的可分享卡片。

零第三方依赖，输出自包含 HTML（内联 CSS），便于保存 / 分享 / 冲 Star。
入口：render_plan_card(plan) -> str
"""

import html

from themes import get_theme


def _esc(x):
    return html.escape(str(x if x is not None else ""))


def render_plan_card(plan):
    """把 compose_plan 产出的 plan 渲染成一张主题化 HTML 方案卡。"""
    t = get_theme(plan.get("category"))
    product = plan.get("product", {})
    city = plan.get("city", {})
    store = plan.get("store", {})
    date = plan.get("date", "")
    sessions = plan.get("sessions", [])
    people = plan.get("people")

    session_rows = "".join(
        "<tr><td>{time}</td><td>{people}</td><td class=\"price\">{price}</td>"
        "<td>余 {left} 位</td></tr>".format(
            time=_esc(s.get("time")), people=_esc(s.get("people")),
            price=_esc(s.get("price")), left=_esc(s.get("left")))
        for s in sessions
    ) or '<tr><td colspan="4">该日暂无可预约场次，可改约其他日期</td></tr>'

    people_line = f"{people} 人" if people else "人数待定"
    store_rows = "".join(
        "<div class=\"row\"><span class=\"k\">备选 {i}</span><span class=\"v\">{n}｜{d}</span></div>".format(
            i=i + 1, n=_esc(s.get("name")), d=_esc(s.get("distanceText")))
        for i, s in enumerate(plan.get("stores", [])[1:4])
    )

    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{emoji} {name} · 派对方案</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin:0; padding:24px; font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;
         background:{bg}; color:{text}; min-height:100vh; }}
  .card {{ max-width:520px; margin:0 auto; background:{card}; border-radius:20px;
          box-shadow:0 12px 40px rgba(0,0,0,.18); overflow:hidden; }}
  .hero {{ padding:28px 24px; background:{primary}; color:#fff; }}
  .hero .emoji {{ font-size:40px; }}
  .hero h1 {{ margin:8px 0 4px; font-size:21px; line-height:1.3; }}
  .hero .tag {{ display:inline-block; margin-top:10px; padding:4px 12px; border-radius:999px;
               background:rgba(255,255,255,.22); font-size:12px; }}
  .body {{ padding:18px 24px 24px; }}
  .badge {{ display:inline-block; background:{chip}; color:{text}; border-radius:6px;
           padding:3px 10px; font-size:12px; margin:0 6px 6px 0; }}
  .row {{ display:flex; justify-content:space-between; padding:9px 0; border-bottom:1px dashed {chip}; }}
  .row .k {{ color:{muted}; font-size:13px; }}
  .row .v {{ font-size:14px; font-weight:600; text-align:right; max-width:62%; }}
  h2 {{ font-size:15px; margin:18px 0 6px; color:{primary}; }}
  table {{ width:100%; border-collapse:collapse; font-size:13px; }}
  th, td {{ text-align:left; padding:8px 6px; border-bottom:1px solid {chip}; }}
  th {{ color:{muted}; font-weight:500; }}
  .price {{ color:{primary}; font-weight:700; }}
  .foot {{ margin-top:16px; font-size:11px; color:{muted}; line-height:1.7; }}
</style>
</head>
<body>
  <div class="card">
    <div class="hero">
      <div class="emoji">{emoji}</div>
      <h1>{name}</h1>
      <div class="tag">{tagline}</div>
    </div>
    <div class="body">
      <div><span class="badge">{category}</span><span class="badge">{people_line}</span></div>
      <h2>📍 门店</h2>
      <div class="row"><span class="k">城市</span><span class="v">{city}</span></div>
      <div class="row"><span class="k">餐厅</span><span class="v">{store}</span></div>
      <div class="row"><span class="k">地址</span><span class="v">{address}</span></div>
      {store_rows}
      <h2>🗓 日期 {date}</h2>
      <table>
        <thead><tr><th>时段</th><th>人数</th><th>价格</th><th>余位</th></tr></thead>
        <tbody>{session_rows}</tbody>
      </table>
      <div class="foot">
        数据来自麦当劳中国官方 MCP 实时返回，仅供参考，以门店实际为准。<br>
        本卡片由「麦麦派对策划师」生成，非麦当劳官方出品；下单需用户确认后进行。
      </div>
    </div>
  </div>
</body>
</html>""".format(
        emoji=_esc(t["emoji"]), name=_esc(product.get("spuName") or t["title"]),
        tagline=_esc(t["tagline"]), bg=t["bg"], card=t["card"], primary=t["primary"],
        text=t["text"], muted=t["muted"], chip=t["chip"],
        category=_esc(plan.get("category") or "派对"), people_line=_esc(people_line),
        city=_esc(city.get("name")), store=_esc(store.get("name")),
        address=_esc(store.get("address")), store_rows=store_rows,
        date=_esc(date), session_rows=session_rows,
    )


def render_showcase(items):
    """把多张卡片纵向拼成展示页。items: [(label, card_html), ...]。

    每张卡用 <iframe srcdoc> 隔离渲染——否则各卡自带 <style> 会作为全局样式
    互相覆盖（同名选择器后者胜出），导致主题配色失效。
    """
    frames = []
    for label, doc in items:
        esc = html.escape(doc, quote=True)
        frames.append(
            '<div class="wrap"><div class="label">{label}</div>'
            '<iframe class="cardframe" loading="lazy" title="{label}" srcdoc="{esc}"></iframe></div>'
            .format(label=html.escape(label), esc=esc))
    frames_html = "".join(frames)
    return """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>麦麦派对策划师 · 主题风格一览</title>
<style>
  body {{ margin:0; padding:24px; background:#EEF1F5;
         font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif; }}
  h1 {{ text-align:center; font-size:18px; color:#374151; margin:8px 0 22px; }}
  .wrap {{ max-width:560px; margin:0 auto 30px; }}
  .label {{ font-size:13px; color:#6B7280; margin:0 0 8px 4px; font-weight:600; }}
  .cardframe {{ width:100%; border:0; border-radius:20px; display:block;
               box-shadow:0 10px 30px rgba(0,0,0,.12); background:transparent; }}
</style></head>
<body>
<h1>🎉 麦麦派对策划师 · 不同主题风格方案卡</h1>
{frames}
<script>
  function fit() {{
    document.querySelectorAll('iframe.cardframe').forEach(function(f) {{
      try {{ f.style.height = (f.contentDocument.body.scrollHeight + 48) + 'px'; }}
      catch (e) {{ f.style.height = '760px'; }}
    }});
  }}
  window.addEventListener('load', fit);
</script>
</body></html>""".format(frames=frames_html)
