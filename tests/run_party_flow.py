"""实跑派对规划：默认广州，按类目生成不同主题方案卡，并演示下单安全闸。

产出：
- examples/showcase.html            多主题风格一览
- examples/party_card_<slug>.html   各主题单独方案卡
用法：python tests/run_party_flow.py [城市名，默认广州市]
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from party_flow import (PartyPlanner, OrderNotConfirmed, submit_party_order)  # noqa: E402
from report import render_plan_card, render_showcase  # noqa: E402

SLUG = {"生日类派对": "birthday", "主题类派对": "theme", "品鉴会": "tasting",
        "读书会": "reading", "麦麦体验营": "camp"}
SHOWCASE_CATS = ["生日类派对", "主题类派对", "品鉴会", "读书会"]
EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def main():
    city_name = sys.argv[1] if len(sys.argv) > 1 else "广州市"
    p = PartyPlanner()
    p.c.initialize()

    groups = p.products_by_category()
    print(f"== 派对商品分类（默认城市 {city_name}）==")
    for cat, items in groups.items():
        print(f"  {cat}: {len(items)} 款")

    cards = []
    for cat in SHOWCASE_CATS:
        if cat not in groups:
            continue
        print(f"\n== 生成方案卡：{cat} ==")
        try:
            plan = p.compose_plan(category=cat, city_name=city_name, people=8)
        except ValueError as e:
            print(f"  跳过：{e}")
            continue
        print(f"  主题：{plan['product'].get('spuName')}（spuId={plan['product'].get('spuId')}）")
        print(f"  门店：{plan['city'].get('name')} {plan['store'].get('name')}")
        print(f"  日期：{plan['date']}  场次：{len(plan['sessions'])} 个")
        for s in plan["sessions"]:
            print(f"    - {s['time']} {s['people']} {s['price']} 余 {s['left']} 位")

        card = render_plan_card(plan)
        cards.append((cat, card))
        slug = SLUG.get(cat, "party")
        (EXAMPLES / f"party_card_{slug}.html").write_text(card, encoding="utf-8")

    if cards:
        (EXAMPLES / "showcase.html").write_text(render_showcase(cards), encoding="utf-8")
        print(f"\n✅ 已生成 {len(cards)} 张主题方案卡 + showcase.html 于 examples/")

    # ---- 演示下单安全闸（绝不下单）----
    print("\n== 演示下单安全闸（confirm=False，应被拦截）==")
    if "生日类派对" in groups:
        plan = p.compose_plan(category="生日类派对", city_name=city_name, people=8)
        if plan["sessions_raw"]:
            raw = plan["sessions_raw"][0]
            try:
                submit_party_order(p, plan, raw, people=8, confirm=False)
                print("  ⚠️ 未被拦截（异常！）")
            except OrderNotConfirmed as e:
                print("  ✅ 已被安全闸拦截，未发送订单。确认摘要：")
                for line in str(e).splitlines():
                    print("    " + line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
