@echo off

SET toolchainpath=%~dp0
CALL %toolchainpath%\setenv.bat
  
SET cfile=%~1
SET jsonfile=%~2
SET projectname=%~3

if not {%~1} == {} if not {%~2} == {} if not {%~3} == {} (
  if not {%llvmfilepath%} == {""} (
    %toolchainpath%\batch\ifmake.bat %cfile% %jsonfile% %toolchainpath% %llvmfilepath%
  ) else (
    %toolchainpath%\batch\ifmake.bat %cfile% %jsonfile% %toolchainpath%
  )

  %toolchainpath%\batch\runhls.bat %cfile:~-0,-2%_hw_re.c %jsonfile% %projectname% %toolchainpath%
  %toolchainpath%\batch\runvivado.bat %jsonfile% %projectname% %projectname%_hls %cd% %toolchainpath%
  %toolchainpath%\batch\runsdk.bat %cfile% %jsonfile% %projectname% %toolchainpath%
 
) else (
    echo "few arguments!"
)
