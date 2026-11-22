"""Useful as a replacement for the null-coalescing operator."""

from dataclasses import dataclass
from functools import total_ordering
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator


@total_ordering
@dataclass(slots=True, frozen=True, eq=False)
class Maybe[T]:
    """Python implementation of Optional type."""

    option: T | None

    def __init__(self, obj: T | Maybe[T] | None = None) -> None:
        """Collapse another ``Maybe`` into ``T``."""
        object.__setattr__(self, "option", obj.option if isinstance(obj, Maybe) else obj)

    def has_value(self) -> bool:
        """Return ``True`` if ``self.option`` not ``None`` - the value of a non-None option is not considered here."""
        return self.option is not None

    def value(self) -> T:
        """Return the contained ``T`` or raise a ``ValueError`` if it is ``None``."""
        if self.option is None:
            raise ValueError("None is not allowed here")
        return self.option

    def or_default(self, value: T) -> T:
        """Return the contained ``T`` or a default value if it is ``None``."""
        return self.option if self.option is not None else value

    def or_else(self, func: Callable[[], T]) -> T:
        """Return the contained ``T`` or the result of a function it is ``None``."""
        if self.option is not None:
            return self.option
        return func()

    def and_then[U](self, func: Callable[[T], U | None]) -> Maybe[U]:
        """Call the given function with ``T`` if it is not ``None``, else return an empty ``Maybe``."""
        if self.option is not None:
            return Maybe(func(self.option))
        return Maybe()

    def __str__(self) -> str:
        """Stringify ``self.option``."""
        return str(self.option)

    def __eq__(self, value: object, /) -> bool:
        """A ``Maybe`` == another ``Maybe`` with the same ``.option``, or to a ``T`` that equals its ``.option``."""
        if isinstance(value, Maybe):
            return self.option == value.option
        return self.option == value

    def __lt__(self, value: object, /) -> bool:
        """A ``Maybe`` of ``None`` is < than everything sans ``None`` and ``Maybe()``, else delegate to ``.option``."""
        # Collapse Maybe down to T | None
        other = value.option if isinstance(value, Maybe) else value
        # None is less than everything except another None, to which it is equal
        if self.option is None:
            return other is not None
        if other is None:
            return False
        # pyrefly: ignore[unsupported-operation]
        return self.option < other

    def __hash__(self) -> int:
        """Hash the inner option."""
        return hash(self.option)

    def __iter__(self) -> Iterator[T]:
        """Iterate over 1 or 0 items, depending on if our option is ``None``."""
        if self.option is not None:
            yield self.option


def maybe[T](optional: T | Maybe[T] | None) -> Maybe[T]:
    """Create a Maybe[T] without a default init arg."""
    return Maybe(optional)
