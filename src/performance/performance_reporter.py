from typing import Dict, Set

from custom_types.portfolio import Portfolio
from myutils.utils import Utils
import performance
from performance.portfolio_performance import (
    PortfolioPerformance,
    PortfolioPerformanceResult,
)


class PerformanceReporter:
    @staticmethod
    def to_markdown(result: Dict[Portfolio, PortfolioPerformanceResult]) -> str:
        return Utils.dict_to_md_table(
            {portfolio: result[portfolio].result_dict for portfolio in result}
        )

    @classmethod
    def print(
        cls, performance: PortfolioPerformance, portfolios: Set[Portfolio]
    ) -> None:
        print(performance.get_paramters_name())
        result = performance.evaluate(portfolios)
        print(cls.to_markdown(result))
