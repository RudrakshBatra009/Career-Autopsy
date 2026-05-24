from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class AnalyzeCareerRequest(BaseModel):
    job_title: str = Field(min_length=2, description="Your current or target job title")
    years_of_experience: int = Field(ge=0, le=60, description="Your years of experience in the field")
    country: str = Field(min_length=2, description="The country you work or plan to work in")
    current_stack: str = Field(min_length=2, description="Your current skill stack or tech tools you use")
    current_salary: Optional[str] = Field(None, description="Your current salary (optional)")
    work_hours_per_week: Optional[int] = Field(None, ge=0, le=168, description="Your average work hours per week (optional)")
    company_type: Optional[str] = Field(None, description="Your current company archetype (optional)")
    career_goals: Optional[str] = Field(None, description="Your career goals (optional)")


class CareerMetrics(BaseModel):
    salary_stagnation_probability: float = Field(ge=0.0, le=100.0)
    burnout_risk: float = Field(ge=0.0, le=100.0)
    automation_pressure: float = Field(ge=0.0, le=100.0)
    promotion_ceiling: float = Field(ge=0.0, le=100.0)
    industry_decline_exposure: float = Field(ge=0.0, le=100.0)


class CareerDashboard(BaseModel):
    career_peak_forecast: str  # e.g., "Your role peaks in 4 years"
    replacement_pressure: str  # e.g., "High replacement pressure"
    pivot_recommendation: str  # e.g., "Management pivot recommended"
    verdict: str  # "THRIVING" / "STABLE" / "HIGH PLATEAU" / "CRITICAL THREAT"
    verdict_emoji: str  # emoji representation
    metrics: CareerMetrics
    summary: str
    strengths: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    comparable_paths: list[str] = Field(default_factory=list)
    survival_tips: list[str] = Field(default_factory=list)
    detailed_report: str = ""


class CareerAnalysisResponse(BaseModel):
    mode: str = "gemini_career_autopsy"
    job_title: str
    years_of_experience: int
    country: str
    current_stack: str = ""
    current_salary: Optional[str] = None
    work_hours_per_week: Optional[int] = None
    company_type: Optional[str] = None
    career_goals: Optional[str] = None
    dashboard: CareerDashboard
    share_url: Optional[str] = None
    history_saved: bool = False
    history_error: Optional[str] = None


class HistoryItem(BaseModel):
    job_title: str
    years_of_experience: int
    country: str
    slug: str
    url: str
    verdict: str
    created_at: str
