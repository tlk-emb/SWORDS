@echo off

SET vivadopath=%xilinxpath%\Vivado_HLS\2015.4\bin

SET cfile=%~1
SET jsonfile=%~2
SET projectname=%~3
SET hlsipdir=%projectname%_hls
SET tclfile=%projectname%_hls.tcl

SET toolchainpath=%~4


if not {%~1} == {} if not {%~2} == {} if not {%~3} == {} (

  mkdir %hlsipdir%
  copy %cfile% %hlsipdir%
  echo python %toolchainpath%generatehlstcl.py
  python %toolchainpath%generatehlstcl.py %cfile% %jsonfile% %projectname%

  copy %tclfile% %hlsipdir%
  %vivadopath%\vivado_hls -f %hlsipdir%/%tclfile%

) else (
    echo "few arguments!"
)
