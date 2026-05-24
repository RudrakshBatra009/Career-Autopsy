from __future__ import annotations

import json
from typing import Optional

import httpx

from app.config import settings
from app.models.schemas import (
    CareerAnalysisResponse,
    CareerDashboard,
    CareerMetrics,
)


class GeminiEngine:
    """Calls Gemini AI to perform a career autopsy analysis."""

    def __init__(self) -> None:
        self.timeout = httpx.Timeout(60.0)

    def analyze_career(
        self,
        job_title: str,
        years_of_experience: int,
        country: str,
        current_stack: str,
        current_salary: Optional[str] = None,
        work_hours_per_week: Optional[int] = None,
        company_type: Optional[str] = None,
        career_goals: Optional[str] = None,
        resume_text: Optional[str] = None,
    ) -> CareerAnalysisResponse:
        if not self._is_configured(settings.gemini_api_key):
            return self._fallback_response(
                job_title,
                years_of_experience,
                country,
                "GEMINI_API_KEY is not configured.",
                current_stack,
                current_salary,
                work_hours_per_week,
                company_type,
                career_goals,
            )

        endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent"
            f"?key={settings.gemini_api_key}"
        )

        prompt = self._build_prompt(
            job_title=job_title,
            years_of_experience=years_of_experience,
            country=country,
            current_stack=current_stack,
            current_salary=current_salary,
            work_hours_per_week=work_hours_per_week,
            company_type=company_type,
            career_goals=career_goals,
            resume_text=resume_text,
        )

        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 4000,
                "responseMimeType": "application/json",
            },
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(endpoint, json=body)
                resp.raise_for_status()

            data = resp.json()
            text = self._extract_text(data)
            parsed = self._extract_json(text)

            if parsed is None:
                parsed = self._repair_json(text, endpoint)

            sanitized = self._sanitize(parsed)
            sanitized = self._ensure_non_empty(job_title, sanitized)

            dashboard = CareerDashboard.model_validate(sanitized)

            return CareerAnalysisResponse(
                job_title=job_title,
                years_of_experience=years_of_experience,
                country=country,
                current_stack=current_stack,
                current_salary=current_salary,
                work_hours_per_week=work_hours_per_week,
                company_type=company_type,
                career_goals=career_goals,
                dashboard=dashboard,
            )
        except Exception as exc:
            return self._fallback_response(
                job_title,
                years_of_experience,
                country,
                f"Analysis failed: {exc}",
                current_stack,
                current_salary,
                work_hours_per_week,
                company_type,
                career_goals,
            )


    def _build_prompt(
        self,
        job_title: str,
        years_of_experience: int,
        country: str,
        current_stack: str,
        current_salary: Optional[str] = None,
        work_hours_per_week: Optional[int] = None,
        company_type: Optional[str] = None,
        career_goals: Optional[str] = None,
        resume_text: Optional[str] = None,
    ) -> str:
        return f"""You are an elite career strategist, corporate anthropologist, and tech industry workforce analyst.
Your job is to perform a BRUTALLY HONEST, realistic career diagnostic (Autopsy) of why a user's career trajectory might fail, plateau, or face severe disruption.

=== CAREER INPUT ===
Job Title: {job_title}
Years of Experience: {years_of_experience}
Country: {country}
Current Stack/Skills: {current_stack}
Current Salary: {current_salary or 'Not provided'}
Work Hours/Week: {work_hours_per_week or 'Not provided'}
Company Type: {company_type or 'Not provided'}
Career Goals: {career_goals or 'Not provided'}
Resume/Background Details (Optional): {resume_text or 'Not provided'}
====================

Evaluate this career trajectory deeply. Ground your analysis in actual market data, tech displacement trends, salary tables, and local economic realities for the specified country.

Specifically incorporate these details to make the autopsy hyper-personalized:
1. Salary Audit: If a salary is provided, evaluate whether they are currently underpaid or overpaid compared to market rates in their country, and assess how it affects their stagnation odds.
2. Burnout Valuation: Use their weekly work hours to evaluate workload stress (e.g. over 45 hours greatly spikes burnout risk).
3. Company Archetype Bottlenecks: Analyze risks specific to their company type (e.g., startup volatility vs. enterprise red tape vs. consultancy fatigue).
4. Goal Feasibility & Trajectory: Target your recommendations and comparable paths specifically to help them achieve their stated career goals (e.g., transition to management vs. deep tech specialization), evaluating if their current skills support it.
5. Resume Experience Analysis: If resume text is provided, analyze their career history (tenure gaps, employer changes, credential level) to identify hidden vulnerabilities or strengths.


Scoring guidelines (All metrics are 0-100 where higher is MORE dangerous/worse):
- salary_stagnation_probability: Risk of pay flattening in the next 3-5 years due to skills becoming commoditized or lack of advancement.
- burnout_risk: Risk of stress/overwork. Look at typical demands for this role and stack.
- automation_pressure: Risk of AI, LLMs, or software automating major parts of this role.
- promotion_ceiling: Level of difficulty in rising to principal/staff/management levels.
- industry_decline_exposure: Macroeconomic exposure of this role/industry to shrinking budgets or obsolescence.

Verdict rules (Determine based on the severity of the risks analyzed):
- If risk metrics are low (average < 35) → "THRIVING" (emoji: 🚀)
- If risks are moderate (average < 55) → "STABLE" (emoji: ✅)
- If risks are high (average < 75) → "HIGH PLATEAU" (emoji: ⚠️)
- If risks are extreme (average >= 75) → "CRITICAL THREAT" (emoji: 💀)

Key Output Fields required:
- career_peak_forecast: A short punchy statement forecasting when this career peaks or plateaus (e.g., "Your role peaks in 4 years", "Your career has plateaued", "Your role peaks in 2 years").
- replacement_pressure: A short label of automation/offshoring pressure (e.g., "High replacement pressure", "Moderate replacement pressure", "Low replacement pressure").
- pivot_recommendation: A short recommendation for their next major career pivot (e.g., "Management pivot recommended", "Systems Architecture transition recommended", "Domain specialization required").

JSON schema (Return ONLY this JSON structure, no markdown code blocks, no trailing comments, no extra text):
{{
  "career_peak_forecast": "<Punchy forecast, e.g. 'Your role peaks in 4 years'>",
  "replacement_pressure": "<Label, e.g. 'High replacement pressure'>",
  "pivot_recommendation": "<Label, e.g. 'Management pivot recommended'>",
  "verdict": "<THRIVING | STABLE | HIGH PLATEAU | CRITICAL THREAT>",
  "verdict_emoji": "<emoji>",
  "metrics": {{
    "salary_stagnation_probability": <number 0-100>,
    "burnout_risk": <number 0-100>,
    "automation_pressure": <number 0-100>,
    "promotion_ceiling": <number 0-100>,
    "industry_decline_exposure": <number 0-100>
  }},
  "summary": "<2-3 sentence executive summary explaining the career prognosis>",
  "strengths": ["<3-5 positive assets/skills in their profile that keep them relevant>"],
  "red_flags": ["<3-5 critical warnings about their stack, country market, or career trajectory>"],
  "recommendations": ["<3-5 highly specific, actionable career adjustments or training actions>"],
  "comparable_paths": ["<3-5 real career trajectories/examples showing what happens to people in this role, be specific>"],
  "survival_tips": ["<3-5 concrete anti-stagnation or anti-burnout hacks tailored to this profile>"],
  "detailed_report": "<A punchy, forensic 1-2 paragraph analysis summarizing why this career path is plateauing or failing. Be specific about their tech stack, experience level, and country constraints. Keep the response under 150 words.>"
}}""".strip()

    def _extract_text(self, payload: dict) -> str:
        candidates = payload.get("candidates", [])
        if not candidates:
            raise ValueError("No candidates in Gemini response")
        parts = candidates[0].get("content", {}).get("parts", [])
        text = "\n".join(
            str(part.get("text", "")).strip()
            for part in parts
            if part.get("text")
        )
        if not text.strip():
            raise ValueError("Gemini returned empty text")
        return text

    def _extract_json(self, raw_text: str) -> Optional[dict]:
        text = raw_text.strip()
        if not text:
            return None
        try:
            obj = json.loads(text)
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass

        start = raw_text.find("{")
        end = raw_text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        try:
            return json.loads(raw_text[start : end + 1])
        except Exception:
            return None

    def _repair_json(self, raw_text: str, endpoint: str) -> dict:
        repair_prompt = (
            "Convert the following content into a valid JSON object matching the Career Autopsy schema. "
            "Return JSON only, no markdown. All numeric fields must be numbers 0-100.\n\n"
            f"CONTENT:\n{raw_text}"
        )
        body = {
            "contents": [{"parts": [{"text": repair_prompt}]}],
            "generationConfig": {
                "temperature": 0.0,
                "maxOutputTokens": 3000,
                "responseMimeType": "application/json",
            },
        }
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(endpoint, json=body)
            resp.raise_for_status()
        repaired_text = self._extract_text(resp.json())
        repaired = self._extract_json(repaired_text)
        if repaired is None:
            raise ValueError("JSON repair failed")
        return repaired

    def _sanitize(self, raw: dict) -> dict:
        metrics_raw = raw.get("metrics", {}) if isinstance(raw.get("metrics"), dict) else {}
        return {
            "career_peak_forecast": str(raw.get("career_peak_forecast") or "Prognosis uncertain"),
            "replacement_pressure": str(raw.get("replacement_pressure") or "Moderate replacement pressure"),
            "pivot_recommendation": str(raw.get("pivot_recommendation") or "Pivot trajectory recommended"),
            "verdict": str(raw.get("verdict") or "HIGH PLATEAU"),
            "verdict_emoji": str(raw.get("verdict_emoji") or "⚠️"),
            "metrics": {
                "salary_stagnation_probability": self._clamp(metrics_raw.get("salary_stagnation_probability")),
                "burnout_risk": self._clamp(metrics_raw.get("burnout_risk")),
                "automation_pressure": self._clamp(metrics_raw.get("automation_pressure")),
                "promotion_ceiling": self._clamp(metrics_raw.get("promotion_ceiling")),
                "industry_decline_exposure": self._clamp(metrics_raw.get("industry_decline_exposure")),
            },
            "summary": str(raw.get("summary") or ""),
            "strengths": self._to_str_list(raw.get("strengths")),
            "red_flags": self._to_str_list(raw.get("red_flags")),
            "recommendations": self._to_str_list(raw.get("recommendations")),
            "comparable_paths": self._to_str_list(raw.get("comparable_paths") or raw.get("comparable_projects")),
            "survival_tips": self._to_str_list(raw.get("survival_tips")),
            "detailed_report": str(raw.get("detailed_report") or ""),
        }

    def _clamp(self, value: object, default: float = 50.0) -> float:
        if value is None:
            return default
        if isinstance(value, (int, float)):
            return max(0.0, min(100.0, float(value)))
        if isinstance(value, str):
            cleaned = value.strip().replace("%", "").strip()
            try:
                return max(0.0, min(100.0, float(cleaned)))
            except Exception:
                return default
        return default

    def _to_str_list(self, value: object) -> list[str]:
        if isinstance(value, list):
            return [str(v).strip() for v in value if str(v).strip()]
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        return []

    def _ensure_non_empty(self, job_title: str, dashboard: dict) -> dict:
        if not dashboard.get("summary"):
            dashboard["summary"] = f"Career analysis for '{job_title}' — review core risk vectors below to identify key failure modes."

        if not dashboard.get("strengths"):
            dashboard["strengths"] = [
                "Profile exhibits foundational specialized skills.",
                "Stated experience provides a buffer against immediate redundancy.",
                "Awareness of skill durability allows for preemptive career course correction.",
            ]

        if not dashboard.get("red_flags"):
            dashboard["red_flags"] = [
                "Market salary stagnation patterns detected in this stack/role segment.",
                "High dependency on transactional technical execution rather than business strategy.",
                "Pace of AI automation threatens to absorb routine codegen or documentation work.",
            ]

        if not dashboard.get("recommendations"):
            dashboard["recommendations"] = [
                "Begin moving from syntax/tool execution to product management or high-level architecture.",
                "Diversify skill stack to include domain-specific system integration.",
                "Establish concrete limits on work hours to address high burnout indicators.",
            ]

        if not dashboard.get("survival_tips"):
            dashboard["survival_tips"] = [
                "Focus on building deep organizational leverage rather than just writing clean code.",
                "Regularly audit local market salary trends and negotiate adjustments preemptively.",
                "Dedicate 10% of weekly effort to learning adjacent non-automatable skills.",
            ]

        report = str(dashboard.get("detailed_report", "")).strip()
        if len(report) < 50:
            dashboard["detailed_report"] = (
                f"Career Diagnosis: {dashboard.get('summary', '')}\n\n"
                f"This autopsy indicates a salary stagnation risk of {dashboard.get('metrics', {}).get('salary_stagnation_probability', 50):.0f}% "
                f"and an automation pressure rating of {dashboard.get('metrics', {}).get('automation_pressure', 50):.0f}%. "
                "The analysis factors in stack decay rates, regional constraints, and promotion dynamics.\n\n"
                "To optimize trajectory health, we strongly recommend implementing the recommended pivots immediately."
            )

        return dashboard

    def _fallback_response(
        self,
        job_title: str,
        years_of_experience: int,
        country: str,
        reason: str,
        current_stack: str = "",
        current_salary: Optional[str] = None,
        work_hours_per_week: Optional[int] = None,
        company_type: Optional[str] = None,
        career_goals: Optional[str] = None,
    ) -> CareerAnalysisResponse:
        dashboard = CareerDashboard(
            career_peak_forecast="Prognosis Unavailable",
            replacement_pressure="Error in analysis pipeline",
            pivot_recommendation="Retry recommended",
            verdict="HIGH PLATEAU",
            verdict_emoji="⚠️",
            metrics=CareerMetrics(
                salary_stagnation_probability=50.0,
                burnout_risk=50.0,
                automation_pressure=50.0,
                promotion_ceiling=50.0,
                industry_decline_exposure=50.0,
            ),
            summary=f"Unable to generate career autopsy. {reason}",
            strengths=[],
            red_flags=[reason],
            recommendations=["Please try again. Verify API configuration and network connectivity."],
            comparable_paths=[],
            survival_tips=[],
            detailed_report=f"Career trajectory analysis failed to execute. {reason}",
        )
        return CareerAnalysisResponse(
            job_title=job_title,
            years_of_experience=years_of_experience,
            country=country,
            current_stack=current_stack,
            current_salary=current_salary,
            work_hours_per_week=work_hours_per_week,
            company_type=company_type,
            career_goals=career_goals,
            dashboard=dashboard,
        )


    def _is_configured(self, value: str) -> bool:
        v = (value or "").strip()
        if not v:
            return False
        lower = v.lower()
        return not any(
            token in lower
            for token in ("your_", "placeholder", "changeme", "example")
        )
