"""Agent Workflow Service — Manages pipeline execution and syncs results to shared memory."""

from __future__ import annotations

import asyncio
from datetime import datetime, UTC

from backend.core.config import get_settings
from backend.models.schemas import AgentWorkflow, WorkflowStatus
from backend.repositories.opportunity_repository import OpportunityRepository
from backend.repositories.session_repository import SessionRepository
from backend.repositories.workflow_repository import WorkflowRepository


class AgentWorkflowService:
    def __init__(self):
        settings = get_settings()
        self.db_url = settings.database_url
        self.repo = WorkflowRepository(self.db_url)
        self.opp_repo = OpportunityRepository(self.db_url)
        self.session_repo = SessionRepository(self.db_url)

    async def create_workflow(self, student_id: str, resume_id: str) -> AgentWorkflow:
        workflow = AgentWorkflow(
            student_id=student_id,
            resume_id=resume_id,
            status=WorkflowStatus.PROFILE_READY,
            current_stage="profile_ready",
        )
        await self.repo.save(workflow)
        return workflow

    async def _sync_to_memory_and_db(
        self,
        student_id: str,
        resume_id: str | None,
        resume_profile: dict,
        recommendations: list[dict],
        agent_trace: list[str],
        session_id: str | None = None,
    ) -> None:
        """Persist ranked internships to SQLite and sync into the active conversation session."""
        if recommendations and student_id:
            try:
                await self.opp_repo.save_ranked_recommendations(student_id, recommendations)
            except Exception:
                pass

        # Sync with session memory so the Chat Assistant immediately knows the resume & #1..#N internships
        target_session_id = session_id or student_id or "default-session"
        try:
            state = await self.session_repo.get_or_create(target_session_id)
            state.student_id = student_id
            state.resume_id = resume_id or resume_profile.get("resume_id")
            state.resume_profile = resume_profile
            state.skills = resume_profile.get("skills_display") or resume_profile.get("skills", [])
            state.opportunities = recommendations
            state.agent_trace = agent_trace
            await self.session_repo.save(state)
        except Exception:
            pass

    async def run_resume_to_opportunities(
        self, workflow_id: str, session_id: str | None = None
    ) -> dict | None:
        """
        Execute the full Coordinator -> Discovery -> Eligibility pipeline.
        Updates workflow status and syncs results to shared memory.
        """
        from backend.agents.coordinator import run_pipeline

        workflow = await self.repo.get(workflow_id)
        if not workflow:
            return None

        workflow.status = WorkflowStatus.DISCOVERING
        workflow.current_stage = "discovering"
        workflow.updated_at = datetime.now(UTC)
        await self.repo.save(workflow)

        try:
            result = await run_pipeline(
                resume_id=workflow.resume_id,
                student_id=workflow.student_id,
            )

            workflow = await self.repo.get(workflow_id) or workflow

            if result.status == "completed":
                workflow.status = WorkflowStatus.COMPLETED
                workflow.current_stage = "completed"
                workflow.opportunities_discovered = len(result.recommendations)
            elif result.status == "no_results":
                workflow.status = WorkflowStatus.NO_RESULTS
                workflow.current_stage = "completed"
            else:
                workflow.status = WorkflowStatus.FAILED
                workflow.current_stage = "failed"

            workflow.updated_at = datetime.now(UTC)
            await self.repo.save(workflow)

            await self._sync_to_memory_and_db(
                student_id=workflow.student_id,
                resume_id=workflow.resume_id,
                resume_profile=result.resume_profile,
                recommendations=result.recommendations,
                agent_trace=result.agent_trace,
                session_id=session_id,
            )

            return {
                "workflow_id": workflow.workflow_id,
                "resume_profile": result.resume_profile,
                "agent_trace": result.agent_trace,
                "recommendations": result.recommendations,
                "status": result.status,
            }

        except asyncio.CancelledError:
            workflow = await self.repo.get(workflow_id) or workflow
            workflow.status = WorkflowStatus.CANCELLED
            workflow.current_stage = "cancelled"
            workflow.updated_at = datetime.now(UTC)
            await self.repo.save(workflow)
            return None
        except Exception as e:
            workflow = await self.repo.get(workflow_id) or workflow
            workflow.status = WorkflowStatus.FAILED
            workflow.current_stage = "failed"
            workflow.errors.append(str(e))
            workflow.updated_at = datetime.now(UTC)
            await self.repo.save(workflow)
            return None

    async def run_pipeline_sync(
        self,
        student_id: str,
        resume_id: str | None = None,
        location: str | None = None,
        session_id: str | None = None,
    ) -> dict:
        """
        One-shot pipeline — runs to completion, persists to shared session memory,
        and returns full results immediately.
        """
        from backend.agents.coordinator import run_pipeline

        result = await run_pipeline(
            resume_id=resume_id,
            student_id=student_id,
            location=location,
        )

        await self._sync_to_memory_and_db(
            student_id=student_id,
            resume_id=resume_id or result.resume_profile.get("resume_id"),
            resume_profile=result.resume_profile,
            recommendations=result.recommendations,
            agent_trace=result.agent_trace,
            session_id=session_id,
        )

        return {
            "resume_profile": result.resume_profile,
            "agent_trace": result.agent_trace,
            "recommendations": result.recommendations,
            "status": result.status,
        }

    async def get_workflow_status(self, workflow_id: str) -> AgentWorkflow | None:
        return await self.repo.get(workflow_id)