"""Problem exists with the user or their machine."""

from abc import ABC
from enum import IntEnum
from typing import Any, ClassVar


class Code(IntEnum):
    OK = 0

    #: Errors Relating to: Host Operating System
    SYSTEM = 100
    MISSING_PROGRAM = 101


class UserError(ABC, Exception):
    """Base exception class denoting an issue with the user's command invocation or environment.

    This is the only exception type that should ever propagate to the top of the application. Any other error
    propagating is considered a bug.
    """

    code: ClassVar[int]
    """Human readable error code. Base on a code from above."""

    def __str__(self) -> str:
        return f"E{self.code:03}: {super().__str__()}"

    #: Codes that have been recorded so far
    _codes: ClassVar[set[int]] = set()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        if cls.code is None:
            raise TypeError(f"{cls.__name__} must define a code")

        if cls.code in UserError._codes:
            raise TypeError(f"Duplicate UserError code: {cls.code}")

        UserError._codes.add(cls.code)


class MissingProgramError(UserError):
    code = Code.MISSING_PROGRAM

    def __init__(self, *, program: str) -> None:
        # It would be nice if we could use apt-file or something to look up package name hints
        super().__init__(f'Could not find a program named "{program}"')
