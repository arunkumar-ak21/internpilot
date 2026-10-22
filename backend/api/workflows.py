"""Workflow status and one-shot pipeline endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend.services.agent_workflow_service import AgentWorkflowService
from backend.repositories.opportunity_repository import OpportunityRepository
from backend.core.config import get_settings

router = APIRouter(prefix="/workflows", tags=["workflows"])


class RunPipelineRequest(BaseModel):
    student_id: str = Field(..., description="Student ID to run pipeline for")
    resume_id: str | None = Field(None, description="Specific resume ID (optional)")
    location: str | None = Field(None, description="Preferred location filter")


@router.get("/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    """Get the current status of a background workflow."""
    workflow_service = AgentWorkflowService()
    workflow = await workflow_service.get_workflow_status(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow.model_dump()


@router.get("/{workflow_id}/opportunities")
async def get_workflow_opportunities(workflow_id: str):
    """Get opportunities discovered by a workflow."""
    workflow_service = AgentWorkflowService()
    workflow = await workflow_service.get_workflow_status(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    repo = OpportunityRepository(get_settings().database_url)
    opportunities = await repo.get_matches_for_student(workflow.student_id)

    return {"opportunities": opportunities}


@router.post("/run")
async def run_pipeline(request: RunPipelineRequest):
    """
    One-shot synchronous pipeline endpoint.
    Runs Coordinator -> Discovery -> Eligibility to completion.
    Returns resume_profile, agent_trace, and ranked recommendations immediately.
    """
    workflow_service = AgentWorkflowService()
    result = await workflow_service.run_pipeline_sync(
        student_id=request.student_id,
        resume_id=request.resume_id,
        location=request.location,
    )

    return result
