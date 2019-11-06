from pyfomod.errors import ErrorKind


def test_compare():
    assert ErrorKind.NOTE < ErrorKind.WARNING
    assert ErrorKind.WARNING < ErrorKind.ERROR
