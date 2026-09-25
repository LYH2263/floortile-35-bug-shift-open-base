from app.db import connect


class ShiftValidationError(ValueError):
    pass


def _validate(start_hour, end_hour, surcharge_pct) -> None:
    try:
        start = float(start_hour)
        end = float(end_hour)
        surcharge = float(surcharge_pct)
    except (TypeError, ValueError):
        raise ShiftValidationError("钟点与加耗必须是数字")
    if surcharge < 0:
        raise ShiftValidationError("加耗百分点不能为负")
    if not (0.0 <= start <= 24.0 and 0.0 <= end <= 24.0):
        raise ShiftValidationError("钟点必须在 0~24 之间")
    if start == end:
        raise ShiftValidationError("起止钟点相同，窗口非法")


def list_shifts(enabled_only: bool = False) -> list[dict]:
    conn = connect()
    try:
        sql = "SELECT * FROM shifts"
        if enabled_only:
            sql += " WHERE enabled=1"
        sql += " ORDER BY id"
        return [dict(r) for r in conn.execute(sql).fetchall()]
    finally:
        conn.close()


def get_shift(shift_id: int) -> dict | None:
    conn = connect()
    try:
        row = conn.execute("SELECT * FROM shifts WHERE id=?", (shift_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def create_shift(name: str, start_hour, end_hour, surcharge_pct, enabled: bool = True) -> int:
    name = (name or "").strip()
    if not name:
        raise ShiftValidationError("班次名称不能为空")
    _validate(start_hour, end_hour, surcharge_pct)
    conn = connect()
    try:
        cur = conn.execute(
            "INSERT INTO shifts(name,start_hour,end_hour,surcharge_pct,enabled) VALUES (?,?,?,?,?)",
            (name, float(start_hour), float(end_hour), float(surcharge_pct), 1 if enabled else 0),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def update_shift(
    shift_id: int,
    name: str | None = None,
    start_hour=None,
    end_hour=None,
    surcharge_pct=None,
    enabled: bool | None = None,
) -> None:
    current = get_shift(shift_id)
    if not current:
        raise ShiftValidationError("班次不存在")
    new_name = current["name"] if name is None else (name or "").strip()
    if not new_name:
        raise ShiftValidationError("班次名称不能为空")
    new_start = current["start_hour"] if start_hour is None else start_hour
    new_end = current["end_hour"] if end_hour is None else end_hour
    new_surcharge = current["surcharge_pct"] if surcharge_pct is None else surcharge_pct
    _validate(new_start, new_end, new_surcharge)
    new_enabled = current["enabled"] if enabled is None else (1 if enabled else 0)
    conn = connect()
    try:
        conn.execute(
            "UPDATE shifts SET name=?,start_hour=?,end_hour=?,surcharge_pct=?,enabled=? WHERE id=?",
            (new_name, float(new_start), float(new_end), float(new_surcharge), new_enabled, shift_id),
        )
        conn.commit()
    finally:
        conn.close()


def set_enabled(shift_id: int, enabled: bool) -> None:
    if not get_shift(shift_id):
        raise ShiftValidationError("班次不存在")
    conn = connect()
    try:
        conn.execute("UPDATE shifts SET enabled=? WHERE id=?", (1 if enabled else 0, shift_id))
        conn.commit()
    finally:
        conn.close()


def delete_shift(shift_id: int) -> None:
    conn = connect()
    try:
        conn.execute("DELETE FROM shifts WHERE id=?", (shift_id,))
        conn.commit()
    finally:
        conn.close()


def match_shift(construction_hour: float) -> dict | None:
    """Return the enabled shift whose window contains construction_hour, else None.

    Windows may wrap past midnight, e.g. 22:00-06:00. End hour is exclusive
    except for a 24:00 end, which is treated as the midnight boundary.
    """
    h = float(construction_hour)
    for shift in list_shifts(enabled_only=True):
        start, end = shift["start_hour"], shift["end_hour"]
        if start < end:
            hit = start <= h < end
        else:
            hit = h >= start or h < end
        if hit:
            return shift
    return None
