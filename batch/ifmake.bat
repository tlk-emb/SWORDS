@echo off

SET cfile=%~1
SET jsonfile=%~2
SET toolchainpath=%~3
SET llvmpath=%~4
SET hwfile=%cfile:~0,-2%_hw.c

python %toolchainpath%\python\hwifmake.py %hwfile% %jsonfile% %toolchainpath%
python %toolchainpath%\python\ifmake.py %hwfile% %jsonfile%

exit /b 0
