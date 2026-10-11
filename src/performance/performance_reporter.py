from pathlib import Path
from typing import Dict, Set

from custom_types.portfolio.portfolio import Portfolio
from myutils.utils import Utils
from performance.portfolio_performance import (
    PortfolioPerformance,
    PortfolioPerformanceResult,
)


class PerformanceReporter:
    @staticmethod
    def to_markdown(result: Dict[Portfolio, PortfolioPerformanceResult]) -> str:
        ret = []
        ret.append(
            Utils.dict_to_md_table(
                {portfolio: result[portfolio].result_dict for portfolio in result},
                header="Metric/Event",
            )
        )
        for portfolio in result:
            if not result[portfolio].details_info:
                continue
            ret.append(str(portfolio))
            ret.append(
                Utils.dict_to_md_table(
                    result[portfolio].details_info,
                )
            )

        return "\n".join(ret)

    @classmethod
    def print(
        cls,
        performance: PortfolioPerformance,
        portfolios: Set[Portfolio],
        details: bool = False,
    ) -> None:
        result = performance.evaluate(portfolios, details)
        if not result:
            raise ValueError()
        print(performance.get_paramters_name())
        nbr_windows = len(result[portfolios.copy().pop()].details_info)
        print(
            f"Evaluated {nbr_windows} windows in the {performance.rolling_window.get_range()}"
        )
        print(cls.to_markdown(result))

    @classmethod
    def save(
        cls,
        filepath: str,
        performance: PortfolioPerformance,
        portfolios: Set[Portfolio],
        details: bool = False,
    ) -> None:
        result = performance.evaluate(portfolios, details)
        if not result:
            raise ValueError()
        path = Path(filepath)
        with open(path, "w") as file:
            file.write(cls.to_markdown(result))
