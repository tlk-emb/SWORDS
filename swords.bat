@echo off

SET toolchainpath=%~dp0
CALL %toolchainpath%\setenv.bat
  
SET cfile=..\%~1
SET jsonfile=..\%~2
SET projectname=%~3

if not {%~1} == {} if not {%~2} == {} if not {%~3} == {} (
  mkdir %projectname%
  cd %projectname%

  if not {%llvmfilepath%} == {""} (
    %toolchainpath%\batch\ifmake.bat %cfile% %jsonfile% %toolchainpath% %llvmfilepath%
  ) else (
    %toolchainpath%\batch\ifmake.bat %cfile% %jsonfile% %toolchainpath%
  )

  move ..\%projectname%_* .

  %toolchainpath%\batch\runhls.bat %cfile:~3,-2%_hw_re.c %jsonfile% %projectname% %toolchainpath%
  %toolchainpath%\batch\runvivado.bat %jsonfile% %projectname% %projectname%_hls %cd%\%projectname% %toolchainpath%
  %toolchainpath%\batch\runsdk.bat %cfile% %jsonfile% %projectname% %toolchainpath%
  
  cd ..\
 
) else (
    echo "few arguments!"
)

