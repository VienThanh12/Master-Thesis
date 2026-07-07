// Defect: double-free.
// A UE context is heap-allocated and deleted twice (e.g. two release paths both
// believing they own it). Detected by AddressSanitizer.
#include <cstdio>

struct UeContext {
  unsigned long ue_id;
};

int main() {
  UeContext* c = new UeContext{1001};
  delete c;  // first release
  delete c;  // double-free: c is a dangling owner
  std::printf("released ue_id twice\n");
  return 0;
}
