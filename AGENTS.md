# Oppo A37fw development

- Target: user's Oppo A37fw, ARM64 Snapdragon 410, V2 ZIP-based Android 10 ROM.
- Prioritize actual battery runtime, responsiveness, storage and RAM efficiency. Preserve CPU/GPU overclocks, IMS, calls, SIM, SMS and mobile data. Do not equate less page cache with lower memory cost or better battery life.
- Before changing behavior, explain the hypothesis, possible regressions, real-device comparison and rollback. The user can test experimental changes. Never present an untested experiment as a proven improvement.
- Keep each independent fix/experiment in its own commit. Do not combine governor, GPU, charging and debloat changes in one test.
- Work in existing isolated checkouts; do not create worktrees unless requested.
- ROM editing uses extracted release files, not a complete Android source build. Read docs/V2-BASELINE.md and docs/BATTERY-TESTS.md.
- Keep binaries/images outside Git. rom/v2 contains unchanged original editable files initially; preserve extraction manifests and use small reviewed diffs for future changes. Original system.img holds authoritative Android ownership, SELinux labels, capabilities, hardlinks and other filesystem metadata.
- Keep IMS/radio components. Never use generic wakelock blocking, cache dropping or thermal bypass as a battery optimization. Investigate existing behavior before adding more tuning.
- Hardware results are required before making any experiment permanent. Current kernel source is not proven byte-for-byte equivalent to the dirty kernel embedded in V2.
