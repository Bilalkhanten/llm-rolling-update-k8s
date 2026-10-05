#!/usr/bin/env bash
# Advertise 1 fake "nvidia.com/gpu" on the first N workers.
#   ./scripts/advertise-gpus.sh 3   # the crime scene: exactly 3 GPUs for 3 replicas
#   ./scripts/advertise-gpus.sh 4   # "we bought a spare GPU node"
# Uses the documented "advertise extended resources for a node" trick (PATCH node/status).
# Re-run it if a kind node container restarts.
set -euo pipefail
COUNT="${1:-3}"
mapfile -t WORKERS < <(kubectl get nodes -l '!node-role.kubernetes.io/control-plane' -o name | sort)
for i in $(seq 0 $((COUNT - 1))); do
  node="${WORKERS[$i]#node/}"
  kubectl patch node "$node" --subresource=status --type=json \
    -p '[{"op":"add","path":"/status/capacity/nvidia.com~1gpu","value":"1"}]' >/dev/null
  echo "advertised 1 fake GPU on ${node}"
done
kubectl get nodes -o custom-columns='NAME:.metadata.name,GPU:.status.allocatable.nvidia\.com/gpu'
