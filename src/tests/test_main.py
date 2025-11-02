import pytest


@pytest.mark.parametrize(
    "x, y, expected",
    [
        (1, 1, 1),
        (2, 1, 2),
        (3, 2, 6),
        (1, -4, -4),
        (0, 999, 0),
    ],
)
def test_user(x, y, expected):
    result = x * y
    assert result == expected
