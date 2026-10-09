"""Tavily Search API implementation of the OpportunityProvider."""

import httpx
import os
from typing import List
from backend.providers.base import OpportunityProvider, RawOpportunity, SearchCriteria
from backend.core.config import get_settings

class TavilyProvider(OpportunityProvider):
    """Fetches opportunities using the Tavily Search API."""
    
    def __init__(self):
        settings = get_settings()
        self.api_key = getattr(settings, "tavily_api_key", None) or os.environ.get("TAVILY_API_KEY")
        if not self.api_key:
            self._configured = False
        else:
            self._configured = True
            
        self.url = "https://api.tavily.com/search"

    async def search(self, criteria: SearchCriteria) -> List[RawOpportunity]:
        if not self._configured:
            raise ValueError("Tavily provider is not configured. Missing TAVILY_API_KEY.")
            
        query = f"{criteria.query} internship apply"
        if criteria.location:
            query += f" {criteria.location}"
            
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "basic",
            "include_answer": False,
            "include_images": False,
            "include_raw_content": False,
            "max_results": min(criteria.max_results, 10),
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.url, json=payload, timeout=10.0)
                response.raise_for_status()
                data = response.json()
            except httpx.RequestError as e:
                raise RuntimeError(f"Error connecting to Tavily: {e}") from e
            except httpx.HTTPStatusError as e:
                raise RuntimeError(f"Tavily returned HTTP {e.response.status_code}") from e
                
        results = []
        for result in data.get("results", []):
            results.append(
                RawOpportunity(
                    source="web_search",
                    source_id=result.get("url"),
                    company="Company (Extracted via Web)",
                    role=result.get("title", "Internship Opportunity"),
                    location=criteria.location,
                    description=result.get("content", ""),
                    application_url=result.get("url")
                )
            )
            
        return results
