import pytest

from app import seed
from app.repositories import history, shifts
from app.services import estimate_service


@pytest.fixture()
def fresh_db(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"
    monkeypatch.setattr("app.db.DB_PATH", db_file)
    seed.init_db()
    return db_file


def test_seeded_night_shift_window(fresh_db):
    # 22:00-06:00 wraps past midnight; end hour is exclusive
    assert shifts.match_shift(23.0)["name"] == "夜班"
    assert shifts.match_shift(2.5)["name"] == "夜班"
    assert shifts.match_shift(22.0)["name"] == "夜班"
    assert shifts.match_shift(6.0) is None
    assert shifts.match_shift(12.0) is None


def test_day_window_boundaries(fresh_db):
    sid = shifts.create_shift("白班", 8.0, 18.0, 0.0)
    assert shifts.match_shift(8.0)["id"] == sid
    assert shifts.match_shift(17.99)["id"] == sid
    assert shifts.match_shift(18.0) is None


def test_estimate_applies_surcharge_at_night(fresh_db):
    r = estimate_service.run_estimate(1, 1, None, False, "", construction_hour=23.0)
    assert r["base_waste_pct"] == 8.0
    assert r["surcharge_pct"] == 3.0
    assert r["waste_pct"] == 11.0
    assert r["shift_name"] == "夜班"
    assert r["construction_hour"] == 23.0
    # raw 75, with 11% -> 84
    assert r["raw_count"] == 75
    assert r["order_count"] == 84


def test_estimate_daytime_uses_base_only(fresh_db):
    r = estimate_service.run_estimate(1, 1, None, False, "", construction_hour=12.0)
    assert r["waste_pct"] == 8.0
    assert r["surcharge_pct"] == 0.0
    assert r["shift_id"] is None
    assert r["order_count"] == 81


def test_estimate_without_hour_uses_base_only(fresh_db):
    r = estimate_service.run_estimate(1, 1, None, False, "")
    assert r["waste_pct"] == 8.0
    assert r["construction_hour"] is None


def test_invalid_construction_hour_rejected(fresh_db):
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        estimate_service.run_estimate(1, 1, None, False, "", construction_hour=25.0)
    assert exc.value.status_code == 422


def test_disabled_shift_adds_no_surcharge(fresh_db):
    night = shifts.list_shifts()[0]
    shifts.set_enabled(night["id"], False)
    assert shifts.match_shift(23.0) is None
    r = estimate_service.run_estimate(1, 1, None, False, "", construction_hour=23.0)
    assert r["waste_pct"] == 8.0
    assert r["surcharge_pct"] == 0.0


def test_saved_run_records_total_waste_and_hour(fresh_db):
    r = estimate_service.run_estimate(1, 1, None, True, "夜班单", construction_hour=23.0)
    saved = history.get_run(r["run_id"])
    assert saved["waste_pct"] == 11.0
    assert saved["base_waste_pct"] == 8.0
    assert saved["surcharge_pct"] == 3.0
    assert saved["construction_hour"] == 23.0
    assert saved["shift_name"] == "夜班"
    assert saved["result"]["order_count"] == 84


def test_changing_shift_does_not_recompute_old_run(fresh_db):
    r = estimate_service.run_estimate(1, 1, None, True, "", construction_hour=23.0)
    run_id = r["run_id"]
    before = history.get_run(run_id)

    night = shifts.list_shifts()[0]
    shifts.update_shift(night["id"], surcharge_pct=10.0)
    shifts.set_enabled(night["id"], False)

    after = history.get_run(run_id)
    assert after["waste_pct"] == 11.0 == before["waste_pct"]
    assert after["result"]["order_count"] == 84
    assert after["construction_hour"] == 23.0


def test_negative_surcharge_fails_save(fresh_db):
    with pytest.raises(shifts.ShiftValidationError):
        shifts.create_shift("错误班", 22.0, 6.0, -1.0)
    assert shifts.list_shifts() == [s for s in shifts.list_shifts() if s["name"] != "错误班"]


def test_illegal_windows_rejected(fresh_db):
    with pytest.raises(shifts.ShiftValidationError):
        shifts.create_shift("零窗", 9.0, 9.0, 2.0)
    with pytest.raises(shifts.ShiftValidationError):
        shifts.create_shift("越界", 24.5, 3.0, 2.0)
    with pytest.raises(shifts.ShiftValidationError):
        shifts.create_shift("越界2", -1.0, 3.0, 2.0)


def test_update_to_negative_surcharge_fails_and_keeps_old_value(fresh_db):
    sid = shifts.create_shift("临时班", 20.0, 22.0, 1.5)
    with pytest.raises(shifts.ShiftValidationError):
        shifts.update_shift(sid, surcharge_pct=-2.0)
    assert shifts.get_shift(sid)["surcharge_pct"] == 1.5
