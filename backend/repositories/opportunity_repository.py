import json
import aiosqlite
from backend.core.database import sqlite_path
from backend.models.schemas import Opportunity, OpportunityMatch, EligibilityStatus, DeadlineRisk

class OpportunityRepository:
    def __init__(self, database_url: str): 
        self.database_path = sqlite_path(database_url)

    async def save_opportunity(self, opp: Opportunity) -> None:
        async with aiosqlite.connect(self.database_path) as connection:
            await connection.execute(
                "INSERT OR REPLACE INTO opportunities (opportunity_id, source, source_id, company, role, description, location, work_mode, stipend, duration, deadline, eligibility_requirements_json, required_skills_json, application_url, fetched_at, normalized_data_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    opp.opportunity_id, opp.source, opp.source_id, opp.company, opp.role, 
                    opp.description, opp.location, opp.work_mode, opp.stipend, opp.duration, 
                    opp.deadline.isoformat() if opp.deadline else None,
                    json.dumps(opp.eligibility_requirements) if opp.eligibility_requirements else None,
                    json.dumps(opp.required_skills) if opp.required_skills else None,
                    opp.application_url, opp.fetched_at.isoformat(),
                    json.dumps(opp.normalized_data) if opp.normalized_data else None
                )
            )
            await connection.commit()

    async def save_match(self, match: OpportunityMatch) -> None:
        async with aiosqlite.connect(self.database_path) as connection:
            await connection.execute(
                "INSERT OR REPLACE INTO opportunity_matches (id, student_id, opportunity_id, eligibility, eligibility_reason, skill_match, role_match, location_match, preference_match, deadline_risk, overall_score, missing_skills_json, explanation, calculated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    match.id, match.student_id, match.opportunity_id, match.eligibility.value, match.eligibility_reason,
                    match.skill_match, match.role_match, match.location_match, match.preference_match,
                    match.deadline_risk.value if match.deadline_risk else None,
                    match.overall_score,
                    json.dumps(match.missing_skills) if match.missing_skills else None,
                    match.explanation, match.calculated_at.isoformat()
                )
            )
            await connection.commit()

    async def get_matches_for_student(self, student_id: str) -> list[dict]:
        async with aiosqlite.connect(self.database_path) as connection:
            connection.row_factory = aiosqlite.Row
            cursor = await connection.execute(
                "SELECT o.*, m.eligibility, m.eligibility_reason, m.skill_match, m.overall_score, m.explanation, m.missing_skills_json "
                "FROM opportunity_matches m "
                "JOIN opportunities o ON m.opportunity_id = o.opportunity_id "
                "WHERE m.student_id = ? "
                "ORDER BY m.calculated_at DESC", 
                (student_id,)
            )
            rows = await cursor.fetchall()
            results = []
            for r in rows:
                row_dict = dict(r)
                row_dict["missing_skills"] = json.loads(row_dict["missing_skills_json"]) if row_dict.get("missing_skills_json") else []
                results.append(row_dict)
            return results
