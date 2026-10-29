# The Creed (1999) – Unofficial Patch

<p align="center"><img src="docs/images/cover.png" alt="The Creed (1999) box art" width="320"></p>

Makes **The Creed** (Insomnia Entertainment / Dreamtime Interactive / Electronic Arts, 1999) playable on **Windows 10 and 11**, in full screen, with an optional **No-CD** mode and the **CD music** working again.

The Creed is a cyberpunk action-adventure that was famous for being buggy even in 1999. On modern Windows it would not install, crashed or showed black screens. This patch fixes the game's own bugs and bundles a tested graphics/music setup. Since v2.0 your original `Creed.exe` stays untouched: a small open-source `dinput.dll` applies the fixes in memory when the game starts.

> **Status:** community test release (v2.0). The fixes were tested on Windows 11 (Intel graphics) through several missions, including Alt+Tab, No-CD and music. Please [report](../../issues/new/choose) what works and what breaks.

By **Andromeda Kiwi + Claude**.

---

## Download & install

1. Download **`TheCreed_UnofficialPatch_v2.0.zip`** from [Releases](../../releases/latest).
2. Extract the zip into your game folder (the one with `Creed.exe` and `Data\`).
3. Run `Creed.exe` and play.

No installer, no registry, no admin rights, and `Creed.exe` is not modified. With the CD in the drive the game behaves like the original. The patch writes what it did to `creedfix.log` in the game folder.

**Requirements:** the *Hardware Accelerated* version of the game (`Data\Scene16.cus` present) with the **original** `Creed.exe` **v1.6 build 160**. *Upgrading from v1.x:* put your original `Creed.exe` back (`Creed.exe.original` or your backup) – the patched v1.x executable is detected and the fixes are not applied. If the original CD setup does not run, copying the game files to a folder such as `C:\Games\The Creed` (not `Program Files`) is enough.

### Optional: play without the CDs
Run `Extras\CopyCDs.bat`. It asks for CD 1 ("Main") and CD 2 ("Data") and copies the ~120 MB the game reads from them into `cd1\` and `cd2\`. If those folders are missing the game just asks for the CD, as before.

### Optional: music
The ambient soundtrack is CD 1 audio tracks 2–19. Rip them with [fre:ac](https://www.freac.org/) (portable, free) to Ogg Vorbis as `Music\Track02.ogg` … `Music\Track19.ogg`. The bundled `winmm.dll` ([ogg-winmm](https://github.com/ayuanx/ogg-winmm)) plays them in place of the CD, and the in-game *music* volume slider now controls them.

### Optional: skip the intro video
In the launcher's **Configuration**, untick **Intro Videos** (formerly *Intro Attract*) to go straight to the game menu. Ticked, the original intro and the idle "attract" video play as before.

---

## What it fixes

| Problem | Cause | Fix |
|---|---|---|
| *"Non-Accelerated scene data not found"* | Mode chosen from a registry key the original installer wrote; without it the game forces software mode | The game no longer depends on the registry |
| Black menu backgrounds, mouse cursor trails | 640×480 background buffer created as a *texture* surface; modern DirectDraw refuses to blit it (`DDERR_UNSUPPORTED`) | Created as a plain off-screen surface |
| Crash a few seconds into gameplay | **Original 1999 bug**: "dirty rectangles" outside the screen are copied without clipping → depth copy reads outside the buffer (access violation) | Rectangles clipped to the screen |
| Cursor / character trails at the screen edges | Same unclipped rectangles: the background restore `BltFast` rejects the whole rectangle, so nothing is redrawn | Same clipping |
| Alt+Tab / Ctrl+Alt+Del: game never comes back, mouse stuck | Focus-loss pause waits for DirectDraw exclusive mode, which the wrapper never reports back; keyboard opened in exclusive background mode | Pause driven by `WM_ACTIVATEAPP`; keyboard non-exclusive; dgVoodoo mouse capture off |
| Cursor gone after Alt+Tab | Mouse read in immediate mode: movement made on the desktop is delivered all at once on return, throwing the cursor far off screen | Accumulated movement discarded on resume |
| Needs the CDs | Disc check by volume label (`CREED_MAIN` / `CREED_DATA`) to read `data.v00` / `Data.v01-03` | Uses `cd1\` / `cd2\` when present, otherwise the real CD |
| No music without the CD | CD-Audio via MCI | ogg-winmm |
| Music volume slider does nothing | Volume set through the sound card's analogue *CD-audio mixer line*, which modern PCs don't have | Slider routed to ogg-winmm's volume (`auxSetVolume`) |
| Intro video can't be skipped | Startup video always played; the *Intro Attract* option only affected the idle attract video | The option (now *Intro Videos*) also skips the startup video |
| Graphics on modern GPUs | DirectDraw 6 + Direct3D HAL, 16-bit | dgVoodoo2 2.87.6 with a tested config |

All the details – addresses, disassembly and how each bug was found – are in **[docs/TECHNICAL.md](docs/TECHNICAL.md)**.

## Known issues

- **Windows 11 Smart App Control**: v1.x shipped a modified `Creed.exe`, which SAC often blocked. v2.0 keeps the original executable; the new `dinput.dll` is not code-signed yet, so please report if SAC blocks it.
- Intro videos play in a window (untick *Intro Videos* in Configuration to skip them); the game goes full screen after Enter/Esc.
- Not yet tested to the end of the campaign (the game was infamous for freezing before the ending).
- Multiplayer untested. The *Non-Accelerated* (software/Ramp) version is not supported – its 3D renders almost black on modern systems.
- Don't run DxWnd at the same time; avoid saving from `dgVoodooCpl.exe` (see `patch/README.txt` for the settings that matter).

## Reporting problems

Open an [issue](../../issues/new/choose) with your Windows version, GPU and what you were doing. For crashes, run `Extras\EnableCrashDumps.bat` as administrator once – every crash then writes a `.dmp` into `CrashDumps\`; attach it.

## Repository layout

```
src/creedfix/     the fixes: dinput.dll proxy (C + inline asm, MinGW), MIT
patch/            release content, ready to extract into the game folder
  dinput.dll        built from src/creedfix by the release workflow
  DDraw.dll, D3DImm.dll, dgVoodoo.conf   dgVoodoo2 2.87.6 + config
  winmm.dll, winmm.ini                   ogg-winmm (CD music)
  Extras/           CopyCDs.bat (No-CD), EnableCrashDumps.bat
tools/legacy/     v1.x tools that patched Creed.exe on disk (reference)
docs/             technical write-up, changelog, release notes
```

Build `dinput.dll` yourself: `make -C src/creedfix` with `i686-w64-mingw32-gcc`. Releases are built and published by GitHub Actions from this source.

## Credits & licenses

- Patch (`src/creedfix`), tools and docs: **Andromeda Kiwi + Claude** – [MIT](LICENSE).
- [dgVoodoo2](https://dege.freeweb.hu/) 2.87.6 by Dege – freeware, included unmodified.
- [ogg-winmm](https://github.com/ayuanx/ogg-winmm) by ayuanx – GPL-2.0, built unmodified from source (see `patch/Licenses/`).
- *The Creed* © 1998 Insomnia Entertainment Pty Limited; box art shown for identification only. This is an unofficial fan patch, not affiliated with Insomnia Entertainment, Dreamtime Interactive or Electronic Arts. The game is abandonware; no game files are included or modified.
