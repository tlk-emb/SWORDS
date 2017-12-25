@echo off

SET vivadopath=%xilinxpath%\Vivado\%xilinxversion%\bin

SET jsonfile=%~1
SET projectname=%~2
SET hlsippath=%cd%\%~3
SET projectpath=%~4

SET vivadodir=%projectname%_vivado
SET tclfile=%projectname%_vivado.tcl

SET toolchainpath=%~5

if not {%~1} == {} if not {%~2} == {} if not {%~3} == {} (

  python %toolchainpath%\python\generatevivadotcl.py %jsonfile% %projectname% %projectpath% %hlsippath% %toolchainpath%
  mkdir %vivadodir%
  copy %tclfile% %vivadodir%
  %vivadopath%\vivado -mode batch -source %vivadodir%/%tclfile%

) else (

  echo "few arguments!"
)
