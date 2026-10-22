"""Resume upload endpoint; original documents are preserved, not overwritten."""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, BackgroundTasks

from backend.core.config import get_settings
from backend.repositories.resume_repository import ResumeRepository
from backend.repositories.session_repository import SessionRepository
from backend.services.resume_ingestion import resume_payload
from backend.services.agent_workflow_service import AgentWorkflowService

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.post("/upload")
async def upload_resume(background_tasks: BackgroundTasks, student_id: str = Form(...), file: UploadFile = File(...)) -> dict:
    """Upload resume, extract profile, and start background workflow."""
    try:
        payload = await resume_payload(student_id, file.filename or "", await file.read(), file.content_type or "")
        await ResumeRepository(get_settings().database_url).save(payload)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    await SessionRepository(get_settings().database_url).audit(
        "resume-upload", "resume_ingested",
        {"resume_id": payload["resume_id"], "file_name": payload["file_name"]}
    )

    # Create workflow and start background execution
    workflow_service = AgentWorkflowService()
    workflow = await workflow_service.create_workflow(student_id=student_id, resume_id=payload["resume_id"])

    extraction_status = payload.get("extraction_metadata", {}).get("status", "completed")

    if extraction_status == "failed":
        workflow.status = "failed"
        workflow.errors.append("Profile extraction failed.")
        await workflow_service.repo.save(workflow)
        workflow_status = "failed"
    else:
        workflow_status = workflow.status.value
        background_tasks.add_task(workflow_service.run_resume_to_opportunities, workflow.workflow_id)

    # Build response with full parsed profile visible to frontend
    profile = payload.get("parsed_profile", {})

    return {
        "resume_id": payload["resume_id"],
        "student_id": student_id,
        "file_name": payload["file_name"],
        "workflow_id": workflow.workflow_id,
        "profile_status": extraction_status,
        "workflow_status": workflow_status,
        "message": "Resume uploaded successfully and workflow initiated.",
        "parsed_profile": profile,
    }
