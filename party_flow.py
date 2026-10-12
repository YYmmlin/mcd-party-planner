"""派对规划编排层：把麦当劳派对 MCP 工具串成可用链路。

设计原则：
- 查询层只做**只读**（列商品 / 城市 / 门店 / 日期 / 场次）。
- 下单走**安全闸** submit_party_order：confirm=False 时只生成确认摘要、绝不发送；
  仅当用户明确确认(confirm=True)且补齐 skuId 后才真正调用 party-order-create。
- 默认城市：广州市。复用 mcp_client.McDonaldsMCP（零第三方依赖）。

P0 已实测确认的字段口径：
- 派对商品来自 mall-points-products 全量目录（不传 catRuleIds），shopId=5。
- query-party-city(spuId) -> data[].code/name/latitude/longitude
- query-party-store(code=cityCode, spuId) -> data[].code(门店码)/name/distance/distanceText/businessStatus
- query-party-store-date(spuId, storeCode) -> data[].date/storeCode
- query-party-store-session(spuId, storeCode, dateStr) -> data[].id/timeStart/timeEnd/partyMin/partyMax/price(分)/leftNum
"""

from mcp_client import McDonaldsMCP, as_list

PARTY_CATEGORIES = ("生日类派对", "主题类派对", "品鉴会", "读书会", "麦麦体验营")
DEFAULT_CITY = "广州市"


def fen_to_yuan(fen):
    """分 -> 元字符串。"""
    try:
        return f"¥{int(fen) / 100:.2f}"
    except (TypeError, ValueError):
        return "价格待询"


def resolve_city(cities, name=DEFAULT_CITY):
    """在城市列表里按名称找城市；找不到则包含匹配；再不行取第一个。"""
    for c in cities:
        if c.get("name") == name:
            return c
    key = (name or "").replace("市", "")
    for c in cities:
        if key and key in (c.get("name") or ""):
            return c
    return cities[0] if cities else None


class OrderNotConfirmed(Exception):
    """下单未获用户明确确认（或信息不全）时抛出，阻止真实交易。"""


class PartyPlanner:
    def __init__(self, client=None):
        self.c = client or McDonaldsMCP()
        self._catalog = None

    # ---- 只读查询 ----
    def list_party_products(self, refresh=False):
        """派对/主题活动商品（shopId=5），含 spuId/spuName/catName/point。"""
        if self._catalog is None or refresh:
            self._catalog = as_list(self.c.call("mall-points-products", {}))
        return [it for it in self._catalog
                if isinstance(it, dict) and str(it.get("shopId")) == "5"]

    def products_by_category(self):
        """按类目分组返回 {catName: [products]}。"""
        groups = {}
        for it in self.list_party_products():
            groups.setdefault(it.get("catName") or "其他", []).append(it)
        return groups

    def cities(self, spu_id):
        return as_list(self.c.call("query-party-city", {"spuId": spu_id}))

    def stores(self, spu_id, city_code, lat=None, lng=None):
        args = {"code": city_code, "spuId": spu_id}
        if lat is not None:
            args["latitude"] = lat
        if lng is not None:
            args["longitude"] = lng
        return as_list(self.c.call("query-party-store", args))

    def dates(self, spu_id, store_code):
        return as_list(self.c.call("query-party-store-date", {"spuId": spu_id, "storeCode": store_code}))

    def sessions(self, spu_id, store_code, date_str):
        return as_list(self.c.call("query-party-store-session",
                                   {"spuId": spu_id, "storeCode": store_code, "dateStr": date_str}))

    def nearby_stores(self, spu_id, city_code, limit=5):
        stores = self.stores(spu_id, city_code)

        def dist(s):
            d = s.get("distance")
            return d if isinstance(d, (int, float)) else float("inf")

        return sorted(stores, key=dist)[:limit]

    @staticmethod
    def format_session(s):
        return {
            "sessionId": s.get("id"),
            "time": f"{s.get('timeStart')}–{s.get('timeEnd')}",
            "people": f"{s.get('partyMin')}~{s.get('partyMax')}人",
            "price": fen_to_yuan(s.get("price")),
            "left": s.get("leftNum"),
        }

    # ---- 组装方案（只读）----
    def compose_plan(self, product=None, category=None, city_name=DEFAULT_CITY,
                     people=None, date_str=None):
        """组装一份派对方案。product 为空时取该类目第一款；默认城市广州。"""
        if product is None:
            if category:
                items = self.products_by_category().get(category, [])
            else:
                items = self.list_party_products()
            if not items:
                raise ValueError("未找到派对商品")
            product = items[0]

        spu = product.get("spuId")
        cat = product.get("catName")
        cities = self.cities(spu)
        city = resolve_city(cities, city_name)
        if not city:
            raise ValueError(f"商品 {product.get('spuName')} 不支持城市 {city_name}")
        cc = city.get("code")

        stores = self.nearby_stores(spu, cc, limit=5)
        if not stores:
            raise ValueError(f"{city.get('name')} 暂无可办该主题的门店")
        store = stores[0]
        sc = store.get("code")

        dates = self.dates(spu, sc)
        chosen_date = date_str or (dates[0].get("date") if dates else None)
        raw_sessions = self.sessions(spu, sc, chosen_date) if chosen_date else []

        return {
            "product": product,
            "category": cat,
            "city": city,
            "stores": stores,
            "store": store,
            "dates": dates,
            "date": chosen_date,
            "sessions": [self.format_session(s) for s in raw_sessions],
            "sessions_raw": raw_sessions,
            "people": people,
        }


