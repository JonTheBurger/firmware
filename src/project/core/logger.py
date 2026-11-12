import json
import logging
import shutil
import subprocess
from collections.abc import Callable, Mapping
from logging import FileHandler, Filter, Formatter, Handler, Logger, LoggerAdapter, LogRecord
from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING, Any, ClassVar, Self, override

from opentelemetry import trace
from opentelemetry.trace import StatusCode, Tracer

from project.core.error import user
from project.core.metrics import Metrics

if TYPE_CHECKING:
    from opentelemetry.trace.span import Span

type Attributes = Mapping[str, bool | int | float | str | Attributes]
type ExcInfo = (
    bool
    | BaseException
    | tuple[type[BaseException], BaseException, TracebackType | None]
    | tuple[None, None, None]
    | None
)
type LogArgs = tuple[object, ...] | Mapping[str, object]
type LogFilter = Filter | Callable[[LogRecord], bool | LogRecord] | Any
type CallerInfo = tuple[str, int, str, str | None]


def setup() -> Logger:
    """Opt-in to this project's preferred logging defaults"""
    setup_log_levels()
    return setup_std_logger()


def setup_log_levels() -> None:
    """Registers custom log levels with the global python logging framework."""
    logging.addLevelName(Log.NOTICE, "NOTICE")
    logging.addLevelName(Log.VERBOSE, "VERBOSE")
    logging.addLevelName(Log.TRACE, "TRACE")


def setup_std_logger() -> Logger:
    if not (git := shutil.which("git")):
        raise user.MissingProgramError(program="git")
    proc = subprocess.run([git, "rev-parse", "--show-toplevel"], text=True, check=False, capture_output=True)
    project_root = (proc.stdout or "").strip()
    log_file = Path(project_root) / ".artifacts/project.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    file_handler = FileHandler(log_file)
    file_handler.setFormatter(BracketFormatter())
    root.addHandler(file_handler)

    return root


