# Release notes

One file per version (`v1.3.md`, ...). To publish a release: add the notes file, update `patch/`, then set `VERSION` to the new number and push to `main`. The `Release` workflow verifies `patch/Creed.exe` against `tools/patch_creed.py`, zips `patch/` and creates the GitHub Release.
