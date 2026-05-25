import logging
import os

logger = logging.getLogger("cost_tracker")

PRICING = {
    "claude-opus-4-7":           (5.00, 25.00),
    "claude-sonnet-4-6":         (3.00, 15.00),
    "claude-haiku-4-5-20251001": (1.00,  5.00),
}

class CostTracker:
    def __init__(self):
        self.total_usd = 0.0
        self.alert_threshold = float(os.getenv("COST_ALERT_USD", "5.00"))
        self.breakdown: list[dict] = []

    def record(self, agent: str, model: str, cost_usd: float,
               input_tokens: int, output_tokens: int) -> None:
        self.total_usd += cost_usd
        self.breakdown.append({
            "agent": agent, "model": model,
            "cost_usd": round(cost_usd, 6),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        })
        if self.total_usd > self.alert_threshold:
            logger.warning("Cost alert: $%.4f exceeds threshold $%.2f",
                           self.total_usd, self.alert_threshold)

    def compute(self, model: str, input_tokens: int, output_tokens: int) -> float:
        in_rate, out_rate = PRICING.get(model, (3.0, 15.0))
        return (input_tokens * in_rate + output_tokens * out_rate) / 1_000_000

    def summary(self) -> dict:
        return {
            "total_usd": round(self.total_usd, 4),
            "alert_threshold_usd": self.alert_threshold,
            "breakdown": self.breakdown,
        }
