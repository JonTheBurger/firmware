import asyncio
import os
import shutil
import time
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from functools import cache
from pathlib import Path
from subprocess import CompletedProcess, run
from typing import TYPE_CHECKING, Any, ClassVar, Self

from pydantic import BaseModel

from project.core.error import user
from project.core.logger import Log
from project.core.units import Duration, s
from project.formats.sarif import SarifTool, SarifToolComponent

if TYPE_CHECKING:
    from asyncio.subprocess import Process
    from collections.abc import AsyncGenerator, Iterable

logger = Log.get(__name__)


class Tool(BaseModel):
    name: str
    path: Path
    version: str
    uri: ClassVar[str | None] = None

    def execute(
        self,
        args: Iterable[Any] | None = None,
        *,
        check: bool = True,
        capture: bool = True,
        timeout: Duration | None = None,
    ) -> CompletedProcess[str]:
        return execute(self.path, args, check=check, capture=capture, timeout=timeout)

    def stream(
        self, args: Iterable[Any] | None = None, *, env: dict[str, str] | None = None
    ) -> AbstractAsyncContextManager[Process]:
        return stream(self.path, args, env=env)

    def sarif(self) -> SarifTool:
        """Sarif tool section for this program."""
        return SarifTool(
            driver=SarifToolComponent(
                name=self.name,
                information_uri=self.uri,
                version=self.version,
            )
        )

    @classmethod
    def tool(cls, name: str | None = None, version_command: tuple[str, ...] = ("--version",)) -> Self:
        name = name or cls.__name__.lower()
        return cls.model_validate(find_program(name, version_command=version_command).model_dump())


@cache
def find_program(name: str | Path, *, version_command: tuple[str, ...] = ("--version",)) -> Tool:
    path = shutil.which(name)
    if not path:
        raise user.MissingProgramError(program=name)
    path = Path(path)

    if not isinstance(name, str):
        name = path.stem

    version = run([path, *version_command], capture_output=True, text=True, check=False, timeout=0.5).stdout or ""  # noqa: S603
    # Maybe we should symlink this path in .cache?
    return Tool(name=name, path=path.absolute(), version=version)


def execute(
    executable: Path | str,
    args: Iterable[Any] | None = None,
    *,
    check: bool = True,
    capture: bool = True,
    timeout: Duration | None = None,
) -> CompletedProcess[str]:
    """Run a short-lived program and immediately collect its output text.

    Args:
        executable: Path to an existing program, or the name of a program to look up.
        args: Arguments to pass to the program, stringified.
        check: Set to false to manually inspect the return code instead of throwing.
        capture: Set to ``False`` to forward stdout/stderr to the controlling shell.
        timeout: Max time to wait for the process to finish; ``None`` for no limit.

    Returns:
        Standard subprocess.CompletedProcess[str].
    """
    program = find_program(executable)
    args = [str(a) for a in args or []]
    with logger.span("program.run", {"path": str(program.path), "version": program.version}, level=Log.NOTICE) as span:
        cmd: list[str] = [str(program.path), *args]
        timeout_s = timeout.to(s).m if timeout else None

        start_s = time.perf_counter()
        process = run(cmd, capture_output=capture, text=True, check=check, timeout=timeout_s)  # noqa: S603
        duration_s = time.perf_counter() - start_s

        span.log(
            span.level,
            " ".join(args),
            code=process.returncode,
            seconds=duration_s,
            bytes_streamed=len(process.stdout or "") + len(process.stderr or ""),
        )
    return process


@asynccontextmanager
async def stream(
    executable: Path | str, args: Iterable[Any] | None = None, *, env: dict[str, str] | None = None
) -> AsyncGenerator[Process]:
    program = find_program(executable)
    args = [str(a) for a in args or []]
    cmd: list[str] = [str(program.path), *args]
    env = env or {}
    start_s = time.perf_counter()
    proc = await asyncio.create_subprocess_exec(
        *cmd, env={**os.environ, "CLICOLOR_FORCE": "1", "FORCE_COLOR": "1", "PYTHONUNBUFFERED": "1", **env}
    )

    with logger.span(
        "program.async", {"path": str(program.path), "version": program.version}, level=Log.NOTICE
    ) as span:
        try:
            yield proc
        finally:
            if proc.returncode is None:
                await proc.wait()
            print(cmd)
            duration_s = time.perf_counter() - start_s
            span.log(
                span.level,
                " ".join(args),
                code=proc.returncode,
                seconds=duration_s,
            )
