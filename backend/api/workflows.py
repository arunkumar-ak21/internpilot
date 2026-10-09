from fastapi import APIRouter, HTTPException
from backend.services.agent_workflow_service import AgentWorkflowService
from backend.repositories.opportunity_repository import OpportunityRepository
from backend.core.config import get_settings

router = APIRouter(prefix="/workflows", tags=["workflows"])

@router.get("/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    workflow_service = AgentWorkflowService()
    workflow = await workflow_service.get_workflow_status(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow.model_dump()

@router.get("/{workflow_id}/opportunities")
async def get_workflow_opportunities(workflow_id: str):
    workflow_service = AgentWorkflowService()
    workflow = await workflow_service.get_workflow_status(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Since workflows are bound to students, we fetch matches for the student
    repo = OpportunityRepository(get_settings().database_url)
    opportunities = await repo.get_matches_for_student(workflow.student_id)
    
    return {"opportunities": opportunities}
