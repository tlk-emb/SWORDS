#!/usr/bin/env python
# -*- coding: utf-8 -*-
# python dump_tree.py test.m

import clang.cindex
from clang.cindex import Config 
import json
import re
import subprocess

class ExtractParameter: #抽出/使用するパラメータの定義
    def __init__(self, hw_file_name, json_file_name, llvm_libdir, llvm_libfile):

        #llvmのファイルをセット
        if llvm_libfile != None:
            Config.set_library_file(llvm_libfile)
        if llvm_libdir != None:
            Config.set_library_path(llvm_libdir)

        #clangにソースコードをぶちこむ
        self.index = clang.cindex.Index.create()
        self.tree = self.index.parse(hw_file_name)

        self.hw_file_name = hw_file_name
        self.json_file_name = json_file_name

        #抽出するデータたち
        self.func_name = ""
        self.func_decl = ""
        self.return_type = ""
        self.parm_decls = []
        self.parm_types = []
        self.parm_suffixs = []
        self.parm_data_numbers = []
        self.parm_interfaces = []
        self.parm_bundles = []
        self.parm_directions = []
        self.parm_slave_bundles_noduplication = []
        self.bundle_port_dic = {}
        self.use_hp_ports = False

        self.func_find_flag = False
        self.func_find_flag_once = False

        #Json/C解析
        self.__analyzeJson()
        self.__extractParameter()

        #関数名の成形
        self.func_name_u = self.func_name.upper()
        self.func_name_l = self.func_name.lower()
        self.func_name_ul = (self.func_name[0]).upper() + self.func_name[1:]

    def __analyzeJson(self): #jsonファイルの解析

        f = open(self.json_file_name,'r')

        json_file = json.loads(f.read())

        #とろあえず1つ目のHWタスクだけ抽出，2つ以上に対応するときは変更が必要
        self.func_name = str(json_file["hardware_tasks"][0]["name"])

        parameters_list = json_file["hardware_tasks"][0]["arguments"]

        for parameter in parameters_list:
            self.parm_interfaces.append(str(parameter["mode"]))

        for parameter in parameters_list:
            self.parm_bundles.append(str(parameter["bundle"]))

        for parameter in parameters_list:
            self.parm_directions.append(str(parameter["direction"]))

        #bundleがGP/HP/ACPどれか？の情報
        bundle_setting_list = []

        if "bundles" in json_file["hardware_tasks"][0] :
            bundle_setting_list = json_file["hardware_tasks"][0]["bundles"]
            for bundle_port_pair in  bundle_setting_list:
                port = str(bundle_port_pair["port"])
                self.bundle_port_dic[str(bundle_port_pair["bundle"])] = port #型チェックが必要?(GP0/1，HP0~4,ACPのどれか)
                if port == "HP0" or port == "HP1" or port == "HP2" or port == "HP3":
                    self.use_hp_ports = True # HPポートを使うようならOnにしてキャッシュ無効化が必要なことをifmake.pyで反映

    def __visitNodeExtract(self, node, indent=0):

        if (node.kind.name == "FUNCTION_DECL"):
            if (node.displayname.startswith(self.func_name) and (self.func_find_flag_once == False)):
                self.func_decl = node.displayname
                self.func_find_flag = True
                self.func_find_flag_once = True
            else:
                self.func_find_flag = False
        
        elif (node.kind.name == "PARM_DECL" and self.func_find_flag):
            self.parm_decls.append(node.displayname)

        for c in node.get_children():
            self.__visitNodeExtract(c, indent=indent+1)
            
    def __extractParameter(self):

        ##clangによる解析

        self.__visitNodeExtract(self.tree.cursor)
        parameters = (self.func_decl.split(self.func_name,1)[1])[1:-1]
        parameters_list_clang = re.split("( *),( *)",parameters)
        #，で分割

        parameters_list_clang = filter(lambda n: len(n) > 0,filter(lambda n: not(re.match(" ",n)),parameters_list_clang))
        #空文字列と空白を消去

        parameters_list_clang = map(lambda n: n.rsplit(" ",1),parameters_list_clang)
#       self.parm_types = map(lambda n: n[0],parameters_list_clang)

        ##Cソースそのまま解析

        func_decl_pattern = "(.+)" + self.func_name + "(.*)\(((.*) (.*))*\)"

        #hw_source = commands.getoutput('\"C:\Program Files (x86)\LLVM\bin\clang -E ' + self.hw_file_name) #マクロ展開で定数などを数字に置換しておく
        hw_source = subprocess.check_output('clang -E ' + self.hw_file_name) #マクロ展開で定数などを数字に置換しておく

        for line in reversed(hw_source.splitlines()): #関数定義の行を抜き出す 現状の仕様は1行で関数定義が書いていないといけない プロトタイプ宣言も引数名が書いてないとだめ
            if (re.match(func_decl_pattern,line)):
                break

        self.return_type = line.split(" ",1)[0]

        parameters = ((((line.split(" ",1))[1].split(self.func_name,1))[1]).split(")",1)[0]).split("(",1)[1] #引数抽出
        parameters_list_c = re.split("( *),( *)",parameters)

        parameters_list_c = filter(lambda n: len(n) > 0,filter(lambda n: not(re.match(" ",n)),parameters_list_c))
        #空文字列と空白を消去

        parameters_list_c = map(lambda n: n.rsplit(" ",1),parameters_list_c)


        for i in range(0,len(self.parm_decls)): # 引数のデータ数を計算
            self.parm_types.append(parameters_list_c[i][0])
            suffix = re.sub(self.parm_decls[i] + " *","",parameters_list_c[i][1])
            if (suffix != ""):
                suffix_list =  filter(lambda n: len(n) > 0, re.split("[\[\]]",suffix))
                data_number = 1
                self.parm_suffixs.append(suffix_list)
                for i in suffix_list:
                    data_number = data_number * int(eval(i))
                self.parm_data_numbers.append(data_number)
            else:
                self.parm_data_numbers.append(1)
                self.parm_suffixs.append([])

        for i in range(0,len(self.parm_decls)):

            if self.parm_interfaces[i] == "s_axilite":
                if self.parm_bundles[i] in self.parm_slave_bundles_noduplication:
                    pass
                else:
                    self.parm_slave_bundles_noduplication.append(self.parm_bundles[i])

        """
        print self.func_name
        print self.parm_interfaces
        print self.return_type # 返り値の型
        print self.parm_decls # パラメータ名
        print self.parm_types # パラメータ型
        print self.parm_suffixs
        print self.parm_data_numbers # パラメータ要素数
        print self.parm_bundles
        print self.parm_directions
        print self.parm_slave_bundles_noduplication
        """
