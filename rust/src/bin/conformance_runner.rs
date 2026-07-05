//! Shared conformance/parity runner (Rust side), spec §11.
//!
//! Reads a language-neutral vector file (see spec/conformance/README.md), executes
//! each operation against the threaded `Service`, and emits a canonical "actual"
//! transcript (one line per operation) to stdout. Each actual is also compared
//! against the expected result in the file; mismatches are reported on stderr and
//! cause a non-zero exit code. The stdout transcript is what `run.sh` diffs across
//! the C++ and Rust implementations.

use std::collections::HashMap;
use std::fs;
use std::process::ExitCode;

use uecm::hash::shard_index;
use uecm::{
    Config, CreateParams, DrbEntry, OpError, ReconfigParams, Service, SignalingMsg, UeId, UeState,
};

fn err_str(e: OpError) -> String {
    format!("Err({})", e.as_str())
}

fn state_name(s: UeState) -> &'static str {
    match s {
        UeState::Idle => "Idle",
        UeState::Connected => "Connected",
        UeState::Reconfiguring => "Reconfiguring",
        UeState::Released => "Released",
    }
}

fn void_str(r: Result<(), OpError>) -> String {
    match r {
        Ok(()) => "Ok".to_string(),
        Err(e) => err_str(e),
    }
}

struct Line {
    op: String,
    pos: Vec<String>,
    kv: HashMap<String, String>,
    expected: String,
    has_arrow: bool,
}

fn parse(raw: &str) -> Line {
    let body = raw.split('#').next().unwrap_or("").trim();
    let mut ln = Line {
        op: String::new(),
        pos: Vec::new(),
        kv: HashMap::new(),
        expected: String::new(),
        has_arrow: false,
    };
    if body.is_empty() {
        return ln;
    }
    let (lhs, expected, has_arrow) = match body.split_once("=>") {
        Some((l, r)) => (l.trim(), r.trim().to_string(), true),
        None => (body, String::new(), false),
    };
    ln.expected = expected;
    ln.has_arrow = has_arrow;
    for (i, tok) in lhs.split_whitespace().enumerate() {
        if i == 0 {
            ln.op = tok.to_string();
        } else if let Some((k, v)) = tok.split_once('=') {
            ln.kv.insert(k.to_string(), v.to_string());
        } else {
            ln.pos.push(tok.to_string());
        }
    }
    ln
}

fn u64_of(kv: &HashMap<String, String>, k: &str, dflt: u64) -> u64 {
    kv.get(k).and_then(|s| s.parse().ok()).unwrap_or(dflt)
}

fn main() -> ExitCode {
    let path = match std::env::args().nth(1) {
        Some(p) => p,
        None => {
            eprintln!("usage: conformance_runner <vector-file>");
            return ExitCode::from(2);
        }
    };
    let text = match fs::read_to_string(&path) {
        Ok(t) => t,
        Err(e) => {
            eprintln!("cannot open {path}: {e}");
            return ExitCode::from(2);
        }
    };

    let mut cfg = Config::default();
    let mut svc: Option<Service> = None;
    let mut mismatches = 0u64;
    let mut ops = 0u64;

    let mut out = String::new();

    for (i, raw) in text.lines().enumerate() {
        let lineno = i + 1;
        let ln = parse(raw);
        if ln.op.is_empty() {
            continue;
        }

        if ln.op == "config" {
            if svc.is_some() {
                eprintln!("line {lineno}: config after operations");
                return ExitCode::from(2);
            }
            cfg.n_shards = u64_of(&ln.kv, "n_shards", cfg.n_shards);
            cfg.queue_capacity =
                u64_of(&ln.kv, "queue_capacity", cfg.queue_capacity as u64) as usize;
            cfg.max_contexts_per_shard =
                u64_of(&ln.kv, "max_contexts_per_shard", cfg.max_contexts_per_shard);
            continue;
        }

        // shard is a pure function; every other op needs a running service.
        if svc.is_none() && ln.op != "shard" {
            let mut s = Service::new(cfg);
            s.start();
            svc = Some(s);
        }

        let id: UeId = ln.pos.first().and_then(|s| s.parse().ok()).unwrap_or(0);

        let actual = match ln.op.as_str() {
            "shard" => shard_index(id, cfg.n_shards).to_string(),
            "count" => svc.as_ref().unwrap().count().to_string(),
            "create" => {
                let p = CreateParams {
                    serving_cell_id: u64_of(&ln.kv, "cell", 0) as u32,
                    security_key: [0u8; 32],
                };
                void_str(svc.as_ref().unwrap().create_context(id, p))
            }
            "setup" => void_str(svc.as_ref().unwrap().setup_connection(id)),
            "signal" => {
                let m = SignalingMsg {
                    kind: u64_of(&ln.kv, "kind", 0) as u8,
                    payload_len: u64_of(&ln.kv, "len", 0) as u16,
                    payload: [0u8; 64],
                };
                match svc.as_ref().unwrap().handle_signaling(id, m) {
                    Ok(a) => format!(
                        "Ok(accepted={},handled={})",
                        a.accepted, a.new_messages_handled
                    ),
                    Err(e) => err_str(e),
                }
            }
            "adddrb" => {
                let d = DrbEntry {
                    drb_id: u64_of(&ln.kv, "id", 0) as u8,
                    qos_flow_id: u64_of(&ln.kv, "qfi", 0) as u8,
                    teid: u64_of(&ln.kv, "teid", 0) as u32,
                };
                void_str(svc.as_ref().unwrap().add_drb(id, d))
            }
            "begin_reconf" => {
                let p = ReconfigParams {
                    target_cell_id: u64_of(&ln.kv, "cell", 0) as u32,
                };
                void_str(svc.as_ref().unwrap().begin_reconfigure(id, p))
            }
            "complete_reconf" => void_str(svc.as_ref().unwrap().complete_reconfigure(id)),
            "abort_reconf" => void_str(svc.as_ref().unwrap().abort_reconfigure(id)),
            "release" => void_str(svc.as_ref().unwrap().release_context(id)),
            "lookup" => match svc.as_ref().unwrap().lookup(id) {
                Ok(v) => format!(
                    "Ok(state={},cell={},drbs={},messages_handled={})",
                    state_name(v.state),
                    v.serving_cell_id,
                    v.drbs.len(),
                    v.messages_handled
                ),
                Err(e) => err_str(e),
            },
            other => {
                eprintln!("line {lineno}: unknown op '{other}'");
                return ExitCode::from(2);
            }
        };

        ops += 1;
        out.push_str(&actual);
        out.push('\n');
        if ln.has_arrow && actual != ln.expected {
            mismatches += 1;
            eprintln!(
                "MISMATCH line {lineno}: expected '{}' got '{}'",
                ln.expected, actual
            );
        }
    }

    if let Some(mut s) = svc.take() {
        s.shutdown();
    }
    print!("{out}");
    eprintln!("conformance_runner(rust): {path}: {ops} ops, {mismatches} mismatches");
    if mismatches == 0 {
        ExitCode::SUCCESS
    } else {
        ExitCode::FAILURE
    }
}
