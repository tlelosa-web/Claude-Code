"""RED: src/doc_gen/schema.py doesn't exist yet — this import must fail first."""

import pytest

from src.doc_gen.schema import GenerationStatus


class TestGenerationStatus:
    def test_success_value(self):
        assert GenerationStatus.SUCCESS.value == "success"

    def test_throttled_value(self):
        assert GenerationStatus.THROTTLED.value == "throttled"

    def test_error_value(self):
        assert GenerationStatus.ERROR.value == "error"

    def test_only_three_members(self):
        assert {member.value for member in GenerationStatus} == {
            "success",
            "throttled",
            "error",
        }

    def test_rejects_free_text(self):
        with pytest.raises(ValueError):
            GenerationStatus("bogus")
