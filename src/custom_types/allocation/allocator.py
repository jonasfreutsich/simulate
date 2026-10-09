from datetime import datetime, timedelta
from typing import Dict, Optional

from custom_types.allocation.allocation_strategies import AllocationStrategy


class AllocationSchedule:
    def __init__(self, strategy: AllocationStrategy | None, period: timedelta):
        self.strategy: Optional[AllocationStrategy] = strategy
        self.period: timedelta = period
        self.last_execution_at: datetime | None = None
        self.first_execution_at: datetime | None = None
        self.total_contributions: float = 0.0
        self.total_withdrawls: float = 0.0

    def apply(
        self,
        allocation: Dict[str, float],
        timestamp: datetime,
    ) -> None:
        if self.strategy is None or (
            self.last_execution_at is not None
            and timestamp - self.last_execution_at < self.period
        ):
            return
        if self.first_execution_at is None:
            self.first_execution_at = timestamp

        self.last_execution_at = timestamp
        amount = self.strategy.reallocate(
            allocation, timestamp - self.first_execution_at
        )
        if amount > 0:
            self.total_contributions += amount
        else:
            self.total_withdrawls -= amount
