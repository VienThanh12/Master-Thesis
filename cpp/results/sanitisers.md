# C++ parity suite under dynamic analysis

Regenerate with `cpp/sanitise.sh`. Categorical outcomes only, so they do
not move with host load.

- C++ compiler: `g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0`
- ASLR wrapper: `setarch x86_64 -R`
- `ASAN_OPTIONS`: `detect_leaks=1:detect_stack_use_after_return=1:strict_string_checks=1`
- `TSAN_OPTIONS`: `detect_deadlocks=1:second_deadlock_stack=1:halt_on_error=1`
- `UBSAN_OPTIONS`: `print_stacktrace=1:halt_on_error=1`
- Generated vectors per run: 9 (at 400 ops each)

| Sanitiser | Test binaries | Conformance vectors |
|---|---|---|
| `address+undefined` | clean | clean (16 vectors) |
| `thread` | clean | clean (16 vectors) |
| `undefined` | clean | clean (16 vectors) |

All clean: no memory error, no undefined behaviour, and no data race was
reported anywhere in the C++ implementation across the parity suite.

This is a negative result and is worth exactly what a negative result is
worth: sanitisers observe the executions that happen, so this covers the
paths the suite drives and says nothing about paths it does not. It is not
the compile-time guarantee the Rust variant has, and the distinction is the
point -- the coverage-bounded version of the same property.
