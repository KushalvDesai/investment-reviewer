from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field


# ── Ingest ────────────────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    month_key: str
    chunks_indexed: int
    namespace: str


class MonthsResponse(BaseModel):
    months: list[str]


class DeleteMonthResponse(BaseModel):
    deleted: bool
    month_key: str


# ── Query ─────────────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    month_key: str
    question: str


class KeyTransaction(BaseModel):
    description: str
    amount: float


class SingleMonthAnalysis(BaseModel):
    summary: str
    total_income: float
    total_expenses: float
    net_pnl: float
    key_transactions: list[KeyTransaction] = Field(default_factory=list)
    insights: list[str] = Field(default_factory=list)


class ChangeMetric(BaseModel):
    amount: float
    percent: float
    direction: str  # "up" | "down" | "unchanged"


class CompareRequest(BaseModel):
    current_month: str
    previous_month: str


class MonthComparisonResult(BaseModel):
    current_month: str
    previous_month: str
    income_change: ChangeMetric
    expense_change: ChangeMetric
    net_pnl_change: ChangeMetric
    highlights: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class AskRequest(BaseModel):
    question: str
    months: list[str]


class SourceChunk(BaseModel):
    month_key: str
    chunk_preview: str


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceChunk] = Field(default_factory=list)


# ── Health ────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    pinecone_namespaces: list[str]


# ── Error ─────────────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    error: str
    message: str
