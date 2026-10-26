# Changelog

## v1.4 – 2026-10-26
- No more cursor/character trails at the screen edges: all dirty rectangles are clipped to the screen at the start of the restore function (replaces the depth-only clipping from v1.0).
- Cursor no longer thrown off screen after Alt+Tab: mouse movement accumulated while paused is discarded on resume.
- Executable rebuilt from the original by a single script (`tools/dev/build_v1.4.py`); new cave layout.
- README: note about Windows 11 Smart App Control.

## v1.3 – 2026-10-26
- Alt+Tab / Ctrl+Alt+Del fixed: the game pauses on focus loss (WM_ACTIVATEAPP) and resumes when you return, restoring its surfaces.
- DirectInput keyboard switched from exclusive to non-exclusive background mode.
- dgVoodoo2: `CaptureMouse = false`, so the mouse is free outside the game.

## v1.2 – 2026-10-25
- Ships the patched `Creed.exe`: extract into the game folder and play. No installer, no registry key needed.
- Hybrid No-CD: uses `cd1\` / `cd2\` when present, otherwise the real CD.
- Optional `Extras\CopyCDs.bat` to copy the CD files.

## v1.1 – 2026-10-25
- No-CD (installer copies the CD files once).
- CD music through ogg-winmm (`Music\TrackNN.ogg`).

## v1.0 – 2026-10-25
- Registry key recreated (hardware accelerated mode starts).
- Menu background / cursor trail fix.
- Gameplay crash fix (depth-buffer dirty rect clipping).
- dgVoodoo2 configuration.
