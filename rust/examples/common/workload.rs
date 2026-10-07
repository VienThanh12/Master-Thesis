//! Pinned workload generator. Kept in lock-step with `cpp/bench/workload.hpp`.

use uecm::MAX_DRBS;

struct SplitMix64 {
    s: u64,
}
impl SplitMix64 {
    fn next(&mut self) -> u64 {
        self.s = self.s.wrapping_add(0x9E3779B97F4A7C15);
        let mut z = self.s;
        z = (z ^ (z >> 30)).wrapping_mul(0xBF58476D1CE4E5B9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94D049BB133111EB);
        z ^ (z >> 31)
    }
}

#[allow(dead_code)] // used by examples/bench.rs; the pipeline example counts by index
pub const KIND_COUNT: usize = 8;
#[allow(dead_code)]
pub const KIND_NAMES: [&str; KIND_COUNT] = [
    "create",
    "setup",
    "signal",
    "adddrb",
    "begin_reconf",
    "complete_reconf",
    "abort_reconf",
    "release",
];

#[derive(Clone, Copy, PartialEq, Eq)]
pub enum WKind {
    Create = 0,
    Setup = 1,
    Signal = 2,
    AddDrb = 3,
    BeginReconf = 4,
    CompleteReconf = 5,
    AbortReconf = 6,
    Release = 7,
}

pub struct WOp {
    pub kind: WKind,
    pub slot: u64,
    pub drb_id: u8,
}

const EMPTY: u8 = 0;
const IDLE: u8 = 1;
const CONNECTED: u8 = 2;
const RECONFIGURING: u8 = 3;

pub struct Workload {
    n: u64,
    rng: SplitMix64,
    state: Vec<u8>,
    ndrbs: Vec<u8>,
}

impl Workload {
    pub fn new(active_ues: u64, seed: u64) -> Self {
        let n = if active_ues == 0 { 1 } else { active_ues };
        Self {
            n,
            rng: SplitMix64 { s: seed },
            state: vec![EMPTY; n as usize],
            ndrbs: vec![0u8; n as usize],
        }
    }

    pub fn next(&mut self) -> WOp {
        let slot = self.rng.next() % self.n;
        let si = slot as usize;
        let mut op = WOp {
            kind: WKind::Signal,
            slot,
            drb_id: 0,
        };
        match self.state[si] {
            EMPTY => {
                op.kind = WKind::Create;
                self.state[si] = IDLE;
            }
            IDLE => {
                op.kind = WKind::Setup;
                self.state[si] = CONNECTED;
            }
            CONNECTED => {
                let r = self.rng.next() % 100;
                if r < 70 {
                    op.kind = WKind::Signal;
                } else if r < 80 {
                    if (self.ndrbs[si] as usize) < MAX_DRBS {
                        op.kind = WKind::AddDrb;
                        op.drb_id = self.ndrbs[si];
                        self.ndrbs[si] += 1;
                    } else {
                        op.kind = WKind::Signal;
                    }
                } else if r < 95 {
                    op.kind = WKind::BeginReconf;
                    self.state[si] = RECONFIGURING;
                } else {
                    op.kind = WKind::Release;
                    self.state[si] = EMPTY;
                    self.ndrbs[si] = 0;
                }
            }
            _ => {
                let r = self.rng.next() % 100;
                op.kind = if r < 80 {
                    WKind::CompleteReconf
                } else {
                    WKind::AbortReconf
                };
                self.state[si] = CONNECTED;
            }
        }
        op
    }
}
