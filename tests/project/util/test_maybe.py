import pytest

from project.util.maybe import maybe


def test_init_collapses_maybe() -> None:
    assert maybe(0).option == 0
    assert maybe(None).option is None
    assert maybe(maybe(0)).option == 0
    assert maybe(maybe(None)).option is None


def test_has_value() -> None:
    assert maybe(0).has_value()
    assert not maybe(None).has_value()


def test_value() -> None:
    assert maybe(0).value() == 0
    with pytest.raises(ValueError):  # noqa: PT011
        maybe(None).value()


def test_or_default() -> None:
    assert maybe(0).or_default(1) == 0
    assert maybe(None).or_default(0) == 0


def test_or_else() -> None:
    assert maybe(0).or_else(lambda: 1) == 0
    assert maybe(None).or_else(lambda: 0) == 0


def test_and_then() -> None:
    assert maybe(0).and_then(lambda _: 1).option == 1
    assert maybe(None).and_then(lambda _: 0).option is None


def test_str() -> None:
    assert str(maybe(0)) == "0"
    assert str(maybe(None)) == "None"


def test_eq() -> None:
    assert maybe(0) == maybe(0)
    assert maybe(0) == 0
    assert maybe(None) == maybe(None)
    assert maybe(None) == None  # noqa: E711


def test_lt() -> None:
    assert not maybe(None) < maybe(None)
    assert not maybe(None) < None
    assert maybe(None) < maybe(0)
    assert maybe(0) < maybe(1)
    assert maybe(0) < 1
    assert maybe(0) > None


def test_iter() -> None:
    assert list(maybe(0)) == [0]
    assert list(maybe(None)) == []
