//! A bounded blocking queue built the way the C++ side builds one.
//!
//! This is NOT part of the compared implementation. The reported Rust arm uses
//! `std::sync::mpsc::sync_channel`, because the study compares each language as a
//! developer actually finds it and a developer wanting bounded backpressure in
//! Rust reaches for the standard channel.
//!
//! The problem that leaves is attribution. Past saturation the two languages
//! diverge sharply in sustained throughput, and that divergence is the study's
//! strongest single result — but the threats table concedes it is attributed
//! rather than localised. Two entries in the forced-idiom log are the candidates:
//! this queue, and the tagged-struct-versus-enum dispatch. The contended-primitive
//! microbenchmark already showed the primitives alone do not reproduce the
//! ordering, which narrows it to the full handoff path but does not name the part.
//!
//! So this holds the language fixed and changes only the queue, to the same
//! design the C++ arm uses: one mutex, a `VecDeque`, and two condition variables,
//! one for "not full" and one for "not empty". If the overload divergence closes,
//! the standard channel was the cause; if it does not, the queue is exonerated and
//! the remaining candidate is dispatch. Either outcome localises the result.
//!
//! Enable with `--features mutex-queue`. Record any result in
//! `spec/SPECIFICATION.md` §12.

use std::collections::VecDeque;
use std::fmt;
use std::sync::{Arc, Condvar, Mutex};

struct Shared<T> {
    state: Mutex<State<T>>,
    not_full: Condvar,
    not_empty: Condvar,
    capacity: usize,
}

struct State<T> {
    queue: VecDeque<T>,
    senders: usize,
    receivers: usize,
}

/// Returned by [`SyncSender::send`] when every receiver is gone. Carries the
/// value back, as the standard channel does, so no message is silently dropped.
pub struct SendError<T>(pub T);

impl<T> fmt::Debug for SendError<T> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("SendError(..)")
    }
}

/// Returned by [`Receiver::recv`] when every sender is gone and the queue is drained.
#[derive(Debug)]
pub struct RecvError;

pub struct SyncSender<T> {
    shared: Arc<Shared<T>>,
}

pub struct Receiver<T> {
    shared: Arc<Shared<T>>,
}

/// A bounded queue with blocking backpressure, mirroring `BoundedQueue` in
/// `cpp/include/uecm/bounded_queue.hpp`.
///
/// A capacity of zero is clamped to one, matching the C++ constructor: the
/// rendezvous semantics `sync_channel(0)` would give are a different design, and
/// substituting one here would make the probe measure the wrong thing.
pub fn bounded<T>(capacity: usize) -> (SyncSender<T>, Receiver<T>) {
    let shared = Arc::new(Shared {
        state: Mutex::new(State {
            queue: VecDeque::new(),
            senders: 1,
            receivers: 1,
        }),
        not_full: Condvar::new(),
        not_empty: Condvar::new(),
        capacity: capacity.max(1),
    });
    (
        SyncSender {
            shared: Arc::clone(&shared),
        },
        Receiver { shared },
    )
}

impl<T> SyncSender<T> {
    /// Blocks while the queue is full, which is the backpressure the spec asks for.
    pub fn send(&self, value: T) -> Result<(), SendError<T>> {
        let mut state = self.shared.state.lock().expect("queue mutex");
        // Re-checked after every wake rather than once on entry: the receiver can
        // go away while this producer is parked on a full queue, and returning the
        // value is better than blocking forever.
        while state.queue.len() >= self.shared.capacity && state.receivers > 0 {
            state = self.shared.not_full.wait(state).expect("queue mutex");
        }
        if state.receivers == 0 {
            return Err(SendError(value));
        }
        state.queue.push_back(value);
        drop(state);
        self.shared.not_empty.notify_one();
        Ok(())
    }
}

impl<T> Clone for SyncSender<T> {
    fn clone(&self) -> Self {
        self.shared.state.lock().expect("queue mutex").senders += 1;
        SyncSender {
            shared: Arc::clone(&self.shared),
        }
    }
}

impl<T> Drop for SyncSender<T> {
    fn drop(&mut self) {
        let mut state = self.shared.state.lock().expect("queue mutex");
        state.senders -= 1;
        let last = state.senders == 0;
        drop(state);
        // A receiver parked on an empty queue would otherwise wait forever.
        if last {
            self.shared.not_empty.notify_all();
        }
    }
}

impl<T> Receiver<T> {
    /// Blocks while the queue is empty; fails once it is empty and no sender remains.
    pub fn recv(&self) -> Result<T, RecvError> {
        let mut state = self.shared.state.lock().expect("queue mutex");
        loop {
            if let Some(value) = state.queue.pop_front() {
                drop(state);
                self.shared.not_full.notify_one();
                return Ok(value);
            }
            if state.senders == 0 {
                return Err(RecvError);
            }
            state = self.shared.not_empty.wait(state).expect("queue mutex");
        }
    }
}

impl<T> Drop for Receiver<T> {
    fn drop(&mut self) {
        let mut state = self.shared.state.lock().expect("queue mutex");
        state.receivers -= 1;
        drop(state);
        // Release any producer parked on a full queue, so it can observe that
        // there is no longer anyone to receive what it is holding.
        self.shared.not_full.notify_all();
    }
}

// No `unsafe impl` is needed to make these cross threads, and none is used: the
// auto traits already hold, because every mutable field sits behind the mutex.
// That is the point of the exercise -- the probe changes the queue's design
// without changing the safety story the thesis reports for the core.

#[cfg(test)]
mod tests {
    use super::*;
    use std::thread;
    use std::time::Duration;

    #[test]
    fn fifo_and_roundtrip() {
        let (tx, rx) = bounded(4);
        for i in 0..4 {
            tx.send(i).unwrap();
        }
        for i in 0..4 {
            assert_eq!(rx.recv().unwrap(), i);
        }
    }

    #[test]
    fn send_blocks_when_full() {
        // The property the probe exists to preserve: at capacity 1 a second send
        // must not complete until the receiver has taken the first.
        let (tx, rx) = bounded(1);
        tx.send(1).unwrap();
        let producer = thread::spawn(move || {
            tx.send(2).unwrap();
            tx.send(3).unwrap();
        });
        thread::sleep(Duration::from_millis(50));
        assert_eq!(rx.recv().unwrap(), 1);
        assert_eq!(rx.recv().unwrap(), 2);
        assert_eq!(rx.recv().unwrap(), 3);
        producer.join().unwrap();
    }

    #[test]
    fn recv_fails_once_all_senders_drop() {
        let (tx, rx) = bounded::<u32>(2);
        let tx2 = tx.clone();
        drop(tx);
        drop(tx2);
        assert!(rx.recv().is_err());
    }
}
