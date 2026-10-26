# The Creed – technical notes

Reverse-engineering notes behind the unofficial patch. All addresses refer to **`Creed.exe` v1.6 build 160** (6 Jan 1999, MD5 `746DFE681C5B157DBD53C3CD18D336C5`, image base `0x00400000`, `.text` file offset = VA − `0x00400C00`).

Tools used: DxWnd logs, Windows Error Reporting minidumps, Task Manager full dumps, Python (`pefile`, `capstone`, `keystone`, `minidump`).

## The game at a glance

- `Creed.exe` is the game, `AGOS.exe` a separate tool (no DirectDraw).
- Two builds on the CD share the **same** `Creed.exe`:
  - *Non-Accelerated*: `Data\Scene8.cus`, DirectDraw 640×480×8 (palette) + Direct3D **Ramp** device.
  - *Hardware Accelerated*: `Data\Scene16.cus`, Direct3D **HAL**, 16-bit.
- Two CDs: *Main* (volume `CREED_MAIN`, `Data\data.v00` + CD-Audio tracks 2–19) and *Data* (volume `CREED_DATA`, `Data\Data.v01-v03`, scene files).

## 1. Black menu background and cursor trails

**Symptom:** menu buttons visible, background black, the mouse leaves a trail.

**Evidence (DxWnd log):** ~5,550 × `IDirectDrawSurface::BltFast ... ERROR DDERR_UNSUPPORTED`, all with the same source surface – a 640×480 buffer the game composes every screen into, then copies to the back buffer.

**Cause:** at VA `0x00406D0E` the buffer is created with

```
mov dword ptr [esp+0x84], 0x1800     ; ddsCaps = SYSTEMMEMORY | TEXTURE
```

Windows 98 DirectDraw tolerated blitting a texture surface to the back buffer; modern implementations reject it. The surface is stored in `[0x4F69C0]` and only ever used with Lock/Unlock/BltFast/SetPalette/Restore – never as a Direct3D texture – so the `TEXTURE` cap is unnecessary. The cursor trail has the same cause: the game erases the cursor by restoring background pixels from this buffer.

**Fix:** caps → `0x2840` (`OFFSCREENPLAIN | SYSTEMMEMORY | 3DDEVICE`; `3DDEVICE` because a Z-buffer is attached to it). File offset `0x06115`.

## 2. "Non-Accelerated scene data not found"

**Cause:** at start-up (`0x0043C5B2`) the game opens `HKEY_CLASSES_ROOT\The Creed` and reads `Scene8`, `Scene16`, `InstallType`, `InstallDir`, `Password`, `LockCode`. Only if `Scene16` exists does it set `[0x4F7234] = 1`. At `0x0043C852`, if that flag is not 1 the device is forced to *Software Only*, so the accelerated install looks for `Scene8.cus` and fails. The key was written by the original setup, which does not run on modern Windows.

`InstallType == "MAXIMUM"` sets `[0x4F5368] = 1` (everything on disk), otherwise 2.

**Fix (v1.2):** `0x0043C7D1` (the point both registry paths reach, before the launcher dialog) → `jmp 0x00488384` (v1.4 address):

```
mov dword ptr [0x4F7234], 1      ; accelerated scene data installed
mov byte  ptr [0x4F5368], 1      ; full install
mov ecx, dword ptr [esp+0x24]    ; replaced instructions
push 0x80
jmp 0x0043C7DA
```

The default scene path (`data/scene16.cus`, relative to the game folder) is already set at `0x0043C57A`. (v1.0/v1.1 wrote the registry key instead.)

## 3. Crash a few seconds into gameplay (original bug)

**Evidence (minidump):** `EXCEPTION_ACCESS_VIOLATION` reading `0x0B45DBAA` at `0x00425880` (`rep movsd`). The function locks the background Z-buffer `[0x4F69C4]` and the back buffer's Z-buffer `[0x4F69BC]` and copies 16-bit depth row by row for each rectangle in the dirty list at `0x004B689C` (`left, top, right, bottom`, count in `0x004B6898`).

