@echo off

SET cfilepath=%~1
SET jsonfilepath=%~2
SET projectname=%~3
SET hlsipdir=%projectname%_hls
SET tclfilename=%projectname%_hls.tcl

SET toolchainpath=%~p0

if not {%~1} == {} if not {%~2} == {} if not {%~3} == {} (

    mkdir %hlsipdir%
    copy %cfilepath% %hlsipdir%
    python %toolchainpath%generatehlstcl.py %cfilepath% %jsonfilepath% %projectname%
    copy %tclfilename% %hlsipdir%
    vivado_hls -f %hlsipdir%/%tclfilename%

) else (
    echo "few arguments!"
)