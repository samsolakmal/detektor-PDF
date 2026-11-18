import os
from datetime import datetime
from functools import lru_cache
from uuid import uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    JSON,
    String,
    create_engine,
    func,
    select,
    text,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    """Base metadata for Alembic and SQLAlchemy models."""

    pass


# Persistent, privacy-minimized history shown on the Streamlit history tab.
class AnalysisRecord(Base):
    __tablename__ = "analysis_records"
    __table_args__ = (
        CheckConstraint(
            "document_type IN ('pdf', 'docx')", name="ck_analysis_document_type"
        ),
        CheckConstraint("score BETWEEN 0 AND 100", name="ck_analysis_score_range"),
        CheckConstraint("word_count >= 0", name="ck_analysis_word_count"),
        Index("ix_analysis_records_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    document_type: Mapped[str] = mapped_column(String(10), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False)
    findings: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


def build_engine(database_url: str) -> Engine:
    """Create an engine with lightweight SQLite test support or pooled PostgreSQL."""
    if database_url.startswith("sqlite"):
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,
        )
    return create_engine(
        database_url,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=1800,
        pool_pre_ping=True,
    )


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Read and validate the PostgreSQL URL once per application process."""
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise ValueError(
            "DATABASE_URL belum diatur. Ikuti petunjuk di README.md untuk menjalankan PostgreSQL."
        )
    if not database_url.startswith(("postgresql://", "postgresql+psycopg://")):
        raise ValueError("DATABASE_URL harus menunjuk ke database PostgreSQL.")
    return build_engine(database_url)


def check_database(engine: Engine | None = None) -> None:
    """Fail early if PostgreSQL cannot answer a basic health query."""
    db_engine = engine or get_engine()
    with db_engine.connect() as connection:
        connection.execute(select(1))


def get_database_overview(engine: Engine | None = None) -> dict[str, object]:
    """Return PostgreSQL database and pgvector status for the in-app database page."""
    db_engine = engine or get_engine()
    if db_engine.dialect.name != "postgresql":
        return {
            "database": db_engine.url.database or "Tidak diketahui",
            "server": f"{db_engine.dialect.name} (mode pengujian)",
            "pgvector": "Tidak berlaku untuk SQLite",
        }

    with db_engine.connect() as connection:
        database_name, server_version = connection.execute(
            text("SELECT current_database(), version()")
        ).one()
        vector_version = connection.execute(
            text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
        ).scalar_one_or_none()

    return {
        "database": database_name,
        "server": server_version.splitlines()[0],
        "pgvector": f"Aktif (versi {vector_version})" if vector_version else "Belum aktif",
    }


def list_database_records(
    limit: int = 100, engine: Engine | None = None
) -> tuple[int, list[dict[str, object]]]:
    """Read actual stored rows for the database page, bounded to the newest records."""
    db_engine = engine or get_engine()
    with sessionmaker(bind=db_engine)() as session:
        total = session.scalar(select(func.count(AnalysisRecord.id))) or 0
        records = session.scalars(
            select(AnalysisRecord)
            .order_by(AnalysisRecord.created_at.desc())
            .limit(limit)
        ).all()
    rows = [
        {
            "ID lengkap": record.id,
            "Waktu dibuat": record.created_at,
            "Jenis file": record.document_type.upper(),
            "Skor": record.score,
            "Jumlah halaman": record.page_count,
            "Jumlah kata": record.word_count,
            "Rincian indikator": record.findings,
        }
        for record in records
    ]
    return total, rows


def save_analysis(
    document_type: str,
    page_count: int | None,
    findings: dict,
    engine: Engine | None = None,
) -> str:
    """Persist summary metrics and indicator counts without document text."""
    db_engine = engine or get_engine()
    stored_findings = dict(findings)
    list_matches = stored_findings.pop("list_matches", [])
    stored_findings["list_match_count"] = len(list_matches)
    record = AnalysisRecord(
        document_type=document_type,
        score=findings["total_score"],
        page_count=page_count,
        word_count=findings["word_count"],
        findings=stored_findings,
    )
    with sessionmaker(bind=db_engine)() as session:
        session.add(record)
        session.commit()
        return record.id


def list_recent_analyses(
    limit: int = 50, engine: Engine | None = None
) -> tuple[int, float | None, list[dict]]:
    """Return dashboard totals and a bounded list of recent findings."""
    db_engine = engine or get_engine()
    with sessionmaker(bind=db_engine)() as session:
        total, average = session.execute(
            select(func.count(AnalysisRecord.id), func.avg(AnalysisRecord.score))
        ).one()
        records = session.scalars(
            select(AnalysisRecord)
            .order_by(AnalysisRecord.created_at.desc())
            .limit(limit)
        ).all()
        history = [
            {
                "ID": record.id[:8],
                "Waktu": record.created_at,
                "Format": record.document_type.upper(),
                "Skor": record.score,
                "Halaman": record.page_count if record.page_count is not None else "—",
                "Kata": record.word_count,
                "Temuan": record.findings,
            }
            for record in records
        ]
    return total, float(average) if average is not None else None, history
