@echo off

SET toolchainpath=%~dp0
CALL %toolchainpath%\..\setenv.bat
  
SET sdkpath=%xilinxpath%\SDK\%xilinxversion%\bin

SET projectname=%~1

SET toolchainpath=%~dp0


if not {%~1} == {} (
   
  cd %projectname%

  %sdkpath%\xsdk.bat -batch -source %projectname%_config_sdk.tcl

  cd ..\

) else (
    echo "few arguments!"
)
