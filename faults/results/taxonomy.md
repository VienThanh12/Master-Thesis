# RQ2 defect-class taxonomy

- C++ compiler: `g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0` (`-std=c++23`)
- Rust compiler: `rustc 1.97.1 (8bab26f4f 2026-07-14)` (`--edition 2021`)
- ASLR wrapper: `setarch x86_64 -R`

| Defect class | C++ ASan | C++ TSan | C++ detection stage | Rust outcome |
|---|---|---|---|---|
| use_after_free | detected | detected | runtime (ASan+TSan) | compile-time prevented (E0499) |
| double_free | detected | clean | runtime (ASan) | compile-time prevented (E0382) |
| iterator_invalidation | detected | detected | runtime (ASan+TSan) | compile-time prevented (E0502) |
| data_race | clean | detected | runtime (TSan) | compile-time prevented (E0373,E0382,E0502) |
| unguarded_shared_mutation | clean | detected | runtime (TSan) | compile-time prevented (E0502,E0524,E0597) |
| lock_order_deadlock | hung | detected | runtime (TSan) | not prevented (compiles; deadlocks) |
| lost_update | clean | clean | undetected | not prevented (compiles; wrong result) |
