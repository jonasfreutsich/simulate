from __future__ import annotations
from datetime import datetime, timedelta
import random

from types.simulators.linear import LinearTrend

from types.data_series import DataPoint, DataSeries

# ---------------------------------------------------------------------------
# Simulator
# ---------------------------------------------------------------------------


class DataSeriesSimulator:
    """
    Generates DataSeries using a pluggable SimulationModel.

    The simulator is responsible for:

    - timestamps
    - endpoints
    - random number generation
    - volatility
    - deviation limits
    - minimum/maximum constraints

    The model is responsible for determining the shape of the data.
    """

    def __init__(
        self,
        *,
        model: SimulationModel | None = None,
        seed: int | None = None,
        rng: random.Random | None = None,
    ) -> None:
        if rng is not None and seed is not None:
            raise ValueError("Specify either seed or rng, not both")

        self.model = model or LinearTrend()

        self._rng = rng if rng is not None else random.Random(seed)

    def simulate(
        self,
        *,
        start_value: float,
        end_value: float,
        start_time: datetime,
        end_time: datetime,
        interval: timedelta,
        constraints: SimulationConstraints | None = None,
    ) -> DataSeries:
        """
        Generate a DataSeries.

        The first and final points are always exactly equal to
        start_value and end_value.
        """

        constraints = constraints or SimulationConstraints()

        self._validate(
            start_value=start_value,
            end_value=end_value,
            start_time=start_time,
            end_time=end_time,
            interval=interval,
            constraints=constraints,
        )

        timestamps = self._timestamps(
            start_time,
            end_time,
            interval,
        )

        points: list[DataPoint] = []

        previous_value = start_value

        for index, timestamp in enumerate(timestamps):
            # Exact starting point.
            if index == 0:
                value = start_value

            # Exact ending point.
            elif index == len(timestamps) - 1:
                value = end_value

            else:
                context = SimulationContext(
                    index=index,
                    count=len(timestamps),
                    timestamp=timestamp,
                    start_time=start_time,
                    end_time=end_time,
                    start_value=start_value,
                    end_value=end_value,
                    previous_value=previous_value,
                )

                target = self.model.next_value(
                    context,
                    self._rng,
                )

                value = self._apply_constraints(
                    value=target,
                    target=target,
                    constraints=constraints,
                )

            points.append(
                DataPoint(
                    timestamp=timestamp,
                    value=value,
                )
            )

            previous_value = value

        return DataSeries(points)

    def _apply_constraints(
        self,
        *,
        value: float,
        target: float,
        constraints: SimulationConstraints,
    ) -> float:
        # Apply generic volatility.
        if constraints.volatility:
            value += self._rng.gauss(
                0.0,
                constraints.volatility,
            )

        # Mean-revert toward model target.
        if constraints.mean_reversion:
            value += (target - value) * constraints.mean_reversion

        # Limit deviation from target.
        if constraints.deviation is not None:
            lower = target - constraints.deviation
            upper = target + constraints.deviation

            value = max(lower, min(upper, value))

        # Apply absolute bounds.
        if constraints.minimum is not None:
            if value < constraints.minimum:
                if constraints.clamp:
                    value = constraints.minimum
                else:
                    raise ValueError(
                        f"Generated value {value} is below "
                        f"minimum {constraints.minimum}"
                    )

        if constraints.maximum is not None:
            if value > constraints.maximum:
                if constraints.clamp:
                    value = constraints.maximum
                else:
                    raise ValueError(
                        f"Generated value {value} is above "
                        f"maximum {constraints.maximum}"
                    )

        return value

    @staticmethod
    def _timestamps(
        start_time: datetime,
        end_time: datetime,
        interval: timedelta,
    ) -> list[datetime]:
        timestamps: list[datetime] = []

        current = start_time

        while current < end_time:
            timestamps.append(current)
            current += interval

        # Always include exact end time.
        if not timestamps or timestamps[-1] != end_time:
            timestamps.append(end_time)

        return timestamps

    @staticmethod
    def _validate(
        *,
        start_value: float,
        end_value: float,
        start_time: datetime,
        end_time: datetime,
        interval: timedelta,
        constraints: SimulationConstraints,
    ) -> None:
        if start_time >= end_time:
            raise ValueError("start_time must be before end_time")

        if interval <= timedelta(0):
            raise ValueError("interval must be greater than zero")

        if constraints.minimum is not None and (
            start_value < constraints.minimum or end_value < constraints.minimum
        ):
            raise ValueError("start_value and end_value must satisfy minimum")

        if constraints.maximum is not None and (
            start_value > constraints.maximum or end_value > constraints.maximum
        ):
            raise ValueError("start_value and end_value must satisfy maximum")
