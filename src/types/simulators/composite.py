# ---------------------------------------------------------------------------
# Composite model
# ---------------------------------------------------------------------------


from dataclasses import dataclass
import random

from simulation_model import SimulationContext, SimulationModel


@dataclass(frozen=True, slots=True)
class CompositeModel(SimulationModel):
    """
    Combines multiple models.

    weights:
        Optional weights for each model.

    Example:

        CompositeModel(
            models=(
                LinearTrend(),
                Sinusoidal(amplitude=5),
                RandomWalk(step_size=0.5),
            )
        )
    """

    models: tuple[SimulationModel, ...]
    weights: tuple[float, ...] | None = None

    def __post_init__(self) -> None:
        if not self.models:
            raise ValueError("At least one model is required")

        if self.weights is not None:
            if len(self.weights) != len(self.models):
                raise ValueError("weights must have the same length as models")

            if any(weight < 0 for weight in self.weights):
                raise ValueError("weights must be >= 0")

            if sum(self.weights) == 0:
                raise ValueError("At least one weight must be > 0")

    def next_value(
        self,
        context: SimulationContext,
        rng: random.Random,
    ) -> float:
        values = [model.next_value(context, rng) for model in self.models]

        if self.weights is None:
            return sum(values) / len(values)

        total = sum(self.weights)

        return (
            sum(value * weight for value, weight in zip(values, self.weights)) / total
        )
