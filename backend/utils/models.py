"""The one list of models, with their prices.

This lived in three places -- the API allowlist, the proxy allowlist and
the pricing table -- so adding a model to two of them silently gave it
an unlimited budget. One registry now, and a model with no price is not
a model we will run.
"""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ModelSpec:
    key: str
    label: str
    input_per_mtok: Decimal    # USD per million input tokens
    output_per_mtok: Decimal   # USD per million output tokens

    # Cached input is not free. A cache write costs more than fresh input
    # and a read costs a fraction of it, both priced off the input rate.
    CACHE_WRITE_MULTIPLIER = Decimal("1.25")
    CACHE_READ_MULTIPLIER = Decimal("0.10")

    def cost(
        self,
        input_tokens: int,
        output_tokens: int,
        cache_write_tokens: int = 0,
        cache_read_tokens: int = 0,
    ) -> Decimal:
        """What a call costs, cached input included.

        Claude Code caches its system prompt and tool definitions, so on a
        warm request almost every input token arrives as a cache read and
        `input_tokens` alone reads as a handful. Billing on that number
        alone undercounts the real spend by orders of magnitude.
        """
        billable_input = (
            Decimal(input_tokens)
            + Decimal(cache_write_tokens) * self.CACHE_WRITE_MULTIPLIER
            + Decimal(cache_read_tokens) * self.CACHE_READ_MULTIPLIER
        )
        return (
            billable_input * self.input_per_mtok
            + Decimal(output_tokens) * self.output_per_mtok
        ) / Decimal(1_000_000)


class UnknownModel(Exception):
    """Not on the list, so it has no price and no budget. Refused."""


class ModelRegistry:
    def __init__(self, specs: list[ModelSpec]):
        self._specs = {s.key: s for s in specs}

    def get(self, key: str) -> ModelSpec:
        try:
            return self._specs[key]
        except KeyError:
            raise UnknownModel(f"unknown model: {key}") from None

    def keys(self) -> list[str]:
        return sorted(self._specs)

    def __contains__(self, key: str) -> bool:
        return key in self._specs


MODELS = ModelRegistry([
    ModelSpec("claude-opus-5",   "Opus 5",   Decimal("5.00"), Decimal("25.00")),
    ModelSpec("claude-sonnet-5", "Sonnet 5", Decimal("2.00"), Decimal("10.00")),
    ModelSpec("claude-haiku-4-5", "Haiku 4.5", Decimal("1.00"), Decimal("5.00")),
])
