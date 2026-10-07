//! Configuration parameters. See `../spec/SPECIFICATION.md` §9.

#[derive(Debug, Clone, Copy)]
pub struct Config {
    /// Number of shards / worker threads.
    pub n_shards: u64,
    /// Per-shard bounded queue capacity (blocking backpressure).
    pub queue_capacity: usize,
    /// Max contexts per shard before `CapacityExceeded`.
    pub max_contexts_per_shard: u64,
    /// Initial reserved capacity of each shard's map.
    pub initial_shard_capacity: usize,
    /// Diagnostic only. When set, the worker reads the clock after dequeue and
    /// before the operation. Compared and confirmatory runs leave this false.
    pub stamp_start: bool,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            n_shards: 8,
            queue_capacity: 1024,
            max_contexts_per_shard: 200_000,
            initial_shard_capacity: 4096,
            stamp_start: false,
        }
    }
}

/// Max data radio bearers per context (spec §4.2 / §9).
pub const MAX_DRBS: usize = 8;
/// Max signaling payload length in bytes (spec §6 / §9).
pub const MAX_SIGNALING_PAYLOAD: usize = 64;
