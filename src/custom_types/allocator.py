from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional

from custom_types.allocation_strategies import AllocationStrategy


@dataclass
class AllocationSchedule:
    strategy: Optional[AllocationStrategy]
    period: timedelta
    last_execution_at: datetime | None = None
    total_contributions: float = 0.0

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

        self.last_execution_at = timestamp
        self.total_contributions += self.strategy.reallocate(allocation)
