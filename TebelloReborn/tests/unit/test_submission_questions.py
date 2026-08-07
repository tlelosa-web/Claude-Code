"""RED: src/submission/questions.py doesn't exist yet — these imports must fail
first.

Phase E of docs/specs/indeed-submit-adapter.md, the pure-judgment half: A6's
drift fingerprint and A11's sensitivity classification.

**Same judgment/observation split Phase D established.** The adapter observes a
form control (its label, its type, its option labels); this module judges what
that observation *means* — whether two observations are the same question, and
whether a question may be drafted by an LLM at all. Nothing here touches a
browser, a database, or the network, so every rule below is exercisable now
rather than after the live recon.

The fingerprint tests carry the weight A6 intended: a fingerprint that changes
when nothing meaningful changed aborts a submission Tebello already reviewed,
and one that stays equal across a real change lets an unreviewed question reach
an employer. Both directions are pinned.
"""

import hashlib

import pytest

from src.submission.questions import (
    EXACT_MATCH_KEYWORDS,
    SENSITIVITY_KEYWORDS,
    classify_sensitivity,
    compute_fingerprint,
    norm,
)
from src.submission.schema import FieldType, Sensitivity


class TestNorm:
    """A6's normalizer. Styling is not identity."""

    def test_casefolds(self):
        assert norm("Are You Proficient?") == norm("are you proficient?")

    def test_collapses_every_whitespace_run_to_one_space(self):
        assert norm("describe   your\n\n most  recent\tproject") == (
            "describe your most recent project"
        )

    def test_strips_surrounding_whitespace(self):
        assert norm("   location   ") == "location"

    def test_strips_one_trailing_required_marker(self):
        assert norm("Expected salary *") == norm("Expected salary")

    def test_strips_one_trailing_colon(self):
        assert norm("Location:") == norm("Location")

    def test_strips_only_one_trailing_marker(self):
        # "one trailing * or :" is literal — a second marker is part of the text.
        # Pinned so a future "strip them all" reading is a visible test change,
        # not a silent widening of what counts as the same question.
        assert norm("Location:*") == "location:"

    def test_marker_removal_leaves_no_trailing_space(self):
        # The spec's four steps end at the marker strip, which would leave
        # "question " for a form that renders "Question *" and "question" for one
        # that renders "Question" — two fingerprints for one question, and the
        # required-marker is exactly the styling A6 set out to ignore.
        assert norm("Are you proficient in AutoCAD? *") == "are you proficient in autocad?"

    def test_internal_punctuation_is_preserved(self):
        # Only *trailing* markers are styling. A question mark mid-text, or a
        # colon inside a clause, is content.
        assert norm("Do you have a valid driver's licence (Code 08)?") == (
            "do you have a valid driver's licence (code 08)?"
        )


class TestFingerprintIdentity:
    """Equal fingerprints mean "the same question" — A6's proceed case."""

    def test_is_a_sha256_hexdigest(self):
        fp = compute_fingerprint("Location", FieldType.TEXT, False, None)
        assert len(fp) == 64
        assert set(fp) <= set("0123456789abcdef")

    def test_matches_the_documented_construction(self):
        # The literal construction from A6, recomputed here rather than trusted:
        # if the module ever changes its separator or field order, every stored
        # fingerprint silently stops matching and every submission aborts.
        expected = hashlib.sha256(
            ("location" + "\x1f" + "text" + "\x1f" + "False" + "\x1f" + "").encode(
                "utf-8"
            )
        ).hexdigest()
        assert compute_fingerprint("Location", FieldType.TEXT, False, None) == expected

    def test_restyled_label_is_the_same_question(self):
        plain = compute_fingerprint("Expected salary", FieldType.TEXT, True, None)
        styled = compute_fingerprint("  Expected   Salary *  ", FieldType.TEXT, True, None)
        assert plain == styled

    def test_reordered_options_are_the_same_question(self):
        # A6 sorts option labels deliberately: a reordered <select> is the same
        # question, and aborting on it would make every A/B-tested form unusable.
        a = compute_fingerprint(
            "Notice period", FieldType.SELECT, True, ["Immediate", "1 month", "2 months"]
        )
        b = compute_fingerprint(
            "Notice period", FieldType.SELECT, True, ["2 months", "1 month", "Immediate"]
        )
        assert a == b

    def test_option_labels_are_normalized_too(self):
        a = compute_fingerprint("Notice period", FieldType.SELECT, True, ["1 Month"])
        b = compute_fingerprint("Notice period", FieldType.SELECT, True, ["  1   month "])
        assert a == b


