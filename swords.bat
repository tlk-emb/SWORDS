@echo off

if "%~3" == "" (
  echo few arguments!
  echo Usage:
  echo   ^$ swords.bat ^<design^>.c ^<conf^>.json ^<proj_name^> [^<exec_mode^>]
  exit /b 1
)

set toolchainpath=%~dp0
call %toolchainpath%\setenv.bat
  
if not "%~4" == "" (
  set opmode=%~4
) else (
  echo Info: [^<exec_mode^>] can select {all,divide,ifmake,hls,hwsyn,swbuild}
  set opmode=all
)
echo Operation mode is set to %opmode%


set cfile=..\%~1
set jsonfile=..\%~2
set projectname=%~3
  
mkdir %projectname%
cd %projectname%


set divide=False
if "%opmode%" == "all" set divide=True
if "%opmode%" == "divide" set divide=True

if "%divide%" == "True" (
  if not "%llvmfilepath%" == "" (
    call %toolchainpath%\batch\ifmake.bat %cfile% %jsonfile% %toolchainpath% %llvmfilepath%
  ) else (
    call %toolchainpath%\batch\ifmake.bat %cfile% %jsonfile% %toolchainpath%
  )
  move /Y %cfile:~0,-2%_*.c .
)


set hls=False
if "%opmode%" == "all" set hls=True
if "%opmode%" == "hls" set hls=True

if "%hls%" == "True" (
  set hwcfile=%cfile:~3,-2%_hw_re.c
  if not exist "%hwcfile%" (
    echo Error: hls process cannot be operated because %hwcfile% does not exist.
    cd ..\
    exit /b 1
  )
  call %toolchainpath%\batch\runhls.bat %hwcfile% %jsonfile% %projectname% %toolchainpath%
)


set hwsyn=False
if "%opmode%" == "all" set hwsyn=True
if "%opmode%" == "hwsyn" set hwsyn=True

if "%hwsyn%" == "True" (
  if not exist "%projectname%_hls\solution1\impl" (
    echo Error: hwsyn process cannot be operated because hls has not been done.
    cd ..\
    exit /b 1
  )
  call %toolchainpath%\batch\runvivado.bat %jsonfile% %projectname% %projectname%_hls %cd% %toolchainpath%
) 


set build=False
if "%opmode%" == "all" set build=True
if "%opmode%" == "swbuild" set build=True

set cfile=..\%~1
if "%build%" == "True" (
  if not exist "%projectname%_vivado\%projectname%.runs" (
    echo Error: swbuild process cannot be operated because hwsyn has not been done.
    cd ..\
    exit /b 1
  )
  call %toolchainpath%\batch\runsdk.bat %cfile% %jsonfile% %projectname% %toolchainpath%
) 

cd ..\
