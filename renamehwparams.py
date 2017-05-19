#!/usr/bin/env python
# -*- coding: utf-8 -*-
# python dump_tree.py test.m

import sys
import re
import commands
import argparse
import logging

from extractparameter import ExtractParameter

args = sys.argv

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

    hw_file_name = args.c_file
    json_file_name = args.conf_file
    rename_hw_file_name = hw_file_name[0:len(hw_file_name)-2] + "_re.c"

    logging.debug("input C source file: %s", hw_file_name)
    logging.debug("input config file: %s", json_file_name)
    logging.debug("output renamed C source file: %s", rename_hw_file_name)

    llvm_libdir = None
    llvm_libfile = None

    if args.llvm_libdir != None:
        llvm_libdir = args.llvm_libdir

    if args.llvm_libfile != None:
        llvm_libfile = args.llvm_libfile


    rmp = RenameandMemcpyPlus(hw_file_name,json_file_name,llvm_libdir,llvm_libfile)

    renamed_hw_file = rmp.renamandmemcpyplus()

    hw_source = open(rename_hw_file_name,"w")

    hw_source.write(renamed_hw_file)

    hw_source.close()

class RenameandMemcpyPlus:
    def __init__(self,hw_file_name,json_file_name,llvm_libdir,llvm_libfile):

        self.hw_file_name = hw_file_name

        #ExtractParameterで抽出
        self.EP = ExtractParameter(hw_file_name, json_file_name,llvm_libdir,llvm_libfile)

        #ソース分割されたものたち
        self.before_func_decl = ""
        self.func_decl_line = ""
        self.pragmas_lines = ""
        self.return_period_list = [""]

        #追加するリネーム変数宣言・memcpy関数
        self.reserve_buffer = ""
        self.input_memcpy = ""
        self.output_memcpy = ""

        #リネームされた関数
        self.renamed_func_decl = ""

    def __dividesource(self):

        #ソース分割で使用するパターンの定義
        func_pattern = "(.+)%s(.*)\(((.*) (.*))*\)" % self.EP.func_name
        other_func_pattern = "(.+)^(%s)(.*)\(((.*) (.*))*\)" % self.EP.func_name
        pragma_pattern = "#pragma HLS .*"
        return_pattern = "(.*)return (.*)"

        #ソースファイル
        hw_source = open(self.hw_file_name,"r")

        #ソース分割で使用するフラグ
        func_flag = False
        pragma_end_flag = False
        other_func_flag = False
        return_period_number = 0

        for line in hw_source:
            if (re.match(func_pattern,line)): #関数定義行抜き出し
                func_flag = True
                self.func_decl_line = line
            elif (func_flag == True and ((re.match(pragma_pattern,line)) == None) and pragma_end_flag == False): #プラグマ終了把握
                pragma_end_flag = True
            elif (pragma_end_flag == True): # returnで区切る，他の関数定義に入ったら区切りなし
                if (re.search(return_pattern,line) != None and other_func_flag == False):
                    return_period_number = return_period_number + 1
                    self.return_period_list.append("")
                self.return_period_list[return_period_number] +=line
                if (re.match(other_func_pattern,line) != None):
                    other_func_flag = True

            if (func_flag == False): #関数定義より前の行を抽出
                self.before_func_decl += line
            
            if (func_flag == True and re.match(pragma_pattern,line) != None and pragma_end_flag == False): #プラグマ行を抽出
                self.pragmas_lines += line

        hw_source.close()

    #リネーム用・入出力memcpyの宣言の作成
    def __makerenameparm(self):

        for i in range(0,len(self.EP.parm_decls)):
            if self.EP.parm_interfaces[i] == "m_axi":
                parms_str = ""
                if (len(self.EP.parm_suffixs[i]) != 0):
                    for j in range(0,len(self.EP.parm_suffixs[i])):
                        parms_str += "[%s]" % (self.EP.parm_suffixs[i][j])
                self.reserve_buffer += "    " + self.EP.parm_types[i] + " " + self.EP.parm_decls[i] + parms_str + ";\n"

        for i in range(0,len(self.EP.parm_decls)): # リネームからのコピー入力memcpy
            if self.EP.parm_interfaces[i] == "m_axi":
                if (self.EP.parm_directions[i] == "in" or self.EP.parm_directions[i] == "io"):
                    self.input_memcpy += "    memcpy(%s, p%s, sizeof(%s) * %d);\n" % (self.EP.parm_decls[i],self.EP.parm_decls[i],self.EP.parm_types[i],self.EP.parm_data_numbers[i])

        for i in range(0,len(self.EP.parm_decls)): # return文の前につける出力memcpy
            if self.EP.parm_interfaces[i] == "m_axi":
                if (self.EP.parm_directions[i] == "out" or self.EP.parm_directions[i] == "io"):
                    self.output_memcpy += "    memcpy(p%s, %s, sizeof(%s) * %d);\n" % (self.EP.parm_decls[i],self.EP.parm_decls[i],self.EP.parm_types[i],self.EP.parm_data_numbers[i]) #pをつける

    #関数定義行の置き換えした宣言を作成
    def __makerenamefuncdecl(self):

        parms_str = ""

        for i in range(0,len(self.EP.parm_decls)):
            if (i != 0):
                parms_str += ", "
            if self.EP.parm_interfaces[i] == "m_axi":
                parms_str += self.EP.parm_types[i] + " p" + self.EP.parm_decls[i] #m_axiのときは前にpをつけてリネーミング
            else:
                parms_str += self.EP.parm_types[i] + " " + self.EP.parm_decls[i]
            if (len(self.EP.parm_suffixs[i]) != 0):
                for j in range(0,len(self.EP.parm_suffixs[i])):
                    parms_str += "[%s]" % (self.EP.parm_suffixs[i][j])
    
        parms_str = "(%s)" % (parms_str)

        self.renamed_func_decl = re.sub("\((.+)\)",parms_str,self.func_decl_line)

    def renamandmemcpyplus(self):

        #それぞれ分割など実行
        self.__dividesource()
        self.__makerenameparm()
        self.__makerenamefuncdecl()

        renamed_hw_file = ""

        # hwファイルを再構築
        renamed_hw_file += self.before_func_decl
        renamed_hw_file += self.renamed_func_decl
        renamed_hw_file += re.sub("m_axi port=","m_axi port=p",self.pragmas_lines)
        renamed_hw_file += self.reserve_buffer
        renamed_hw_file += self.input_memcpy

        #return文ごとに出力memcpyを記述
        for i in range(0,len(self.return_period_list)):
            renamed_hw_file += self.return_period_list[i]
            if (i+1 != len(self.return_period_list)):
                renamed_hw_file += self.output_memcpy

        return renamed_hw_file

if __name__ == "__main__":
    sys.exit(main())
