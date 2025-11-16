from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime, String, UniqueConstraint


class ReasonerAccuracy(SQLModel, table=True):
    __tablename__ = "reasoner_accuracy"
    __table_args__ = (UniqueConstraint("technique", name="uq_reasoner_accuracy_technique"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    technique: str = Field(
        sa_column=Column(String(length=64), nullable=False, unique=True, index=True)
    )
    sample_size: int = Field(nullable=False)
    success_count: int = Field(nullable=False)
    accuracy: float = Field(nullable=False)
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=False), default=datetime.utcnow, nullable=False)
    )
