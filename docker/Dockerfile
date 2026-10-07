# Measurement image for the RQ1/RQ3 campaign.
#
# WHAT A CONTAINER DOES AND DOES NOT BUY. A container shares the host kernel, so
# it changes nothing about the scheduler, the clocksource, the frequency
# governor, or the hypervisor underneath. Running this image on the KVM guest
# leaves the far tail exactly as unresolved as bench/TESTBED.md says it is, and
# running it on a laptop is still a laptop. What it does buy is threefold:
#
#   1. The toolchain becomes a property of the image instead of a property of
#      whichever box was free. Every version below is pinned and recorded in
#      /etc/uecm-image.txt, which bench/capture_env.sh copies into the campaign's
#      environment record.
#   2. It carries the two tools the measurement host is missing. `jeprof` (from
#      jemalloc-devel) is what bench/alloc_profile.sh needs to symbolise a heap
#      dump, and `perf` is what bench/counters.sh needs. Neither has to be
#      installed on the host to get them.
#   3. A bare-metal box, rented or borrowed, becomes a one-command target: install
#      Docker, run docker/run.sh, and the campaign runs with the same compiler as
#      the numbers already in the thesis.
#
# TOOLCHAIN PARITY WITH THE HOST OF RECORD. The campaign the thesis reports ran
# on Rocky Linux 8.10 with g++ (GCC) 15.1.1, rustc 1.97.1, cmake 3.30.2 and the
# distribution's jemalloc 5.2.1 (bench/results/env-20260812-154523.txt). This
# image reproduces that: same distribution, same GCC series from gcc-toolset-15,
# the same rustc, the same cmake, the same EPEL jemalloc the C++ arm links. The
# one difference is the GCC patch level, since the toolset now ships 15.2.1
# against the host's 15.1.1, and the image records both so a comparison across
# the two can say so.
#
# NOT A SANITISER OR COVERAGE IMAGE by intent, though the sanitiser runtimes are
# installed so faults/run_faults.sh and cpp/sanitise.sh also work here.

FROM rockylinux/rockylinux:8.10

# Pinned deliberately. Bumping any of these makes a new image, and docker/run.sh
# builds the tag out of them so a bumped toolchain cannot silently reuse the old
# image against a new campaign.
ARG GCC_TOOLSET=15
ARG RUST_VERSION=1.97.1
ARG CMAKE_VERSION=3.30.2
ARG NINJA_VERSION=1.11.1.1
ARG PYTHON=python3.11

ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    CARGO_HOME=/opt/cargo \
    RUSTUP_HOME=/opt/rustup \
    CARGO_NET_OFFLINE=true \
    MPLCONFIGDIR=/tmp/matplotlib \
    UECM_IN_CONTAINER=1

# --- Distribution packages ---------------------------------------------------
# powertools is enabled because several EPEL packages depend on it, and EPEL is
# where the jemalloc the C++ arm links comes from on this distribution.
RUN dnf -y install dnf-plugins-core \
 && dnf config-manager --set-enabled powertools \
 && dnf -y install epel-release \
 && dnf -y update \
 && dnf -y install \
      gcc-toolset-${GCC_TOOLSET}-gcc \
      gcc-toolset-${GCC_TOOLSET}-gcc-c++ \
      gcc-toolset-${GCC_TOOLSET}-libasan-devel \
      gcc-toolset-${GCC_TOOLSET}-libtsan-devel \
      gcc-toolset-${GCC_TOOLSET}-libubsan-devel \
      gcc-toolset-${GCC_TOOLSET}-binutils \
      make autoconf \
      ${PYTHON} ${PYTHON}-pip \
      jemalloc jemalloc-devel \
      perf \
      util-linux procps-ng \
      perl binutils \
      curl ca-certificates tar gzip xz \
      diffutils findutils which hostname \
 && dnf clean all \
 && rm -rf /var/cache/dnf

# `python3` has to resolve to 3.11 for the analysis scripts (matplotlib needs
# 3.9 or newer) while dnf keeps the platform 3.6 at /usr/bin/python3. /usr/local
# comes first on PATH, so a symlink there is enough and nothing in the
# distribution's own tooling moves.
RUN ln -s /usr/bin/${PYTHON} /usr/local/bin/python3

# --- cmake, ninja, matplotlib ------------------------------------------------
# cmake comes from pip rather than from the distribution because the version has
# to match the host of record (3.30.2) and appstream carries 3.26.5. matplotlib
# is installed from bench/requirements.txt so the image cannot drift from the
# repository's own declared dependency; it only draws plots, so its exact version
# is recorded rather than pinned.
COPY bench/requirements.txt /tmp/requirements.txt
RUN ${PYTHON} -m pip install --no-cache-dir --upgrade pip \
 && ${PYTHON} -m pip install --no-cache-dir \
      "cmake==${CMAKE_VERSION}" "ninja==${NINJA_VERSION}" \
 && ${PYTHON} -m pip install --no-cache-dir -r /tmp/requirements.txt \
 && rm -f /tmp/requirements.txt

# --- Rust --------------------------------------------------------------------
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \
      | sh -s -- -y --no-modify-path --profile minimal \
                 --default-toolchain "${RUST_VERSION}" \
 && ln -s ${CARGO_HOME}/bin/cargo  /usr/local/bin/cargo \
 && ln -s ${CARGO_HOME}/bin/rustc  /usr/local/bin/rustc \
 && ln -s ${CARGO_HOME}/bin/rustup /usr/local/bin/rustup

