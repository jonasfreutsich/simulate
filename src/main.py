from datetime import datetime
from typing import Dict

from matplotlib.dates import relativedelta


from backtracking.flow_backtracker import FlowBacktracker
from custom_types.allocation.allocation_strategies import (
    FireStrategy,
)
from custom_types.portfolio.portfolio_comparison import PortfolioComparison
from custom_types.rolling_time_window import RollingTimeWindow, TimeWindow
from custom_types.portfolio.portfolio import Portfolio
from custom_types.dataseries.snapshot import TimeSeriesSnapshot
from custom_types.time_types import CalendarDelta, Period
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("simulate")
logger.setLevel(logging.INFO)


def test_comparison():
    strategy = FireStrategy(Period.MONTHLY, 1, 4, relativedelta(years=4))
    portfolios = {
        Portfolio({"IWDA.AS": 1}),
        Portfolio({"XWD.TO": 1}),
    }
    comp = PortfolioComparison(portfolios)
    start = datetime.fromisoformat("2009-01-01")
    end = datetime.fromisoformat("2025-01-01")
    comp.compare(
        strategy,
        time_frame=TimeWindow(start, end),
        window_size=CalendarDelta.FIVE_YEARS,
        step_size=CalendarDelta.ONE_YEAR,
    )


def rolling_window_backtrack(
    start, end, window_size, step_size, portfolio
) -> Dict[TimeWindow, TimeSeriesSnapshot]:
    now = time.time()
    backtracker = FlowBacktracker(TimeWindow(start, end), portfolio)
    rolling_window = RollingTimeWindow(start, end, window_size, step_size)
    result = backtracker.rolling_backtrack(rolling_window)

    print(f"Rolling window backtrack time: {time.time() - now}")

    return result


if __name__ == "__main__":
    test_comparison()
