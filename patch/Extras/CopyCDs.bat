@echo off
title The Creed - copy CD files (No-CD)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0CopyCDs.ps1"
echo.
pause
