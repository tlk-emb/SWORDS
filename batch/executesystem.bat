@echo off

SET toolchainpath=%~dp0
CALL %toolchainpath%\..\setenv.bat
  
SET sdkpath=%xilinxpath%\SDK\%xilinxversion%\bin

SET projectname=%~1

SET toolchainpath=%~dp0

SET arm_reset_tcl=%toolchainpath%arm_reset.tcl
SET arm_reconnect_tcl=%toolchainpath%arm_reconnect.tcl
if not {%~1} == {} (
    
  cd %projectname%
  %sdkpath%\xmd.bat -tcl %arm_reset_tcl:\=/%
  %sdkpath%\xmd.bat -tcl %arm_reconnect_tcl:\=/%
  timeout 5
  %sdkpath%\xsdk.bat -batch -source %projectname%_config_sdk.tcl
  %sdkpath%\xsdk.bat -batch -source %projectname%_execute_sdk.tcl

  cd ..

) else (
  echo "few arguments!"
)
