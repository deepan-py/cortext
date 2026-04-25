"""Tests for Cortex pydantic models."""

from datetime import date

import pytest

from cortex.models import (
    AlternativeRejected,
    Author,
    DecisionRecord,
    Resolves,
    Status,
)


class TestDecisionRecord:
    def test_minimal_valid_record(self) -> None:
        record = DecisionRecord(
            id="2025-04-25-001",
            status=Status.ACTIVE,
            date=date(2025, 4, 25),
            author=Author.HUMAN,
            domains=["auth"],
            decision="Use JWT for auth.",
            context="Need stateless auth.",
        )
        assert record.id == "2025-04-25-001"
        assert record.status == Status.ACTIVE
        assert record.parents == []
        assert record.tags == []

    def test_invalid_id_format(self) -> None:
        with pytest.raises(ValueError, match="YYYY-MM-DD-NNN"):
            DecisionRecord(
                id="bad-id",
                status=Status.ACTIVE,
                date=date(2025, 4, 25),
                author=Author.HUMAN,
                domains=["auth"],
                decision="Test.",
                context="Test.",
            )

    def test_date_must_match_id(self) -> None:
        with pytest.raises(ValueError, match="does not match"):
            DecisionRecord(
                id="2025-04-25-001",
                status=Status.ACTIVE,
                date=date(2025, 4, 26),
                author=Author.HUMAN,
                domains=["auth"],
                decision="Test.",
                context="Test.",
            )

    def test_domains_cannot_be_empty(self) -> None:
        with pytest.raises(ValueError):
            DecisionRecord(
                id="2025-04-25-001",
                status=Status.ACTIVE,
                date=date(2025, 4, 25),
                author=Author.HUMAN,
                domains=[],
                decision="Test.",
                context="Test.",
            )

    def test_decision_cannot_be_empty(self) -> None:
        with pytest.raises(ValueError):
            DecisionRecord(
                id="2025-04-25-001",
                status=Status.ACTIVE,
                date=date(2025, 4, 25),
                author=Author.HUMAN,
                domains=["auth"],
                decision="",
                context="Test.",
            )

    def test_whitespace_only_decision_rejected(self) -> None:
        with pytest.raises(ValueError):
            DecisionRecord(
                id="2025-04-25-001",
                status=Status.ACTIVE,
                date=date(2025, 4, 25),
                author=Author.HUMAN,
                domains=["auth"],
                decision="   \n  ",
                context="Test.",
            )

    def test_none_parents_coerced_to_empty_list(self) -> None:
        record = DecisionRecord.model_validate(
            {
                "id": "2025-04-25-001",
                "status": "active",
                "date": "2025-04-25",
                "author": "human",
                "domains": ["auth"],
                "decision": "Test.",
                "context": "Test.",
                "parents": None,
            }
        )
        assert record.parents == []

    def test_none_assumptions_coerced_to_empty_list(self) -> None:
        record = DecisionRecord.model_validate(
            {
                "id": "2025-04-25-001",
                "status": "active",
                "date": "2025-04-25",
                "author": "human",
                "domains": ["auth"],
                "decision": "Test.",
                "context": "Test.",
                "assumptions": None,
            }
        )
        assert record.assumptions == []

    def test_invalid_parent_id_format(self) -> None:
        with pytest.raises(ValueError, match="YYYY-MM-DD-NNN"):
            DecisionRecord(
                id="2025-04-25-001",
                status=Status.ACTIVE,
                date=date(2025, 4, 25),
                author=Author.HUMAN,
                domains=["auth"],
                decision="Test.",
                context="Test.",
                parents=["not-a-valid-id"],
            )

    def test_full_record_from_dict(self) -> None:
        data = {
            "id": "2025-04-25-001",
            "status": "active",
            "date": "2025-04-25",
            "author": "ai",
            "domains": ["auth", "identity"],
            "decision": "Use JWT with RS256.",
            "context": "Need stateless auth.",
            "parents": [],
            "alternatives_rejected": [
                {"option": "Session auth", "reason": "Doesn't scale"}
            ],
            "assumptions": ["Tokens are stateless"],
            "tensions": ["Mobile session handling"],
            "resolves": {"tension": "Single expiry", "from": "2025-04-20-001"},
            "tags": ["jwt", "auth"],
            "reviewed_by": "deepan",
        }
        record = DecisionRecord.model_validate(data)
        assert record.author == Author.AI
        assert record.resolves is not None
        assert record.resolves.from_id == "2025-04-20-001"
        assert record.tags == ["jwt", "auth"]
        assert record.reviewed_by == "deepan"
        assert len(record.alternatives_rejected) == 1

    def test_date_parsed_from_string(self) -> None:
        record = DecisionRecord.model_validate(
            {
                "id": "2025-04-25-001",
                "status": "active",
                "date": "2025-04-25",
                "author": "human",
                "domains": ["auth"],
                "decision": "Test.",
                "context": "Test.",
            }
        )
        assert record.date == date(2025, 4, 25)

    def test_date_accepted_as_date_object(self) -> None:
        record = DecisionRecord.model_validate(
            {
                "id": "2025-04-25-001",
                "status": "active",
                "date": date(2025, 4, 25),
                "author": "human",
                "domains": ["auth"],
                "decision": "Test.",
                "context": "Test.",
            }
        )
        assert record.date == date(2025, 4, 25)


class TestResolves:
    def test_valid_resolves(self) -> None:
        r = Resolves.model_validate(
            {"tension": "Expiry problem", "from": "2025-04-20-001"}
        )
        assert r.tension == "Expiry problem"
        assert r.from_id == "2025-04-20-001"

    def test_invalid_from_id(self) -> None:
        with pytest.raises(ValueError, match="YYYY-MM-DD-NNN"):
            Resolves.model_validate(
                {"tension": "Expiry problem", "from": "bad-ref"}
            )

    def test_accepts_field_name_and_alias(self) -> None:
        # alias "from" works
        r1 = Resolves.model_validate(
            {"tension": "T", "from": "2025-04-20-001"}
        )
        assert r1.from_id == "2025-04-20-001"

        # field name "from_id" also works (populate_by_name=True)
        r2 = Resolves.model_validate(
            {"tension": "T", "from_id": "2025-04-20-001"}
        )
        assert r2.from_id == "2025-04-20-001"


class TestAlternativeRejected:
    def test_valid(self) -> None:
        a = AlternativeRejected(option="Redis", reason="Too expensive")
        assert a.option == "Redis"
        assert a.reason == "Too expensive"
