"""End-to-End Demonstration of Labs 1-5 capabilities.

This script simulates a complete user journey through the InternPilot backend:
1. User uploads a resume (Mocked as a text file for this demo).
2. Resume Parser extracts the student profile.
3. User expresses preferences which are stored in Long-Term Memory.
4. The Agent Coordinator resolves intent.
5. The Opportunity Search tool finds a matching internship.
6. The Internship Research Skill extracts structured insights.
"""

import asyncio
import logging

from backend.core.config import get_settings
from backend.core.database import initialize_database
from backend.repositories.preference_repository import PreferenceRepository
from backend.repositories.session_repository import SessionRepository
from backend.skills.memory_manager import MemoryManager
from backend.skills.internship_research import InternshipResearchSkill
from backend.agents.coordinator import coordinate, new_state
from backend.tools.opportunity_search import search_opportunities
from backend.models.schemas import CandidatePreference, Opportunity

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger("E2E_Demo")

async def run_demo():
    logger.info("Initializing Agentic System (Labs 1-5)")
    
    # 0. Setup
    settings = get_settings()
    await initialize_database()
    session_repo = SessionRepository(settings.database_url)
    pref_repo = PreferenceRepository(settings.database_url)
    student_id = "demo-student-e2e"
    session_id = "session-e2e-1"
    
    from backend.services.resume_ingestion import resume_payload
    
    # 1. Resume Ingestion
    logger.info("\n--- STEP 1: Resume Ingestion ---")
    mock_resume_text = (
        "Arun Mokashi\n"
        "Education: B.Tech in Computer Science, MIT\n"
        "Skills: Python, TypeScript, Machine Learning, React\n"
        "Experience: Built an agentic AI system for a hackathon."
    )
    
    logger.info("Parsing resume using ingestion service...")
    # Simulate a plain text file upload
    payload = resume_payload(
        student_id=student_id,
        file_name="resume.txt",
        content=mock_resume_text.encode("utf-8"),
        content_type="text/plain"
    )
    profile = payload.get("parsed_profile", {})
    logger.info(f"Extracted Profile -> Skills: {profile.get('skills')}")
    
    # 2. Memory Extraction (User states preference)
    logger.info("\n--- STEP 2: Memory Extraction ---")
    user_message = "I want a remote machine learning internship that pays at least $4000."
    logger.info(f"User Message: '{user_message}'")
    
    memory_manager = MemoryManager()
    extraction = await memory_manager.extract_preferences(user_message)
    
    existing_pref = await pref_repo.get_by_student_id(student_id) or CandidatePreference(student_id=student_id)
    updated_pref = memory_manager.merge_preferences(existing_pref, extraction)
    await pref_repo.save(updated_pref)
    
    logger.info(f"Updated Long-Term Memory: Roles={updated_pref.target_roles}, Modes={updated_pref.work_modes}, Stipend=${updated_pref.minimum_stipend}")
    
    # 3. Coordination
    logger.info("\n--- STEP 3: Agent Coordination ---")
    state = await session_repo.get(session_id) or new_state(session_id)
    
    # Inject memory into state
    state.target_role = updated_pref.target_roles[0] if updated_pref.target_roles else None
    state.location = updated_pref.locations[0] if updated_pref.locations else "Remote"  # Fallback to Remote
    
    result = coordinate(user_message, state)
    await session_repo.save(result.state)
    logger.info(f"Coordinator Action Selected: '{result.action}'")
    
    if result.action == "search":
        # 4. Tool Execution (Opportunity Search)
        logger.info("\n--- STEP 4: Tool Execution (Search) ---")
        skills_str = ', '.join(profile.get('skills', [])[:2])
        query = f"{state.target_role} {skills_str}"
        logger.info(f"Searching using query: '{query}' at location: '{state.location}'")
        
        search_results_json = await search_opportunities(
            query=query, 
            location=state.location,
            max_results=1
        )
        
        # It already returns a dict, no need to json.loads
        search_results = search_results_json
        if search_results:
            raw_opp = search_results[0]
            logger.info(f"Found opportunity: {raw_opp.get('company')} - {raw_opp.get('role')}")
            
            opp = Opportunity(**raw_opp)
            
            # 5. Internship Research Skill
            logger.info("\n--- STEP 5: Research Skill Analysis ---")
            research_skill = InternshipResearchSkill()
            analysis = await research_skill.execute(opp)
            
            logger.info(f"Analysis Confidence: {analysis.confidence}")
            logger.info("Important Observations:")
            for obs in analysis.important_observations:
                logger.info(f" - {obs}")
                
            logger.info("Evidence Context:")
            for ev in analysis.evidence:
                logger.info(f" > {ev}")
        else:
            logger.info("No opportunities found.")

    logger.info("\n✅ E2E Demo Completed Successfully.")

if __name__ == "__main__":
    asyncio.run(run_demo())
