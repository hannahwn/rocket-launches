"""Pydantic models for data validation. Replace with your own."""

from typing import Optional

from pydantic import BaseModel, Field


class RocketLaunch(BaseModel):
    """Example model. Replace with your own data structure."""

    id: str
    name: str
    launch_date: Optional[str] = None
    launch_status: Optional[str] = None
    rocket_name: Optional[str] = None
    mission_name: Optional[str] = None
    mission_type: Optional[str] = None
    orbit: Optional[str] = None
    provider_name: Optional[str] = None
    provider_type: Optional[str] = None
    pad_name: Optional[str] = None
    location: Optional[str] = None
    pad: Optional[dict] = None
    launch_service_provider: Optional[dict] = None

    # TODO: Replace these fields with the fields from your API response.
    # Pydantic will reject any record that does not match this schema.

    @classmethod
    def from_api_response(cls, data: dict) -> "RocketLaunch":
        """Convert API response to model instance. Adjust field mappings as needed."""
        return cls(
            id=data["id"],
            name=data["name"],
            launch_date=data.get("launch_date"),
            launch_status=data.get("launch_status"),
            rocket_name=data.get("rocket", {}).get("configuration", {}).get("name"),
            mission_name=data.get("mission", {}).get("name"),
            mission_type=data.get("mission", {}).get("type"),
            orbit=data.get("mission", {}).get("orbit", {}).get("name"),
            provider_name=data.get("launch_service_provider", {}).get("name"),
            provider_type=data.get("launch_service_provider", {}).get("type"),
            pad_name=data.get("pad", {}).get("name"),
            location=data.get("pad", {}).get("location", {}).get("name"),
            pad=data.get("pad"),
            launch_service_provider=data.get("launch_service_provider"),
        )
