import json
import aiosqlite
from backend.core.database import sqlite_path
from backend.models.schemas import AgentWorkflow, WorkflowStatus

class WorkflowRepository:
    def __init__(self, database_url: str): 
        self.database_path = sqlite_path(database_url)

    async def save(self, workflow: AgentWorkflow) -> None:
        async with aiosqlite.connect(self.database_path) as connection:
            await connection.execute(
                "INSERT OR REPLACE INTO agent_workflows (workflow_id, student_id, resume_id, status, current_stage, progress_info, errors_json, opportunities_discovered, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    workflow.workflow_id,
                    workflow.student_id,
                    workflow.resume_id,
                    workflow.status,
                    workflow.current_stage,
                    workflow.progress_info,
                    json.dumps(workflow.errors),
                    workflow.opportunities_discovered,
                    workflow.created_at.isoformat(),
                    workflow.updated_at.isoformat()
                )
            )
            await connection.commit()

    async def get(self, workflow_id: str) -> AgentWorkflow | None:
        async with aiosqlite.connect(self.database_path) as connection:
            connection.row_factory = aiosqlite.Row
            cursor = await connection.execute("SELECT * FROM agent_workflows WHERE workflow_id = ?", (workflow_id,))
            row = await cursor.fetchone()
            if row:
                return AgentWorkflow(
                    workflow_id=row["workflow_id"],
                    student_id=row["student_id"],
                    resume_id=row["resume_id"],
                    status=WorkflowStatus(row["status"]),
                    current_stage=row["current_stage"],
                    progress_info=row["progress_info"],
                    errors=json.loads(row["errors_json"]),
                    opportunities_discovered=row["opportunities_discovered"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"]
                )
            return None
