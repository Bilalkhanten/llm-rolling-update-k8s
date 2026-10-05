# llm-rollout-lab

Companion repo for the article **"Why Does My LLM Rolling Update Hang at '1 out of 3 New Replicas'?"**

Reproduce GPU-rollout problems (surge capacity, probes, progress deadline, graceful shutdown)
on a laptop. **No real GPUs needed**: `kind` nodes advertise a fake `nvidia.com/gpu` and a tiny
fake LLM server behaves like a real one (slow to load, slow to stream, opinionated about SIGTERM).

## Prerequisites
Docker, [kind](https://kind.sigs.k8s.io/), kubectl (1.24+ for `patch --subresource`), make, Python 3.12 (only for the local lab).
Manifests target Kubernetes 1.30+ and were schema-checked with kubeconform against 1.32.

## Layout
```
app/        fake_llm.py (the "model server"), loadgen.py (truncation-aware client), Dockerfile
kind/       4-worker kind cluster
scripts/    advertise-gpus.sh  (patches node/status with a fake nvidia.com/gpu)
k8s/        10 naive  ->  20 fixed (no spare GPU)  /  21 fixed (spare GPU)  + placeholder, PDB, loadgen
lab/        sigterm_lab.py  - replays the kubelet termination sequence locally (no cluster!)
docs/       diagram + terminal-screenshot generators
```

## Quick start
```bash
make cluster          # kind: 1 control-plane + 4 workers
make image            # build fake-llm:lab and load it into kind
make gpus3            # 3 fake GPUs -> exactly enough for 3 replicas
make deploy-naive     # v1: 3/3 Ready
make loadgen          # (second terminal) live scoreboard: ok / truncated / http_err / conn_err

make rollout V=v2     # suspect #1: hangs at "1 out of 3 new replicas have been updated..."
make fix-nospare      # maxSurge 0 / maxUnavailable 1  (or: make gpus4 && make fix-spare)
make rollout V=v3     # now it finishes

python3 lab/sigterm_lab.py   # suspect #3, no cluster needed (~2 min)
make clean
```

## Honest caveats
* The fake server opens its port immediately; real vLLM binds later. Check what *your* probe endpoint
  guarantees and what *your* server version does on SIGTERM before trusting any of this.
* Fake GPUs only exercise scheduling; they say nothing about CUDA, drivers, or real load times.
* Node capacity patches are lost if a kind node container restarts - re-run `make gpus3`.

## Docs
`docs/images/` holds the article diagrams and the real output of `lab/sigterm_lab.py`
(`t1-sigterm-lab.png`). `docs/tools/` has the scripts that draw them (`pip install pillow`).
`lab/sample-output.txt` is the captured output of one run of the SIGTERM lab.
