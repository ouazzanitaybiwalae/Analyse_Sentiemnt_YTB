from typing import Dict, List
from pydantic import BaseModel, Field, field_validator


class BatchRequest(BaseModel):
    comments: List[str] = Field(..., min_length=1, max_length=1000, description="Raw comment texts")

    @field_validator("comments")
    @classmethod
    def no_huge_comment(cls, v: List[str]) -> List[str]:
        return [c[:5000] for c in v]  # truncate instead of failing the whole batch


class Prediction(BaseModel):
    index: int
    text: str
    label: int
    sentiment: str
    confidence: float


class Statistics(BaseModel):
    total: int
    counts: Dict[str, int]
    percentages: Dict[str, float]
    average_confidence: float


class BatchResponse(BaseModel):
    predictions: List[Prediction]
    statistics: Statistics
    processing_ms: float


class HealthResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    status: str
    model_loaded: bool
    version: str
