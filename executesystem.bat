@echo off

SET cfilepath=%~1
SET jsonfilepath=%~2
SET projectname=%~3
SET cswfile=%cfilepath:~0,-2%_sw.c
SET ciffile=%cfilepath:~0,-2%_if.c
SET sdkpath=C:\Xilinx\SDK\2015.4\bin\

SET toolchainpath=%~p0

if not {%~1} == {} if not {%~2} == {} if not {%~3} == {} (
    
    python %toolchainpath%generateexecutesdktcl.py %cfilepath% %jsonfilepath% %projectname%
    %sdkpath%xsdk.bat -batch -source %projectname%_config_sdk.tcl
    %sdkpath%xsdk.bat -batch -source %projectname%_execute_sdk.tcl

) else (
    echo "few arguments!"
)