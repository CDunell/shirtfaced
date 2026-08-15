@echo off
REM Drag an .mp4 onto this file to write its final frame alongside it as a PNG.
REM The final frame is the seed for the next clip in an extension chain --
REM see docs/foundations/GENERATION_PIPELINE.md section 8.

if "%~1"=="" (
  echo Drag an mp4 onto this file, or run: lastframe.bat "path\to\clip.mp4"
  pause
  exit /b 1
)

if not exist "%~1" (
  echo Not found: %~1
  pause
  exit /b 1
)

set "OUT=%~dpn1_lastframe.png"

REM -sseof -0.5 seeks half a second from the end; -update 1 keeps overwriting
REM until the final frame. Seeking to exactly 0 can land past the last
REM keyframe and produce nothing.
ffmpeg -v error -sseof -0.5 -i "%~1" -update 1 -q:v 1 "%OUT%" -y

if exist "%OUT%" (
  echo Wrote: %OUT%
) else (
  echo Failed. Is ffmpeg on PATH?
)
pause
