from datetime import datetime
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
