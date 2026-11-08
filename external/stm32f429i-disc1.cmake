set(_backup "${CMAKE_PROJECT_NAME}")
# Set this temporarily, as STM32 tries to modify our main executable directly (bad bad bad!)
set(CMAKE_PROJECT_NAME ".stm32f429i-disc1")
add_library("${CMAKE_PROJECT_NAME}")
add_subdirectory("${CMAKE_CURRENT_LIST_DIR}/stm32f429i-disc1/cmake/stm32cubemx")
set(CMAKE_PROJECT_NAME "${_backup}")
unset(_backup)

# Forward properties
add_library(stm32f429i-disc1)
target_sources(stm32f429i-disc1 PRIVATE $<TARGET_PROPERTY:.stm32f429i-disc1,SOURCES>)
target_include_directories(
  stm32f429i-disc1
  PUBLIC
    $<TARGET_PROPERTY:.stm32f429i-disc1,INCLUDE_DIRECTORIES>
    $<TARGET_PROPERTY:.stm32f429i-disc1,INTERFACE_INCLUDE_DIRECTORIES>
)
target_compile_definitions(
  stm32f429i-disc1
  PUBLIC
    $<TARGET_PROPERTY:.stm32f429i-disc1,COMPILE_DEFINITIONS>
    $<TARGET_PROPERTY:.stm32f429i-disc1,INTERFACE_COMPILE_DEFINITIONS>
)
target_compile_options(
  stm32f429i-disc1
  PUBLIC
    $<TARGET_PROPERTY:.stm32f429i-disc1,COMPILE_OPTIONS>
    $<TARGET_PROPERTY:.stm32f429i-disc1,INTERFACE_COMPILE_OPTIONS>
)
target_link_options(
  stm32f429i-disc1
  PUBLIC
    $<TARGET_PROPERTY:.stm32f429i-disc1,LINK_OPTIONS>
    $<TARGET_PROPERTY:.stm32f429i-disc1,INTERFACE_LINK_OPTIONS>
)
target_link_directories(
  stm32f429i-disc1
  PUBLIC $<TARGET_PROPERTY:.stm32f429i-disc1,LINK_DIRECTORIES>
)
target_link_libraries(
  stm32f429i-disc1
  PUBLIC
    $<TARGET_PROPERTY:.stm32f429i-disc1,LINK_LIBRARIES>
    $<TARGET_PROPERTY:.stm32f429i-disc1,INTERFACE_LINK_LIBRARIES>
)
