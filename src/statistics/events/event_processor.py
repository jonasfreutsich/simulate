from typing import Dict, List, Tuple, overload


from custom_types.rolling_time_window import TimeWindow
from custom_types.time_series_snapshot import TimeSeriesSnapshot
from statistics.events.event import Event


class EventProcessor:

    def __init__(self, events: Dict[str, Event]):
        self.events = events

    def evaluate_event_rates(
        self, snapshots: Dict[TimeWindow, TimeSeriesSnapshot]
    ) -> Dict[str, Tuple[float, List[TimeWindow]]]:
        processed: Dict[TimeWindow, Dict[str, bool]] = self._process(snapshots)
        return self._event_rates(processed)

    @overload
    def _process(self, snapshot: TimeSeriesSnapshot) -> Dict[str, bool]: ...

    @overload
    def _process(
        self, snapshot: Dict[TimeWindow, TimeSeriesSnapshot]
    ) -> Dict[TimeWindow, Dict[str, bool]]: ...

    def _process(
        self, snapshot: TimeSeriesSnapshot | Dict[TimeWindow, TimeSeriesSnapshot]
    ) -> Dict[str, bool] | Dict[TimeWindow, Dict[str, bool]]:
        if isinstance(snapshot, TimeSeriesSnapshot):
            return {
                event_name: event.filter(snapshot)
                for event_name, event in self.events.items()
            }
        elif isinstance(snapshot, dict) and all(
            isinstance(k, TimeWindow) and isinstance(v, TimeSeriesSnapshot)
            for k, v in snapshot.items()
        ):
            return {
                window: self._process(window_snapshot)
                for window, window_snapshot in snapshot.items()
                if window_snapshot  # filter empty snapshots
            }

        raise TypeError(
            "snapshot must be either a TimeSeriesSnapshot or a dict of TimeWindow to TimeSeriesSnapshot"
        )

    def _event_rates(
        self, snapshots: Dict[TimeWindow, Dict[str, bool]]
    ) -> Dict[str, Tuple[float, List[TimeWindow]]]:
        if not snapshots:
            raise ValueError("Empty snapshots data.")
        total = len(snapshots)
        result = {}
        for event_name in self.events:
            filtered_windows = list(
                filter(lambda window: snapshots[window][event_name], snapshots.keys())
            )
            result[event_name] = (len(filtered_windows) / total, filtered_windows)
        return result
