#!/usr/bin/env python3
"""下載卡拍拍各系列卡表，存成本地快取供 Render 等雲端主機使用。"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from kapaipai import DISK_CACHE_DIR, PACK_MAP, fetch_kapaipai_json

EXTRA_PACKS = ("PR", "PRB-01")


def all_pack_ids() -> list[str]:
    ids: set[str] = set(PACK_MAP.values())
    ids.update(EXTRA_PACKS)
    for pack_id in list(ids):
        if pack_id.startswith("OP-"):
            ids.add(pack_id.replace("OP-", "OP", 1))
        elif pack_id.startswith("OP") and "-" not in pack_id and pack_id.startswith("OP"):
            ids.add(f"OP-{pack_id[2:]}")
        elif pack_id.startswith("EB-"):
            ids.add(pack_id.replace("EB-", "EB", 1))
        elif pack_id.startswith("ST-"):
            ids.add(pack_id.replace("ST-", "ST", 1))
    return sorted(ids)


def main() -> int:
    DISK_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    pack_ids = all_pack_ids()
    ok = 0
    empty = 0
    failed: list[str] = []

    print(f"Fetching {len(pack_ids)} packs from kapaipai...")
    for i, pack_id in enumerate(pack_ids, 1):
        print(f"[{i}/{len(pack_ids)}] {pack_id}...", end=" ", flush=True)
        try:
            data = fetch_kapaipai_json(pack_id)
            cards = data.get("data", {}).get("list", []) or []
            out = DISK_CACHE_DIR / f"{pack_id.replace('/', '_')}.json"
            out.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            if cards:
                ok += 1
                print(f"{len(cards)} cards")
            else:
                empty += 1
                print("empty")
        except Exception as exc:
            failed.append(pack_id)
            print(f"FAIL: {exc}")
        time.sleep(0.15)

    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pack_count": len(pack_ids),
        "with_cards": ok,
        "empty": empty,
        "failed": failed,
    }
    (DISK_CACHE_DIR.parent / "cache_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print()
    print(f"Done: {ok} packs with cards, {empty} empty, {len(failed)} failed")
    if failed:
        print("Failed:", ", ".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
