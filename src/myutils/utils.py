from typing import Dict

from tabulate import tabulate

from custom_types.portfolio import Portfolio
from custom_types.rolling_time_window import TimeWindow
from custom_types.time_series_snapshot import TimeSeriesSnapshot


class Utils:

    @staticmethod
    def float_to_percent(value: float, ndigits: int = 2) -> float:
        return round(value * 100, ndigits)

    @staticmethod
    def float_to_percent_str(value: float | None, ndigits: int = 2) -> str:
        if value is None:
            return "None"
        return str(Utils.float_to_percent(value, ndigits)) + " %"

    @staticmethod
    def dict_to_md_table(data: dict[Portfolio, dict[str, float]]) -> str:
        columns = list(data.keys())
        rows = [
            [
                key,
                *(
                    Utils.float_to_percent_str(data[column].get(key))
                    for column in columns
                ),
            ]
            for key in data[columns[0]]
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
