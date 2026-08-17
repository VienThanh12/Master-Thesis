cmake_minimum_required(VERSION 3.20)
project(uecm_cpp LANGUAGES CXX VERSION 0.1.0)

# --- Standard -----------------------------------------------------------------
set(CMAKE_CXX_STANDARD 23)          # std::expected requires C++23
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
  set(CMAKE_BUILD_TYPE Release CACHE STRING "" FORCE)
endif()

# Matched optimisation with the Rust release build (see spec §3, Design & Impl).
set(CMAKE_CXX_FLAGS_RELEASE "-O2 -DNDEBUG")

add_compile_options(-Wall -Wextra -Wpedantic)

# --- Core library -------------------------------------------------------------
add_library(uecm STATIC
  src/shard_core.cpp
  src/service.cpp
)
target_include_directories(uecm PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)

find_package(Threads REQUIRED)
target_link_libraries(uecm PUBLIC Threads::Threads)

# --- Attribution probe, not a compared configuration --------------------------
# Swaps the node-based std::unordered_map for an open-addressed table with the
# same pinned hash, to test whether the core-operation gap against Rust is the
# container rather than the language. The reported C++ arm keeps the standard
# map; see include/uecm/flat_map.hpp.
option(UECM_FLAT_MAP "PROBE ONLY: open-addressed intra-shard map" OFF)
if(UECM_FLAT_MAP)
  message(STATUS "uecm: PROBE build -- open-addressed map, not the reported configuration")
  target_compile_definitions(uecm PUBLIC UECM_FLAT_MAP)
endif()

# --- Optional jemalloc (spec §3: identical allocator across languages) --------
option(UECM_USE_JEMALLOC "Link jemalloc to isolate language effects from allocator" OFF)
if(UECM_USE_JEMALLOC)
  find_library(JEMALLOC_LIB NAMES jemalloc libjemalloc.so.2)
  if(JEMALLOC_LIB)
    message(STATUS "uecm: linking jemalloc: ${JEMALLOC_LIB}")
    target_link_libraries(uecm PUBLIC ${JEMALLOC_LIB})
  else()
    message(WARNING "uecm: UECM_USE_JEMALLOC=ON but jemalloc not found")
  endif()
endif()

# --- Conformance/parity runner (spec §11) -------------------------------------
add_executable(conformance_runner tools/conformance_runner.cpp)
target_link_libraries(conformance_runner PRIVATE uecm)

# --- Benchmark (spec §3/§10) --------------------------------------------------
add_executable(bench bench/bench.cpp)
target_include_directories(bench PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/bench)
target_link_libraries(bench PRIVATE uecm)
if(UECM_USE_JEMALLOC AND JEMALLOC_LIB)
  target_compile_definitions(bench PRIVATE UECM_ALLOC_NAME="jemalloc")
else()
  target_compile_definitions(bench PRIVATE UECM_ALLOC_NAME="system")
endif()

# --- Latency-budget decomposition ---------------------------------------------
# Separates the operation's own work from the cross-thread handoff the sweep
# bundles into it. See bench/latency_budget.cpp.
add_executable(latency_budget bench/latency_budget.cpp)
target_link_libraries(latency_budget PRIVATE uecm)

# --- Contended-queue microbenchmark -------------------------------------------
# Isolates the bounded queue and completion primitives under multi-producer load.
# See bench/queue_contention.cpp.
add_executable(queue_contention bench/queue_contention.cpp)
target_link_libraries(queue_contention PRIVATE uecm)

# --- Tests --------------------------------------------------------------------
option(UECM_BUILD_TESTS "Build the C++ conformance/smoke tests" ON)
if(UECM_BUILD_TESTS)
  enable_testing()
  foreach(t test_hash test_shard_core test_service test_invariants test_concurrency)
    add_executable(${t} tests/${t}.cpp)
    target_link_libraries(${t} PRIVATE uecm)
    add_test(NAME ${t} COMMAND ${t})
  endforeach()
endif()
