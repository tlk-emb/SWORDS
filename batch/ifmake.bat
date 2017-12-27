@echo off

SET cfile=%~1
SET jsonfile=%~2
SET toolchainpath=%~3
SET llvmpath=%~4
SET hwfile=%cfile:~0,-2%_hw.c

if not {%~4} == {} (
  python %toolchainpath%\python\hwifmake.py %hwfile% %jsonfile% %toolchainpath% --llvm-libfile %llvmpath%
  python %toolchainpath%\python\ifmake.py %cfile% %jsonfile% --llvm-libfile %llvmpath%
) else (
  python %toolchainpath%\python\hwifmake.py %hwfile% %jsonfile% %toolchainpath%
  rem python %toolchainpath%\python\ifmake.py %cfile% %jsonfile%
)

exit /b 0
