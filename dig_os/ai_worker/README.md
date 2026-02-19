# DIG OS AI Worker (Python + Cython)

The AI worker is the useful-compute runtime for DIG OS.

## Core capabilities

- Priority mission queue (high-value jobs preempt lower-value jobs)
- Epoch-level checkpoint save/restore
- Eco-mode runtime policy (off-peak = heavier training)
- Cython metrics kernel for faster training-loop math
- Daemon integration (`/api/v1/missions`, `/api/v1/mode`)

## Setup

```bash
cd dig_os/ai_worker
python -m pip install -r requirements.txt
python setup.py build_ext --inplace
python scripts/run_worker.py
```

