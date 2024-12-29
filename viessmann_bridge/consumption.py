from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel


class Consumption(BaseModel):
    timestamp: datetime

    day: list[int]
    week: list[int]
    month: list[int]
    year: list[int]

    day_readat: datetime
    week_readat: datetime
    month_readat: datetime
    year_readat: datetime


class ConsumptionContext:
    gas_consumption: Optional[Consumption] = None
    total_consumption: int = 0
    previous_total_consumption: int = (
        0  # TODO: Maybe fetch it from Domoticz or something?
    )
    previous_consumption_daily: list[int] = []
    previous_consumption_date: Optional[date] = None
