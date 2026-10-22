"""Pick pipeline in-flight logs for macro generation."""

import glob
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CAMPAIGN_DIR = os.path.join(HERE, "results-pipeline-campaign-jaybird")
LOUSE_DIR = os.path.join(HERE, "results-pipeline-20261006-louse")
ORDER_LEN = 4
REPEATS = 20
CAPACITY_ROWS = 24


def _row_count(path):
    with open(path, encoding="utf-8") as fh:
        return sum(1 for line in fh if line.strip())


def _newest(paths):
    if not paths:
        return None
    return max(paths, key=os.path.getmtime)


def log_dir():
    override = os.environ.get("THESIS_PIPELINE_DIR")
    if override:
        return override
    if os.path.isdir(CAMPAIGN_DIR):
        for pattern in ("pipeline-*.jsonl", "pipeline-mixed-*.jsonl"):
            if glob.glob(os.path.join(CAMPAIGN_DIR, pattern)):
                return CAMPAIGN_DIR
    return LOUSE_DIR


def env_path(directory):
    for name in ("env-host-campaign.txt", "env-host-major-louse.txt"):
        path = os.path.join(directory, name)
        if os.path.isfile(path):
            return path
    matches = sorted(glob.glob(os.path.join(directory, "env-host-*.txt")))
    if matches:
        return matches[-1]
    matches = sorted(glob.glob(os.path.join(directory, "env-*.txt")))
    if matches:
        return matches[-1]
    return None


def _skip_sidecar(path):
    return ".hist." in os.path.basename(path)


def signal_log(directory):
    candidates = []
    for path in glob.glob(os.path.join(directory, "pipeline-*.jsonl")):
        base = os.path.basename(path)
        if _skip_sidecar(path) or "mixed" in base or "diagnose" in base or "reply" in base:
            continue
        if _row_count(path) == REPEATS * ORDER_LEN:
            candidates.append(path)
    return _newest(candidates)


def mixed_logs(directory):
    capacity = []
    confirmatory = []
    for path in glob.glob(os.path.join(directory, "pipeline-mixed-*.jsonl")):
        base = os.path.basename(path)
        if _skip_sidecar(path) or "diagnose" in base or "reply" in base:
            continue
        rows = _row_count(path)
        if rows == CAPACITY_ROWS:
            capacity.append(path)
        elif rows == REPEATS * ORDER_LEN:
            confirmatory.append(path)
    return _newest(capacity), _newest(confirmatory)


def on_campaign_host(directory):
    return os.path.basename(directory.rstrip("/")) == os.path.basename(CAMPAIGN_DIR)
