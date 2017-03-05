@echo off

SET jsonfilepath=%~1
SET projectname=%~2
SET hlsippath=%~3
SET projectpathwin=%~4
echo %projectpathwin%
SET projectpath=%projectpathwin:\=/%

SET vivadodir=%projectname%_vivado
SET tclfilename=%projectname%_vivado.tcl

SET toolchainpath=%~dp0
SET toolchainpathlinuxbefore=%toolchainpath:\=/%
SET toolchaindrive=%toolchainpath:~0,1%
for %%i in (a b c d e f g h i j k l m n o p q r s t u v w x y z) do call set toolchaindrive=%%toolchaindrive:%%i=%%i%%
SET toolchainpathlinux=/mnt/%toolchaindrive%%toolchainpathlinuxbefore:~2%

if not {%~1} == {} if not {%~2} == {} if not {%~3} == {} (

    if {%~4} == {} (
        bash -c "python %toolchainpathlinux%generatevivadotcl.py %jsonfilepath% %projectname% %cd% %hlsippath%"
    ) else (
        bash -c "python %toolchainpathlinux%generatevivadotcl.py %jsonfilepath% %projectname% %projectpath% %hlsippath%"
    )
    mkdir %vivadodir%
    copy %tclfilename% %vivadodir%
    vivado -mode batch -source %vivadodir%/%tclfilename%

) else (

    echo "few arguments!"
)
