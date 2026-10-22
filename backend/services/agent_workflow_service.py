"""Agent Workflow Service — Manages durable background workflow execution."""

import asyncio
from datetime import datetime, UTC
from backend.models.schemas import AgentWorkflow, WorkflowStatus
from backend.repositories.workflow_repository import WorkflowRepository
from backend.core.config import get_settings


class AgentWorkflowService:
    def __init__(self):
        settings = get_settings()
        self.repo = WorkflowRepository(settings.database_url)

    async def create_workflow(self, student_id: str, resume_id: str) -> AgentWorkflow:
        workflow = AgentWorkflow(
            student_id=student_id,
            resume_id=resume_id,
            status=WorkflowStatus.PROFILE_READY,
            current_stage="profile_ready",
        )
        await self.repo.save(workflow)
        return workflow

    async def run_resume_to_opportunities(self, workflow_id: str) -> dict | None:
        """
        Execute the full pipeline in background. Updates workflow status.
        Returns the pipeline result dict, or None on failure.
        """
        from backend.agents.coordinator import run_pipeline

        workflow = await self.repo.get(workflow_id)
        if not workflow:
            return None

        # Update to discovering
        workflow.status = WorkflowStatus.DISCOVERING
        workflow.current_stage = "discovering"
        await self.repo.save(workflow)

        try:
            result = await run_pipeline(
                resume_id=workflow.resume_id,
                student_id=workflow.student_id,
            )

            workflow = await self.repo.get(workflow_id)

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

            await self.repo.save(workflow)

            return {
                "resume_profile": result.resume_profile,
                "agent_trace": result.agent_trace,
                "recommendations": result.recommendations,
                "status": result.status,
            }

        except asyncio.CancelledError:
            workflow = await self.repo.get(workflow_id)
            workflow.status = WorkflowStatus.CANCELLED
            workflow.current_stage = "cancelled"
            await self.repo.save(workflow)
            return None
        except Exception as e:
            workflow = await self.repo.get(workflow_id)
            workflow.status = WorkflowStatus.FAILED
            workflow.current_stage = "failed"
            workflow.errors.append(str(e))
            await self.repo.save(workflow)
            return None

    async def run_pipeline_sync(self, student_id: str, resume_id: str | None = None,
                                 location: str | None = None) -> dict:
        """
        Synchronous one-shot pipeline — runs to completion and returns full results.
        Used by the /run endpoint for immediate results.
        """
        from backend.agents.coordinator import run_pipeline

        result = await run_pipeline(
            resume_id=resume_id,
            student_id=student_id,
            location=location,
        )

        return {
            "resume_profile": result.resume_profile,
            "agent_trace": result.agent_trace,
            "recommendations": result.recommendations,
            "status": result.status,
        }

    async def get_workflow_status(self, workflow_id: str) -> AgentWorkflow | None:
        return await self.repo.get(workflow_id)
