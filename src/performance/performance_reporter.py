from typing import Dict

from custom_types.portfolio import Portfolio
from myutils.utils import Utils
from performance.portfolio_performance import PortfolioPerformanceResult


class PerformanceReporter:
    @staticmethod
    def to_markdown(result: Dict[Portfolio, PortfolioPerformanceResult]) -> str:
        return Utils.dict_to_md_table(
            {portfolio: result[portfolio].result_dict for portfolio in result}
        )

    @classmethod
    def print(cls, result: Dict[Portfolio, PortfolioPerformanceResult]) -> None:
        # TODO print class name
        # TODO print number of windows
        print(cls.to_markdown(result))
