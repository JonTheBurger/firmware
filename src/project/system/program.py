import shutil
import time
from functools import cache
from pathlib import Path
from subprocess import CompletedProcess, run
from typing import Any

from project.core.error import user
from project.core.logger import Log

logger = Log.get(__name__)


@cache
def find_program(name: str) -> Path:
    program = shutil.which(name)
    if not program:
        raise user.MissingProgramError(program=name)
    # Maybe we should symlink this path in .cache
    return Path(program).absolute()


def execute(  # noqa: PLR0913 - We're wrapping subprocess run, which has a lot of args.
    program: Path | str,
    args: list[Any] | None = None,
    *,
    check: bool = True,
    stdin: str | None = None,
    capture: bool = True,
    timeout_s: float | None = None,
) -> CompletedProcess[str]:
    """Run a short-lived program and immediately collect its output text.

    Args:
        program: Path to an existing program, or the name of a program to look up.
        args: Arguments to pass to the program, stringified.
        check: Set to false to manually inspect the return code instead of throwing.
        stdin: Text to send to standard input. Use ``'\n'`` for newlines.
        capture: Set to ``False`` to forward stdout/stderr to the controlling shell.
        timeout_s: Max time to wait for the process to finish; ``None`` for no limit.

    Returns:
        Standard subprocess.CompletedProcess[str].
    """
    if isinstance(program, str):
        program = find_program(program)
    args = [str(a) for a in args or []]
    with logger.span("process.run", {"path": str(program)}) as span:
        cmd = [str(program), *args]

        start_s = time.perf_counter()
        # pyrefly: ignore[no-matching-overload]
        process = run(cmd, capture_output=capture, text=True, check=check, stdin=stdin, timeout=timeout_s)
        duration_s = time.perf_counter() - start_s

        span.log(
            span.level,
            " ".join(args),
            code=process.returncode,
            seconds=duration_s,
            bytes_streamed=len(process.stdout or "") + len(process.stderr or ""),
        )
    return process
