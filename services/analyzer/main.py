"""Analyzer Service - Discovers XML transformation rules using LLM analysis."""

from __future__ import annotations

import logging
import os
import sys
import traceback

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from common import AnalysisResult, LLMClient, XmlPair
from agent import AnalyzerAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Analyzer Service",
    description="Analyzes XML input/output pairs to discover transformation rules.",
    version="1.0.0",
)

llm_client = LLMClient()
agent = AnalyzerAgent(llm_client)


class AnalyzeRequest(BaseModel):
    xml_pairs: list[XmlPair]
    feedback: str = ""


@app.post("/analyze", response_model=AnalysisResult)
async def analyze(request: AnalyzeRequest) -> AnalysisResult:
    """Analyze XML input/output pairs and return discovered transformation rules."""
    if not request.xml_pairs:
        raise HTTPException(status_code=400, detail="At least one XML pair is required.")

    # Check API key
    provider = os.getenv("LLM_PROVIDER", "claude")
    if provider == "claude":
        key = os.getenv("ANTHROPIC_API_KEY", "")
        if not key or key.startswith("your-"):
            raise HTTPException(
                status_code=500,
                detail="ANTHROPIC_API_KEY가 설정되지 않았습니다. .env 파일에 실제 API 키를 입력해주세요.",
            )
    else:
        key = os.getenv("OPENAI_API_KEY", "")
        if not key or key.startswith("your-"):
            raise HTTPException(
                status_code=500,
                detail="OPENAI_API_KEY가 설정되지 않았습니다. .env 파일에 실제 API 키를 입력해주세요.",
            )

    try:
        result = await agent.analyze(request.xml_pairs, feedback=request.feedback)
        return result
    except Exception as e:
        logger.error("Analysis failed: %s\n%s", e, traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "analyzer"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
