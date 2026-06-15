"""Example tests for Pydantic models. Replace with your own."""

import pytest
from pydantic import ValidationError
from src.models import RocketLaunch


def test_valid_reading():
    """A valid record should be accepted."""
    reading = RocketLaunch(
        id="launch-1",
        name="Falcon 9",
        net="2026-03-30T10:00:00Z",
        window_start="2026-03-30T08:00:00Z",
        window_end="2026-03-30T12:00:00Z",
        status={"id": 1, "name": "Go for Launch"},
        rocket={"id": 1, "name": "Falcon 9"},
        mission={"id": 1, "name": "Starlink Mission"},
        pad={"id": 1, "name": "LC-39A"}
    )
    assert reading.id == "launch-1"
    assert reading.name == "Falcon 9"


def test_invalid_temperature_too_high():
    """Temperature above 100 should be rejected."""
    with pytest.raises(ValidationError):
        RocketLaunch(
            id="launch-1",
            name="Falcon 9",
            net="2026-03-30T10:00:00Z",
            window_start="2026-03-30T08:00:00Z",
            window_end="2026-03-30T12:00:00Z",
            status={"id": 1, "name": "Go for Launch"},
            rocket={"id": 1, "name": "Falcon 9"},
            mission={"id": 1, "name": "Starlink Mission"},
            pad={"id": 1, "name": "LC-39A"}
        )


def test_missing_id():
    """Missing required field should be rejected."""
    with pytest.raises(ValidationError):
        RocketLaunch(
            id="",
            name="Falcon 9",
            net="2026-03-30T10:00:00Z",
            window_start="2026-03-30T08:00:00Z",
            window_end="2026-03-30T12:00:00Z",
            status={"id": 1, "name": "Go for Launch"},
            rocket={"id": 1, "name": "Falcon 9"},
            mission={"id": 1, "name": "Starlink Mission"},
            pad={"id": 1, "name": "LC-39A"}
        )
