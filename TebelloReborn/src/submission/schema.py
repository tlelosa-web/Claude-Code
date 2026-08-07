from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SubmissionMethod(Enum):
    AUTO = "auto"
    MANUAL = "manual"


class SubmissionOutcome(Enum):
    SUBMITTED = "submitted"
    FAILED = "failed"
    # No adapter can handle this vacancy — it is still Tebello's to submit by
    # hand, so the vacancy deliberately stays at 'approved' (spec §Outcome →
    # status mapping). Not an error state.
    NOT_SUPPORTED = "not_supported"
    # An adapter exists and the posting is native, but prep hasn't run or its
    # questions aren't fully reviewed. The operator's move is
    # prep-submission/review-questions, not "submit it by hand" — which is why
    # this is its own value and not a second meaning for NOT_SUPPORTED
    # (indeed-submit-adapter.md Amendment A3). Vacancy stays at 'approved'.
    PENDING_REVIEW = "pending_review"


class PrepStatus(Enum):
    """How one `prep-submission` run ended (Amendment A2).

    Prep state is recorded, not inferred. `all_questions_reviewed()` over
    screening_questions alone could not tell "prep never ran" from "prepped and
    this posting genuinely has no questions" — both are zero rows, and only one
    of them may proceed to submit. Absence of a submission_preps row is the one
    state that genuinely is an absence.
    """

    QUESTIONS_EXTRACTED = "questions_extracted"
    NO_QUESTIONS = "no_questions"
    EXTERNAL_ATS = "external_ats"
    CAPTCHA_DETECTED = "captcha_detected"
    SESSION_EXPIRED = "session_expired"
    UNSUPPORTED_FORM = "unsupported_form"
    ERROR = "error"


class FieldType(Enum):
    """The control a screening question is rendered as.

    `radio` is distinct from `checkbox` (A12): the recon found nominally yes/no
    questions rendered as free text, so the control cannot be inferred from the
    question's wording and a single "checkbox" value was carrying too many
    meanings to fill correctly.
    """

    TEXT = "text"
    TEXTAREA = "textarea"
    SELECT = "select"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    FILE = "file"


# Free-text and upload controls have no option labels. Kept as a set rather
# than an inline tuple because both the dataclass guard below and the drift
# fingerprint (A6, Phase E) need the same definition of "has options".
CHOICE_FIELD_TYPES = frozenset({FieldType.SELECT, FieldType.CHECKBOX, FieldType.RADIO})


