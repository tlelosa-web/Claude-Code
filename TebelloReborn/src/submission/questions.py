"""Pure judgment about screening questions — identity (A6) and sensitivity (A11).

Phase E of docs/specs/indeed-submit-adapter.md.

Same split as `browser.py`, for the same reason: the adapter *observes* a form
control (its label, its type, its option labels) and this module *judges* what
that observation means. Nothing here touches a browser, a database or the
network, so every rule below is exercisable now rather than after the live
recon — and both rules are ones a live-only test would exercise once, by
accident, on whichever posting happened to be open.

Two questions are answered here:

- **Is this the same question I already showed Tebello?** (`compute_fingerprint`)
  Stored at extraction; compared as a set at submit time (Phase G).
- **May an LLM draft an answer to it at all?** (`classify_sensitivity`)
"""

import hashlib
import re
from typing import Optional, Sequence

from src.submission.schema import CHOICE_FIELD_TYPES, FieldType, Sensitivity

# ---------------------------------------------------------------------------
# Identity (A6)
# ---------------------------------------------------------------------------

_WHITESPACE_RUN = re.compile(r"\s+")

# One trailing required-marker or label colon. Anchored and non-repeating: A6
# says "one", and "Location:*" keeps its colon because a second marker is text.
_TRAILING_MARKER = re.compile(r"[*:]$")

# A6's field separator. Outside the printable range on purpose — a question
# whose text ends where the next field begins cannot forge a collision.
_SEP = "\x1f"


def norm(text: str) -> str:
    """A6's normalizer: styling is not identity.

    Casefold, collapse whitespace, strip, drop one trailing `*`/`:` — then strip
    once more. **That last strip is not in A6's four steps and is load-bearing.**
    Without it "Question *" normalizes to "question " while "Question"
    normalizes to "question", giving one question two fingerprints over exactly
    the required-marker styling the rule exists to ignore.
    """
    collapsed = _WHITESPACE_RUN.sub(" ", text.casefold()).strip()
    return _TRAILING_MARKER.sub("", collapsed).strip()


def compute_fingerprint(
    question_text: str,
    field_type: FieldType,
    required: bool,
    options: Optional[Sequence[str]],
) -> str:
    """sha256 over the question's identity — text, control, requiredness, options.

    Order and on-page position are deliberately excluded (A6): a reordered form
    is the same form, and position is stored separately, for filling rather than
    for identity.

    Options contribute only for controls that can have them. `CHOICE_FIELD_TYPES`
    is the one definition of that (schema.py's own guard already uses it), so a
    stray option list on a textarea — an extraction bug — can never decide
    whether a reviewed question still counts as reviewed.
    """
    if field_type in CHOICE_FIELD_TYPES and options:
        norm_options = _SEP.join(sorted(norm(option) for option in options))
    else:
        norm_options = ""

    payload = _SEP.join(
        (norm(question_text), field_type.value, str(required), norm_options)
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Sensitivity (A11)
# ---------------------------------------------------------------------------

# Keywords per class, matched against norm()'d text.
#
# Matching is **prefix-anchored** by default: `\b` + keyword, with no closing
# boundary, so "citizen" catches "citizenship", "sponsor" catches "sponsorship"
# and "disab" catches both "disabled" and "disability" without listing every
# inflection. That is the over-matching direction A11 asks for — a wrong
# non-ordinary call costs one hand-typed answer, the reverse costs a drafted
# answer about Tebello's immigration status or salary floor.
#
# The exception is below: a few keywords are real words inside longer, entirely
# ordinary ones, and prefix matching would misfire on the vocabulary a
# manufacturing/operations posting uses every day.
SENSITIVITY_KEYWORDS: dict[Sensitivity, tuple[str, ...]] = {
    Sensitivity.WORK_AUTHORIZATION: (
        "work authoriz",
        "work authoris",
        "authorized to work",
        "authorised to work",
        "eligible to work",
        "right to work",
        "legally able to work",
        "work permit",
        "visa",
        "sponsor",
        "immigration",
        "citizen",
        "nationality",
        "permanent resident",
        "residency",
        "id number",
        "identity number",
        "passport",
    ),
    Sensitivity.COMPENSATION: (
        "salary",
        "salaries",
        "remunerat",
        "compensation",
        "expected pay",
        "desired pay",
        "current pay",
        "pay expectation",
        "hourly rate",
        "rate per hour",
        "wage",
        "ctc",
        "cost to company",
        "earning",
        # "package" is the local phrasing for remuneration ("current package",
        # "expected package") and had to be listed — but bare, prefix-anchored,
        # it also matches "maintenance package" and "package a proposal", which
        # is ordinary vocabulary in exactly the manufacturing/operations
        # postings this pipeline targets. Listed as the money-shaped phrases
        # instead. The residual is a question phrased as "Package?" and nothing
        # else, which "salary"/"ctc"/"remunerat" do not already cover.
        "current package",
        "expected package",
        "desired package",
        "salary package",
        "total package",
        "annual package",
        "package expectation",
    ),
    Sensitivity.DEMOGRAPHIC: (
        "gender",
        "race",
        "racial",
        "ethnic",
        "disab",
        "veteran",
        "date of birth",
        "how old are you",
        "marital",
        "sexual orientation",
        "pregnan",
        "religion",
        "religious",
        "bee",
        "b-bbee",
        "employment equity",
        "designated group",
        "age",
    ),
}

# Matched with a closing `\b` as well, because prefix matching is too loose for
# these specific words:
#
# - "age"     → manage, average, package, agent, agenda
# - "race"    → traceability, bracelet
# - "bee"     → been
# - "wage"    → (safe alone, but paired here for the same class of trailing-text risk)
#
# Every one of those appears in ordinary engineering questions, so leaving them
# prefix-anchored would quietly stop drafting for questions A11 never meant to
# cover. "package" needed the other fix — see the compensation list.
EXACT_MATCH_KEYWORDS = frozenset({"age", "race", "bee", "wage"})

# Order decides only which label a multi-class question carries; every
# non-ordinary value blocks drafting identically. Work authorization leads
# because its questions are the ones where a drafted answer is a legal
# statement rather than a preference.
_CLASSIFICATION_ORDER = (
    Sensitivity.WORK_AUTHORIZATION,
    Sensitivity.DEMOGRAPHIC,
    Sensitivity.COMPENSATION,
)


def _pattern_for(keyword: str) -> re.Pattern:
    boundary = r"\b" if keyword in EXACT_MATCH_KEYWORDS else ""
    return re.compile(r"\b" + re.escape(keyword) + boundary)


_COMPILED: dict[Sensitivity, tuple[re.Pattern, ...]] = {
    sensitivity: tuple(_pattern_for(kw) for kw in keywords)
    for sensitivity, keywords in SENSITIVITY_KEYWORDS.items()
}


def classify_sensitivity(question_text: str) -> Sensitivity:
    """Which A11 class this question falls in — ORDINARY if none.

    ORDINARY is the absence of a match, never a match of its own: it is the only
    value that permits a drafting call, so it must not be reachable by a rule
    firing.
    """
    normalized = norm(question_text)
    for sensitivity in _CLASSIFICATION_ORDER:
        if any(pattern.search(normalized) for pattern in _COMPILED[sensitivity]):
            return sensitivity
    return Sensitivity.ORDINARY
