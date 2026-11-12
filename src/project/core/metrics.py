import logging
import shutil
import subprocess
from logging import Filter, Handler, Logger, LogRecord
from typing import Any, Final

from opentelemetry import metrics, trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from project.core.error import user
from project.core.units import Duration, Memory, byte, ms, s

EXPORT_PERIOD: Duration = 500 * ms
EXPORT_EXIT_WAIT: Duration = 750 * ms


def setup() -> Handler:
    if not (git := shutil.which("git")):
        raise user.MissingProgramError(program="git")
    proc = subprocess.run([git, "config", "--get", "remote.origin.url"], text=True, check=False, capture_output=True)
    project_name = proc.stdout.split("/")[-1].replace(".git", "")
    resource = Resource.create({"service.name": f"project.{project_name}"})
    endpoint = "http://localhost:4317"

    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[
            PeriodicExportingMetricReader(
                OTLPMetricExporter(endpoint=endpoint, insecure=True),
                export_interval_millis=EXPORT_PERIOD.to(ms).m,
            )
        ],
    )
    metrics.set_meter_provider(meter_provider)

    tracer_provider = TracerProvider(resource=resource, meter_provider=meter_provider)
    tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint, insecure=True)))
    trace.set_tracer_provider(tracer_provider)

    provider = LoggerProvider(resource=resource, meter_provider=meter_provider)
    set_logger_provider(provider)
    provider.add_log_record_processor(
        BatchLogRecordProcessor(
            OTLPLogExporter(endpoint=endpoint, timeout=EXPORT_EXIT_WAIT.to(s).m),
            export_timeout_millis=EXPORT_EXIT_WAIT.to(ms).m,
        )
    )
    handler = LoggingHandler(level=logging.NOTSET, logger_provider=provider)
    handler.addFilter(DropTelemetryRecords())

    return handler


_METER: Final = metrics.get_meter("metric")
_BINARY_SIZE: Final = _METER.create_gauge("binary.size", unit="By", description="Binary size")
_EXECUTION_TIME: Final = _METER.create_histogram("execution.time", unit="s", description="Execution time")


class Metrics:
    def __init__(self, logger: Logger, level: int = logging.INFO) -> None:
        self._logger = logger
        self.level = level

    def _log(self, metric: str, measurement: Any, attributes: dict[str, Any]) -> None:
        """Logs with ``metric`` tag, thereby ensuring :class:`DropTelemetryRecords` filters it out for OTel."""
        self._logger.log(self.level, "[metric] [%s] [%s]", metric, measurement, extra={"metric": metric, **attributes})

    def binary_size(self, target: str, size: Memory) -> None:
        """Report the size of a binary."""
        as_bytes = size.to(byte).magnitude
        attributes: dict[str, Any] = {"target": target}
        self._log("binary.size", as_bytes, attributes)
        _BINARY_SIZE.set(as_bytes, attributes)

    def execution_time(self, duration: Duration) -> None:
        """Report the execution time."""
        as_seconds = duration.to(s).magnitude
        attributes: dict[str, Any] = {}
        self._log("execution.time", as_seconds, attributes)
        _EXECUTION_TIME.record(as_seconds, attributes)


class DropTelemetryRecords(Filter):
    """Prevents infinite logger loop by ensuring no telemetry items are piped to the logs."""

    def filter(self, record: LogRecord) -> bool:
        """True when the record should be kept (False = filter it out)."""
        return not hasattr(record, "metric") and not hasattr(record, "span") and not record.name.startswith(_BLOCKED)


_BLOCKED: Final = ("opentelemetry", "urllib3", "grpc", "httpx", "httpcore")
