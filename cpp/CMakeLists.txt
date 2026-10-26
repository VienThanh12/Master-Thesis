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

# --- Sanitisers ---------------------------------------------------------------
# Instruments the whole tree -- library, tests, and the conformance runner -- so
# the parity suite itself can be run under dynamic analysis. This answers a
# fairness question the functional tests cannot: safe Rust rules out data races
# and memory errors at compile time, so unless the C++ arm is checked for them
# too, "the two implementations behave identically" rests on the C++ side merely
# not having failed yet. faults/ shows the tools catch injected defects; this
# shows they find nothing in the real implementation.
#
# Detection builds, not measurement builds: -O1 with frame pointers, because
# sanitiser output from an -O2 build is much harder to read and the numbers from
# an instrumented binary are meaningless anyway. Never report timings from one.
set(UECM_SANITIZER "off" CACHE STRING
    "Sanitiser to instrument the build with: off|address|thread|undefined|address+undefined")
set_property(CACHE UECM_SANITIZER PROPERTY STRINGS
             off address thread undefined address+undefined)

if(NOT UECM_SANITIZER STREQUAL "off")
  set(_san_flags "")
  if(UECM_SANITIZER STREQUAL "address")
    set(_san_flags -fsanitize=address)
  elseif(UECM_SANITIZER STREQUAL "thread")
    set(_san_flags -fsanitize=thread)
  elseif(UECM_SANITIZER STREQUAL "undefined")
    # Recovering from UB would let a test pass while printing a diagnostic, so
    # the run has to abort instead.
    set(_san_flags -fsanitize=undefined -fno-sanitize-recover=undefined)
  elseif(UECM_SANITIZER STREQUAL "address+undefined")
    set(_san_flags -fsanitize=address,undefined -fno-sanitize-recover=undefined)
  else()
    message(FATAL_ERROR "UECM_SANITIZER: unknown value '${UECM_SANITIZER}'"
                        " (off|address|thread|undefined|address+undefined)")
  endif()

  message(STATUS "uecm: SANITISER build (${UECM_SANITIZER}) -- detection only, do not benchmark")
  add_compile_options(${_san_flags} -O1 -g -fno-omit-frame-pointer)
  add_link_options(${_san_flags})
endif()

# --- Coverage -----------------------------------------------------------------
# Instruments for gcov so cpp/coverage.sh can report what fraction of the
# implementation the parity suite actually executes. A test suite's authority
# rests on its reach, and "all tests pass" says nothing about reach; this is the
# number that does.
#
# -O0 because the optimiser inlines and merges lines until per-line attribution
# stops meaning anything. Another detection build, never a measurement one.
option(UECM_COVERAGE "Instrument for gcov line coverage (implies -O0)" OFF)
if(UECM_COVERAGE)
  message(STATUS "uecm: COVERAGE build -- instrumented for gcov, do not benchmark")
  add_compile_options(--coverage -O0 -g)
  add_link_options(--coverage)
endif()

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

# Swaps the deque-backed std::queue inside BoundedQueue for a preallocated ring, so
# the shard queue stops calling the allocator on the hot path while its locking stays
# byte-identical. Tests whether the overload divergence against Rust is allocation
# under the queue mutex rather than the language. See include/uecm/ring_queue.hpp.
option(UECM_RING_QUEUE "PROBE ONLY: preallocated ring inside the bounded queue" OFF)
if(UECM_RING_QUEUE)
  message(STATUS "uecm: PROBE build -- ring-backed shard queue, not the reported configuration")
  target_compile_definitions(uecm PUBLIC UECM_RING_QUEUE)
endif()

# Lets one message carry several signalling operations for one shard
# (Service::handle_signaling_batch), so the batch probe can separate the cost of a
# handoff from the cost of an operation in a loaded service. Twin of the Rust feature
# batch-probe. See docs/OVERLOAD_MECHANISM.md, Method 2.
option(UECM_BATCH_PROBE "PROBE ONLY: batched signalling request and the batch probe" OFF)
if(UECM_BATCH_PROBE)
  message(STATUS "uecm: PROBE build -- batched signalling request, not the reported configuration")
  target_compile_definitions(uecm PUBLIC UECM_BATCH_PROBE)
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

# --- Method 3 pilot (not the campaign bench) ----------------------------------
# Open-loop async signal or mixed lifecycle. Twin of rust/examples/pipeline.rs.
add_executable(pipeline bench/pipeline.cpp)
target_include_directories(pipeline PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/bench)
target_link_libraries(pipeline PRIVATE uecm)
if(UECM_USE_JEMALLOC AND JEMALLOC_LIB)
  target_compile_definitions(pipeline PRIVATE UECM_ALLOC_NAME="jemalloc")
else()
  target_compile_definitions(pipeline PRIVATE UECM_ALLOC_NAME="system")
endif()

# --- Batch probe (Method 2, not the campaign bench) ----------------------------
# Twin of rust/examples/batch.rs. Built only with UECM_BATCH_PROBE.
if(UECM_BATCH_PROBE)
  add_executable(batch bench/batch.cpp)
  target_include_directories(batch PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/bench)
  target_link_libraries(batch PRIVATE uecm)
  if(UECM_USE_JEMALLOC AND JEMALLOC_LIB)
    target_compile_definitions(batch PRIVATE UECM_ALLOC_NAME="jemalloc")
  else()
    target_compile_definitions(batch PRIVATE UECM_ALLOC_NAME="system")
  endif()
endif()

# --- Matched-design probe (not the campaign bench) -----------------------------
# The same hand-written queue and reply slot in both languages around the real
# ShardCore. Changes nothing in the library, and stays off so the full build that
# bench/adoption_cost.py times is unchanged. Twin of rust/examples/matched.rs.
# See docs/OVERLOAD_MECHANISM.md §4.16.
option(UECM_MATCHED_PROBE "PROBE ONLY: matched-design probe executable" OFF)
if(UECM_MATCHED_PROBE)
  add_executable(matched bench/matched.cpp)
  target_include_directories(matched PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/bench)
  target_link_libraries(matched PRIVATE uecm)
  if(UECM_USE_JEMALLOC AND JEMALLOC_LIB)
    target_compile_definitions(matched PRIVATE UECM_ALLOC_NAME="jemalloc")
  else()
    target_compile_definitions(matched PRIVATE UECM_ALLOC_NAME="system")
  endif()
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
  foreach(t test_hash test_shard_core test_service test_invariants test_concurrency
            test_state_matrix)
    add_executable(${t} tests/${t}.cpp)
    target_link_libraries(${t} PRIVATE uecm)
    add_test(NAME ${t} COMMAND ${t})
  endforeach()
  if(UECM_BATCH_PROBE)
    add_executable(test_batch tests/test_batch.cpp)
    target_link_libraries(test_batch PRIVATE uecm)
    add_test(NAME test_batch COMMAND test_batch)
  endif()
endif()
