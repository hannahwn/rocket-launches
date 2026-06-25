"""Pydantic models for data validation."""

from pydantic import BaseModel


class RocketLaunch(BaseModel):
    """Model for a single rocket launch record from the SpaceDevs API."""

    id: str
    name: str
    launch_date: str | None = None
    launch_status: str | None = None
    rocket_name: str | None = None
    mission_name: str | None = None
    mission_type: str | None = None
    orbit: str | None = None
    provider_name: str | None = None
    provider_type: str | None = None
    pad_name: str | None = None
    location: str | None = None

    @classmethod
    def from_api_response(cls, data: dict) -> "RocketLaunch":
        """Convert API response to model instance."""
        return cls(
            id=data.get("id"),
            name=data.get("name"),
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
        )
