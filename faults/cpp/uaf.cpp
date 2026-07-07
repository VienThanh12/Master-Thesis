// Defect: use-after-free.
// A raw pointer into the shard map is retained across an erase that frees the
// node, then dereferenced. This is the C++ analogue of holding a reference to a
// UE context after it has been released. Detected by AddressSanitizer.
#include <cstdio>
#include <unordered_map>

struct UeContext {
  unsigned long ue_id;
  unsigned long messages_handled;
};

int main() {
  std::unordered_map<unsigned long, UeContext> ctxs;
  ctxs[1001] = UeContext{1001, 0};

  UeContext* p = &ctxs.at(1001);  // alias into the container
  ctxs.erase(1001);               // frees the node that p refers to
  p->messages_handled += 1;       // use-after-free

  std::printf("messages_handled=%lu\n", p->messages_handled);
  return 0;
}
