# ---------------------------------------------------------------------------
# Random walk
# ---------------------------------------------------------------------------


from dataclasses import dataclass
import random

from simulation_model import SimulationContext, SimulationModel


@dataclass(frozen=True, slots=True)
class RandomWalk(SimulationModel):
    """
    Random walk that is gently directed toward the end value.

    drift:
        Strength of movement toward the end value.

    step_size:
        Standard deviation of each random step.
    """

    step_size: float = 1.0
    drift: float = 0.05

    def __post_init__(self) -> None:
        if self.step_size < 0:
            raise ValueError("step_size must be >= 0")

        if self.drift < 0:
            raise ValueError("drift must be >= 0")

    def next_value(
        self,
        context: SimulationContext,
        rng: random.Random,
    ) -> float:
        distance = context.end_value - context.previous_value

        directed_move = distance * self.drift
        random_move = rng.gauss(0.0, self.step_size)

        return context.previous_value + directed_move + random_move
