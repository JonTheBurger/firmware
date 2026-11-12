import sys
import sysconfig

import rich.traceback


def setup() -> None:
    rich.traceback.install(
        extra_lines=0,
        max_frames=5,
        suppress=[
            sys.prefix,
            sys.base_prefix,
            sysconfig.get_path("stdlib"),
            sysconfig.get_path("purelib"),
            sysconfig.get_path("platstdlib"),
        ],
    )
