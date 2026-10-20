//! The batch probe's request (`--features batch-probe`). Twin of cpp/tests/test_batch.cpp.
#![cfg(feature = "batch-probe")]

use uecm::hash::shard_index;
use uecm::{Config, CreateParams, Service, SignalingMsg, UeId};

fn ids_on_shard(shard: u64, n_shards: u64, count: usize) -> Vec<UeId> {
    (1u64..)
        .filter(|&id| shard_index(id, n_shards) == shard)
        .take(count)
        .collect()
}

#[test]
fn batch_counts_the_operations_that_succeed() {
    let cfg = Config {
        n_shards: 4,
        ..Config::default()
    };
    let mut svc = Service::new(cfg);
    svc.start();
    let ids = ids_on_shard(2, 4, 4);
    for &id in &ids[..3] {
        svc.create_context(
            id,
            CreateParams {
                serving_cell_id: 7,
                security_key: [0u8; 32],
            },
        )
        .unwrap();
        svc.setup_connection(id).unwrap();
    }
    let msg = SignalingMsg {
        kind: 3,
        payload_len: 10,
        payload: [0u8; 64],
    };

    let all = svc.handle_signaling_batch(ids[..3].to_vec(), msg).unwrap();
    assert!(all.accepted);
    assert_eq!(all.new_messages_handled, 3);

    // The fourth id was never created, so one of four fails.
    let some = svc.handle_signaling_batch(ids.clone(), msg).unwrap();
    assert!(!some.accepted);
    assert_eq!(some.new_messages_handled, 3);

    // Each successful operation in a batch is a real signalling call.
    let one = svc.handle_signaling(ids[0], msg).unwrap();
    assert_eq!(one.new_messages_handled, 3);

    let empty = svc.handle_signaling_batch(Vec::new(), msg).unwrap();
    assert!(empty.accepted);
    assert_eq!(empty.new_messages_handled, 0);
    svc.shutdown();
}
