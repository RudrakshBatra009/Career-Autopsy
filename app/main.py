from __future__ import annotations

import io
from typing import Dict, Optional, Union

from fastapi import FastAPI, HTTPException, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

try:
    import pypdf
except ImportError:
    pypdf = None

from app.config import settings
from app.models.schemas import (
    AnalyzeCareerRequest,
    HistoryItem,
    CareerAnalysisResponse,
)
from app.services.gemini_engine import GeminiEngine
from app.services.history_store import HistoryStore

app = FastAPI(
    title="Career Autopsy",
    description="AI-powered analyzer: Why careers silently fail.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

gemini_engine = GeminiEngine()
history_store = HistoryStore(settings.database_url)


def extract_resume_text(file_bytes: bytes, filename: str) -> str:
    filename_lower = filename.lower()
    if filename_lower.endswith(".txt"):
        try:
            return file_bytes.decode("utf-8", errors="ignore")
        except Exception:
            return ""
    elif filename_lower.endswith(".pdf"):
        if pypdf is None:
            return "[Error: pypdf not installed. Could not extract PDF.]"
        try:
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            text = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
            return "\n".join(text)
        except Exception as e:
            return f"[Error parsing PDF: {e}]"
    else:
        try:
            return file_bytes.decode("utf-8", errors="ignore")
        except Exception:
            return ""


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "gemini_configured": "true" if settings.gemini_api_key else "false",
        "history_enabled": "true" if history_store.enabled else "false",
    }


@app.get("/", response_class=HTMLResponse)
def root(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api")
def api_info() -> dict[str, str]:
    return {
        "message": "Career Autopsy API is running.",
        "swagger_ui": "/docs",
        "redoc": "/redoc",
    }


@app.get("/api/history/status")
def history_status() -> Dict[str, Union[str, bool, None]]:
    return history_store.status()


@app.post("/analyze", response_model=CareerAnalysisResponse)
async def analyze_career(
    job_title: str = Form(...),
    years_of_experience: int = Form(...),
    country: str = Form(...),
    current_stack: str = Form(...),
    current_salary: Optional[str] = Form(None),
    work_hours_per_week: Optional[int] = Form(None),
    company_type: Optional[str] = Form(None),
    career_goals: Optional[str] = Form(None),
    resume_file: Optional[UploadFile] = File(None),
) -> CareerAnalysisResponse:
    resume_text = None
    if resume_file and resume_file.filename:
        try:
            file_bytes = await resume_file.read()
            if file_bytes:
                resume_text = extract_resume_text(file_bytes, resume_file.filename)
                if resume_text and len(resume_text) > 3000:
                    resume_text = resume_text[:3000] + "\n... [resume truncated to save tokens] ..."
        except Exception as e:
            resume_text = f"[Failed to read uploaded file: {e}]"

    response = gemini_engine.analyze_career(
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

    saved, save_error = history_store.save(
        job_title=response.job_title,
        years_of_experience=response.years_of_experience,
        country=response.country,
        verdict=response.dashboard.verdict,
        response=response,
    )

    slug = history_store.slugify(f"{response.job_title} {response.country} {response.years_of_experience}")
    response.share_url = f"/{slug}"
    response.history_saved = saved
    response.history_error = save_error

    return response


@app.get("/api/history", response_model=list[HistoryItem])
def get_history() -> list[HistoryItem]:
    return history_store.list_recent(limit=30)


@app.get("/api/history/{project_slug}", response_model=CareerAnalysisResponse)
def get_history_item(project_slug: str) -> CareerAnalysisResponse:
    item = history_store.get_latest(project_slug)
    if item is None:
        raise HTTPException(
            status_code=404,
            detail="No saved analysis found for this career path.",
        )
    item.share_url = f"/{project_slug}"
    item.history_saved = True
    item.history_error = None
    return item


@app.get("/{project_slug}", response_class=HTMLResponse)
def project_page(request: Request, project_slug: str) -> HTMLResponse:
    # Just serve the home page index; javascript will parse the pathname and fetch the data
    return templates.TemplateResponse("index.html", {"request": request})
