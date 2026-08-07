/* RQ4 FFI prototype, C ABI over the Rust UECM service.
 *
 * This header is the migration seam a C++ host compiles against. It is written by
 * hand (no bindgen) to keep the prototype dependency-free and to make the interop
 * surface explicit and measurable.
 *
 * Ownership / threading:
 *   - `UecmService*` is an opaque owning handle. Create it with
 *     uecm_service_create() and release it exactly once with
 *     uecm_service_destroy(). Do not dereference it.
 *   - The service is internally multi-threaded (thread-per-shard). The handle may
 *     be shared by multiple C++ threads: every entry point is a message submit +
 *     blocking completion, so concurrent calls are safe.
 *
 * Status convention (see spec sec 6.6):
 *   0  = Ok
 *   1..5 = 1 + OpError    (NotFound=1, AlreadyExists=2, InvalidState=3,
 *                          CapacityExceeded=4, InvalidArgument=5)
 *   -1 = null handle / misuse from the C++ side
 */
#ifndef UECM_FFI_H
#define UECM_FFI_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct UecmService UecmService;

enum {
  UECM_OK = 0,
  UECM_ERR_NULL = -1
};

/* Lifecycle. */
UecmService* uecm_service_create(uint64_t n_shards, uint32_t queue_capacity);
void         uecm_service_destroy(UecmService* h);

/* Operations (mirror the spec sec 6 API). Return a status code as above. */
int32_t uecm_create_context(UecmService* h, uint64_t ue_id, uint32_t serving_cell_id);
int32_t uecm_setup_connection(UecmService* h, uint64_t ue_id);
int32_t uecm_handle_signaling(UecmService* h, uint64_t ue_id, uint8_t kind,
                              uint16_t payload_len, uint64_t* out_new_count);
int32_t uecm_add_drb(UecmService* h, uint64_t ue_id, uint8_t drb_id,
                     uint8_t qos_flow_id, uint32_t teid);
int32_t uecm_release_context(UecmService* h, uint64_t ue_id);
int32_t uecm_lookup(UecmService* h, uint64_t ue_id, uint8_t* out_state,
                    uint64_t* out_messages_handled);

/* Total live contexts across all shards. */
uint64_t uecm_count(UecmService* h);

/* Raw boundary-cost probe: crosses the C ABI and returns x+1. Lets the host
 * measure the intrinsic FFI crossing cost separately from the op round-trip. */
uint64_t uecm_abi_noop(uint64_t x);

/* Diagnostic name for a status code; points to a static string (do not free). */
const char* uecm_status_str(int32_t code);

#ifdef __cplusplus
}  /* extern "C" */
#endif

#endif /* UECM_FFI_H */
