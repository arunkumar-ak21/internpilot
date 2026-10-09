"""Resume upload endpoint; original documents are preserved, not overwritten."""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from backend.core.config import get_settings
from backend.repositories.resume_repository import ResumeRepository
from backend.repositories.session_repository import SessionRepository
from backend.services.resume_ingestion import resume_payload

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.post("/upload")
async def upload_resume(student_id: str = Form(...), file: UploadFile = File(...)) -> dict:
    try:
        payload = await resume_payload(student_id, file.filename or "", await file.read(), file.content_type or "")
        await ResumeRepository(get_settings().database_url).save(payload)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    await SessionRepository(get_settings().database_url).audit("resume-upload", "resume_ingested", {"resume_id": payload["resume_id"], "file_name": payload["file_name"]})
    return {key: value for key, value in payload.items() if key not in {"file_path", "extracted_text"}}
