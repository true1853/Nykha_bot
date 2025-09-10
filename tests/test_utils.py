"""
Tests for utility functions.
"""
import pytest
from src.utils.utils import escape_md, get_sun_times


def test_escape_md():
    """Test Markdown escaping."""
    assert escape_md("Hello *world*") == "Hello \\*world\\*"
    assert escape_md("Test [link](url)") == "Test \\[link\\]\\(url\\)"
    assert escape_md("Normal text") == "Normal text"


def test_get_sun_times():
    """Test sun times calculation."""
    # Test with Moscow coordinates
    result = get_sun_times(55.7558, 37.6173, "Europe/Moscow")
    
    assert "sunrise" in result
    assert "sunset" in result
    # Sunrise and sunset should be datetime objects or None
    assert result["sunrise"] is None or hasattr(result["sunrise"], "hour")
    assert result["sunset"] is None or hasattr(result["sunset"], "hour")
