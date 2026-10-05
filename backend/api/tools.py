"""Observable Lab 2 tool endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.core.config import get_settings
from backend.repositories.session_repository import SessionRepository
from backend.tools.calculator import calculate
from backend.tools.file_reader import read_uploaded_text
from backend.tools.opportunity_search import search_opportunities

router = APIRouter(prefix="/tools", tags=["tools"])


class CalculatorRequest(BaseModel):
    expression: str = Field(min_length=1, max_length=200)


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    location: str | None = None
    max_results: int = Field(default=10, ge=1, le=20)


class FileRequest(BaseModel):
    file_name: str = Field(min_length=1, max_length=255)


async def _audit(tool: str, status: str, details: dict) -> None:
    await SessionRepository(get_settings().database_url).audit("tool-direct", tool, {"status": status, **details})


@router.post("/calculator")
async def calculator(request: CalculatorRequest) -> dict:
    try:
        result = calculate(request.expression)
    except ValueError as error:
        await _audit("calculator", "error", {"message": str(error)})
        raise HTTPException(status_code=422, detail=str(error)) from error
    await _audit("calculator", "success", {"expression": request.expression})
    return {"result": result}


@router.post("/search")
async def search(request: SearchRequest) -> dict:
    results = await search_opportunities(request.query, request.location, request.max_results)
    await _audit("search_opportunities", "success", {"count": len(results), "source": "mock"})
    return {"opportunities": results, "source": "mock", "notice": "Mock development data; not real listings."}


@router.post("/read-file")
async def read_file(request: FileRequest) -> dict:
    try:
        result = read_uploaded_text(request.file_name)
    except (ValueError, FileNotFoundError) as error:
        await _audit("read_resume", "error", {"message": str(error)})
        raise HTTPException(status_code=422, detail=str(error)) from error
    await _audit("read_resume", "success", {"file_name": request.file_name})
    return result
