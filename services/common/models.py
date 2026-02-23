from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class XmlPair(BaseModel):
    input_xml: str
    output_xml: str
    pair_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])


class FieldMapping(BaseModel):
    source_path: str
    target_path: str
    mapping_type: str  # "1:1", "1:N", "N:1", "constant"
    description: str = ""


class TransformationRule(BaseModel):
    rule_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    rule_type: str  # "field_mapping", "value_transform", "conditional", "aggregation", "constant", "sort"
    description: str
    details: dict[str, Any] = {}


class AnalysisResult(BaseModel):
    field_mappings: list[FieldMapping] = []
    transformation_rules: list[TransformationRule] = []
    input_schema_summary: str = ""
    output_schema_summary: str = ""
    notes: str = ""


class GeneratedCode(BaseModel):
    code: str
    language: str = "python"
    description: str = ""
    iteration: int = 1


class TestDetail(BaseModel):
    pair_id: str
    passed: bool
    expected_snippet: str = ""
    actual_snippet: str = ""
    diff: str = ""


class TestResult(BaseModel):
    total_pairs: int
    passed_pairs: int
    accuracy: float
    details: list[TestDetail] = []
    error_message: str = ""


class JobStatus(str, Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    GENERATING = "generating"
    TESTING = "testing"
    ITERATING = "iterating"
    COMPLETED = "completed"
    FAILED = "failed"


class ConversionJob(BaseModel):
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    xml_pairs: list[XmlPair] = []
    analysis: AnalysisResult | None = None
    generated_code: GeneratedCode | None = None
    test_result: TestResult | None = None
    current_iteration: int = 0
    max_iterations: int = 5
    accuracy_threshold: float = 0.95
    message: str = ""