Rectangle list at the time of the crash (surfaces are 640×480, pitch `0x500`):

```
(-159,272)-(0,331)   (853,593)-(917,704)  <- crashing one   (771,661)-(895,788) ...
```

There is no clipping, so anything near or off screen reads/writes outside the buffer. Windows 98 usually survived the stray accesses.

**Same cause, visible symptom – trails at the screen edges:** the function that consumes the list, `0x00425670`, first restores the background of every rectangle from the *previous* frame's list (`0x004B9470`, a copy of `0x004B689C`) with `BltFast(back, left, top, background, &rect)`. A rectangle that sticks out of the screen makes `BltFast` fail with `DDERR_INVALIDRECT` for the whole rectangle, so the cursor or a character leaves a trail along the edges until the scene is redrawn.

**Fix (v1.4):** the function entry `0x00425670` → `jmp 0x004882D0` (CLIP cave), which clips every rectangle of `0x004B689C` in place before anything uses it, then runs the replaced instructions:

```
movzx ecx, word [0x4B6898] ; edx = 0x4B689C ; eax = 0
loop: left  = max(left, 0)    top    = max(top, 0)
      right = min(right, 640) bottom = min(bottom, 480)
      edx += 16 ; dec ecx
mov eax, [0x4F6EEC] ; sub esp, 0xEC ; jmp 0x0042567B
```

Both the colour restore and the depth copy then work on valid rectangles; empty ones are skipped by the original `right > left` / `bottom > top` checks (the depth copy) or rejected harmlessly (`BltFast`). v1.0–v1.3 clipped only inside the depth-copy loop (`0x004257FB` → cave), which fixed the crash but not the trails.

The code caves live in the zero padding at the end of `.text`; its `VirtualSize` is raised from `0x872C6` to `0x87400` (PE header, file offset `0x180`) so the padding is mapped.

## 4. No-CD

**CD check:** `0x00405CF0` enumerates drives (`GetLogicalDriveStringsA`, `GetDriveTypeA == DRIVE_CDROM`, `GetVolumeInformationA`) and accepts `CREED_MAIN` when `[0x4F5368] == 1` or `CREED_DATA` when it is 2; the root is stored in `0x004F5268`. Wrappers at `0x00405B70` / `0x00428C8C` show *"Please insert the CD"* (Retry/Cancel). The root is only used as `"%sData\data.v00"` (`0x00408388`, `0x0040BEF7`, `0x0040E9FE`; disc 2 code swaps the extension to `.v01-.v03`). No copy protection is involved.

**Fix (hybrid, v1.2):** `0x00405CF0` → `jmp 0x00488328` (v1.4 address):

```
mov edx, "cd1\Data\data.v00"
cmp byte ptr [0x4F5368], 2 / jne
mov edx, "cd2\Data\Data.v01"
push edx                                   ; keep the path on the stack: edx is volatile
CreateFileA(edx, GENERIC_READ, FILE_SHARE_READ, 0, OPEN_EXISTING, 0x80, 0)
cmp eax, -1 / je nofiles
CloseHandle(eax) ; pop edx
copy the first 4 bytes ("cd1\" / "cd2\") to 0x4F5268, terminate, return 1
nofiles: pop edx ; sub esp, 0x20C ; jmp 0x00405CF6   ; original drive search
```

## 5. CD music

`0x00431A80` opens MCI `cdaudio`, sets `MCI_FORMAT_TMSF`; `0x00431B20` plays from track *n+1* to *n+2* with `MCI_NOTIFY`. Disabled when the requested disc is 2. ogg-winmm (a `winmm.dll` wrapper) answers these calls and plays `Music\TrackNN.ogg`.

## 6. Graphics wrapper settings (dgVoodoo2 2.87.6)

Findings from testing on Windows 11 (Intel iGPU):

