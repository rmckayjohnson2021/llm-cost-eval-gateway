from dataclasses import dataclass


@dataclass
class BudgetState:
    limit_usd: float
    reserved_usd: float = 0.0

    def reserve(self, amount_usd: float) -> bool:
        if self.reserved_usd + amount_usd > self.limit_usd:
            return False
        self.reserved_usd += amount_usd
        return True
