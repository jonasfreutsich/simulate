from pathlib import Path

from pandas import DataFrame
import yfinance as yf


class YFinanceAPI:

    @staticmethod
    def download(ticker: str, data_dir: Path) -> DataFrame:
        try:
            data = yf.Ticker(ticker).history(period="max")

            if data.empty:
                raise ValueError(
                    f"No data found for ticker '{ticker}'. "
                    "The ticker may not exist or Yahoo Finance may have no historical data."
                )

            path: Path = data_dir / f"{ticker}.parquet"
            print(path.absolute())
            data.to_parquet(path)

            return data

        except ValueError:
            raise

        except Exception as e:
            raise RuntimeError(
                f"Failed to download data for ticker '{ticker}': {e}"
            ) from e
