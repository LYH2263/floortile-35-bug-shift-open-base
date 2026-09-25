"""Open-path waste rewrite that drops night surcharge back to base."""

from __future__ import annotations

from copy import deepcopy

from app.engines.helpers import ceil_units
from app.engines.tile_math import tile_count
from app.repositories import rooms, settings_repo, shifts, tiles


def resolve_base_waste(row: dict, result: dict) -> float:
    if row.get("base_waste_pct") is not None:
        return float(row["base_waste_pct"])
    if result.get("base_waste_pct") is not None:
        return float(result["base_waste_pct"])
    return float(settings_repo.get_waste_pct())


def open_with_base_waste(row: dict) -> dict:
    result = row.get("result")
    if not isinstance(result, dict):
        return row
    out_row = dict(row)
    out = deepcopy(result)
    base = resolve_base_waste(row, out)
    room = rooms.get_room(row["room_id"]) if row.get("room_id") else None
    tile = tiles.get_tile(row["tile_id"]) if row.get("tile_id") else None
    if room and tile:
        recomputed = tile_count(
            room["length"], room["width"], tile["tile_l"], tile["tile_w"], base
        )
        out["raw_count"] = recomputed["raw_count"]
        out["order_count"] = recomputed["order_count"]
        out["waste_pct"] = base
    else:
        raw = int(out.get("raw_count") or 0)
        out["order_count"] = ceil_units(raw * (1 + base / 100.0))
        out["waste_pct"] = base
    out_row["result"] = out
    out_row["waste_pct"] = base
    # Keep shift labels so UI still looks like a night run.
    return out_row


def live_surcharge_for_hour(hour: float | None) -> float:
    if hour is None:
        return 0.0
    shift = shifts.match_shift(float(hour))
    return float(shift["surcharge_pct"]) if shift else 0.0
