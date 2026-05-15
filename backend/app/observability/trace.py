from __future__ import annotations

from typing import Any, Callable, Dict, List, TypeVar

from app.schemas import TraceEvent, utc_now_iso


T = TypeVar("T")


class TraceRecorder:
    def __init__(self) -> None:
        self.events: List[TraceEvent] = []

    def run_node(
        self,
        node_name: str,
        input_summary: Dict[str, Any],
        action: Callable[[], T],
        output_summarizer: Callable[[T], Dict[str, Any]],
    ) -> T:
        started_at = utc_now_iso()
        try:
            result = action()
            finished_at = utc_now_iso()
            self.events.append(
                TraceEvent(
                    node_name=node_name,
                    input_summary=input_summary,
                    output_summary=output_summarizer(result),
                    status="success",
                    started_at=started_at,
                    finished_at=finished_at,
                )
            )
            return result
        except Exception as exc:
            finished_at = utc_now_iso()
            self.events.append(
                TraceEvent(
                    node_name=node_name,
                    input_summary=input_summary,
                    output_summary={},
                    status="failed",
                    started_at=started_at,
                    finished_at=finished_at,
                    error=str(exc),
                )
            )
            raise
