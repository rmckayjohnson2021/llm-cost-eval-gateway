from dataclasses import dataclass


@dataclass
class BudgetState:
    limit_usd: float
    spent_usd: float = 0.0
    reserved_usd: float = 0.0

    @property
    def available_usd(self) -> float:
        return max(0.0, self.limit_usd - self.spent_usd - self.reserved_usd)

    def reserve(self, amount_usd: float) -> bool:
        if amount_usd > self.available_usd:
            return False
        self.reserved_usd += amount_usd
        return True

    def commit(self, reserved_usd: float, actual_usd: float) -> None:
        self.reserved_usd = max(0.0, self.reserved_usd - reserved_usd)
        self.spent_usd += actual_usd

    def release(self, reserved_usd: float) -> None:
        self.reserved_usd = max(0.0, self.reserved_usd - reserved_usd)
