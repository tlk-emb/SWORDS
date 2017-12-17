@echo off

SET vivadopath=%xilinxpath%\Vivado_HLS\%xilinxversion%\bin

SET cfile=%~1
SET jsonfile=%~2
SET projectname=%~3
SET hlsipdir=%projectname%_hls
SET tclfile=%projectname%_hls.tcl

SET toolchainpath=%~4


if not {%~1} == {} if not {%~2} == {} if not {%~3} == {} (

  mkdir %hlsipdir%
  copy %cfile% %hlsipdir%
  python %toolchainpath%\python\generatehlstcl.py %cfile% %jsonfile% %projectname%

  copy %tclfile% %hlsipdir%
  %vivadopath%\vivado_hls -f %hlsipdir%/%tclfile%

) else (
    echo "few arguments!"
)
