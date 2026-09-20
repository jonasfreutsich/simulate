# ---------------------------------------------------------------------------
# Mean reverting model
# ---------------------------------------------------------------------------


from dataclasses import dataclass
import random

from simulation_model import SimulationContext, SimulationModel


@dataclass(frozen=True, slots=True)
class MeanReverting(SimulationModel):
    """
    Mean-reverting process.

    The target moves linearly from start_value to end_value, while
    the generated value tends to return toward that target.

    strength:
        How strongly the value moves toward the target.

    volatility:
        Random movement added at every step.
    """

    strength: float = 0.15
    volatility: float = 1.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.strength <= 1.0:
            raise ValueError("strength must be between 0 and 1")

        if self.volatility < 0:
            raise ValueError("volatility must be >= 0")

    def next_value(
        self,
        context: SimulationContext,
        rng: random.Random,
    ) -> float:
        target = (
            context.start_value
            + (context.end_value - context.start_value) * context.progress
        )

        reversion = (target - context.previous_value) * self.strength

        noise = rng.gauss(0.0, self.volatility)

        return context.previous_value + reversion + noise
