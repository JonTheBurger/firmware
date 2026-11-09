import shutil
import time
from functools import cache
from pathlib import Path
from subprocess import CompletedProcess, run

import structlog

from project.core.error import user

logger = structlog.get_logger()


@cache
def find_program(name: str) -> Path:
    program = shutil.which(name)
    if not program:
        raise user.MissingProgramError(program=name)
    # Maybe we should symlink this path in .cache
    return Path(program).absolute()


def execute(program: Path | str, args: list[str] | None = None) -> CompletedProcess[str]:
    """Run a short-lived program and immediately collect its output text.

    Args:
        program: Path to an existing program, or the name of a program to look up
        args: Arguments to pass to the program

    Returns:
        Standard subprocess.CompletedProcess[str].
    """
    if isinstance(program, str):
        program = find_program(program)
    log = logger.bind(program=program, args=args)
    log.debug("Start")
    start_s = time.monotonic()
    process = run([str(program), *(args or [])], capture_output=True, text=True, check=False)
    duration_s = time.monotonic() - start_s
    log.debug(
        "Finish",
        code=process.returncode,
        seconds=duration_s,
        bytes_streamed=len(process.stdout or "") + len(process.stderr or ""),
    )
    return process


# def launch(program: Path, args: list[str] | None = None) -> None:
#     pass
