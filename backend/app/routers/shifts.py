from fastapi import APIRouter, HTTPException

from app.repositories import shifts as shifts_repo
from app.schemas.shift import ShiftCreate, ShiftUpdate

router = APIRouter(prefix="/shifts", tags=["shifts"])


@router.get("")
def list_shifts():
    return {"items": shifts_repo.list_shifts()}


@router.post("", status_code=201)
def create_shift(body: ShiftCreate):
    try:
        shift_id = shifts_repo.create_shift(
            body.name, body.start_hour, body.end_hour, body.surcharge_pct, body.enabled
        )
    except shifts_repo.ShiftValidationError as e:
        raise HTTPException(422, str(e))
    return shifts_repo.get_shift(shift_id)


@router.put("/{shift_id}")
def update_shift(shift_id: int, body: ShiftUpdate):
    try:
        shifts_repo.update_shift(
            shift_id,
            body.name,
            body.start_hour,
            body.end_hour,
            body.surcharge_pct,
            body.enabled,
        )
    except shifts_repo.ShiftValidationError as e:
        raise HTTPException(422, str(e))
    row = shifts_repo.get_shift(shift_id)
    if not row:
        raise HTTPException(404, "shift not found")
    return row


@router.delete("/{shift_id}", status_code=204)
def delete_shift(shift_id: int):
    shifts_repo.delete_shift(shift_id)
