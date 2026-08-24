// Defect: use-after-move.
// Admission builds a UE context, moves it into the shard map, and then composes
// its acknowledgement from the local variable it has just moved from. The
// identity comes back empty.
//
// This case is in the catalogue for what the sanitizers do *not* say about it.
// Nothing here is corrupted and nothing is undefined: a moved-from std::string
// is in a valid but unspecified state, and reading it is well-formed C++. So
// ASan, TSan and UBSan all report clean while the context is admitted under an
// empty IMSI. Every other memory-safety class in the catalogue is caught by at
// least one of the three. See rust/use_after_move.rs, where the same program
// does not build.
#include <cstdio>
#include <map>
#include <string>
#include <utility>

struct UeContext {
  std::string imsi;
  int drb_count;
};

int main() {
  std::map<unsigned long, UeContext> store;
  UeContext ctx{"244091234567890", 3};

  store.emplace(1001, std::move(ctx));

  // The acknowledgement is built from `ctx`, which no longer owns its identity.
  std::printf("admitted UE '%s' with %d bearers\n", ctx.imsi.c_str(),
              ctx.drb_count);

  const bool identity_lost = ctx.imsi.empty();
  std::printf("identity lost: %s\n", identity_lost ? "yes" : "no");
  return identity_lost ? 1 : 0;
}
