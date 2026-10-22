#!/usr/bin/env bash
cd /root/thesis.local
{
  echo "== started $(date -Is) =="
  cat /proc/cmdline
  echo "smt active: $(cat /sys/devices/system/cpu/smt/active)  boost: $(cat /sys/devices/system/cpu/cpufreq/boost)  governor: $(cat /sys/devices/system/cpu/cpu2/cpufreq/scaling_governor)  thp: $(cat /sys/kernel/mm/transparent_hugepage/enabled)  isolated: [$(cat /sys/devices/system/cpu/isolated)]"
  docker/run.sh env 2>&1
} > /root/bream-env.txt 2>&1
docker/run.sh --cpuset 2-17 exec -- bash bench/matched_probes.sh --stages --repeats 20 --pin 2-17 > /root/bream-stages-console.txt 2>&1
echo "stages exit: $? at $(date -Is)" >> /root/bream-stages-console.txt
docker/run.sh --cpuset 2-17 exec -- bash bench/matched_probes.sh --repeats 20 --pin 2-17 > /root/bream-matched-console.txt 2>&1
echo "matched exit: $? at $(date -Is)" >> /root/bream-matched-console.txt
