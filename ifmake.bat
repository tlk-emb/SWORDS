@echo off

SET cfile=%~1
SET jsonfile=%~2
SET toolchainpath=%~3
SET llvmpath=%~4
SET hwfile=%cfile:~0,-2%_hw.c

if not {%~4} == {} (
  python %toolchainpath%\divide.py %cfile% %jsonfile% --llvm-libfile %llvmpath%
  python %toolchainpath%\ifmake.py %cfile% %jsonfile% --llvm-libfile %llvmpath%
  python %toolchainpath%\renamehwparams.py %cfile% %jsonfile% --llvm-libfile %llvmpath%
) else (
  python %toolchainpath%\divide.py %cfile% %jsonfile%
  python %toolchainpath%\ifmake.py %cfile% %jsonfile%
  python %toolchainpath%\renamehwparams.py %hwfile% %jsonfile%
)
