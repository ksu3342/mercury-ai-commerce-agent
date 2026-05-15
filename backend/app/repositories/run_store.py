from __future__ import annotations

from typing import Dict

from app.schemas import HumanReview, RunSummary, utc_now_iso


class InMemoryRunStore:
    """Small in-memory run store for the demo API lifecycle."""

    def __init__(self) -> None:
        self._runs: Dict[str, RunSummary] = {}

    def save(self, run: RunSummary) -> RunSummary:
        self._runs[run.run_id] = run
        return run

    def get(self, run_id: str) -> RunSummary:
        try:
            return self._runs[run_id]
        except KeyError as exc:
            raise KeyError(f"Run not found: {run_id}") from exc

    def attach_review(self, run_id: str, review: HumanReview, status: str, current_state: str) -> RunSummary:
        run = self.get(run_id)
        updated = run.model_copy(
            update={
                "human_review": review,
                "status": status,
                "current_state": current_state,
                "updated_at": utc_now_iso(),
            },
            deep=True,
        )
        return self.save(updated)
