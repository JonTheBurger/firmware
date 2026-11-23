from contextlib import contextmanager
from typing import TYPE_CHECKING

import project.core.backtrace
import project.core.logger
import project.core.metrics
from project.core.logger import Log

if TYPE_CHECKING:
    from collections.abc import Generator


@contextmanager
def setup() -> Generator:
    project.core.backtrace.setup()
    with project.core.metrics.setup() as otel_handler:
        project.core.logger.setup().addHandler(otel_handler)
        try:
            yield
        finally:
            Log.get().remove_handler(otel_handler)
