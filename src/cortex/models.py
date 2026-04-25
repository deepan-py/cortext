"""Pydantic models for Cortex decision records."""

from __future__ import annotations

import re
from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ID_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{3}$")


class Status(str, Enum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"


class Author(str, Enum):
    HUMAN = "human"
    AI = "ai"


class AIPlatform(str, Enum):
    COPILOT = "copilot"
    CLAUDE = "claude"


class AlternativeRejected(BaseModel):
    """A rejected alternative considered during decision-making."""

    option: str
    reason: str


class Resolves(BaseModel):
    """Reference to a tension that this decision resolves."""

    model_config = ConfigDict(populate_by_name=True)

    tension: str
    from_id: str = Field(alias="from")

    @field_validator("from_id")
    @classmethod
    def validate_from_id_format(cls, v: str) -> str:
        if not ID_PATTERN.match(v):
            raise ValueError(f"Must match YYYY-MM-DD-NNN format, got '{v}'")
        return v


class DecisionRecord(BaseModel):
    """A single architectural decision record."""

    model_config = ConfigDict(populate_by_name=True)

    # Required
    id: str
    status: Status
    date: date
    author: Author
    domains: list[str] = Field(min_length=1)
    decision: str = Field(min_length=1)
    context: str = Field(min_length=1)

    # Recommended
    parents: list[str] = Field(default_factory=list)
    alternatives_rejected: list[AlternativeRejected] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    tensions: list[str] = Field(default_factory=list)
    resolves: Optional[Resolves] = None
    tags: list[str] = Field(default_factory=list)

    # Optional
    reviewed_by: Optional[str] = None

    @field_validator(
        "parents",
        "alternatives_rejected",
        "assumptions",
        "tensions",
        "tags",
        mode="before",
    )
    @classmethod
    def coerce_none_to_list(cls, v: object) -> object:
        if v is None:
            return []
        return v

    @field_validator("decision", "context", mode="before")
    @classmethod
    def strip_text_fields(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("id")
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        if not ID_PATTERN.match(v):
            raise ValueError(f"ID must match YYYY-MM-DD-NNN format, got '{v}'")
        return v

    @field_validator("parents")
    @classmethod
    def validate_parent_id_formats(cls, v: list[str]) -> list[str]:
        for parent_id in v:
            if not ID_PATTERN.match(parent_id):
                raise ValueError(
                    f"Parent ID must match YYYY-MM-DD-NNN format, got '{parent_id}'"
                )
        return v

    @model_validator(mode="after")
    def validate_date_matches_id(self) -> DecisionRecord:
        id_date_str = self.id[:10]
        record_date_str = self.date.isoformat()
        if id_date_str != record_date_str:
            raise ValueError(
                f"Date in ID ({id_date_str}) does not match date field ({record_date_str})"
            )
        return self
