# -*- coding: utf-8 -*-
from __future__ import print_function
import argparse
import logging
from clang.cindex import Config 
from operator import itemgetter
import sys

from analyzer.designparam import DesignAnalysis
from analyzer.jsonparam import TasksConfig

def write_source_files(output, hardware_file, software_file):

    hardware_output = map(itemgetter(2),
                          filter(lambda t: t[0] is True, output))
    software_output = map(itemgetter(2),
                          filter(lambda t: t[1] is True, output))
    
    software_output.insert(0, "#include \"xtime_l.h\"")

    with open(hardware_file, "w") as f:
        f.write("\n".join(hardware_output))
    with open(software_file, "w") as f:
        f.write("\n".join(software_output))

def print_output(output):
    for is_hardware, is_software, line in output:
        if is_hardware and not is_software:
            tag = "H "
        elif is_software and not is_hardware:
            tag = " S"
        else:
            tag = "HS"
        logging.info("%s %s", tag, line.rstrip())

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("c_file")
    parser.add_argument("conf_file")
    parser.add_argument("--llvm-libdir", default=None, required=False)
    parser.add_argument("--llvm-libfile", default=None, required=False)
    parser.add_argument(
        "--logging", default="WARNING",
        choices=["debug", "info", "warning", "error", "critical"])
    parser.add_argument("--debug", required=False, action="store_true")

    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.logging.upper()))

    c_file = args.c_file
    conf_file = args.conf_file
    hardware_file = args.c_file[:-2] + "_hw.c"
    software_file = args.c_file[:-2] + "_sw.c"

    logging.debug("input C source file: %s", c_file)
    logging.debug("input JSON config file: %s", conf_file)
    logging.debug("output C hardware source file: %s", hardware_file)
    logging.debug("output C software source file: %s", software_file)

    # JSONから設定を読み込み
    config = TasksConfig.parse_config(conf_file)
    if config is None:
        return 1
    # clang で関数の情報を収集
    analyzer = DesignAnalysis(c_file, llvm_libdir=args.llvm_libdir,
                        llvm_libfile=args.llvm_libfile)
    # 設定を元に解析
    analyzer.analyze(config)
    # 解析結果を出力
    output = analyzer.generate_output()
    # ソースコードを分解
    print_output(output)
    write_source_files(output, hardware_file, software_file)

if __name__ == "__main__":
    sys.exit(main())
