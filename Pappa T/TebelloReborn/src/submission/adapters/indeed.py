"""Indeed's native SmartApply flow — the project's first submit adapter.

Phase E of docs/specs/indeed-submit-adapter.md.

Three methods with three very different characters, and the difference is the
design:

- `can_handle()` — **pure, offline, side-effect-free** (A1). Called by
  `eligibility.get_adapter()` on *every* submit run, including `--manual` and
  every `not_supported` case, so it is a static URL predicate and nothing more.
- `inspect_apply_flow()` — live, read-only, and deliberately **not** part of the
  `SubmitAdapter` Protocol. Only `prep-submission` calls it.
- `submit()` — live and writing. Phase G.

The adapter observes; it never judges and never persists. It returns a
`PrepResult` of what it saw, and `prep.py` decides what that means.
"""

from pathlib import Path
from urllib.parse import urlsplit

from src.submission.schema import PrepResult
from src.vacancy_search.schema import Vacancy

# A posting's canonical detail page. Indeed serves the same job under every
# country subdomain, so the country is not part of the shape.
_JOB_PATH_PREFIX = "/viewjob"
_INDEED_APEX = "indeed.com"

SUBMIT_NOT_BUILT_DETAIL = (
    "IndeedAdapter.submit() is not built yet (Phase G) — submit this one by hand"
)


def is_indeed_host(host: str) -> bool:
    """Exact apex or a real subdomain of it — never a suffix match.

    `"notindeed.com".endswith("indeed.com")` is `True`, and so is
    `"indeed.com.evil.example".startswith("indeed.com")`. A1's sketch uses the
    bare `endswith`; `browser.py._is_google_block_page` already refuses that
    shortcut for the same reason, and this follows it.

    Public because `tools/indeed_login_setup.py` needs the same judgment about a
    cookie's domain, and writing it twice is how one copy keeps the bug — which
    is exactly what happened on the first attempt.
    """
    return host == _INDEED_APEX or host.endswith("." + _INDEED_APEX)


class IndeedAdapter:
    """`SubmitAdapter` for postings that use Indeed's own apply form."""

    platform = "indeed"

    def can_handle(self, vacancy: Vacancy) -> bool:
        """Static URL shape only. No network, no browser, no database (A1).

        A posting that redirects to an external ATS deliberately **passes** this
        check — that can't be known from a scraped URL, and finding out requires
        a browser. `inspect_apply_flow()` records it as prep state, and the gate
        in `pipeline.py` declines the vacancy one layer down, reaching the same
        operator-visible `not_supported` without a networked predicate.
        """
        if vacancy.platform != self.platform:
            return False

        try:
            parts = urlsplit(vacancy.url or "")
        except ValueError:
            # urlsplit raises on a few malformed inputs (a bad IPv6 literal, for
            # one). A predicate called on every submit run may not propagate
            # that — an unparseable URL is simply not one this adapter handles.
            return False

        host = (parts.hostname or "").lower()
        return is_indeed_host(host) and parts.path.startswith(_JOB_PATH_PREFIX)

    def inspect_apply_flow(
        self, vacancy: Vacancy, session_state_path: Path
    ) -> PrepResult:
        """Walk the apply wizard read-only and report what is there.

        Not in the `SubmitAdapter` Protocol on purpose (A1): everything live
        lives here, so the Protocol's `can_handle()` can stay a predicate.

        Unimplemented until the live recon supplies real selectors. `browser.py`
        stores landmark *names* rather than selectors, and `WIZARD_STEPS` omits
        the review step entirely, precisely so this method maps them from
        something observed instead of something plausible — the Apify
        payload-shape lesson. The adapter is not registered in
        `eligibility.ADAPTERS` while this raises, so no vacancy can reach it.
        """
        raise NotImplementedError(
            "inspect_apply_flow() needs selectors from the live recon — see "
            "docs/specs/indeed-submit-adapter.md Build Queue, Phase E"
        )

    def submit(self, vacancy: Vacancy, session_state_path: Path) -> tuple[bool, str]:
        """Phase G. Reports a failure rather than raising.

        `pipeline._decide()` turns an adapter exception into "adapter raised:
        ...", which reads like a bug in code that ran. The truth is that this
        half isn't built, and the detail says so.
        """
        return False, SUBMIT_NOT_BUILT_DETAIL