| Setting | Value | Why |
|---|---|---|
| `AppControlledScreenMode` | `true` | `false` (forced windowed) → game minimises after the intro and never recovers |
| `FullScreenMode` | `true` | |
| `ScalingMode` | `stretched_ar` | `centered` shows a 640×480 box |
| `FastVideoMemoryAccess` | `false` | `true` → image freezes on the last menu frame (game draws via Lock) |
| `PrimarySurfaceBatchedUpdate` | `false` | `true` → menu selector never shown (menus draw straight to the primary surface) |
| `PresentationModel` | `discard` | with batching off, keeps the menu fast |
| `CaptureMouse` | `false` | `true` keeps the cursor locked to the game after Alt+Tab |

DxWnd + Ramp (Non-Accelerated build): the Ramp device lights by writing colour ramps into the 8-bit palette; under emulation characters and the cursor come out black and scenes very dark – not fixed.

## 7. Alt+Tab / Ctrl+Alt+Del (v1.3)

**Symptom:** after leaving the game it could not be brought back (sound kept playing), and the mouse stayed locked to the game.

**Evidence (Task Manager dump):** main thread inside `0x0042A180`, the per-frame message pump. When `IDirectDraw4::TestCooperativeLevel` ([`0x4F6A08`] vtable `+0x68`) fails, the game loops on `WaitMessage` until it succeeds again, then calls `RestoreAllSurfaces` (`+0x64`) and reloads its textures (`0x0040A7B0` accelerated / `0x0040A4D0` software). Under dgVoodoo2 exclusive mode is never reported back, so the loop never ends; the audio runs on its own thread.

Also: the window procedure (`0x0043C3F0`) only handles `WM_DESTROY`, `WM_CLOSE`, `SC_KEYMENU` and `0x3B9`; the DirectInput keyboard is set to `DISCL_EXCLUSIVE | DISCL_BACKGROUND` (9) at `0x00405FC1` and is never re-acquired; the mouse has no cooperative level set.

**Fix:**
- WndProc `0x0043C3FA` → `jmp 0x004883A4` (v1.4 address): on `WM_ACTIVATEAPP` store `[0x4F8F00] = !wParam`, then continue the original code. `0x4F8F00` lies in the zero-filled tail of the `.data` page (`VirtualSize` ends at `0x4F86D0`), which nothing else references.
- Pause loop: `0x0042A205` and `0x0042A254` test `[0x4F8F00]` instead of calling `TestCooperativeLevel`. On return the original restore/reload path runs unchanged.
- Keyboard cooperative level `9` → `0xA` (`NONEXCLUSIVE | BACKGROUND`; background is kept because the game never re-acquires the device).
- dgVoodoo2 `CaptureMouse = false`.

**Cursor gone after returning (v1.4):** the mouse is read with `GetDeviceState` in immediate mode (`0x0040884D`, deltas in `0x004E7BF0`, added to the cursor at `0x004F6FF0/F4`). For relative axes that returns the movement since the previous read, so everything done on the desktop while the game was paused arrived in one frame and threw the cursor far off screen. Fix: on leaving the pause loop (`0x0042A25D`) a `call` to the MOUSE cave does one throw-away `GetDeviceState` before the original restore path.

Cave layout in v1.4 (built directly from the original exe by `tools/dev/build_v1.4.py`): CLIP `0x004882D0`, CD `0x00488328`, REG `0x00488384`, WND `0x004883A4`, MOUSE `0x004883C4`, strings `0x004883D8`. The PE `TimeDateStamp` is +1 – a fresh hash for the release build after Windows Smart App Control blocked the first v1.4 build.

## 8. Known remaining issues

- **Smart App Control** (Windows 11) blocks unsigned executables without reputation, so the patched `Creed.exe` may be blocked until it is code-signed.

- **Intro videos** are played through DirectShow before the exclusive full-screen mode is set, so they appear in a window.
