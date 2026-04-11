"""Response schemas."""
from pydantic import BaseModel
from datetime import datetime


class JobResponse(BaseModel):
    id: str
    filename: str
    status: str
    error_message: str | None = None
    node_count: int = 0
    edge_count: int = 0
    user_persona_count: int = 0
    adversarial_persona_count: int = 0
    created_at: datetime | None = None


class UploadResponse(BaseModel):
    job_id: str
    message: str


class CoverageEntry(BaseModel):
    taxonomy_id: str
    name: str
    category: str
    description: str
    team: str
    owasp_mapping: str | None = None
    status: str  # covered, partial, missing
    covered_by: list[str] = []
    coverage_count: int = 0


class CoverageResponse(BaseModel):
    total: int
    covered: int
    partial: int
    missing: int
    coverage_percentage: float
    entries: list[CoverageEntry]
