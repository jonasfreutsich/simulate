from datetime import datetime
from typing import Dict


from custom_types.allocation.allocation_strategies import AllocationStrategy
from custom_types.time_types import Period


class AllocationSchedule:
    def __init__(self, strategy: AllocationStrategy):
        self.strategy: AllocationStrategy = strategy
        self.period: Period = strategy.period
        self.last_execution_at: datetime | None = None
        self.first_execution_at: datetime | None = None
        self.total_contributions: float = 0.0
        self.total_withdrawls: float = 0.0

    def apply(
        self,
        allocation: Dict[str, float],
        timestamp: datetime,
    ) -> None:
        if self.strategy is None:
            # No scheduled strategy configured
            return
        if self.last_execution_at is not None and self.period.is_same_period(
            self.last_execution_at, timestamp
        ):
            # timestamp is still in the executed period / or allocation was never executed
            return

        if self.first_execution_at is None:
            self.first_execution_at = timestamp

        self.last_execution_at = timestamp
        amount = self.strategy.reallocate(
            allocation, self.first_execution_at, timestamp
        )
        if amount > 0:
            self.total_contributions += amount
        else:
            self.total_withdrawls -= amount
