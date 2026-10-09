"""Search tools for the Discovery Agent."""

from langchain_core.tools import tool
from duckduckgo_search import DDGS
from backend.core.config import get_settings
import httpx

@tool
def search_duckduckgo(query: str) -> str:
    """Search the internet for unstructured job postings, company pages, or internship information."""
    import httpx
    import re
    try:
        # Use raw HTTP request with a strict timeout instead of the broken DDGS library
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = httpx.get("https://html.duckduckgo.com/html/", params={"q": query}, headers=headers, timeout=5.0)
        response.raise_for_status()
        
        # Simple extraction of text snippets
        html = response.text
        snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', html, re.IGNORECASE | re.DOTALL)
        
        if not snippets:
            return "No results found or rate limited."
            
        clean_snippets = [re.sub(r'<[^>]+>', '', s).strip() for s in snippets[:5]]
        return "\n\n".join(clean_snippets)
    except Exception as e:
        return f"DuckDuckGo search error: {e}"

@tool
def search_adzuna(role: str, location: str = "") -> str:
    """Search the Adzuna API for structured, real-time job postings. Provide the target role and optionally a location."""
    settings = get_settings()
    app_id = settings.adzuna_app_id
    app_key = settings.adzuna_app_key
    
    if not app_id or not app_key:
        return "Error: Adzuna API keys are not configured. Use DuckDuckGo instead."
        
    url = f"https://api.adzuna.com/v1/api/jobs/gb/search/1"
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": 5,
        "what": role,
        "where": location
    }
    
    try:
        response = httpx.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for job in data.get("results", []):
            title = job.get("title", "")
            company = job.get("company", {}).get("display_name", "")
            loc = job.get("location", {}).get("display_name", "")
            desc = job.get("description", "")
            results.append(f"Title: {title}\nCompany: {company}\nLocation: {loc}\nDescription: {desc[:200]}...")
            
        if not results:
            return f"No jobs found on Adzuna for {role} in {location}."
            
        return "\n\n".join(results)
    except Exception as e:
        return f"Error connecting to Adzuna API: {str(e)}"
