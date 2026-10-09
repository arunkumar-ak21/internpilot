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
            current_stage="profile_ready"
        )
        await self.repo.save(workflow)
        return workflow

    async def run_resume_to_opportunities(self, workflow_id: str):
        # Local import to prevent circular dependencies
        from backend.agents.coordinator import app as workflow_app
        from langchain_core.messages import HumanMessage
        
        workflow = await self.repo.get(workflow_id)
        if not workflow:
            return
            
        workflow.status = WorkflowStatus.DISCOVERING
        workflow.current_stage = "discovering"
        await self.repo.save(workflow)
        
        try:
            initial_graph_state = {
                "workflow_id": workflow_id,
                "session_id": f"workflow_{workflow_id}",
                "student_id": workflow.student_id,
                "messages": [HumanMessage(content="Please run the automatic discovery and matching workflow for my profile.")],
                "next": ""
            }
            
            # Execute the langgraph application asynchronously
            result = await workflow_app.ainvoke(initial_graph_state)
            
            # Re-fetch just in case it was updated during the run
            workflow = await self.repo.get(workflow_id)
            workflow.status = WorkflowStatus.COMPLETED
            workflow.current_stage = "completed"
            await self.repo.save(workflow)
            
        except asyncio.CancelledError:
            workflow = await self.repo.get(workflow_id)
            workflow.status = WorkflowStatus.CANCELLED
            workflow.current_stage = "cancelled"
            await self.repo.save(workflow)
        except Exception as e:
            workflow = await self.repo.get(workflow_id)
            workflow.status = WorkflowStatus.FAILED
            workflow.current_stage = "failed"
            workflow.errors.append(str(e))
            await self.repo.save(workflow)

    async def get_workflow_status(self, workflow_id: str) -> AgentWorkflow | None:
        return await self.repo.get(workflow_id)
