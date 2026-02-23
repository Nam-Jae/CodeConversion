"""
Orchestrator
============
Coordinates the multi-agent workflow by calling the Analyzer, Generator, and
Tester micro-services in sequence.  Implements an iterative refinement loop:
if test accuracy falls below the configured threshold the orchestrator feeds
failure details back to the Generator and retries (up to *max_iterations*).
"""

from __future__ import annotations

import logging
import traceback

import httpx

from common import ConversionJob, JobStatus

logger = logging.getLogger(__name__)


class Orchestrator:
    """Drive an XML-conversion job through Analyze -> Generate -> Test."""

    def __init__(
        self,
        analyzer_url: str,
        generator_url: str,
        tester_url: str,
    ) -> None:
        self.analyzer_url = analyzer_url.rstrip("/")
        self.generator_url = generator_url.rstrip("/")
        self.tester_url = tester_url.rstrip("/")

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------
    async def run(self, job: ConversionJob) -> ConversionJob:
        """Execute the full orchestration loop, mutating *job* in place.

        Flow per iteration:
            Analyze (with feedback) → Generate (with feedback) → Test
        If test accuracy < threshold, build feedback and loop again.
        """
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(300.0)) as client:
                feedback = ""

                while job.current_iteration < job.max_iterations:
                    job.current_iteration += 1

                    # ----- Step 1: Analyze (re-analyze with feedback on retry) -----
                    await self._analyze(client, job, feedback=feedback)

                    # ----- Step 2: Generate (with feedback on retry) -----
                    await self._generate(client, job, feedback=feedback)

                    # ----- Step 3: Test -----
                    await self._test(client, job)

                    # Evaluate accuracy
                    if (
                        job.test_result is not None
                        and job.test_result.accuracy >= job.accuracy_threshold
                    ):
                        job.status = JobStatus.COMPLETED
                        job.message = (
                            f"Completed with {job.test_result.accuracy:.0%} accuracy "
                            f"after {job.current_iteration} iteration(s)."
                        )
                        return job

                    # Build feedback for next iteration
                    feedback = self._build_feedback(job)

                    if job.current_iteration < job.max_iterations:
                        job.status = JobStatus.ITERATING
                        job.message = (
                            f"Iteration {job.current_iteration} accuracy "
                            f"{job.test_result.accuracy:.0%} below threshold "
                            f"{job.accuracy_threshold:.0%} -- re-analyzing rules."
                        )
                        logger.info(job.message)

                # Exhausted iterations -- return the best we have.
                accuracy_str = (
                    f"{job.test_result.accuracy:.0%}"
                    if job.test_result
                    else "N/A"
                )
                job.status = JobStatus.COMPLETED
                job.message = (
                    f"Completed after {job.current_iteration} iteration(s) "
                    f"with {accuracy_str} accuracy (max iterations reached)."
                )
                return job

        except Exception as exc:
            logger.exception("Orchestration failed for job %s", job.job_id)
            job.status = JobStatus.FAILED
            job.message = f"Error: {exc}\n{traceback.format_exc()}"
            return job

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _check_response(resp: httpx.Response, service_name: str) -> dict:
        """Check response and extract JSON, raising with detail on error."""
        if resp.status_code >= 400:
            detail = ""
            try:
                body = resp.json()
                detail = body.get("detail", str(body))
            except Exception:
                detail = resp.text[:500]
            raise RuntimeError(f"[{service_name}] {resp.status_code}: {detail}")
        return resp.json()

    async def _analyze(
        self,
        client: httpx.AsyncClient,
        job: ConversionJob,
        feedback: str = "",
    ) -> None:
        """Call the Analyzer service."""
        if feedback:
            job.status = JobStatus.ANALYZING
            job.message = f"Re-analyzing rules with feedback (iteration {job.current_iteration})..."
        else:
            job.status = JobStatus.ANALYZING
            job.message = "Analyzing XML pairs..."

        payload: dict = {
            "xml_pairs": [p.model_dump() for p in job.xml_pairs],
        }
        if feedback:
            payload["feedback"] = feedback

        resp = await client.post(f"{self.analyzer_url}/analyze", json=payload)
        data = self._check_response(resp, "Analyzer")

        from common import AnalysisResult

        job.analysis = AnalysisResult(**data)

    async def _generate(
        self,
        client: httpx.AsyncClient,
        job: ConversionJob,
        feedback: str = "",
    ) -> None:
        """Call the Generator service."""
        job.status = JobStatus.GENERATING
        job.message = f"Generating code (iteration {job.current_iteration})..."

        payload: dict = {
            "xml_pairs": [p.model_dump() for p in job.xml_pairs],
            "analysis": job.analysis.model_dump() if job.analysis else None,
        }
        if feedback:
            payload["feedback"] = feedback

        resp = await client.post(f"{self.generator_url}/generate", json=payload)
        data = self._check_response(resp, "Generator")

        from common import GeneratedCode

        job.generated_code = GeneratedCode(**data)

    async def _test(
        self,
        client: httpx.AsyncClient,
        job: ConversionJob,
    ) -> None:
        """Call the Tester service."""
        job.status = JobStatus.TESTING
        job.message = f"Testing generated code (iteration {job.current_iteration})..."

        payload: dict = {
            "xml_pairs": [p.model_dump() for p in job.xml_pairs],
            "code": job.generated_code.code if job.generated_code else "",
        }

        resp = await client.post(f"{self.tester_url}/test", json=payload)
        data = self._check_response(resp, "Tester")

        from common import TestResult

        job.test_result = TestResult(**data)

    # ------------------------------------------------------------------
    @staticmethod
    def _build_feedback(job: ConversionJob) -> str:
        """Compile human-readable feedback from the most recent test run."""
        if job.test_result is None:
            return ""

        if job.test_result.accuracy >= job.accuracy_threshold:
            return ""

        lines: list[str] = [
            f"Previous iteration accuracy: {job.test_result.accuracy:.0%}.",
            f"Passed {job.test_result.passed_pairs}/{job.test_result.total_pairs} pairs.",
            "",
        ]

        if job.test_result.error_message:
            lines.append(f"Error: {job.test_result.error_message}")
            lines.append("")

        for detail in job.test_result.details:
            if not detail.passed:
                lines.append(f"--- Pair {detail.pair_id} FAILED ---")
                if detail.diff:
                    lines.append(f"Diff:\n{detail.diff}")
                elif detail.expected_snippet or detail.actual_snippet:
                    lines.append(f"Expected snippet:\n{detail.expected_snippet}")
                    lines.append(f"Actual snippet:\n{detail.actual_snippet}")
                lines.append("")

        return "\n".join(lines)
