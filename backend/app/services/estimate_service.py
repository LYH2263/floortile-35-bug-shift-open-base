from fastapi import HTTPException

from app.engines.tile_math import tile_count
from app.repositories import history, rooms, settings_repo, shifts, tiles


def run_estimate(
    room_id: int,
    tile_id: int,
    waste_pct: float | None,
    save: bool,
    note: str,
    construction_hour: float | None = None,
):
    room = rooms.get_room(room_id)
    if not room:
        raise HTTPException(404, "room not found")
    tile = tiles.get_tile(tile_id)
    if not tile:
        raise HTTPException(404, "tile not found")
    if room.get("data_quality") == "dirty":
        raise HTTPException(422, "room marked dirty; fix dimensions before estimate")

    base_waste = float(waste_pct) if waste_pct is not None else settings_repo.get_waste_pct()

    hour = None
    shift = None
    surcharge = 0.0
    if construction_hour is not None:
        hour = float(construction_hour)
        if not (0.0 <= hour <= 24.0):
            raise HTTPException(422, "施工钟点必须在 0~24 之间")
        shift = shifts.match_shift(hour)
        if shift:
            surcharge = float(shift["surcharge_pct"])

    total_waste = base_waste + surcharge  # live path; open-path may drop surcharge
    calc = tile_count(room["length"], room["width"], tile["tile_l"], tile["tile_w"], total_waste)

    run_id = None
    if save:
        payload = {**calc, "room_id": room_id, "tile_id": tile_id}
        run_id = history.insert_run(
            room_id,
            tile_id,
            total_waste,
            payload,
            note,
            construction_hour=hour,
            shift_id=shift["id"] if shift else None,
            shift_name=shift["name"] if shift else None,
            base_waste_pct=base_waste,
            surcharge_pct=surcharge,
        )

    return {
        "room_id": room_id,
        "tile_id": tile_id,
        "room": room,
        "tile": tile,
        "run_id": run_id,
        "construction_hour": hour,
        "shift_id": shift["id"] if shift else None,
        "shift_name": shift["name"] if shift else None,
        "base_waste_pct": base_waste,
        "surcharge_pct": surcharge,
        **calc,
    }
