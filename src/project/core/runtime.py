import project.core.backtrace
import project.core.logger


def setup() -> None:
    project.core.logger.setup()
    project.core.backtrace.setup()
