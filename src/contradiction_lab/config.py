import json
import os
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from .schemas import Contract


class Settings(Contract):
    source: Literal["corpus", "live"] = "corpus"
    model_backend: Literal["ollama"] = "ollama"
    runtime: Literal["langgraph"] = "langgraph"
    vector_backend: Literal["chroma"] = "chroma"
    embedding_backend: Literal["ollama"] = "ollama"
    embedding_model: str = "nomic-embed-text"
    max_papers: int = Field(default=6, ge=1, le=50)
    top_k: int = Field(default=8, ge=1, le=50)
    chunk_size_tokens: int = Field(default=550, ge=20)
    chunk_overlap_tokens: int = Field(default=75, ge=0)
    max_iterations: int = Field(default=2, ge=0, le=5)
    min_claims: int = Field(default=2, ge=1)
    min_comparable_pairs: int = Field(default=1, ge=1)
    max_structured_output_repairs: int = Field(default=1, ge=0, le=2)
    context_tokens: int = Field(default=6000, ge=100)
    request_timeout: float = Field(default=180, gt=0)
    max_retries: int = Field(default=2, ge=0, le=4)
    max_claims_per_paper: int = Field(default=3, ge=1, le=10)
    max_comparisons: int = Field(default=15, ge=1, le=100)
    context_config: Literal["compact", "evidence-rich"] = "evidence-rich"
    data_dir: Path = Field(default_factory=lambda: Path(os.getenv("LAB_DATA_DIR", ".runtime")))

    discovery_min_similarity: float = Field(default=0.45, ge=0, le=1)
    ollama_model: str = "qwen2.5:7b"

    @model_validator(mode="after")
    def validate_combination(self):
        if self.chunk_overlap_tokens >= self.chunk_size_tokens:
            raise ValueError("overlap must be smaller than chunk size")
        return self

    @classmethod
    def load(cls, path: str | Path | None = None, **overrides):
        values = json.loads(Path(path).read_text()) if path else {}
        values.update({key: value for key, value in overrides.items() if value is not None})
        return cls.model_validate(values)
