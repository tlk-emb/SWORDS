@echo off
 
SET cfilepath=%~1
SET jsonfilepath=%~2
SET projectname=%~3
SET llvmpath=%~4
SET toolchainpath=%~dp0
SET toolchainpathlinuxbefore=%toolchainpath:\=/%
SET toolchaindrive=%toolchainpath:~0,1%
for %%i in (a b c d e f g h i j k l m n o p q r s t u v w x y z) do call set toolchaindrive=%%toolchaindrive:%%i=%%i%%
SET toolchainpathlinux=/mnt/%toolchaindrive%%toolchainpathlinuxbefore:~2%
 
if not {%~1} == {} if not {%~2} == {} if not {%~3} == {} (

    if not {%~4} == {} (
        bash %toolchainpathlinux%ifmake.sh %cfilepath% %jsonfilepath% %llvmpath% %toolchainpathlinux%
    ) else (
        bash %toolchainpathlinux%ifmake.sh %cfilepath% %jsonfilepath% /usr/lib/llvm-3.4/lib/libclang-3.4.so %toolchainpathlinux%
    )
 
    
    %toolchainpath%runhls.bat %cfilepath:~-0,-2%_hw_re.c %jsonfilepath% %projectname%
    %toolchainpath%runvivado.bat %jsonfilepath% %projectname% %projectname%_hls %cd%
    %toolchainpath%runsdk.bat %cfilepath% %jsonfilepath% %projectname%
 
) else (
    echo "few arguments!"
)