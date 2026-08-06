"""Which vacancies can be submitted automatically, and by what.

Dispatch is capability-based: an adapter is found by platform, then asked
whether it can handle *this specific vacancy*. Platform alone is too coarse —
Indeed's application flow varies per employer, and many postings redirect to an
external ATS with no fixed shape. An adapter must be able to decline an
individual vacancy and have it fall through to manual submission.

The registry is empty in this build, deliberately. With no adapter registered,
every vacancy is "not auto-submittable" and routes to manual with a recorded
outcome — which is the honest state of this project until the platform question
in docs/specs/submission-core.md §Open Items is answered.
"""

from pathlib import Path
from typing import Optional, Protocol

from src.vacancy_search.schema import Vacancy


class SubmitAdapter(Protocol):
    """The contract a site-specific adapter implements.

    Adapters never touch the database and never transition vacancy status —
    `pipeline.py` owns all persistence. That is what makes it impossible for a
    future adapter to route around the human approval gate.
    """

    platform: str

    def can_handle(self, vacancy: Vacancy) -> bool:
        """False for anything this adapter can't submit reliably — an external
        ATS redirect, an unrecognised form. Declining is a normal answer."""
        ...

    def submit(self, vacancy: Vacancy, session_state_path: Path) -> tuple[bool, str]:
        """Returns (succeeded, detail). `detail` is recorded verbatim on both
        paths — a success detail is as useful as a failure one. Receives just
        the resolved session path, never the whole Settings object."""
        ...


# Intentionally empty. To add one: implement SubmitAdapter and register it here
# as ADAPTERS["<platform>"] = <adapter>. Nothing in pipeline.py changes, and no
# `if platform == ...` branch is needed anywhere.
ADAPTERS: dict[str, SubmitAdapter] = {}


def get_adapter(vacancy: Vacancy) -> Optional[SubmitAdapter]:
    """The adapter that will actually submit this vacancy, or None.

    An adapter that declines the vacancy is indistinguishable from no adapter at
    all — both mean "no automated path exists for this one", which is the only
    distinction the pipeline needs.
    """
    adapter = ADAPTERS.get(vacancy.platform)
    if adapter is None or not adapter.can_handle(vacancy):
        return None
    return adapter


def is_auto_submittable(vacancy: Vacancy) -> bool:
    return get_adapter(vacancy) is not None
