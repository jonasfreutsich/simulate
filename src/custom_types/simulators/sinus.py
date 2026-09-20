# ---------------------------------------------------------------------------
# Sinusoidal model
# ---------------------------------------------------------------------------


from dataclasses import dataclass
import math
import random

from simulation_model import SimulationContext, SimulationModel


@dataclass(frozen=True, slots=True)
class Sinusoidal(SimulationModel):
    """
    Sinusoidal variation around a linear start -> end trend.

    amplitude:
        Size of the oscillation.

    cycles:
        Number of complete oscillations over the simulation.

    phase:
        Initial phase in radians.
    """

    amplitude: float = 1.0
    cycles: float = 1.0
    phase: float = 0.0

    def next_value(
        self,
        context: SimulationContext,
        rng: random.Random,
    ) -> float:
        base = (
            context.start_value
            + (context.end_value - context.start_value) * context.progress
        )

        oscillation = self.amplitude * math.sin(
            2.0 * math.pi * self.cycles * context.progress + self.phase
        )

        return base + oscillation