class Log:
    """Wraps a :class:`logging.Logger`, adding telemetry functionality.

    Changes from :class:`logging.Logger`:

    - ``getLogger(__name__)`` -> ``Log.get(__name__)``
    - ``logging.INFO`` -> ``Log.INFO``
    - Adds additional log levels, NOTICE, VERBOSE, and TRACE.
    - ``log()`` methods now accept ``kwargs``, which are merged into ``extra`` at a lower priority.
    - ``native_handle`` enables access to the original log.
    """

    def __init__(self, logger: Logger) -> None:
        self.native_handle: Logger = logger
        self.metric = Metrics(logger, level=Log.NOTICE)
        self._tracer = trace.get_tracer(logger.name)

    CRITICAL: ClassVar[int] = logging.CRITICAL  #: Never suppress this line
    FATAL: ClassVar[int] = logging.FATAL  #: Program cannot continue
    ERROR: ClassVar[int] = logging.ERROR  #: User intervention needed
    WARNING: ClassVar[int] = logging.WARNING  #: Unexpected event, may require user intervention
    NOTICE: ClassVar[int] = 25  #: Used for metrics
    INFO: ClassVar[int] = logging.INFO  #: State changes, steps in a pipeline, etc.
    VERBOSE: ClassVar[int] = 15
    DEBUG: ClassVar[int] = logging.DEBUG  #: Only use for debugging - DEBUG logs should not be committed
    TRACE: ClassVar[int] = 5  #: Process output, per-function call, etc.
    NOTSET: ClassVar[int] = logging.NOTSET

    @classmethod
    def get(cls, name: str | None = None) -> Self:
        """Factory analogous to ``logging.getLogger(name)``."""
        return cls(logging.getLogger(name))

    def span(self, event: str, attributes: Attributes | None = None, level: int | None = None) -> ScopedLog:
        return ScopedLog(self, self._tracer, event, attributes, level)

    def __repr__(self) -> str:
        return f"{type(self).__name__}{self.native_handle!r}"

    def __getattr__(self, name: str) -> Any:
        """Delegate any unknown members to the logger."""
        return getattr(self.native_handle, name)

    def debug(
        self,
        msg: object,
        /,
        *args: object,
        exc_info: ExcInfo = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Attributes | None = None,
        **kwargs: Any,
    ) -> None:
        self.native_handle.debug(
            msg,
            *args,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel + 1,
            extra=_merge_extra(extra, kwargs),
        )

    def info(
        self,
        msg: object,
        /,
        *args: object,
        exc_info: ExcInfo = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Attributes | None = None,
        **kwargs: Any,
    ) -> None:
        self.native_handle.info(
            msg,
            *args,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel + 1,
            extra=_merge_extra(extra, kwargs),
        )

    def warning(
        self,
        msg: object,
        /,
        *args: object,
        exc_info: ExcInfo = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Attributes | None = None,
        **kwargs: Any,
    ) -> None:
        self.native_handle.warning(
            msg,
            *args,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel + 1,
            extra=_merge_extra(extra, kwargs),
        )

    def error(
        self,
        msg: object,
        /,
        *args: object,
        exc_info: ExcInfo = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Attributes | None = None,
        **kwargs: Any,
    ) -> None:
        self.native_handle.error(
            msg,
            *args,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel + 1,
            extra=_merge_extra(extra, kwargs),
        )

    def exception(
        self,
        msg: object,
        /,
        *args: object,
        exc_info: ExcInfo = True,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Attributes | None = None,
        **kwargs: Any,
    ) -> None:
        self.native_handle.exception(
            msg,
            *args,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel + 1,
            extra=_merge_extra(extra, kwargs),
        )

    def critical(
        self,
        msg: object,
        /,
        *args: object,
        exc_info: ExcInfo = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Attributes | None = None,
        **kwargs: Any,
    ) -> None:
        self.native_handle.critical(
            msg,
            *args,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel + 1,
            extra=_merge_extra(extra, kwargs),
        )

    def fatal(
        self,
        msg: object,
        /,
        *args: object,
        exc_info: ExcInfo = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Attributes | None = None,
        **kwargs: Any,
    ) -> None:
        self.native_handle.fatal(
            msg,
            *args,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel + 1,
            extra=_merge_extra(extra, kwargs),
        )

    def log(  # noqa: PLR0913
        self,
        level: int,
        msg: object,
        /,
        *args: object,
        exc_info: ExcInfo = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Attributes | None = None,
        **kwargs: Any,
    ) -> None:
        self.native_handle.log(
            level,
            msg,
            *args,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel + 1,
            extra=_merge_extra(extra, kwargs),
        )

    # ------------------------------------------------------------------------------------------------------------------
    # The following are the same as in logging.Logger, except camelCase has been converted to snake_case.
    # ------------------------------------------------------------------------------------------------------------------

    @property
    def name(self) -> str:
        return self.native_handle.name

    @property
    def level(self) -> int:
        return self.native_handle.level

    @level.setter
    def level(self, value: int) -> None:
        self.native_handle.level = value

    @property
    def parent(self) -> Logger | None:
        return self.native_handle.parent

    @parent.setter
    def parent(self, value: Logger | None) -> None:
        self.native_handle.parent = value

    @property
    def propagate(self) -> bool:
        return self.native_handle.propagate

    @propagate.setter
    def propagate(self, value: bool) -> None:
        self.native_handle.propagate = value

    @property
    def handlers(self) -> list[Handler]:
        return self.native_handle.handlers

    @handlers.setter
    def handlers(self, value: list[Handler]) -> None:
        self.native_handle.handlers = value

    @property
    def disabled(self) -> bool:
        return self.native_handle.disabled

    @disabled.setter
    def disabled(self, value: bool) -> None:
        self.native_handle.disabled = value

    @property
    def filters(self) -> list[LogFilter]:
        return self.native_handle.filters

    @filters.setter
    def filters(self, value: list[LogFilter]) -> None:
        self.native_handle.filters = value

    @property
    def root(self) -> Logger:
        return self.native_handle.root

    @property
    def manager(self) -> logging.Manager:
        return self.native_handle.manager

    def set_level(self, level: int | str) -> None:
        self.native_handle.setLevel(level)

    def is_enabled_for(self, level: int) -> bool:
        return self.native_handle.isEnabledFor(level)

    def get_effective_level(self) -> int:
        return self.native_handle.getEffectiveLevel()

    def find_caller(self, stack_info: bool = False, stacklevel: int = 1) -> CallerInfo:  # noqa: FBT001, FBT002
        return self.native_handle.findCaller(stack_info, stacklevel)

    def make_record(  # noqa: PLR0913, PLR0917
        self,
        name: str,
        level: int,
        fn: str,
        lno: int,
        msg: object,
        args: LogArgs,
        exc_info: ExcInfo,
        func: str | None = None,
        extra: Mapping[str, object] | None = None,
        sinfo: str | None = None,
    ) -> LogRecord:
        return self.native_handle.makeRecord(
            name,
            level,
            fn,
            lno,
            msg,
            args,
            # pyrefly: ignore[bad-argument-type]
            exc_info,
            func,
            extra,
            sinfo,  # type: ignore[arg-type]
        )

    def handle(self, record: LogRecord) -> None:
        self.native_handle.handle(record)

    def call_handlers(self, record: LogRecord) -> None:
        self.native_handle.callHandlers(record)

    def add_handler(self, hdlr: Handler) -> None:
        self.native_handle.addHandler(hdlr)

    def remove_handler(self, hdlr: Handler) -> None:
        self.native_handle.removeHandler(hdlr)

    def has_handlers(self) -> bool:
        return self.native_handle.hasHandlers()

    def add_filter(self, filter: LogFilter) -> None:  # noqa: A002
        self.native_handle.addFilter(filter)

    def remove_filter(self, filter: LogFilter) -> None:  # noqa: A002
        self.native_handle.removeFilter(filter)

    def filter(self, record: LogRecord) -> bool | LogRecord:
        return self.native_handle.filter(record)

    def get_child(self, suffix: str) -> Self:
        """Return a wrapper (of the same type) around the child logger."""
        return type(self)(self.native_handle.getChild(suffix))

    def get_children(self) -> set[Logger]:
        return self.native_handle.getChildren()


