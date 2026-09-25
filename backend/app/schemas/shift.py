from pydantic import BaseModel


class ShiftBase(BaseModel):
    name: str
    start_hour: float
    end_hour: float
    surcharge_pct: float
    enabled: bool = True


class ShiftCreate(ShiftBase):
    pass


class ShiftUpdate(BaseModel):
    name: str | None = None
    start_hour: float | None = None
    end_hour: float | None = None
    surcharge_pct: float | None = None
    enabled: bool | None = None
