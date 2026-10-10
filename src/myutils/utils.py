from typing import Dict

from tabulate import tabulate

from custom_types.custom_types import Currency, Percentage
from custom_types.portfolio.portfolio import Portfolio
from custom_types.rolling_time_window import TimeWindow
from custom_types.dataseries.snapshot import TimeSeriesSnapshot


class Utils:

    @staticmethod
    def dict_to_md_table(
        data: (
            dict[Portfolio, dict[str, Currency | Percentage]]
            | dict[TimeWindow, dict[str, str]]
        ),
    ) -> str:
        columns = list(data.keys())
        rows = [
            [
                key,
                *(str(data[column].get(key)) for column in columns),  # type: ignore
            ]
            for key in data[columns[0]]  # type: ignore
        ]

        return tabulate(
            rows,
            headers=["Metric/Event", *list(map(lambda col: str(col), columns))],
            tablefmt="github",
        )

    @staticmethod
    def filter_empty_snapshots(snapshots: Dict[TimeWindow, TimeSeriesSnapshot]) -> None:
        del_keys = set(filter(lambda key: not bool(snapshots[key]), snapshots.keys()))
        for key in del_keys:
            del snapshots[key]