class ScopedLog(LoggerAdapter):
    START_FMT: ClassVar[str] = "[start] [%s]"
    FINISH_FMT: ClassVar[str] = "[finish] [%s]"

    def __init__(
        self, logger: Log, tracer: Tracer, event: str, attributes: Attributes | None = None, level: int | None = None
    ) -> None:
        super().__init__(logger)
        self._logger = logger
        self._tracer = tracer
        self._event: str = event
        self._attributes: Attributes = attributes or {}
        self._level: int = level or self.logger.level

        self._id: str = ""
        self._span: Span | None = None
        self._ctx: Any | None = None

        self.namespace = self._event.rsplit(".", 1)[0]

    def __enter__(self) -> Self:
        self._ctx = self._tracer.start_as_current_span(self._event)
        self._span = self._ctx.__enter__()
        self._id = f"{self._span.get_span_context().span_id:x}"
        for name, value in self._attributes.items():
            self.set_attribute(name, value)
        self.log(self._level, self.START_FMT, self._event, extra={"span": self._id})
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None
    ) -> None:
        try:
            self.log(self._level, self.FINISH_FMT, self._event)
        finally:
            if self._ctx:
                self._ctx.__exit__(exc_type, exc, tb)

    def set_attribute(self, name: str, value: Any) -> None:
        if name.startswith(("_", "span")):
            return

        if not name.startswith(self.namespace):
            name = f"{self.namespace}.{name}"

        if self._span:
            self._span.set_attribute(name, value)

    def add_event(self, name: str, attributes: Attributes | None = None) -> None:
        if self._span:
            self._span.add_event(name, attributes)

    def set_success(self, *, description: str | None = None) -> None:
        if self._span:
            self._span.set_status(StatusCode.OK, description)

    def set_failed(self, *, description: str | None = None) -> None:
        if self._span:
            self._span.set_status(StatusCode.ERROR, description)

    @property
    def metric(self) -> Metrics:
        return self._logger.metric

    @override
    def process(self, msg: str, kwargs: Any) -> tuple[str, Any]:
        kwargs = self._attributes | kwargs
        for name, value in kwargs.items():
            self.set_attribute(name, value)
        return msg, kwargs

    def __getattr__(self, name: str) -> Any:
        """Delegate any unknown members to the logger."""
        return getattr(self._logger, name)


class BracketFormatter(Formatter):
    """Formats a log entry into an easily parseable text line."""

    @override
    def format(self, record: Any) -> str:
        msg = record.getMessage()
        if record.exc_info:
            msg = self.formatException(record.exc_info)

        return "[{t}] [{lvl:<5}] [{src}] | {msg:<32} | [{meta}]".format(
            t=self.formatTime(record, "%Y-%m-%d %H:%M:%S"),
            lvl=record.levelname.lower(),
            src=record.name.split(".")[0],
            msg=msg,
            meta=json.dumps({k: v for k, v in vars(record).items() if k not in _RESERVED}, cls=_JsonEncoder),
        )


class _JsonEncoder(json.JSONEncoder):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.precision = kwargs.pop("precision", 4)
        super().__init__(*args, **kwargs)

    @override
    def default(self, o: object) -> str:
        return str(o)

    @override
    def encode(self, o: object) -> str:
        return super().encode(self._round_floats(o))

    def _round_floats(self, obj: object) -> object:
        if isinstance(obj, float):
            return round(obj, self.precision)
        if isinstance(obj, dict):
            return {k: self._round_floats(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._round_floats(v) for v in obj]
        return obj


class JsonFormatter(Formatter):
    """Dumps all log fields as json."""

    @override
    def format(self, record: Any) -> str:
        """Dump all fields in record to a json string."""
        return json.dumps(record.__dict__, cls=_JsonEncoder)


def _merge_extra(extra: Attributes | None, kwargs: Mapping[str, object]) -> dict[str, object] | None:
    """Merges the extra and kwargs dicts, with extra at a higher precedence."""
    if not extra and not kwargs:
        return None
    merged = {**kwargs, **(extra or {})}
    if clash := _RESERVED & merged.keys():
        raise ValueError(f"extra keys collide with LogRecord attributes: {sorted(clash)}")
    return merged


_RESERVED: frozenset[str] = frozenset(LogRecord("", 0, "", 0, "", (), None).__dict__) | {"message", "asctime"}
