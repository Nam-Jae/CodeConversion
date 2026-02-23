"""
Gateway + Orchestrator Service
==============================
Main API gateway that orchestrates the multi-agent XML conversion workflow.
Runs on port 8000 and coordinates calls to the Analyzer, Generator, and Tester
services through an iterative refinement loop.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from common import ConversionJob, JobStatus, XmlPair
from orchestrator import Orchestrator

app = FastAPI(title="XML Conversion Gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# In-memory job store
# ---------------------------------------------------------------------------
jobs: dict[str, ConversionJob] = {}

# ---------------------------------------------------------------------------
# Orchestrator (lazily created so env vars are read at request time)
# ---------------------------------------------------------------------------
_orchestrator: Orchestrator | None = None


def _get_orchestrator() -> Orchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator(
            analyzer_url=os.getenv("ANALYZER_URL", "http://localhost:8001"),
            generator_url=os.getenv("GENERATOR_URL", "http://localhost:8002"),
            tester_url=os.getenv("TESTER_URL", "http://localhost:8003"),
        )
    return _orchestrator


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------
class JsonJobRequest(BaseModel):
    xml_pairs: list[XmlPair]


class JobSummary(BaseModel):
    job_id: str
    status: JobStatus
    message: str = ""


# ---------------------------------------------------------------------------
# Background task wrapper
# ---------------------------------------------------------------------------
async def _run_orchestration(job_id: str) -> None:
    """Run the orchestration loop for *job_id* in the background."""
    job = jobs.get(job_id)
    if job is None:
        return
    orchestrator = _get_orchestrator()
    await orchestrator.run(job)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "ok", "service": "gateway"}


@app.post("/api/jobs", response_model=JobSummary)
async def create_job(
    background_tasks: BackgroundTasks,
    input_xml: list[UploadFile] = File(...),
    output_xml: list[UploadFile] = File(...),
):
    """Create a new conversion job from multipart file uploads.

    Expects equal-length lists of ``input_xml`` and ``output_xml`` files.
    Each positional pair is treated as one XML conversion example.
    """
    if len(input_xml) != len(output_xml):
        raise HTTPException(
            status_code=400,
            detail="The number of input_xml and output_xml files must match.",
        )

    xml_pairs: list[XmlPair] = []
    for in_file, out_file in zip(input_xml, output_xml):
        in_content = (await in_file.read()).decode("utf-8")
        out_content = (await out_file.read()).decode("utf-8")
        xml_pairs.append(XmlPair(input_xml=in_content, output_xml=out_content))

    job = ConversionJob(xml_pairs=xml_pairs)
    jobs[job.job_id] = job

    background_tasks.add_task(_run_orchestration, job.job_id)

    return JobSummary(job_id=job.job_id, status=job.status, message="Job created")


@app.post("/api/jobs/json", response_model=JobSummary)
async def create_job_json(
    request: JsonJobRequest,
    background_tasks: BackgroundTasks,
):
    """Create a new conversion job from a JSON payload."""
    if not request.xml_pairs:
        raise HTTPException(status_code=400, detail="xml_pairs must not be empty.")

    job = ConversionJob(xml_pairs=request.xml_pairs)
    jobs[job.job_id] = job

    background_tasks.add_task(_run_orchestration, job.job_id)

    return JobSummary(job_id=job.job_id, status=job.status, message="Job created")


@app.get("/api/jobs", response_model=list[JobSummary])
async def list_jobs():
    """Return a summary of every known job."""
    return [
        JobSummary(job_id=j.job_id, status=j.status, message=j.message)
        for j in jobs.values()
    ]


@app.get("/api/jobs/{job_id}", response_model=ConversionJob)
async def get_job(job_id: str):
    """Return full details for a single job."""
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.post("/api/jobs/{job_id}/run", response_model=JobSummary)
async def rerun_job(job_id: str, background_tasks: BackgroundTasks):
    """Re-run an existing job from scratch."""
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    # Reset mutable state so the orchestrator starts fresh.
    job.status = JobStatus.PENDING
    job.analysis = None
    job.generated_code = None
    job.test_result = None
    job.current_iteration = 0
    job.message = ""

    background_tasks.add_task(_run_orchestration, job.job_id)

    return JobSummary(job_id=job.job_id, status=job.status, message="Job re-started")
