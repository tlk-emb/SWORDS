@echo off

if "%~3" == "" (
  echo few arguments!
  echo Usage:
  echo   ^$ swords.bat ^<design^>.c ^<conf^>.json ^<proj_name^> [^<operation_mode^>]
  exit /b 1
)

set toolchainpath=%~dp0
call %toolchainpath%\setenv.bat
  
if not "%~4" == "" (
  set opmode=%~4
) else (
  echo Info: [^<operation_mode^>] can select {all,divide,ifmake,hls,hwsyn,swbuild}
  set opmode=all
)

if not "%opmode%" == "all" (
  if not "%opmode%" == "divide" (
    if not "%opmode%" == "ifmake" (
      if not "%opmode%" == "hls" (
        if not "%opmode%" == "hwsyn" (
          if not "%opmode%" == "swbuild" (
            echo Error: [^<operation_mode^>] cannot be selected as %opmode%.
            exit /b 1
          )
        )
      )
    )
  )
)

echo Operation mode is set to %opmode%.


set cfile=%~1
set jsonfile=%~2
set projectname=%~3
  
if not exist "%cfile%" (
  echo Error: %cfile% does not exist
  exit /b 1
)

if not exist "%jsonfile%" (
  echo Error: %jsonfile% does not exist
  exit /b 1
)

if not exist "%projectname%" (
  mkdir %projectname%
)
cd %projectname%


set divide=False
if "%opmode%" == "all" set divide=True
if "%opmode%" == "divide" set divide=True

if "%divide%" == "True" (
  copy /Y ..\%cfile% .
  copy /Y ..\%jsonfile% .
  if not "%llvmfilepath%" == "" (
    call %toolchainpath%\batch\divide.bat %cfile% %jsonfile% %llvmfilepath%
  ) else (
    call %toolchainpath%\batch\divide.bat %cfile% %jsonfile%
  )
)

set ifmake=False
if "%opmode%" == "all" set ifmake=True
if "%opmode%" == "ifmake" set ifmake=True

if "%ifmake%" == "True" (
  if not exist "%cfile:~0,-2%_sw.c" (
    echo Error: ifmake process cannot be operated because divide has not been done.
    cd ..\
    exit /b 1
  )
  call %toolchainpath%\batch\ifmake.bat %cfile% %jsonfile% %toolchainpath%
)


set hls=False
if "%opmode%" == "all" set hls=True
if "%opmode%" == "hls" set hls=True

set cfile=%~1
if "%hls%" == "True" (
  set hwcfile=%cfile:~0,-2%_hwif.c
  if not exist "%hwcfile%" (
    echo Error: hls process cannot be operated because ifmake has not been done.
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

set cfile=%~1
if "%build%" == "True" (
  if not exist "%projectname%_vivado\%projectname%.sdk" (
    echo Error: swbuild process cannot be operated because hwsyn has not been done.
    cd ..\
    exit /b 1
  )
  call %toolchainpath%\batch\runsdk.bat %cfile% %jsonfile% %projectname% %toolchainpath%
) 

cd ..\
