@echo off
setlocal
 title Lost and Found System
 echo Starting Lost and Found System. Please wait...
 "%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-System.ps1" -OpenBrowser
 set "launch_exit=%errorlevel%"
 if not "%launch_exit%"=="0" (
     echo.
     echo Startup failed. Please send a screenshot of the error above.
     pause
 )
 exit /b %launch_exit%
