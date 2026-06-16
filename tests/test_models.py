"""Example tests for Pydantic models. Replace with your own."""

import pytest
from pydantic import ValidationError
from src.models import RocketLaunch


def test_valid_reading():
    """A valid record should be accepted."""
    reading = RocketLaunch(
        id="launch-1",
        name="Falcon 9",
        
      
    )
    assert reading.id == "launch-1"
    assert reading.name == "Falcon 9"


def test_fetch_data():
    with pytest.raises(ValidationError):
        RocketLaunch(
            id="launch-1",
            name="Falcon 9",
            
        
        )


def test_validate_skips_invalid():
    with pytest.raises(ValidationError):
        RocketLaunch(
            id="launch-1",
            name="Falcon 9",
            
        
        )

def test_invalid_temperature_too_high():
    """Temperature above 100 should be rejected."""
    with pytest.raises(ValidationError):
        RocketLaunch(
            id="launch-1",
            name="Falcon 9",
           
        )


def test_missing_id():
    """Missing required field should be rejected."""
    with pytest.raises(ValidationError):
        RocketLaunch(
            id="",
            name="Falcon 9",
            
        
        )
