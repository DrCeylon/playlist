from scripts.check_environment import validate_python_version


def test_validate_python_version_accepts_312() -> None:
    result = validate_python_version((3, 12, 0))
    assert result.ok is True


def test_validate_python_version_rejects_39() -> None:
    result = validate_python_version((3, 9, 19))
    assert result.ok is False
    assert "Python 3.12+" in result.message

