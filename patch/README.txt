=====================================================================
 THE CREED (1999) - UNOFFICIAL PATCH v1.2
 by Andromeda Kiwi + Claude
=====================================================================

Makes The Creed (Insomnia Entertainment / Dreamtime Interactive /
Electronic Arts, 1999) playable on Windows 10/11 in full screen, with
optional No-CD and CD music.

For the HARDWARE ACCELERATED version of the game only
(Creed.exe v1.6 build 160, Data\Scene16.cus present).

This is a community TEST release - please report what works and what
breaks (see "Reporting problems").


---------------------------------------------------------------------
 INSTALL
---------------------------------------------------------------------

1. (Optional) Keep a copy of your original Creed.exe somewhere safe.

2. Extract this zip into your The Creed game folder (the folder with
   Creed.exe and the Data folder) and overwrite when asked.

3. Start Creed.exe and play.

That's it. No installer, no registry, no admin rights. With the CD in
the drive the game runs exactly like the original did.

If the original CD setup does not run on your PC, copying the
Hardware Accelerated game files to a folder (e.g. C:\Games\The Creed,
not C:\Program Files) is enough.

If the launcher's Configuration screen shows "Software Only", select
the 3D accelerator / Direct3D HAL there.


---------------------------------------------------------------------
 OPTIONAL: PLAY WITHOUT THE CDs
---------------------------------------------------------------------

Run Extras\CopyCDs.bat. It asks for CD 1 ("Main Disc") and CD 2
("Data Disc") and copies the ~120 MB the game reads from them into
the folders cd1 and cd2. From then on the CDs are not needed.

You can also copy them by hand:
   CD 1: Data\data.v00                -> <game>\cd1\Data\data.v00
   CD 2: Data\Data.v01, .v02, .v03    -> <game>\cd2\Data\

If those folders are missing, the game simply asks for the CD, as the
original did - so this step can be skipped.


---------------------------------------------------------------------
 OPTIONAL: MUSIC
---------------------------------------------------------------------

The ambient music is stored on CD 1 as audio tracks 2 to 19. Rip them
to Ogg Vorbis files named

   <game>\Music\Track02.ogg ... <game>\Music\Track19.ogg

