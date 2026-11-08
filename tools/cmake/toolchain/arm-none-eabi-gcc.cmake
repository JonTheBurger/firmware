#[=======================================================================[.rst:

.. _toolchain-arm-none-eabi-gcc:

arm-none-eabi-gcc
-----------------

.. _ARM GNU Toolchain: https://developer.arm.com/tools-and-software/gnu-toolchain

Uses the 32-bit ARM GNU compiler without special flags.
Install from `ARM GNU Toolchain`_ or from you distro's package manager:

.. code-block:: bash

   # Ubuntu
   sudo apt-get install -y \
     binutils-arm-none-eabi \
     gcc-arm-none-eabi \
     libnewlib-nano-arm-none-eabi \
     libstdc++-arm-none-eabi-newlib

   # Fedora
   sudo dnf install -y \
     arm-none-eabi-gcc-cs \
     arm-none-eabi-gcc-cs-c++ \
     arm-none-eabi-newlib

Input Variables
^^^^^^^^^^^^^^^

``CC_SEARCH_PATHS``

A semicolon-separated list of directories to search for ``arm-none-eabi-gcc``, in addition to typical system paths.

Example Usages
^^^^^^^^^^^^^^

The toolchain can be set from the command line:

.. code-block:: bash

   cmake -DCMAKE_TOOLCHAIN_FILE=<path-to>/arm-none-eabi-gcc.cmake

It can also be included from a more specific toolchain file instead:

.. code-block:: cmake

   # your-toolchain.cmake
   include("<path-to>/arm-none-eabi-gcc.cmake")

   set(_arch_flags "-ffreestanding -mcpu=cortex-m4 -mthumb -mfloat-abi=hard -mfpu=fpv4-sp-d16")
   set(CMAKE_C_FLAGS_INIT "${_arch_flags} -ffunction-sections -fdata-sections")
   set(CMAKE_CXX_FLAGS_INIT "${CMAKE_C_FLAGS} -fno-exceptions -fno-rtti -fno-threadsafe-statics")
   set(CMAKE_ASM_FLAGS_INIT "-x assembler-with-cpp")
   set(CMAKE_EXE_LINKER_FLAGS_INIT "${_arch_flags} --specs=nosys.specs --specs=nano.specs LINKER:--gc-sections")
   unset(_arch_flags)

   set(CMAKE_C_FLAGS_DEBUG "-Og -g3 -DDEBUG=1")
   set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_C_FLAGS_DEBUG}")
   set(CMAKE_ASM_FLAGS_DEBUG "${CMAKE_C_FLAGS_DEBUG}")

   set(CMAKE_C_FLAGS_RELEASE "-Os -g3 -DNDEBUG=1")
   set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_C_FLAGS_RELEASE}")
   set(CMAKE_ASM_FLAGS_RELEASE "${CMAKE_C_FLAGS_RELEASE}")

#]=======================================================================]
cmake_minimum_required(VERSION 4.3)

set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_SYSTEM_VERSION 1)
set(CMAKE_SYSTEM_PROCESSOR arm)
set(CMAKE_EXECUTABLE_SUFFIX ".elf")
set(CMAKE_EXECUTABLE_SUFFIX_C ".elf")
set(CMAKE_EXECUTABLE_SUFFIX_CXX ".elf")
set(CMAKE_EXECUTABLE_SUFFIX_ASM ".elf")
set(CMAKE_LINK_LIBRARY_USING_WHOLE_ARCHIVE "LINKER:--push-state,--whole-archive" "<LINK_ITEM>" "LINKER:--pop-state")
set(CMAKE_LINK_LIBRARY_USING_WHOLE_ARCHIVE_SUPPORTED True)
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)
set_property(GLOBAL PROPERTY TARGET_SUPPORTS_SHARED_LIBS FALSE)

find_program(CMAKE_C_COMPILER NAMES "arm-none-eabi-gcc" HINTS ${CC_SEARCH_PATHS} PATH_SUFFIXES bin REQUIRED)
set(CMAKE_ASM_COMPILER "${CMAKE_C_COMPILER}" CACHE FILEPATH "")
cmake_path(GET CMAKE_C_COMPILER PARENT_PATH _CC_BINDIR)
cmake_path(GET _CC_BINDIR PARENT_PATH CMAKE_FIND_ROOT_PATH)
find_program(CMAKE_CXX_COMPILER NAMES "arm-none-eabi-g++" "arm-none-eabi-gcc" HINTS "${CMAKE_FIND_ROOT_PATH}")

set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)
