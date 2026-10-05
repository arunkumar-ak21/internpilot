"""Adzuna API implementation of the OpportunityProvider."""

import httpx
from typing import List

from backend.providers.base import OpportunityProvider, RawOpportunity, SearchCriteria
from backend.core.config import get_settings


class AdzunaProvider(OpportunityProvider):
    """Fetches opportunities from the Adzuna API."""

    def __init__(self, app_id: str | None = None, app_key: str | None = None):
        settings = get_settings()
        self.app_id = app_id or settings.adzuna_app_id
        self.app_key = app_key or settings.adzuna_app_key
        
        if not self.app_id or not self.app_key:
            # We don't fail on init, but we will fail on search if credentials are missing
            self._configured = False
        else:
            self._configured = True
            
        self.base_url = "https://api.adzuna.com/v1/api/jobs/in/search/1"

    async def search(self, criteria: SearchCriteria) -> List[RawOpportunity]:
        if not self._configured:
            raise ValueError("Adzuna provider is not configured with app_id and app_key.")

        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "results_per_page": min(criteria.max_results, 50),
            "what": criteria.query,
            "content-type": "application/json",
        }

        if criteria.location:
            params["where"] = criteria.location

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.base_url, params=params, timeout=10.0)
                response.raise_for_status()
                data = response.json()
            except httpx.RequestError as e:
                # Log error in a real app
                raise RuntimeError(f"Error fetching from Adzuna: {e}") from e
            except httpx.HTTPStatusError as e:
                raise RuntimeError(f"Adzuna API returned error status: {e.response.status_code}") from e

        results = []
        for job in data.get("results", []):
            company_name = job.get("company", {}).get("display_name", "Unknown Company")
            location_name = job.get("location", {}).get("display_name", None)
            
            results.append(
                RawOpportunity(
                    source="adzuna",
                    source_id=str(job.get("id")),
                    company=company_name,
                    role=job.get("title", "Unknown Role"),
                    location=location_name,
                    description=job.get("description", ""),
                    application_url=job.get("redirect_url")
                )
            )

        return results
