from dataclasses import dataclass



@dataclass(frozen=True)
class Percentage:
    value: float

    def __add__(self, other: "Percentage") -> "Percentage":
        return Percentage(self.value + other.value)

    def __truediv__(self, other: float | int) -> "Percentage":
        if isinstance(other, float) or isinstance(other, int):
            if other != 0.0:
                return Percentage(self.value / other)
            else:
                raise ValueError("Division by 0 not allowed.")
        else:
            raise NotImplementedError

    def __gt__(self, other: "Percentage") -> bool:
        if isinstance(other, Percentage):
            return self.value > other.value
        else:
            raise NotImplementedError

    def __str__(self) -> str:
        return str(round(self.value * 100, 2)) + "%"


@dataclass(frozen=True)
class Currency:
    value: float
    currency: str

    def __add__(self, other: "Currency | float") -> "Currency":
        if isinstance(other, float):
            if other != 0.0:
                raise ValueError("May not add a non-zero float to a currency.")
            else:
                return self
        elif isinstance(other, Currency):
            if other.currency != self.currency:
                raise ValueError(
                    f"You are trying to add different currencies: {self.currency} + {other.currency}"
                )
            return Currency(self.value + other.value, self.currency)
        else:
            raise NotImplementedError

    def __mul__(self, other: float) -> "Currency":
        if isinstance(other, float):
            return Currency(self.value * other, self.currency)
        else:
            raise NotImplementedError

    def __truediv__(self, other: float | int) -> "Currency":
        if isinstance(other, float) or isinstance(other, int):
            if other != 0.0:
                return Currency(self.value / other, self.currency)
            else:
                raise ValueError("Division by 0 not allowed.")
        else:
            raise NotImplementedError

    def __str__(self) -> str:
        return self.currency + str(round(self.value, 2))
