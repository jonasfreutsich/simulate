from datetime import datetime
from typing import Dict


from custom_types.rolling_time_window import TimeWindow

SYMBOL_NAME_MAP: Dict[str, str] = {"^GSPC": "S&P500", "^990100-USD-STRD": "MSCI World"}


class YTicker:
    def __init__(self, yticker: str, name: str | None = None):
        self.name = name or self.get_ticker_name(yticker)
        self.yticker = yticker
        self.range: TimeWindow | None = None

    def set_range(self, start: datetime, end: datetime):
        self.range = TimeWindow(start, end)

    @staticmethod
    def by_name(name: str) -> "YTicker":
        for ticker, value in SYMBOL_NAME_MAP.items():
            if name == value:
                return YTicker(yticker=ticker, name=name)
        raise ValueError()

    @staticmethod
    def get_ticker_name(symbol: str) -> str:
        if symbol in SYMBOL_NAME_MAP:
            return SYMBOL_NAME_MAP[symbol]
        else:
            raise ValueError()
