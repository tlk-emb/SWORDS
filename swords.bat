@echo off

SET toolchainpath=%~dp0
CALL %toolchainpath%setenv.bat

SET cfile=%~1
SET jsonfile=%~2
SET projectname=%~3

if not {%~1} == {} if not {%~2} == {} if not {%~3} == {} (
  if not {%llvmfilepath%} == {""} (
    %toolchainpath%\ifmake.bat %cfile% %jsonfile% %toolchainpath% %llvmfilepath%
  ) else (
    %toolchainpath%\ifmake.bat %cfile% %jsonfile% %toolchainpath%
  )

  %toolchainpath%\runhls.bat %cfile:~-0,-2%_hw_re.c %jsonfile% %projectname% %toolchainpath%
  %toolchainpath%runvivado.bat %jsonfile% %projectname% %projectname%_hls %cd% %toolchainpath%
  %toolchainpath%runsdk.bat %cfile% %jsonfile% %projectname% %toolchainpath%
 
) else (
    echo "few arguments!"
)
