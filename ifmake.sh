
#!/bin/sh

cfile=$1
jsonfile=$2
llvmpath=$3
hwfile=${cfile:0:-2}_hw.c
#hwfile=matrixmul_hw.c
toolchainpath=$4
defaultpath=/usr/lib/llvm-3.4/lib/libclang-3.4.so

if [ $# = 2 ]; then

    toolchainpath=$(dirname $0)
    python ${toolchainpath}/divide.py --llvm-libfile ${defaultpath} ${cfile} ${jsonfile}
    python ${toolchainpath}/ifmake.py --llvm-libfile ${defaultpath} ${cfile} ${jsonfile}
    python ${toolchainpath}/renamehwparms.py --llvm-libfile ${defaultpath} ${hwfile} ${jsonfile}
fi

if [ $# = 3 ]; then

    toolchainpath=$(dirname $0)
    python ${toolchainpath}/divide.py --llvm-libfile ${llvmpath} ${cfile} ${jsonfile}
    python ${toolchainpath}/ifmake.py --llvm-libfile ${llvmpath} ${cfile} ${jsonfile}
    python ${toolchainpath}/renamehwparms.py --llvm-libfile ${llvmpath} ${hwfile} ${jsonfile}
fi

if [ $# = 4 ]; then

    python ${toolchainpath}/divide.py --llvm-libfile ${llvmpath} ${cfile} ${jsonfile}
    python ${toolchainpath}/ifmake.py --llvm-libfile ${llvmpath} ${cfile} ${jsonfile}
    python ${toolchainpath}/renamehwparms.py --llvm-libfile ${llvmpath} ${hwfile} ${jsonfile}
fi

if [ $# = 0 ]; then
    echo "must need project name as parameter."
fi
