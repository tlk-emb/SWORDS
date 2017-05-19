@echo off

SET sdkpath=%xilinxpath%\SDK\2015.4\bin

SET cfile=%~1
SET jsonfile=%~2
SET projectname=%~3
SET cswfile=%cfile:~3,-2%_sw.c
SET ciffile=%cfile:~3,-2%_if.c

SET toolchainpath=%~4


if not {%~1} == {} if not {%~2} == {} if not {%~3} == {} (

  mkdir software
  copy %ciffile% software
  copy %cswfile% software\helloworld.c
  copy %toolchainpath%\utils\lscript.ld software
  copy %toolchainpath%\utils\timer.c software
  copy %toolchainpath%\utils\timer.h software
  python %toolchainpath%\python\generatesdktcl.py %cfile% %jsonfile% %projectname%
  %sdkpath%\xsdk.bat -batch -source %projectname%_build_sdk.tcl

) else (
    echo "few arguments!"
)
