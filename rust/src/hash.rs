//! Pinned hashing functions. See `../spec/SPECIFICATION.md` §8.
//! These MUST be bit-for-bit identical to the C++ implementation.

use std::hash::{BuildHasher, Hasher};

/// Shard selection via the SplitMix64 finalizer, then modulo `n_shards` (§8.1).
/// All arithmetic wraps modulo 2^64.
#[inline]
pub fn shard_index(ue_id: u64, n_shards: u64) -> u64 {
    let mut x = ue_id;
    x = (x ^ (x >> 30)).wrapping_mul(0xBF58476D1CE4E5B9);
    x = (x ^ (x >> 27)).wrapping_mul(0x94D049BB133111EB);
    x ^= x >> 31;
    x % n_shards
}

/// FNV-1a 64-bit over the 8 little-endian bytes of the key (§8.2).
#[inline]
pub fn fnv1a_64(key: u64) -> u64 {
    let mut h: u64 = 0xcbf29ce484222325;
    for b in key.to_le_bytes() {
        h = (h ^ b as u64).wrapping_mul(0x100000001b3);
    }
    h
}

/// A `Hasher` that computes FNV-1a; keys are hashed as little-endian bytes so
/// the result matches [`fnv1a_64`] and the C++ `FnvHash` exactly.
pub struct FnvHasher {
    state: u64,
}

impl Default for FnvHasher {
    fn default() -> Self {
        Self {
            state: 0xcbf29ce484222325,
        }
    }
}

impl Hasher for FnvHasher {
    #[inline]
    fn finish(&self) -> u64 {
        self.state
    }

    #[inline]
    fn write(&mut self, bytes: &[u8]) {
        for &b in bytes {
            self.state = (self.state ^ b as u64).wrapping_mul(0x100000001b3);
        }
    }

    #[inline]
    fn write_u64(&mut self, i: u64) {
        // Force little-endian regardless of platform (spec §8.2).
        self.write(&i.to_le_bytes());
    }
}

#[derive(Default, Clone, Copy)]
pub struct FnvBuildHasher;

impl BuildHasher for FnvBuildHasher {
    type Hasher = FnvHasher;
    #[inline]
    fn build_hasher(&self) -> FnvHasher {
        FnvHasher::default()
    }
}
