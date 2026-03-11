"""Tests for MCP server tools."""

from server import multiply


def test_multiply() -> None:
    """Test the multiply tool."""
    result = multiply(2, 3)
    assert result == 6


def test_multiply_negative() -> None:
    """Test multiply with negative numbers."""
    result = multiply(-2, 3)
    assert result == -6


def test_multiply_zero() -> None:
    """Test multiply with zero."""
    result = multiply(0, 5)
    assert result == 0


def test_multiply_floats() -> None:
    """Test multiply with floats."""
    result = multiply(2.5, 4.0)
    assert result == 10.0
