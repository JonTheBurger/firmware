cmake_minimum_required(VERSION 4.3)
project(
  firmware
  LANGUAGES
    C
    CXX
    ASM
)

add_subdirectory(external SYSTEM EXCLUDE_FROM_ALL)
add_executable(firmware.main "src/firmware/main.cxx")
target_link_libraries(firmware.main PRIVATE firmware.hal)
target_link_options(
  firmware.main
  PRIVATE
    -T
    "${CMAKE_CURRENT_LIST_DIR}/src/firmware/STM32F429xx_FLASH.ld"
)

add_library(firmware.hal)
target_sources(
  firmware.hal
  PRIVATE
    "src/firmware/hal/led.cxx"
  PUBLIC
    FILE_SET HEADERS
      BASE_DIRS
        "src"
      FILES
        "src/firmware/hal/led.hxx"
)
target_link_libraries(firmware.hal PUBLIC "$<LINK_LIBRARY:WHOLE_ARCHIVE,stm32f429i-disc1>")
