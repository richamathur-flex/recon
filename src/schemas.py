"""Pydantic schemas for agent inputs and outputs."""

from pydantic import BaseModel, Field


class CompanyProfile(BaseModel):
    """Output of the Web Intelligence Agent."""

    company_name: str = Field(description="The company being analyzed")

    value_proposition: str = Field(
        description="One-sentence description of what the company does and for whom"
    )

    target_customer: str = Field(
        description="Who their primary customer segment is"
    )

    key_features: list[str] = Field(
        description="3-5 bullet points of their main product features",
        max_length=5,
    )

    positioning_keywords: list[str] = Field(
        description="3-5 keywords they use to describe themselves",
        max_length=5,
    )

    source_url: str = Field(
        description="The URL the data was extracted from"
    )


class HiringSnapshot(BaseModel):
    """Output of the Hiring Signals Agent."""

    company_name: str
    total_openings: int

    top_departments: list[str] = Field(
        default_factory=list,
        max_length=5,
    )

    key_skills: list[str] = Field(
        default_factory=list,
        max_length=8,
    )

    strategic_signal: str

    locations: list[str] = Field(
        default_factory=list,
        max_length=5,
    )

    source: str = Field(
        description="Where jobs were sourced: greenhouse, lever, none"
    )