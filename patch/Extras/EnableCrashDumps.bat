@echo off
title The Creed - enable crash dumps
net session >nul 2>&1 || (echo Right-click this file and choose "Run as administrator". & pause & exit /b 1)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0EnableCrashDumps.ps1"
echo.
pause
