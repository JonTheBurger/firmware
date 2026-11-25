from project.tools.cmake import CMake


async def build() -> None:
    cmake = CMake.tool()
    cmake.preset = "stm32f4-debug"
    await cmake.configure()
    await cmake.build()
