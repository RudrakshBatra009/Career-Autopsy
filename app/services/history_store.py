from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Dict, Optional, Union

from sqlalchemy import DateTime, Integer, String, Text, create_engine, select
from sqlalchemy.orm import (
    Mapped,
    Session,
    declarative_base,
    mapped_column,
    sessionmaker,
)

from app.models.schemas import CareerAnalysisResponse, HistoryItem

Base = declarative_base()


class CareerAnalysisHistory(Base):
    __tablename__ = "career_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(200), index=True)
    job_title: Mapped[str] = mapped_column(String(200), index=True)
    years_of_experience: Mapped[int] = mapped_column(Integer)
    country: Mapped[str] = mapped_column(String(100))
    verdict: Mapped[str] = mapped_column(String(30), default="HIGH PLATEAU")
    payload_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )


class HistoryStore:
    def __init__(self, database_url: str) -> None:
        self.enabled = False
        self.init_error: Optional[str] = None
        self._session_factory: Optional[sessionmaker[Session]] = None

        try:
            normalized_url = self._normalize_db_url(database_url)
            engine = create_engine(
                normalized_url, future=True, pool_pre_ping=True
            )
            Base.metadata.create_all(engine)
            self._session_factory = sessionmaker(
                bind=engine, expire_on_commit=False
            )
            self.enabled = True
            self.init_error = None
        except Exception as exc:
            self.enabled = False
            self.init_error = str(exc)

    def save(
        self,
        job_title: str,
        years_of_experience: int,
        country: str,
        verdict: str,
        response: CareerAnalysisResponse,
    ) -> tuple[bool, Optional[str]]:
        if not self.enabled or self._session_factory is None:
            return False, self.init_error or "History store is disabled."

        slug = self.slugify(f"{job_title} {country} {years_of_experience}")
        payload = json.dumps(response.model_dump(mode="json"))

        try:
            with self._session_factory() as session:
                row = CareerAnalysisHistory(
                    slug=slug,
                    job_title=job_title[:200],
                    years_of_experience=years_of_experience,
                    country=country[:100],
                    verdict=verdict,
                    payload_json=payload,
                )
                session.add(row)
                session.commit()
            return True, None
        except Exception as exc:
            return False, str(exc)

    def list_recent(self, limit: int = 20) -> list[HistoryItem]:
        if not self.enabled or self._session_factory is None:
            return []

        try:
            with self._session_factory() as session:
                stmt = (
                    select(CareerAnalysisHistory)
                    .order_by(CareerAnalysisHistory.created_at.desc())
                    .limit(limit)
                )
                rows = session.execute(stmt).scalars().all()

            return [
                HistoryItem(
                    job_title=row.job_title,
                    years_of_experience=row.years_of_experience,
                    country=row.country,
                    slug=row.slug,
                    url=f"/{row.slug}",
                    verdict=row.verdict,
                    created_at=row.created_at.isoformat(),
                )
                for row in rows
            ]
        except Exception:
            return []

    def get_latest(self, slug: str) -> Optional[CareerAnalysisResponse]:
        if not self.enabled or self._session_factory is None:
            return None

        try:
            with self._session_factory() as session:
                stmt = (
                    select(CareerAnalysisHistory)
                    .where(CareerAnalysisHistory.slug == slug)
                    .order_by(CareerAnalysisHistory.created_at.desc())
                    .limit(1)
                )
                row = session.execute(stmt).scalars().first()

            if row is None:
                return None

            data = json.loads(row.payload_json)
            return CareerAnalysisResponse.model_validate(data)
        except Exception:
            return None

    def status(self) -> Dict[str, Union[Optional[str], bool]]:
        return {
            "enabled": self.enabled,
            "error": self.init_error,
        }

    @staticmethod
    def slugify(text: str) -> str:
        # Lowercase, replace non-alphanumeric with spaces, then squeeze spaces into dashes
        cleaned = re.sub(
            r"[^a-zA-Z0-9\s-]", "", (text or "").strip().lower()
        )
        compact = re.sub(r"[\s_-]+", "-", cleaned).strip("-")
        return (compact[:80]) or "career"

    @staticmethod
    def _normalize_db_url(url: str) -> str:
        value = (url or "").strip().strip('"').strip("'")
        if value.startswith("postgres://"):
            value = "postgresql://" + value[len("postgres://"):]
        if value.startswith("postgresql://") and "+" not in value.split("://", 1)[0]:
            return "postgresql+psycopg2://" + value[len("postgresql://"):]
        return value
