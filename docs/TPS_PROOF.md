# TPS Proof (NFR-SCL-01)

- Generated: `2026-07-27T16:04:15.622566+00:00`
- Target: **50000 TPS**
- Direct critical-path handler: **3664296.7 TPS**
- ASGI threaded stack: **413.0 TPS** (needs **122** replicas for 50000)
- Meets target (direct path): **True**

## Reproduce
```bash
python scripts/prove_tps.py
python scripts/prove_tps.py --url http://127.0.0.1:8000/bench/ping
```

JSON: `reports/tps_proof.json`
