@echo off

SET toolchainpath=%~dp0
CALL %toolchainpath%\..\setenv.bat
  
SET sdkpath=%xilinxpath%\SDK\%xilinxversion%\bin

SET cfile=..\%~1
SET jsonfile=..\%~2
SET projectname=%~3

SET toolchainpath=%~dp0

if not {%~1} == {} if not {%~2} == {} if not {%~3} == {} (
    
  cd %projectname%

  python %toolchainpath%\..\python\generateexecutesdktcl.py %cfile% %jsonfile% %projectname%
  rem %sdkpath%\xsdk.bat -batch -source %projectname%_config_sdk.tcl
  %sdkpath%\xsdk.bat -batch -source %projectname%_execute_sdk.tcl

  cd ..

) else (
  echo "few arguments!"
)
