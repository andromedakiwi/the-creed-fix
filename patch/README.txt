=====================================================================
 THE CREED (1999) - UNOFFICIAL PATCH v2.0
 by Andromeda Kiwi + Claude
=====================================================================

Makes The Creed (Insomnia Entertainment / Dreamtime Interactive /
Electronic Arts, 1999) playable on Windows 10/11 in full screen, with
optional No-CD and CD music. Your original Creed.exe is not modified:
the included dinput.dll applies the fixes in memory when the game
starts (and logs them to creedfix.log).

For the HARDWARE ACCELERATED version of the game only, with the
ORIGINAL Creed.exe v1.6 build 160 (Data\Scene16.cus present).

This is a community TEST release - please report what works and what
breaks (see "Reporting problems").


---------------------------------------------------------------------
 INSTALL
---------------------------------------------------------------------

1. Extract this zip into your The Creed game folder (the folder with
   Creed.exe and the Data folder) and overwrite when asked.

2. Start Creed.exe and play.

That's it. No installer, no registry, no admin rights, and Creed.exe
is not changed. With the CD in the drive the game runs exactly like
the original did.

Upgrading from patch v1.x: v1.x replaced Creed.exe. Put the original
back (Creed.exe.original or your backup). With a v1.x Creed.exe the
fixes are not applied and a message tells you so.

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
game asks for a CD audio track. In-game, this is the "music" volume,
and the music volume slider now controls it. Without the Music folder
the game is simply silent there.


---------------------------------------------------------------------
 OPTIONAL: SKIP THE INTRO VIDEO
---------------------------------------------------------------------

In the launcher, open Configuration and untick "Intro Videos"
(formerly "Intro Attract"): Single Player then goes straight to the
game menu. Ticked, the intro and the idle "attract" video play as in
the original.


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

3. Crash a few seconds into gameplay, and cursor/character trails at
   the screen edges (original 1999 bug). When something is near or
   past the screen edge, the game's "dirty rectangles" go outside the
   640x480 screen: the depth copy then reads outside its buffer
   (crash) and the background restore is rejected (trails). The
   rectangles are now clipped to the screen.

4. Graphics on modern GPUs: dgVoodoo2 2.87.6 (by Dege) is included,
   configured for full screen, 4:3 aspect ratio, working menu
   selector and normal speed.

5. Optional No-CD. The game looked for a CD labelled CREED_MAIN or
   CREED_DATA and read Data\data.v00 (CD 1) or Data\Data.v01-v03
   (CD 2) from it. The game now uses the cd1 / cd2 folders when they
   exist, and falls back to the real CD when they don't. There is no
   copy protection involved - only a disc check.

6. CD music without the CD: ogg-winmm (by ayuanx, GPL-2.0).

7. Alt+Tab / Ctrl+Alt+Del. The game paused on focus loss until
   DirectDraw reported exclusive mode back - which never happens under
   a modern wrapper - so it never resumed, and the keyboard was opened
   in exclusive background mode. The game now pauses and resumes on
   WM_ACTIVATEAPP and uses a non-exclusive keyboard; the mouse is no
   longer captured by dgVoodoo2, and mouse movement made while the
   game was paused is discarded (it used to throw the cursor off
   screen).

8. Music volume. The slider changed the sound card's analogue
   "CD audio" mixer line, which modern PCs don't have, so it did
   nothing. It now sets ogg-winmm's volume.

9. Intro video. The startup video always played; the "Intro
   Attract" option only affected the idle attract video. The option
   is now called "Intro Videos" and also skips the startup video.


---------------------------------------------------------------------
 KNOWN ISSUES
---------------------------------------------------------------------

- Windows 11 Smart App Control: v2.0 keeps the original Creed.exe, but
  the new dinput.dll is not code-signed yet. Please report if it is
  blocked ("could not verify its publisher").
- The intro videos play in a window (desktop visible at the sides);
  the game goes full screen as soon as you press Enter/Esc. Untick
  "Intro Videos" in Configuration to skip them.
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
     CaptureMouse                = false   (true keeps the mouse
                                            locked after Alt+Tab)


---------------------------------------------------------------------
 UNINSTALL
---------------------------------------------------------------------

Delete dinput.dll, DDraw.dll, D3DImm.dll, dgVoodoo.conf, winmm.dll,
winmm.ini and creedfix.log (and the cd1, cd2 and Music folders if you
created them). Creed.exe was never modified.


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

v2.0  Creed.exe is no longer modified: the same fixes are applied in
      memory by dinput.dll (open source, src/creedfix), which checks
      the executable first and logs to creedfix.log. No-CD folders
      are found next to Creed.exe regardless of the working folder.
v1.5  Music volume slider works (with ogg-winmm); "Intro Videos"
      option in Configuration skips the startup video.
v1.4  No more cursor/character trails at the screen edges; cursor no
      longer lost after Alt+Tab.
v1.3  Alt+Tab / Ctrl+Alt+Del fixed: the game pauses when you leave and
      resumes when you come back; mouse and keyboard are released.
v1.2  Just extract and play: ships the patched Creed.exe, no installer
      or registry needed. No-CD now falls back to the real CD when the
      cd1/cd2 folders are missing. Optional Extras\CopyCDs.bat.
v1.1  No-CD (copies the CD files once), CD music via ogg-winmm.
v1.0  First release: registry fix, menu background fix, gameplay
      crash fix, dgVoodoo2 configuration.


---------------------------------------------------------------------
 TECHNICAL DETAILS (Creed.exe v1.6 build 160)
---------------------------------------------------------------------

Creed.exe imports DINPUT.dll; Windows loads dinput.dll from the game
folder first. On load it checks the image (base 0x400000, PE
timestamp 3692CA5C, original bytes at every site - all or nothing),
patches the code in memory and forwards DirectInputCreateA/W/Ex to
the system dinput.dll. Source: src/creedfix/creedfix.c.

VA          Change (in memory)
0x00406D15  background buffer caps 0x1800 (SYSTEMMEMORY|TEXTURE) ->
            0x2840 (OFFSCREENPLAIN|SYSTEMMEMORY|3DDEVICE)
0x00405FC2  DirectInput keyboard cooperative level 9 -> 0xA
0x00405CF0  CD drive search -> cd_find(): <game>\cd1\ or cd2\ if the
            data file exists, else the original search (trampoline)
0x00408367  startup video only if "Intro Videos" ([0x4F5258]) is on
            and not in multiplayer
0x00425670  clip every dirty rect (0x4B689C) to 640x480 in place
0x0042A205  focus pause entered while the app is inactive
0x0042A254  ...left when active again; mouse delta flushed
            (GetDeviceState), then the original restore/reload
0x0043C3FA  window procedure records WM_ACTIVATEAPP
0x0043C7D1  after the registry read: [0x4F7234]=1, [0x4F5368]=1
0x00431BB0  music volume -> winmm auxSetVolume (ogg-winmm)
(resource)  Configuration checkbox "Intro Attract" -> "Intro Videos"

v1.x applied the same changes to Creed.exe on disk (code caves at
0x004882D0+); docs/TECHNICAL.md in the repository has the details.

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
