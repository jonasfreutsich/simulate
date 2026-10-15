from pathlib import Path
from typing import Dict

from custom_types.portfolio.portfolio import Portfolio
from myutils.utils import Utils
from performance.portfolio_performance import (
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
    def print(cls, results: Dict[Portfolio, PortfolioPerformanceResult]) -> None:
        if not results:
            raise ValueError()
        nbr_windows = -1
        for portfolio, result in results.items():
            local_nbr = len(result.details_info)
            if nbr_windows != -1 and local_nbr != nbr_windows:
                raise RuntimeError()
            nbr_windows = local_nbr
        print(f"Evaluated {nbr_windows} time frames.")
        print(cls.to_markdown(results))

    @classmethod
    def save(
        cls, filepath: str, results: Dict[Portfolio, PortfolioPerformanceResult]
    ) -> None:
        if not results:
            raise ValueError()
        path = Path(filepath)
        with open(path, "w") as file:
            file.write(cls.to_markdown(results))
