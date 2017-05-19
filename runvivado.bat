@echo off

SET vivadopath=%xilinxpath%\Vivado\2015.4\bin

SET jsonfile=%~1
SET projectname=%~2
SET hlsippath=%~3
SET projectpath=%~4

SET vivadodir=%projectname%_vivado
SET tclfile=%projectname%_vivado.tcl

SET toolchainpath=%~5

if not {%~1} == {} if not {%~2} == {} if not {%~3} == {} (

  python %toolchainpath%\generatevivadotcl.py %jsonfile% %projectname% %projectpath% %hlsippath%
  mkdir %vivadodir%
  copy %tclfile% %vivadodir%
  %vivadopath%\vivado -mode batch -source %vivadodir%/%tclfile%

) else (

  echo "few arguments!"
)