class TestFingerprintDrift:
    """Different fingerprints mean "this changed" — A6's abort case."""

    def test_changed_text_changes_it(self):
        a = compute_fingerprint("Expected salary", FieldType.TEXT, True, None)
        b = compute_fingerprint("Minimum salary", FieldType.TEXT, True, None)
        assert a != b

    def test_changed_field_type_changes_it(self):
        # The recon's own finding: a nominally yes/no question rendered as free
        # text. If the employer swaps it to a radio, the answer Tebello approved
        # may no longer be fillable at all.
        a = compute_fingerprint("Proficient in AutoCAD?", FieldType.TEXT, True, None)
        b = compute_fingerprint("Proficient in AutoCAD?", FieldType.TEXTAREA, True, None)
        assert a != b

    def test_changed_required_flag_changes_it(self):
        a = compute_fingerprint("Portfolio URL", FieldType.TEXT, False, None)
        b = compute_fingerprint("Portfolio URL", FieldType.TEXT, True, None)
        assert a != b

    def test_added_option_changes_it(self):
        a = compute_fingerprint("Notice period", FieldType.SELECT, True, ["Immediate"])
        b = compute_fingerprint(
            "Notice period", FieldType.SELECT, True, ["Immediate", "3 months"]
        )
        assert a != b

    def test_separator_is_not_forgeable_from_text(self):
        # The \x1f separator exists so a question whose text ends where the next
        # field begins can't collide with a different (text, type) pair. A join
        # on "" or " " would make these two equal.
        a = compute_fingerprint("ab", FieldType.TEXT, False, None)
        b = compute_fingerprint("a", FieldType.TEXT, False, None)
        assert a != b


class TestFingerprintOptionsPolicy:
    """Which field types contribute option labels to identity."""

    def test_free_text_types_contribute_no_options(self):
        # CHOICE_FIELD_TYPES is the single definition of "has options" (schema.py
        # already uses it for its own guard). A stray option list on a textarea
        # is an extraction bug, and letting it into the fingerprint would make
        # the bug decide whether a reviewed question still counts as reviewed.
        without = compute_fingerprint("Tell us more", FieldType.TEXTAREA, True, None)
        with_stray = compute_fingerprint(
            "Tell us more", FieldType.TEXTAREA, True, ["ignored"]
        )
        assert without == with_stray

    @pytest.mark.parametrize(
        "field_type", [FieldType.SELECT, FieldType.CHECKBOX, FieldType.RADIO]
    )
    def test_choice_types_contribute_options(self, field_type):
        without = compute_fingerprint("Pick one", field_type, True, None)
        with_options = compute_fingerprint("Pick one", field_type, True, ["Yes", "No"])
        assert without != with_options

    def test_empty_option_list_matches_no_option_list(self):
        # A form that renders a choice control with no options yet, versus one
        # the extractor read as None — the same nothing, and not worth an abort.
        assert compute_fingerprint(
            "Pick one", FieldType.SELECT, True, []
        ) == compute_fingerprint("Pick one", FieldType.SELECT, True, None)


