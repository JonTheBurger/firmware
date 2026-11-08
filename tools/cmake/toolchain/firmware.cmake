include("${CMAKE_CURRENT_LIST_DIR}/arm-none-eabi-gcc.cmake")

set(_arch_flags "-ffreestanding -mcpu=cortex-m4 -mthumb -mfloat-abi=hard -mfpu=fpv4-sp-d16")
set(CMAKE_C_FLAGS_INIT "${_arch_flags} -ffunction-sections -fdata-sections")
set(CMAKE_CXX_FLAGS_INIT "${CMAKE_C_FLAGS_INIT} -fno-exceptions -fno-rtti -fno-threadsafe-statics")
set(CMAKE_ASM_FLAGS_INIT "-x assembler-with-cpp")
set(CMAKE_EXE_LINKER_FLAGS_INIT "${_arch_flags} --specs=nosys.specs --specs=nano.specs LINKER:--gc-sections")
unset(_arch_flags)

set(CMAKE_C_FLAGS_DEBUG "-Og -g3 -DDEBUG=1")
set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_C_FLAGS_DEBUG}")
set(CMAKE_ASM_FLAGS_DEBUG "${CMAKE_C_FLAGS_DEBUG}")

set(CMAKE_C_FLAGS_RELEASE "-Os -g3 -DNDEBUG=1")
set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_C_FLAGS_RELEASE}")
set(CMAKE_ASM_FLAGS_RELEASE "${CMAKE_C_FLAGS_RELEASE}")
