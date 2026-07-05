// Shared conformance/parity runner (C++ side), spec §11.
//
// Reads a language-neutral vector file (see spec/conformance/README.md), executes
// each operation against the threaded Service, and emits a canonical "actual"
// transcript (one line per operation) to stdout. Each actual is also compared
// against the expected result in the file; mismatches are reported on stderr and
// cause a non-zero exit code. The stdout transcript is what run.sh diffs across
// the C++ and Rust implementations.

#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <memory>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>

#include "uecm/hash.hpp"
#include "uecm/service.hpp"

using namespace uecm;

namespace {

std::string trim(const std::string& s) {
  const auto b = s.find_first_not_of(" \t\r\n");
  if (b == std::string::npos) return "";
  const auto e = s.find_last_not_of(" \t\r\n");
  return s.substr(b, e - b + 1);
}

const char* state_name(UeState s) {
  switch (s) {
    case UeState::Idle:          return "Idle";
    case UeState::Connected:     return "Connected";
    case UeState::Reconfiguring: return "Reconfiguring";
    case UeState::Released:      return "Released";
  }
  return "Unknown";
}

template <class T>
std::string result_str(const OpResult<T>& r, std::string ok) {
  if (r.has_value()) return ok;
  return std::string("Err(") + std::string(to_string(r.error())) + ")";
}

std::string void_str(const OpResult<void>& r) {
  if (r.has_value()) return "Ok";
  return std::string("Err(") + std::string(to_string(r.error())) + ")";
}

struct Line {
  std::string op;
  std::vector<std::string> pos;
  std::unordered_map<std::string, std::string> kv;
  std::string expected;
  bool has_arrow = false;
};

Line parse(const std::string& raw) {
  Line ln;
  std::string body = raw;
  const auto hash = body.find('#');
  if (hash != std::string::npos) body = body.substr(0, hash);
  body = trim(body);
  if (body.empty()) { ln.op = ""; return ln; }

  const auto arrow = body.find("=>");
  std::string lhs = body;
  if (arrow != std::string::npos) {
    ln.has_arrow = true;
    lhs = trim(body.substr(0, arrow));
    ln.expected = trim(body.substr(arrow + 2));
  }
  std::istringstream is(lhs);
  std::string tok;
  bool first = true;
  while (is >> tok) {
    if (first) { ln.op = tok; first = false; continue; }
    const auto eq = tok.find('=');
    if (eq == std::string::npos) ln.pos.push_back(tok);
    else ln.kv[tok.substr(0, eq)] = tok.substr(eq + 1);
  }
  return ln;
}

std::uint64_t u64(const std::unordered_map<std::string, std::string>& kv,
                  const std::string& k, std::uint64_t dflt) {
  auto it = kv.find(k);
  return it == kv.end() ? dflt : std::strtoull(it->second.c_str(), nullptr, 10);
}

}  // namespace

int main(int argc, char** argv) {
  if (argc < 2) {
    std::cerr << "usage: conformance_runner <vector-file>\n";
    return 2;
  }
  std::ifstream in(argv[1]);
  if (!in) {
    std::cerr << "cannot open " << argv[1] << "\n";
    return 2;
  }

  Config cfg;  // defaults (spec §9)
  std::unique_ptr<Service> svc;
  auto ensure = [&]() {
    if (!svc) { svc = std::make_unique<Service>(cfg); svc->start(); }
  };

  std::string raw;
  int lineno = 0, mismatches = 0, ops = 0;
  while (std::getline(in, raw)) {
    ++lineno;
    Line ln = parse(raw);
    if (ln.op.empty()) continue;

    if (ln.op == "config") {
      if (svc) {
        std::cerr << "line " << lineno << ": config after operations\n";
        return 2;
      }
      cfg.n_shards = u64(ln.kv, "n_shards", cfg.n_shards);
      cfg.queue_capacity = static_cast<std::uint32_t>(u64(ln.kv, "queue_capacity", cfg.queue_capacity));
      cfg.max_contexts_per_shard = u64(ln.kv, "max_contexts_per_shard", cfg.max_contexts_per_shard);
      continue;
    }

    const UeId id = ln.pos.empty() ? 0 : std::strtoull(ln.pos[0].c_str(), nullptr, 10);
    std::string actual;

    if (ln.op == "shard") {
      actual = std::to_string(shard_index(id, cfg.n_shards));
    } else if (ln.op == "count") {
      ensure();
      actual = std::to_string(svc->count());
    } else if (ln.op == "create") {
      ensure();
      CreateParams p; p.serving_cell_id = static_cast<std::uint32_t>(u64(ln.kv, "cell", 0));
      actual = void_str(svc->create_context(id, p));
    } else if (ln.op == "setup") {
      ensure();
      actual = void_str(svc->setup_connection(id));
    } else if (ln.op == "signal") {
      ensure();
      SignalingMsg m;
      m.kind = static_cast<std::uint8_t>(u64(ln.kv, "kind", 0));
      m.payload_len = static_cast<std::uint16_t>(u64(ln.kv, "len", 0));
      auto r = svc->handle_signaling(id, m);
      if (r.has_value())
        actual = "Ok(accepted=" + std::string(r->accepted ? "true" : "false") +
                 ",handled=" + std::to_string(r->new_messages_handled) + ")";
      else
        actual = std::string("Err(") + std::string(to_string(r.error())) + ")";
    } else if (ln.op == "adddrb") {
      ensure();
      DrbEntry d;
      d.drb_id = static_cast<std::uint8_t>(u64(ln.kv, "id", 0));
      d.qos_flow_id = static_cast<std::uint8_t>(u64(ln.kv, "qfi", 0));
      d.teid = static_cast<std::uint32_t>(u64(ln.kv, "teid", 0));
      actual = void_str(svc->add_drb(id, d));
    } else if (ln.op == "begin_reconf") {
      ensure();
      ReconfigParams p; p.target_cell_id = static_cast<std::uint32_t>(u64(ln.kv, "cell", 0));
      actual = void_str(svc->begin_reconfigure(id, p));
    } else if (ln.op == "complete_reconf") {
      ensure();
      actual = void_str(svc->complete_reconfigure(id));
    } else if (ln.op == "abort_reconf") {
      ensure();
      actual = void_str(svc->abort_reconfigure(id));
    } else if (ln.op == "release") {
      ensure();
      actual = void_str(svc->release_context(id));
    } else if (ln.op == "lookup") {
      ensure();
      auto r = svc->lookup(id);
      if (r.has_value())
        actual = "Ok(state=" + std::string(state_name(r->state)) +
                 ",cell=" + std::to_string(r->serving_cell_id) +
                 ",drbs=" + std::to_string(r->drbs.size()) +
                 ",messages_handled=" + std::to_string(r->messages_handled) + ")";
      else
        actual = std::string("Err(") + std::string(to_string(r.error())) + ")";
    } else {
      std::cerr << "line " << lineno << ": unknown op '" << ln.op << "'\n";
      return 2;
    }

    ++ops;
    std::cout << actual << "\n";
    if (ln.has_arrow && actual != ln.expected) {
      ++mismatches;
      std::cerr << "MISMATCH line " << lineno << ": expected '" << ln.expected
                << "' got '" << actual << "'\n";
    }
  }

  if (svc) svc->shutdown();
  std::cerr << "conformance_runner(cpp): " << argv[1] << ": " << ops << " ops, "
            << mismatches << " mismatches\n";
  return mismatches == 0 ? 0 : 1;
}
