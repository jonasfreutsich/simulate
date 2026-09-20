# ---------------------------------------------------------------------------
# Linear trend
# ---------------------------------------------------------------------------


from dataclasses import dataclass
import random

from simulation_model import SimulationContext, SimulationModel


@dataclass(frozen=True, slots=True)
class LinearTrend(SimulationModel):
    """
    Straight-line interpolation from start_value to end_value.
    """

    def next_value(
        self,
        context: SimulationContext,
        rng: random.Random,
    ) -> float:
        return (
            context.start_value
            + (context.end_value - context.start_value) * context.progress
        )
