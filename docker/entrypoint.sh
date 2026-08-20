#!/usr/bin/env bash
# Container entrypoint: put the pinned toolchain on PATH, then get out of the way.
#
# gcc-toolset is a software-collection, so its compiler is not on the default
# PATH: it is selected by sourcing an enable script. Doing that here rather than
# in an ENV line keeps one source of truth for the collection's PATH,
# LD_LIBRARY_PATH and INFOPATH, which is what the distribution supports.
set -uo pipefail

# The enable script is written for an interactive shell and reads variables that
# may be unset, so nounset is relaxed across it and restored after.
set +u
for enable in /opt/rh/gcc-toolset-*/enable; do
  [ -r "$enable" ] && . "$enable"
done
set -u

export PATH="/usr/local/bin:${CARGO_HOME:-/opt/cargo}/bin:$PATH"

# docker run --user with a uid that has no passwd entry leaves HOME unset or
# pointing at a directory this uid cannot write. Nothing here needs a real home
# (CARGO_HOME and MPLCONFIGDIR are set in the image), but a tool that writes a
# dotfile should not fail on it either.
if [ -z "${HOME:-}" ] || [ ! -w "${HOME:-/nonexistent}" ]; then
  export HOME=/tmp
fi
mkdir -p "${MPLCONFIGDIR:-/tmp/matplotlib}" 2>/dev/null || true

# The default command is the readiness check, which is the safe thing to do when
# someone runs the image with no arguments.
if [ "$#" -eq 0 ]; then
  exec preflight.sh
fi

exec "$@"
