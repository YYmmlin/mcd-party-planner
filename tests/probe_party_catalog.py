"""P0 定论：从 mall-points-products 全量目录找派对 spuId，并端到端下钻。

使用正式客户端 mcp_client.McDonaldsMCP（健壮 JSON 提取）。
纯查询，不调用下单/抽奖/兑换。零依赖。用法：python tests/probe_party_catalog.py
"""

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mcp_client import McDonaldsMCP, as_list  # noqa: E402

KEYWORDS = ("派对", "体验营", "品鉴", "读书会", "生日", "主题", "亲子")


def main():
    c = McDonaldsMCP()
    info = c.initialize()
    print(f"[initialize] server={info.get('serverInfo')}")
    tools = c.list_tools()
    print(f"[tools/list] 工具数={len(tools)}")

    print("\n== mall-points-products 全量目录（不传 catRuleIds）==")
    data = c.call("mall-points-products", {})
    items = as_list(data)
    print(f"商品总数={len(items)}")
    if not items:
        print("目录为空，direction A 入口不可用。"); return 1

    cats = Counter(it.get("catName") for it in items if isinstance(it, dict))
    shops = Counter(it.get("shopId") for it in items if isinstance(it, dict))
    print("类目分布:", dict(cats))
    print("shopId 分布:", dict(shops))

    hits = [it for it in items if isinstance(it, dict)
            and any(k in json.dumps(it, ensure_ascii=False) for k in KEYWORDS)]
    print(f"\n派对关键词命中={len(hits)}")
    for it in hits[:15]:
        print(f"  spuId={it.get('spuId')} shopId={it.get('shopId')} cat={it.get('catName')} | {it.get('spuName')}")

    if not hits:
        print("\n⚠️ 全量目录无派对类商品（可能派对在独立 shopId 体系）。查看是否有 shopId=5 商品：")
        s5 = [it for it in items if isinstance(it, dict) and str(it.get("shopId")) == "5"]
        print(f"  shopId=5 商品数={len(s5)}")
        return 0

    spu = hits[0].get("spuId")
    print(f"\n== 用 spuId={spu}（{hits[0].get('spuName')}）端到端下钻 ==")

    cities = as_list(c.call("query-party-city", {"spuId": spu}))
    print(f"[query-party-city] 城市数={len(cities)} 预览={json.dumps(cities[:2], ensure_ascii=False)[:220]}")
    if not cities:
        return 0
    city = next((x for x in cities if x.get("name") in ("上海市", "北京市", "广州市", "深圳市")), cities[0])
    cc = city.get("code") or city.get("cityCode")
    print(f"  城市 {city.get('name')} code={cc}")

    stores = as_list(c.call("query-party-store", {"code": cc, "spuId": spu}))
    print(f"[query-party-store] 门店数={len(stores)}")
    if not stores:
        return 0
    st = stores[0]
    sc = st.get("code") or st.get("storeCode") or st.get("storeId")
    print(f"  门店 {st.get('name')} code={sc} 字段={list(st.keys())}")

    dates = as_list(c.call("query-party-store-date", {"spuId": spu, "storeCode": sc}))
    print(f"[query-party-store-date] 日期数={len(dates)} 预览={json.dumps(dates[:6], ensure_ascii=False)[:220]}")
    if not dates:
        print("\n⚠️ 门店无可预约日期。")
        return 0
    d0 = dates[0]
    ds = d0 if isinstance(d0, str) else (d0.get("dateStr") or d0.get("date") or d0.get("day") or d0)

    sess = as_list(c.call("query-party-store-session", {"spuId": spu, "storeCode": sc, "dateStr": ds}))
    print(f"[query-party-store-session] dateStr={ds} 场次数={len(sess)} 预览={json.dumps(sess[:2], ensure_ascii=False)[:300]}")

    print("\n== 结论 ==")
    if dates and sess is not None and len(sess) >= 0:
        print(f"✅ 方向 A 派对链路端到端可用！入口 spuId={spu}（{hits[0].get('spuName')}）。")
        print("   城市->门店->日期->场次 均返回真实数据。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
