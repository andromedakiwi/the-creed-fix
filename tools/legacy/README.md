# Legacy (v1.x) tools

Patch v1.0–v1.5 shipped a modified `Creed.exe`. Since v2.0 the original `Creed.exe` is left untouched and the same fixes are applied in memory by `dinput.dll` (`src/creedfix`).

- `patch_creed.py` – rebuilds the v1.5 executable from the original (stdlib only).
- `build_v1.5.py` – the keystone script that assembled the v1.5 code caves.

They are kept as a reference for the addresses and byte changes documented in `docs/TECHNICAL.md`.