# Prefetch the locked crate graph so the campaign can run with --network none.
# A run that reaches the network is a run whose dependencies were resolved at
# measurement time instead of at image-build time, which is the thing being
# pinned. The staging copy is thrown away: only the registry cache is kept.
#
# CARGO_HOME is left world-writable on purpose. docker/run.sh runs the container
# as the invoking user so that everything written into the bind-mounted
# repository is owned by that user, and cargo needs to take its package-cache
# lock inside CARGO_HOME whoever that turns out to be.
COPY rust/Cargo.toml rust/Cargo.lock /tmp/cratefetch/
RUN cd /tmp/cratefetch \
 && mkdir -p src examples \
 && : > src/lib.rs \
 && echo 'fn main() {}' > examples/bench.rs \
 && echo 'fn main() {}' > examples/pipeline.rs \
 && CARGO_NET_OFFLINE=false cargo fetch --locked \
 && cd / && rm -rf /tmp/cratefetch \
 && chmod -R a+rwX ${CARGO_HOME}

# --- Heap-profiling jemalloc for the C++ arm ---------------------------------
# The distribution's jemalloc is built without --enable-prof. A binary linking it
# answers `Invalid conf pair: prof:true` and no dump lands, so
# bench/alloc_profile.sh cannot profile the C++ arm with it and correctly refuses
# to profile one language alone. That is true of this image's EPEL package and of
# the same package on the measurement host, which means the peak-RSS attribution
# the profile exists for could not have been collected there either.
#
# The build below keeps the two arms measured by one instrument, which is the
# whole reason the profile uses jemalloc's own prof instead of heaptrack against
# dhat. It is built from the *same source the Rust arm links*, the jemalloc
# vendored inside tikv-jemalloc-sys, with prof compiled in and without the
# _rjem_ symbol prefix so it can interpose malloc for C++. Same source and same
# version therefore, though not an identical configure line: the Rust side is
# static and prefixed, this one is shared and unprefixed. The version is taken
# from the crate directory name because the vendored tree carries no VERSION file
# and configure would otherwise look for a git checkout that is not there.
#
# Installed beside the distribution build and never over it, and deliberately
# left out of ld.so.conf: on the library search path it could satisfy the
# campaign's own jemalloc arm and silently swap a profiling allocator into a
# timed run. Only the extra build tree links it, by absolute path, and only when
# UECM_JEMALLOC_PROF_LIB is set. This image sets it and a host does not.
RUN set -eu \
 && . /opt/rh/gcc-toolset-${GCC_TOOLSET}/enable \
 && crate="$(ls -d ${CARGO_HOME}/registry/src/*/tikv-jemalloc-sys-* | head -1)" \
 && ver="$(basename "$crate")" \
 && ver="${ver#*+}" \
 && cp -a "$crate/jemalloc" /tmp/jemalloc-prof-src \
 && cd /tmp/jemalloc-prof-src \
 && ./autogen.sh --prefix=/opt/jemalloc-prof --enable-prof --with-version="$ver" \
 && make -j"$(nproc)" \
 && make install \
 && cd / && rm -rf /tmp/jemalloc-prof-src
ENV UECM_JEMALLOC_PROF_LIB=/opt/jemalloc-prof/lib/libjemalloc.so

COPY docker/entrypoint.sh docker/preflight.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh /usr/local/bin/preflight.sh

# --- Image manifest ----------------------------------------------------------
# Written at build time from the tools themselves rather than from these ARGs, so
# it records what is installed and not what was requested. bench/capture_env.sh
# reads this file into the campaign's environment record, which is how a result
# produced in a container carries its toolchain with it.
RUN . /opt/rh/gcc-toolset-${GCC_TOOLSET}/enable \
 && { echo "image: uecm-bench (docker/Dockerfile)"; \
      echo "built: $(date -u +%Y-%m-%dT%H:%M:%SZ)"; \
      echo "base: $(sed -n 's/^PRETTY_NAME="\(.*\)"/\1/p' /etc/os-release)"; \
      echo "gcc-toolset: ${GCC_TOOLSET}"; \
      echo "g++: $(g++ --version | head -1)"; \
      echo "rustc: $(rustc --version)"; \
      echo "cargo: $(cargo --version)"; \
      echo "cmake: $(cmake --version | head -1)"; \
      echo "ninja: $(ninja --version)"; \
      echo "python: $(python3 --version 2>&1)"; \
      echo "matplotlib: $(python3 -c 'import matplotlib; print(matplotlib.__version__)' 2>/dev/null || echo '(missing)')"; \
      echo "jemalloc: $(rpm -q --qf '%{VERSION}-%{RELEASE}' jemalloc)"; \
      echo "jemalloc prof build (C++ profile arm only): $(/opt/jemalloc-prof/bin/jemalloc-config --version 2>/dev/null || echo '(not built)')"; \
      echo "jeprof: $(jeprof --version 2>&1 | head -1 || echo '(missing)')"; \
      echo "perf: $(perf --version 2>&1 | head -1)"; \
    } > /etc/uecm-image.txt \
 && cat /etc/uecm-image.txt

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["preflight.sh"]
