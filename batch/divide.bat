@echo off

SET cfile=%~1
SET jsonfile=%~2
SET llvmpath=%~3
SET hwfile=%cfile:~0,-2%_hw.c

if not {%~4} == {} (
  python %toolchainpath%\python\divide.py %cfile% %jsonfile% --llvm-libfile %llvmpath%
) else (
  python %toolchainpath%\python\divide.py %cfile% %jsonfile%
)

exit /b 0
