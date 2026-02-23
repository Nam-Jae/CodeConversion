"""Generator Service - Generates Python transformation code from analysis rules."""

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

from common import AnalysisResult, GeneratedCode, LLMClient, XmlPair
from agent import GeneratorAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Generator Service",
    description="Generates Python transformation code from XML analysis rules.",
    version="1.0.0",
)

llm_client = LLMClient()
agent = GeneratorAgent(llm_client)


class GenerateRequest(BaseModel):
    analysis: AnalysisResult
    xml_pairs: list[XmlPair]
    feedback: str = ""


@app.post("/generate", response_model=GeneratedCode)
async def generate(request: GenerateRequest) -> GeneratedCode:
    """Generate Python transformation code from analysis rules and XML pairs."""
    if not request.analysis.field_mappings and not request.analysis.transformation_rules:
        raise HTTPException(
            status_code=400,
            detail="Analysis must contain at least one field mapping or transformation rule.",
        )
    try:
        result = await agent.generate(
            analysis=request.analysis,
            xml_pairs=request.xml_pairs,
            feedback=request.feedback,
        )
        return result
    except Exception as e:
        logger.error("Code generation failed: %s\n%s", e, traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Code generation failed: {e}")


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "generator"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