With the free, portable fre:ac (https://www.freac.org/): choose the
Ogg Vorbis encoder, set the file name pattern to Track<track>, untick
track 1 (data track) and set the output folder to <game>\Music.

The included winmm.dll (ogg-winmm) plays those files whenever the
game asks for a CD audio track. In-game, this is the "music" volume.
Without the Music folder the game is simply silent there.


---------------------------------------------------------------------
 WHAT IT FIXES
---------------------------------------------------------------------

1. "Non-Accelerated scene data not found" on start-up.
   The game decided its mode from a registry key written by the
   original installer; without it, it forced software mode and looked
   for the wrong data file. Creed.exe no longer needs that key.

2. Black menu backgrounds and mouse cursor trails.
   The 640x480 background buffer was created as a "texture" surface.
   Windows 98 let the game copy it to the screen; modern DirectDraw
   implementations refuse, so the background never appeared.

3. Crash a few seconds into gameplay (original 1999 bug).
   When characters or effects are near or past the screen edge, the
   game copies depth-buffer rectangles outside the 640x480 buffer.
   Windows 98 often survived that; modern Windows does not. Creed.exe
   now clips those rectangles to the screen.

4. Graphics on modern GPUs: dgVoodoo2 2.87.6 (by Dege) is included,
   configured for full screen, 4:3 aspect ratio, working menu
   selector and normal speed.

5. Optional No-CD. The game looked for a CD labelled CREED_MAIN or
   CREED_DATA and read Data\data.v00 (CD 1) or Data\Data.v01-v03
   (CD 2) from it. Creed.exe now uses the cd1 / cd2 folders when they
   exist, and falls back to the real CD when they don't. There is no
   copy protection involved - only a disc check.

6. CD music without the CD: ogg-winmm (by ayuanx, GPL-2.0).


---------------------------------------------------------------------
 KNOWN ISSUES
---------------------------------------------------------------------

- Do not Alt+Tab or Ctrl+Alt+Del while playing. The game pauses when
  it loses focus and never resumes. If it happens, end Creed.exe in
  Task Manager.
- The intro videos play in a window (desktop visible at the sides);
  the game goes full screen as soon as you press Enter/Esc.
- Missions have not been tested to the end yet. The game was infamous
  for freezing before the ending - reports very welcome.
- Multiplayer (DirectPlay) untested.
- Do not run DxWnd at the same time.
- Avoid opening dgVoodooCpl.exe: saving from it rewrites dgVoodoo.conf.
  The settings that matter are:
     FullScreenMode              = true
     ScalingMode                 = stretched_ar  ("stretched" fills the
                                                  whole screen)
     PresentationModel           = discard
     AppControlledScreenMode     = true
     FastVideoMemoryAccess       = false   (true freezes the image)
     PrimarySurfaceBatchedUpdate = false   (true hides the menu
                                            selector)


---------------------------------------------------------------------
 UNINSTALL
---------------------------------------------------------------------

Put your original Creed.exe back and delete DDraw.dll, D3DImm.dll,
dgVoodoo.conf, winmm.dll and winmm.ini (and the cd1, cd2 and Music
folders if you created them).


---------------------------------------------------------------------
 REPORTING PROBLEMS
---------------------------------------------------------------------

Please include your Windows version, graphics card, what you were
doing, and whether it happens every time.

For crashes, a crash dump helps enormously: right-click
Extras\EnableCrashDumps.bat -> "Run as administrator" (only once).
From then on every crash of Creed.exe saves a .dmp file in the game's
CrashDumps folder - attach it to your report.


---------------------------------------------------------------------
 CHANGES
---------------------------------------------------------------------

v1.2  Just extract and play: ships the patched Creed.exe, no installer
      or registry needed. No-CD now falls back to the real CD when the
      cd1/cd2 folders are missing. Optional Extras\CopyCDs.bat.
v1.1  No-CD (copies the CD files once), CD music via ogg-winmm.
v1.0  First release: registry fix, menu background fix, gameplay
      crash fix, dgVoodoo2 configuration.


---------------------------------------------------------------------
 TECHNICAL DETAILS (based on Creed.exe v1.6 build 160)
---------------------------------------------------------------------

Original Creed.exe MD5: 746DFE681C5B157DBD53C3CD18D336C5
Patched  Creed.exe MD5: 13F318E1130BE7545FA6C682291983F3

File offset  VA          Change
0x00180      (PE hdr)    .text VirtualSize 0x872C6 -> 0x87400
                         (maps the code caves below)
0x06115      0x00406D15  CreateSurface caps of the background buffer
                         0x1800 (SYSTEMMEMORY|TEXTURE) ->
                         0x2840 (OFFSCREENPLAIN|SYSTEMMEMORY|3DDEVICE)
0x24BFB      0x004257FB  jmp 0x004882D0 + NOPs
0x876D0      0x004882D0  cave: load dirty rect, clamp left/top >= 0
                         and right/bottom <= surface width/height
                         (from the locked DDSURFACEDESC), jmp back to
                         0x00425813
0x3BBD1      0x0043C7D1  jmp 0x00488390 + NOPs (after the registry read)
0x87790      0x00488390  cave: [0x4F7234] = 1 (accelerated scene data
                         installed), [0x4F5368] = 1 (full install),
                         then the replaced instructions, jmp 0x0043C7DA
0x050F0      0x00405CF0  CD drive search -> jmp 0x00488320
0x87720      0x00488320  cave: disc 1 -> "cd1\", disc 2 -> "cd2\"
                         ([0x4F5368]); if cd?\Data\data.v00 / Data.v01
                         opens (CreateFileA), use it as the CD root and
                         return 1, else run the original drive search
0x877C0      0x004883C0  strings used by the caves

Registry the original game reads: HKEY_CLASSES_ROOT\The Creed
  (Scene8, Scene16, InstallType, InstallDir, Password, LockCode).
CD music: MCI "cdaudio", TMSF, MCI_PLAY from track n+1 to n+2
  with MCI_NOTIFY (0x00431B20).


---------------------------------------------------------------------
 CREDITS / DISCLAIMER
---------------------------------------------------------------------

Patch: Andromeda Kiwi + Claude.
dgVoodoo2 2.87.6 by Dege (https://dege.freeweb.hu/), included
unmodified (DDraw.dll, D3DImm.dll).
ogg-winmm by ayuanx (https://github.com/ayuanx/ogg-winmm), GPL-2.0,
built unmodified from source (winmm.dll; see Licenses folder).

Unofficial fan patch, not affiliated with Insomnia Entertainment,
Dreamtime Interactive or Electronic Arts. The Creed is (c) 1998
Insomnia Entertainment Pty Limited. Use at your own risk.
