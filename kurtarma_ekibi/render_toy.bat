@echo off
rem Minik Ustalar - Windows'ta render.  Kullanim:  render_toy.bat        (1280x720)
rem                                               render_toy.bat --hd   (1920x1080)
rem Blender baska bir yerdeyse asagidaki satiri duzeltin (Blender 4.0 veya 4.1).
set BLENDER="C:\Program Files\Blender Foundation\Blender 4.1\blender.exe"
cd /d "%~dp0"
if not exist build mkdir build
for %%S in (t_intro t_ep1 t_ep2 t_ep3 t_ep4 t_outro) do (
  echo === %%S sahnesi kuruluyor
  %BLENDER% -b -P %%S.py -- %1 > build\%%S.build.log 2>&1
  echo === %%S render ediliyor  ^(kareler: build\%%S^)
  %BLENDER% -b build\%%S.blend -a > build\%%S.render.log 2>&1
)
echo === Birlestiriliyor ^(ffmpeg gerekir^)
%BLENDER% -b -P birlestir.py
pause
