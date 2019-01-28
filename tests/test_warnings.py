import pytest
from pyfomod.warnings import CriticalWarning, ValidationWarning, warn


def test_warn():
    with pytest.warns(ValidationWarning, match="Title - Msg"):
        warn("Title", "Msg", None)
    with pytest.warns(CriticalWarning):
        warn("", "", None, critical=True)
