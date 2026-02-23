from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from common import XmlPair, TestResult
from agent import TesterAgent

app = FastAPI(title="Tester Service", version="1.0.0")
agent = TesterAgent()


class TestRequest(BaseModel):
    code: str
    xml_pairs: list[XmlPair]


@app.post("/test", response_model=TestResult)
async def test_code(request: TestRequest) -> TestResult:
    """Execute generated code against XML pairs and validate results."""
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="Code must not be empty")
    if not request.xml_pairs:
        raise HTTPException(status_code=400, detail="At least one XML pair is required")

    result = await agent.test_code(request.code, request.xml_pairs)
    return result


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "service": "tester"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)