class TestSensitivityClassification:
    """A11: which questions are never LLM-drafted."""

    @pytest.mark.parametrize(
        "text",
        [
            "Are you authorized to work in South Africa?",
            "Do you require visa sponsorship?",
            "Do you have a valid work permit?",
            "Are you a South African citizen?",
            "What is your citizenship status?",
            "Do you hold permanent residency?",
            "Please provide your ID number",
        ],
    )
    def test_work_authorization(self, text):
        assert classify_sensitivity(text) == Sensitivity.WORK_AUTHORIZATION

    @pytest.mark.parametrize(
        "text",
        [
            "What is your expected salary?",
            "Current remuneration package?",
            "State your desired compensation",
            "What is your hourly rate?",
            "Expected CTC per annum",
            "What wage are you looking for?",
        ],
    )
    def test_compensation(self, text):
        assert classify_sensitivity(text) == Sensitivity.COMPENSATION

    @pytest.mark.parametrize(
        "text",
        [
            "What is your gender?",
            "Please state your race",
            "What is your ethnicity?",
            "Do you have a disability?",
            "Are you a designated group member under Employment Equity?",
            "What is your date of birth?",
            "Are you BEE compliant as an individual?",
        ],
    )
    def test_demographic(self, text):
        assert classify_sensitivity(text) == Sensitivity.DEMOGRAPHIC

    @pytest.mark.parametrize(
        "text",
        [
            "Please describe your most recent hospitality or residential project briefly.",
            "Are you proficient in AutoCAD?",
            "Location",
            "How many years of maintenance planning experience do you have?",
            "Why do you want to work here?",
        ],
    )
    def test_ordinary(self, text):
        assert classify_sensitivity(text) == Sensitivity.ORDINARY

    def test_classification_is_case_and_spacing_insensitive(self):
        assert (
            classify_sensitivity("EXPECTED    SALARY *") == Sensitivity.COMPENSATION
        )


class TestSensitivityFalsePositives:
    """A11 errs toward over-matching, but not at the cost of drafting nothing.

    Every question wrongly called sensitive is one Tebello types by hand. These
    are the substrings that would quietly do that to ordinary engineering
    questions — each one is a real word a manufacturing/operations posting uses.
    """

    @pytest.mark.parametrize(
        "text",
        [
            "Describe a project you had to manage end to end",
            "What is the average plant downtime you have achieved?",
            "Have you worked with a maintenance package before?",
            "Do you have experience as an agent for a supplier?",
            "How do you package a proposal for a client?",
        ],
    )
    def test_age_does_not_match_inside_longer_words(self, text):
        assert classify_sensitivity(text) == Sensitivity.ORDINARY

    def test_race_does_not_match_traceability(self):
        assert (
            classify_sensitivity("Describe your approach to material traceability")
            == Sensitivity.ORDINARY
        )

    def test_paid_work_history_is_not_a_compensation_question(self):
        assert (
            classify_sensitivity("Describe your most recent paid internship")
            == Sensitivity.ORDINARY
        )


class TestSensitivityPolicy:
    """Structural guarantees the keyword lists themselves must keep."""

    def test_every_non_ordinary_class_has_keywords(self):
        # A class with an empty list silently never fires, which looks identical
        # to "no question was ever that sensitive".
        for sensitivity in Sensitivity:
            if sensitivity is Sensitivity.ORDINARY:
                continue
            assert SENSITIVITY_KEYWORDS[sensitivity], sensitivity

    def test_ordinary_is_not_a_keyword_class(self):
        # ORDINARY is the absence of a match, never a match of its own.
        assert Sensitivity.ORDINARY not in SENSITIVITY_KEYWORDS

    def test_exact_match_keywords_are_a_subset_of_the_keyword_lists(self):
        # EXACT_MATCH_KEYWORDS narrows how a keyword is matched; a name in it
        # that no class lists is a typo that weakens nothing and does nothing,
        # which is the hardest kind of dead rule to notice.
        listed = {kw for keywords in SENSITIVITY_KEYWORDS.values() for kw in keywords}
        assert EXACT_MATCH_KEYWORDS <= listed

    def test_a_question_matching_two_classes_is_still_not_ordinary(self):
        # Which label wins is informational — every non-ordinary value blocks
        # drafting identically. What must never happen is falling through to
        # ORDINARY because two rules both claimed it.
        text = "What is your expected salary, and do you require sponsorship?"
        assert classify_sensitivity(text) != Sensitivity.ORDINARY
