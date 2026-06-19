"""卡拍拍價格查詢與 OPTCG SIM 牌組解析。"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Literal
from urllib.parse import quote
from urllib.request import Request, urlopen

KAPAIPAI_PACK_API = (
    "https://trade.kapaipai.tw/api/card/getCardPackDetailList?game=onejp&packId={pack}"
)
KAPAIPAI_IMAGE_BASE = "https://static.kapaipai.tw/image/card"
KAPAIPAI_CARD_URL = "https://trade.kapaipai.tw/card/{card_id}"
USER_AGENT = "OPTCG-Deck-Pricing/1.0"

PACK_MAP = {
    "OP01": "OP-01", "OP02": "OP-02", "OP03": "OP-03", "OP04": "OP-04",
    "OP05": "OP-05", "OP06": "OP-06", "OP07": "OP-07", "OP08": "OP-08",
    "OP09": "OP-09", "OP10": "OP-10", "OP11": "OP-11", "OP12": "OP-12",
    "OP13": "OP13", "OP14": "OP-14", "OP15": "OP15", "OP16": "OP16",
    "EB01": "EB-01", "EB02": "EB-02", "EB03": "EB-03", "EB04": "EB-04",
    "ST01": "ST-01", "ST02": "ST-02", "ST03": "ST-03", "ST04": "ST-04",
    "ST05": "ST-05", "ST06": "ST-06", "ST07": "ST-07", "ST08": "ST-08",
    "ST09": "ST-09", "ST10": "ST-10", "ST11": "ST-11", "ST12": "ST-12",
    "ST13": "ST-13", "ST14": "ST-14", "ST15": "ST-15", "ST16": "ST-16",
    "ST17": "ST-17", "ST18": "ST-18", "ST19": "ST-19", "ST20": "ST-20",
    "ST21": "ST-21", "ST22": "ST-22", "ST23": "ST-23", "ST24": "ST-24",
    "ST25": "ST-25", "ST26": "ST-26", "ST27": "ST-27", "ST28": "ST-28",
    "ST29": "ST-29",
}

DECK_ENTRY_RE = re.compile(r"(\d+)x([A-Z]+\d*-[A-Z0-9]+)", re.I)
CARD_ID_RE = re.compile(r"^([A-Z]+)(\d+)-(\d+[A-Z]?)$", re.I)
ALT_MARKERS = ("異圖", "異畫", "漫畫", "SP", "SP2")

_pack_cache: dict[str, tuple[float, list[dict]]] = {}
CACHE_TTL = 3600


def fetch_text(url: str, timeout: int = 60) -> str:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def pack_ids_for_set(set_code: str) -> list[str]:
    primary = PACK_MAP.get(set_code, set_code)
    alts = [primary]
    if primary.startswith("OP-"):
        alts.append(primary.replace("OP-", "OP", 1))
    elif primary.startswith("OP") and "-" not in primary:
        alts.append(f"OP-{primary[2:]}")
    elif primary.startswith("EB-"):
        alts.append(primary.replace("EB-", "EB", 1))
    elif primary.startswith("ST-"):
        alts.append(primary.replace("ST-", "ST", 1))
    seen: set[str] = set()
    out: list[str] = []
    for p in alts:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def packs_for_card(card_id: str) -> list[str]:
    card_id = card_id.upper()
    if card_id.startswith("P-"):
        return ["PR", "PRB-01"]
    m = CARD_ID_RE.match(card_id)
    if not m:
        return ["PRB-01"]
    set_code = f"{m.group(1)}{m.group(2)}"
    packs = pack_ids_for_set(set_code)
    if "PRB-01" not in packs:
        packs.append("PRB-01")
    return packs


def promo_card_match(card_id: str, pack_card_id: str) -> bool:
    """PR 分類：P-115 或 P-001(異圖1) 等變體。"""
    pid = str(pack_card_id).upper()
    if pid == card_id:
        return True
    return pid.startswith(f"{card_id}(")


def fetch_pack(pack_id: str) -> list[dict]:
    now = time.time()
    cached = _pack_cache.get(pack_id)
    if cached and now - cached[0] < CACHE_TTL:
        return cached[1]
    url = KAPAIPAI_PACK_API.format(pack=pack_id)
    data = json.loads(fetch_text(url))
    if data.get("code") != 0:
        cards: list[dict] = []
    else:
        cards = data.get("data", {}).get("list", []) or []
    _pack_cache[pack_id] = (now, cards)
    return cards


def normalize_pack_card_id(card_id: str, raw: str) -> str:
    raw = str(raw).upper()
    if re.match(r"^\d+[A-Z]?$", raw):
        m = CARD_ID_RE.match(card_id.upper())
        if m:
            return f"{m.group(1)}{m.group(2)}-{raw}"
    return raw


def card_id_matches(card_id: str, raw_pack_card_id: str) -> bool:
    raw = str(raw_pack_card_id).upper()
    if card_id.startswith("P-"):
        return promo_card_match(card_id, raw)
    pid = normalize_pack_card_id(card_id, raw)
    return pid == card_id


def find_card_variants(card_id: str) -> list[dict]:
    card_id = card_id.upper()
    variants: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for pack_id in packs_for_card(card_id):
        for row in fetch_pack(pack_id):
            raw_pid = str(row.get("packCardId", "")).upper()
            if not card_id_matches(card_id, raw_pid):
                continue
            rare = (row.get("rare") or [""])[0]
            key = (raw_pid, rare)
            if key in seen:
                continue
            seen.add(key)
            variants.append(row)
    return variants


def is_alt_variant(rare: str, pack_card_id: str = "") -> bool:
    if any(marker in rare for marker in ALT_MARKERS):
        return True
    if "(" in pack_card_id:
        suffix = pack_card_id.split("(", 1)[1]
        if any(m in suffix for m in ("異圖", "異畫", "漫畫", "BCG", "LIVE", "裁判", "ジャン")):
            return True
    return False


def kapaipai_image_url(card: dict) -> str:
    rare = card["rare"][0] if card.get("rare") else "無標記"
    encoded = quote(
        f"onejp/{card['cardGlobalKey']}/{card['packId']}/{card['packCardId']}/{rare}.jpg",
        safe="",
    )
    return f"{KAPAIPAI_IMAGE_BASE}/{encoded}"


PriceBasis = Literal["average", "lowest"]
VariantMode = Literal["standard", "cheapest"]


def variant_price(v: dict, basis: PriceBasis) -> int | None:
    low = v.get("lowestPrice")
    avg = v.get("averagePrice")
    if basis == "average":
        if avg and avg > 0:
            return int(avg)
        if low is not None and low > 0:
            return int(low)
        return None
    if low is not None and low >= 0:
        return int(low)
    return None


def pick_variant(
    variants: list[dict],
    mode: VariantMode = "standard",
    *,
    basis: PriceBasis = "average",
) -> dict | None:
    if not variants:
        return None
    if mode == "cheapest":
        pool = variants
    else:
        standards = [
            v for v in variants
            if not is_alt_variant(
                (v.get("rare") or [""])[0],
                str(v.get("packCardId", "")),
            )
        ]
        pool = standards or variants
    return min(pool, key=lambda v: variant_price(v, basis) or 10**9)


def resolve_unit_price(selected: dict, basis: PriceBasis) -> tuple[int | None, str]:
    """回傳 (單價, 價格來源說明)。"""
    low = selected.get("lowestPrice")
    avg = selected.get("averagePrice")
    if basis == "average":
        if avg and avg > 0:
            return int(avg), "average"
        if low is not None and low >= 0:
            return int(low), "lowest_fallback"
        return None, ""
    if low is not None and low >= 0:
        return int(low), "lowest"
    return None, ""


def parse_deck(text: str) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for m in DECK_ENTRY_RE.finditer(text):
        card_id = m.group(2).upper()
        counts[card_id] = counts.get(card_id, 0) + int(m.group(1))
    return sorted(counts.items())


@dataclass
class VariantInfo:
    id: int
    rare: str
    lowest_price: int
    average_price: int
    card_name: str
    image_url: str
    is_alt: bool


@dataclass
class CardPriceResult:
    card_id: str
    quantity: int
    card_name: str
    rare: str
    unit_price: int | None
    line_total: int | None
    lowest_price: int
    average_price: int
    price_source: str
    image_url: str
    kapaipai_url: str
    variants: list[VariantInfo] = field(default_factory=list)
    status: str = "ok"
    message: str = ""


def price_deck(
    text: str,
    *,
    mode: VariantMode = "standard",
    basis: PriceBasis = "average",
) -> dict:
    entries = parse_deck(text)
    if not entries:
        return {
            "cards": [],
            "total_cards": 0,
            "unique_cards": 0,
            "total_price": 0,
            "priced_cards": 0,
            "missing_cards": 0,
            "error": "無法解析牌組，請確認格式為 OPTCG SIM（例如 4xOP01-016）",
        }

    results: list[CardPriceResult] = []
    total_price = 0
    total_cards = 0
    priced_cards = 0
    missing_cards = 0

    for card_id, qty in entries:
        total_cards += qty
        variants = find_card_variants(card_id)
        selected = pick_variant(variants, mode, basis=basis)
        variant_infos = [
            VariantInfo(
                id=v["id"],
                rare=(v.get("rare") or [""])[0],
                lowest_price=v.get("lowestPrice") or 0,
                average_price=v.get("averagePrice") or 0,
                card_name=v.get("cardName", ""),
                image_url=kapaipai_image_url(v),
                is_alt=is_alt_variant(
                    (v.get("rare") or [""])[0],
                    str(v.get("packCardId", "")),
                ),
            )
            for v in variants
        ]

        if not selected:
            results.append(CardPriceResult(
                card_id=card_id,
                quantity=qty,
                card_name="",
                rare="",
                unit_price=None,
                line_total=None,
                lowest_price=0,
                average_price=0,
                price_source="",
                image_url="",
                kapaipai_url=KAPAIPAI_CARD_URL.format(card_id=card_id),
                variants=variant_infos,
                status="missing",
                message="卡拍拍找不到此卡",
            ))
            missing_cards += 1
            continue

        unit, price_source = resolve_unit_price(selected, basis)
        rare = (selected.get("rare") or [""])[0]
        line_total = unit * qty if unit is not None else None
        if line_total is not None:
            total_price += line_total
            priced_cards += 1

        results.append(CardPriceResult(
            card_id=card_id,
            quantity=qty,
            card_name=selected.get("cardName", ""),
            rare=rare,
            unit_price=unit,
            line_total=line_total,
            lowest_price=selected.get("lowestPrice") or 0,
            average_price=selected.get("averagePrice") or 0,
            price_source=price_source,
            image_url=kapaipai_image_url(selected),
            kapaipai_url=KAPAIPAI_CARD_URL.format(card_id=card_id),
            variants=variant_infos,
            status="ok",
            message="",
        ))

    return {
        "cards": [result_to_dict(r) for r in results],
        "total_cards": total_cards,
        "unique_cards": len(entries),
        "total_price": total_price,
        "priced_cards": priced_cards,
        "missing_cards": missing_cards,
        "price_mode": mode,
        "price_basis": basis,
        "error": "",
    }


def result_to_dict(r: CardPriceResult) -> dict:
    return {
        "cardId": r.card_id,
        "quantity": r.quantity,
        "cardName": r.card_name,
        "rare": r.rare,
        "unitPrice": r.unit_price,
        "lineTotal": r.line_total,
        "lowestPrice": r.lowest_price,
        "averagePrice": r.average_price,
        "priceSource": r.price_source,
        "imageUrl": r.image_url,
        "kapaipaiUrl": r.kapaipai_url,
        "status": r.status,
        "message": r.message,
        "variants": [
            {
                "id": v.id,
                "rare": v.rare,
                "lowestPrice": v.lowest_price,
                "averagePrice": v.average_price,
                "cardName": v.card_name,
                "imageUrl": v.image_url,
                "isAlt": v.is_alt,
            }
            for v in r.variants
        ],
    }