class QuestionDecision(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    EDITED = "edited"
    REJECTED = "rejected"


class Sensitivity(Enum):
    """Why a question may not be LLM-drafted at all (A11).

    Work-authorization, compensation and EEO/demographic questions are legally
    and personally different from "describe a recent project". A draft anchors
    the answer, so for anything other than ORDINARY no drafting call is made and
    drafted_answer stays None — Tebello types it or the vacancy stays
    unsubmittable.
    """

    ORDINARY = "ordinary"
    COMPENSATION = "compensation"
    WORK_AUTHORIZATION = "work_authorization"
    DEMOGRAPHIC = "demographic"


@dataclass
class SubmissionAttempt:
    """One recorded attempt to submit an approved application.

    `submissions` is an append-only attempt log — several rows per vacancy are
    expected (a `not_supported` followed later by a manual submission is the
    ordinary path in this build). `vacancies.status` is current state; this is
    history (spec Amendment B4).
    """

    vacancy_id: int
    method: SubmissionMethod
    outcome: SubmissionOutcome
    detail: Optional[str] = None
    # Timezone-aware, matching ReviewResult.decided_at and Vacancy.scraped_at.
    # A naive utcnow() string sorts inconsistently against those (Amendment A8).
    attempted_at: str = field(default_factory=_utc_now)
    id: Optional[int] = None

    def __post_init__(self):
        # A raw string would pass the dataclass untouched and only fail later at
        # the DB CHECK constraint — a long way from the code that got it wrong.
        if not isinstance(self.method, SubmissionMethod):
            raise TypeError(
                f"method must be a SubmissionMethod, got {type(self.method).__name__}"
            )

        if not isinstance(self.outcome, SubmissionOutcome):
            raise TypeError(
                f"outcome must be a SubmissionOutcome, got {type(self.outcome).__name__}"
            )


@dataclass
class SubmissionPrep:
    """One recorded `prep-submission` run against one vacancy.

    Append-only, same discipline as `submissions` and `approvals` — a failed
    prep followed by a successful re-prep is the ordinary path, so several rows
    per vacancy are expected and `get_latest_prep()` resolves the multiplicity.
    """

    vacancy_id: int
    status: PrepStatus
    detail: Optional[str] = None
    # Where the run stopped. Diagnostic only — never used to decide anything,
    # so a changed Indeed route can't silently alter the submit gate.
    step_url: Optional[str] = None
    prepped_at: str = field(default_factory=_utc_now)
    id: Optional[int] = None

    def __post_init__(self):
        if not isinstance(self.status, PrepStatus):
            raise TypeError(
                f"status must be a PrepStatus, got {type(self.status).__name__}"
            )


@dataclass
class ScreeningQuestion:
    """One employer-authored question extracted from a posting's apply form.

    The text is untrusted content in the same class as `vacancy.description` —
    it reaches an LLM only through `doc_gen.runner.wrap_untrusted_text()`
    (Phase E). `decision` starts PENDING and only `review-questions` moves it:
    nothing generated here reaches an employer unseen.
    """

    vacancy_id: int
    # Ties this question set to the prep run that produced it, so a re-prep's
    # questions never mix with a stale set (A12).
    prep_id: int
    question_text: str
    field_type: FieldType
    step_url: str
    position: int
    # sha256 over normalized text/type/required/options (A6). Computed at
    # extraction in Phase E; stored here so submit can compare sets and abort
    # on drift in either direction rather than guess which change was benign.
    fingerprint: str
    field_key: Optional[str] = None
    required: bool = False
    # Option labels for choice controls, None for free-text and file (A12).
    # Serialized to options_json by db.py, matching profile/db.py's json.dumps
    # convention rather than introducing a second serialization style.
    options: Optional[List[str]] = None
    sensitivity: Sensitivity = Sensitivity.ORDINARY
    drafted_answer: Optional[str] = None
    final_answer: Optional[str] = None
    decision: QuestionDecision = QuestionDecision.PENDING
    extracted_at: str = field(default_factory=_utc_now)
    decided_at: Optional[str] = None
    id: Optional[int] = None

    def __post_init__(self):
        if not isinstance(self.field_type, FieldType):
            raise TypeError(
                f"field_type must be a FieldType, got {type(self.field_type).__name__}"
            )
        if not isinstance(self.decision, QuestionDecision):
            raise TypeError(
                f"decision must be a QuestionDecision, got {type(self.decision).__name__}"
            )
        if not isinstance(self.sensitivity, Sensitivity):
            raise TypeError(
                f"sensitivity must be a Sensitivity, got "
                f"{type(self.sensitivity).__name__}"
            )
        # Options on a textarea means the extractor mis-read the control. Caught
        # here rather than at fill time, because the drift fingerprint is built
        # from these labels and would then compare the wrong thing.
        if self.options is not None and self.field_type not in CHOICE_FIELD_TYPES:
            raise ValueError(
                f"options are only meaningful on {sorted(f.value for f in CHOICE_FIELD_TYPES)}, "
                f"got field_type={self.field_type.value}"
            )


@dataclass(frozen=True)
class PrepReadiness:
    """Whether a vacancy may proceed to `IndeedAdapter.submit()`, and if not,
    what `pipeline.py` should record and tell the operator to do.

    Named for what it answers: A2 renamed `all_questions_reviewed()` to
    `submission_prep_ready()` because the old name described half the check —
    prep state gates submission just as much as the question tally does.
    """

    ready: bool
    outcome: Optional[SubmissionOutcome]
    reason: str

    def __post_init__(self):
        # pipeline.py records `outcome` only on the not-ready path. A truthy
        # pair would log an attempt outcome for a vacancy that proceeded; an
        # empty one would leave the not-ready path with nothing to record.
        if self.ready and self.outcome is not None:
            raise ValueError("a ready vacancy has no outcome to record")
        if not self.ready and self.outcome is None:
            raise ValueError("a vacancy that cannot proceed must carry an outcome")