# ---- 下单安全闸 ----
def build_order_summary(plan, raw_session, people, party_type=2):
    """生成人类可读的下单确认摘要（不发送）。"""
    p, store, city = plan["product"], plan["store"], plan["city"]
    pt = "包场" if party_type == 1 else "拼团"
    return (
        "请确认以下派对订单：\n"
        f"· 主题：{p.get('spuName')}（{plan.get('category')}）\n"
        f"· 门店：{city.get('name')} {store.get('name')}\n"
        f"· 日期 / 场次：{plan.get('date')} {raw_session.get('timeStart')}–{raw_session.get('timeEnd')}\n"
        f"· 人数：{people} 人（{raw_session.get('partyMin')}~{raw_session.get('partyMax')} 人成团）\n"
        f"· 价格：{fen_to_yuan(raw_session.get('price'))} · 类型：{pt}\n"
        "确认后才会真正提交订单。回复“确认”继续，否则取消。"
    )


def submit_party_order(planner, plan, raw_session, people, party_type=2,
                       confirm=False, sku_id=None):
    """下单安全闸。

    - confirm=False：抛 OrderNotConfirmed（附确认摘要），绝不发送。
    - confirm=True 但缺 sku_id：抛 OrderNotConfirmed，拒绝下单。
    - confirm=True 且信息齐全：才调用 party-order-create。
    """
    summary = build_order_summary(plan, raw_session, people, party_type)
    if not confirm:
        raise OrderNotConfirmed(summary)
    if sku_id in (None, ""):
        raise OrderNotConfirmed("缺少 skuId，拒绝下单（请先从商品详情补齐 skuId）。\n" + summary)

    payload = {
        "partyType": party_type,
        "code": str(plan["city"].get("code")),
        "storeCode": str(plan["store"].get("code")),
        "dateStr": plan["date"],
        "id": raw_session.get("id"),
        "count": int(people),
        "spuId": plan["product"].get("spuId"),
        "skuId": sku_id,
        "timeStart": raw_session.get("timeStart"),
        "timeEnd": raw_session.get("timeEnd"),
        "leftNum": raw_session.get("leftNum"),
        "partyTimeInfo": {
            "id": raw_session.get("id"),
            "leftNum": raw_session.get("leftNum"),
            "partyMax": raw_session.get("partyMax"),
            "partyMin": raw_session.get("partyMin"),
            "price": raw_session.get("price"),
            "timeEnd": raw_session.get("timeEnd"),
            "timeStart": raw_session.get("timeStart"),
        },
    }
    return planner.c.call("party-order-create", payload)
