from datetime import date
from typing import Self


class DateRange(tuple[date, date]):
    def __new__(cls, start_date: date, end_date: date) -> Self:
        if start_date > end_date:
            raise ValueError("start_date must be less than end_date")
        return super().__new__(cls, (start_date, end_date))

    @property
    def start_date(self) -> date:
        return self[0]

    @property
    def end_date(self) -> date:
        return self[1]
