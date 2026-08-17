// Report the in-memory size and layout of the compared record types.
//
// Section 6.2.1 and Section 6.4.5 of the thesis quote these as measured values,
// so they are measured here and reach the prose through generated macros rather
// than being typed in. The Rust counterpart is rust/examples/layout.rs; both are
// driven by bench/artefact_facts.py.
//
// Field offsets are reported too, because the prose explains the C++ figure by
// where the padding falls, and an explanation of a number that is regenerated
// should be regenerated with it.
#include <cstddef>
#include <cstdio>

#include "uecm/message.hpp"
#include "uecm/types.hpp"

int main() {
  using namespace uecm;
  std::printf("ue_context_bytes=%zu\n", sizeof(UeContext));
  std::printf("ue_context_align=%zu\n", alignof(UeContext));
  std::printf("ue_context_view_bytes=%zu\n", sizeof(UeContextView));
  std::printf("request_bytes=%zu\n", sizeof(Request));
  std::printf("signaling_msg_bytes=%zu\n", sizeof(SignalingMsg));
  std::printf("drb_entry_bytes=%zu\n", sizeof(DrbEntry));

  std::printf("off_ue_id=%zu\n", offsetof(UeContext, ue_id));
  std::printf("off_state=%zu\n", offsetof(UeContext, state));
  std::printf("off_serving_cell_id=%zu\n", offsetof(UeContext, serving_cell_id));
  std::printf("off_rrc_transaction_id=%zu\n", offsetof(UeContext, rrc_transaction_id));
  std::printf("off_security_key=%zu\n", offsetof(UeContext, security_key));
  std::printf("off_drbs=%zu\n", offsetof(UeContext, drbs));
  std::printf("off_messages_handled=%zu\n", offsetof(UeContext, messages_handled));
  std::printf("off_last_activity_seq=%zu\n", offsetof(UeContext, last_activity_seq));
  return 0;
}
