import pytest

from backend.tools.calculator import calculate


def test_calculator_handles_numeric_arithmetic():
    assert calculate("(10000 * 12) / 6") == 20000


def test_calculator_rejects_code_execution():
    with pytest.raises(ValueError):
        calculate("__import__('os').system('whoami')")
