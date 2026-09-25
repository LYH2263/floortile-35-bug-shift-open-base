import json
from datetime import datetime, timezone

from app.db import connect


def insert_run(
    room_id: int,
    tile_id: int,
    waste_pct: float,
    result: dict,
    note: str = "",
    construction_hour: float | None = None,
    shift_id: int | None = None,
    shift_name: str | None = None,
    base_waste_pct: float | None = None,
    surcharge_pct: float = 0.0,
) -> int:
    conn = connect()
    try:
        cur = conn.execute(
            """
            INSERT INTO calc_runs(
                room_id, tile_id, waste_pct, result_json, note, created_at,
                construction_hour, shift_id, shift_name, base_waste_pct, surcharge_pct
            )
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                room_id,
                tile_id,
                waste_pct,
                json.dumps(result, ensure_ascii=False),
                note,
                datetime.now(timezone.utc).isoformat(),
                construction_hour,
                shift_id,
                shift_name,
                base_waste_pct,
                surcharge_pct,
            ),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def list_runs(limit: int = 50):
    conn = connect()
    try:
        rows = conn.execute(
            """
            SELECT r.*, rm.name AS room_name, t.name AS tile_name
            FROM calc_runs r
            LEFT JOIN rooms rm ON rm.id = r.room_id
            LEFT JOIN tiles t ON t.id = r.tile_id
            ORDER BY r.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        out = []
        for row in rows:
            d = dict(row)
            d["result"] = json.loads(d.pop("result_json"))
            out.append(d)
        return out
    finally:
        conn.close()


def get_run(run_id: int):
    conn = connect()
    try:
        row = conn.execute(
            """
            SELECT r.*, rm.name AS room_name, t.name AS tile_name
            FROM calc_runs r
            LEFT JOIN rooms rm ON rm.id = r.room_id
            LEFT JOIN tiles t ON t.id = r.tile_id
            WHERE r.id=?
            """,
            (run_id,),
        ).fetchone()
        if not row:
            return None
        from app.services.shift_open import open_with_base_waste

        d = dict(row)
        d["result"] = json.loads(d.pop("result_json"))
        return open_with_base_waste(d)
    finally:
        conn.close()
