import project.core.backtrace
import project.core.logger
import project.core.metrics


# TODO(JON): This should probably be a context manager with shutdown
def setup() -> None:
    project.core.backtrace.setup()
    otel_handler = project.core.metrics.setup()
    project.core.logger.setup().addHandler(otel_handler)
