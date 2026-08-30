"""Per-job spend: reserve first, settle after.

Checking the budget and then spending is a race. With the Agent tool the
skill fans out to a dozen subagents, so a dozen requests can all pass the
same check before any of them records a cost.

So the budget is taken in two steps. reserve() charges a pessimistic
worst case up front, in a single atomic UPDATE that only succeeds if the
job can afford it. settle() refunds the difference once the real usage
is known. A request that cannot be reserved never reaches Anthropic.
"""

import logging
from decimal import Decimal

from backend.database.db import Database
from backend.utils.models import MODELS, UnknownModel
from backend.utils.utils import JobStatus

log = logging.getLogger(__name__)

# A job that is over budget or already finished must not spend more.
SPENDABLE = {JobStatus.QUEUED.value, JobStatus.RUNNING.value}

# Used when a request does not say how long its answer may be.
DEFAULT_MAX_TOKENS = 8_192


class BudgetExceeded(Exception):
    """The job cannot afford this request."""


class JobNotSpendable(Exception):
    """The job is finished, failed, or does not exist."""


class SpendTracker:
    def __init__(self, db: Database | None = None):
        self.db = db or Database()

    # --- before the request goes out -----------------------------------

    def reserve(self, job_id: str, model: str, input_tokens: int, max_tokens: int) -> Decimal:
        """Charge the worst case this request could cost. Returns it.

        Raises UnknownModel if we have no price -- an unpriced model
        would otherwise be free, and therefore unlimited.
        """
        spec = MODELS.get(model)          # raises UnknownModel
        worst_case = spec.cost(input_tokens, max_tokens or DEFAULT_MAX_TOKENS)

        # One statement does the check and the charge together, so two
        # requests cannot both pass on the same remaining budget.
        query = """
        UPDATE jobs
           SET cost_usd = cost_usd + %s
         WHERE id = %s
           AND status = ANY(%s)
           AND cost_usd + %s <= budget_usd
        RETURNING cost_usd, budget_usd
        """
        with self.db.get_connection() as conn, conn.cursor() as cur:
            cur.execute(query, (worst_case, job_id, list(SPENDABLE), worst_case))
            row = cur.fetchone()
            conn.commit()

        if row is None:
            self._explain_refusal(job_id, worst_case)
        return worst_case

    def _explain_refusal(self, job_id: str, wanted: Decimal) -> None:
        """The UPDATE matched nothing. Work out why, for the error."""
        query = "SELECT status, cost_usd, budget_usd FROM jobs WHERE id = %s"
        with self.db.get_connection() as conn, conn.cursor() as cur:
            cur.execute(query, (job_id,))
            row = cur.fetchone()

        if row is None:
            raise JobNotSpendable(f"no job with id {job_id}")
        if row["status"] not in SPENDABLE:
            raise JobNotSpendable(f"job is {row['status']}")
        raise BudgetExceeded(
            f"job has ${row['cost_usd']} of ${row['budget_usd']} spent; "
            f"this request needs ${wanted}"
        )

    # --- after the answer comes back ------------------------------------

    def settle(
        self,
        job_id: str,
        model: str,
        reserved: Decimal,
        input_tokens: int,
        output_tokens: int,
        cache_write_tokens: int = 0,
        cache_read_tokens: int = 0,
    ) -> None:
        """Replace the reservation with what it actually cost."""
        try:
            spec = MODELS.get(model)
        except UnknownModel:
            log.error("settling job %s against unpriced model %s", job_id, model)
            return

        actual = spec.cost(
            input_tokens, output_tokens, cache_write_tokens, cache_read_tokens
        )
        # Cached input is real input as far as the token counters go, or
        # the row would claim a job read almost nothing.
        input_tokens = input_tokens + cache_write_tokens + cache_read_tokens
        query = """
        UPDATE jobs
           SET input_tokens  = input_tokens  + %s,
               output_tokens = output_tokens + %s,
               cost_usd      = GREATEST(cost_usd - %s + %s, 0)
         WHERE id = %s
        """
        with self.db.get_connection() as conn, conn.cursor() as cur:
            cur.execute(query, (input_tokens, output_tokens, reserved, actual, job_id))
            conn.commit()
