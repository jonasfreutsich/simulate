from datetime import datetime
from enum import Enum

from matplotlib.dates import relativedelta


class Period(Enum):
    DAILY = relativedelta(days=1)
    MONTHLY = relativedelta(months=1)
    YEARLY = relativedelta(years=1)

    def __add__(self, other: datetime) -> datetime:
        return self.value + other

    def __radd__(self, other: datetime) -> datetime:
        return self.value + other

    def is_same_period(self, first: datetime, second: datetime) -> bool:
        if self == Period.DAILY:
            return first == second
        elif self == Period.MONTHLY:
            return first.month == second.month and first.year == second.year
        elif self == Period.YEARLY:
            return first.year == second.year
        else:
            raise NotImplementedError


class CalendarDelta(Enum):
    ONE_DAY = relativedelta(days=1)
    ONE_MONTH = relativedelta(months=1)
    ONE_YEAR = relativedelta(years=1)
    TWO_YEARS = relativedelta(years=2)
    THREE_YEARS = relativedelta(years=3)
    FOUR_YEARS = relativedelta(years=4)
    FIVE_YEARS = relativedelta(years=5)
    TEN_YEARS = relativedelta(years=10)

    def __add__(self, other: datetime) -> datetime:
        return self.value + other

    def __radd__(self, other: datetime) -> datetime:
        return self.value + other
