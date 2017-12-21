# -*- coding: utf-8 -*-

import json

class ExtractJsonParameter: #抽出/使用するパラメータの定義
    def __init__(self, json_file_name):

        #抽出するデータとデフォルト値の設定
        self.function_name = ""

        self.vendor_name = "xilinx"
        self.board_name = "zedboard"

        #JSONファイルのオープン
        f = open(json_file_name,'r')
        self.json_file = json.loads(f.read())


    def Func_Name(self):
        return str(self.json_file["hardware_tasks"][0]["name"])

    def Vendor_Name(self):
        if "environments" in self.json_file:
            if "vendor" in self.json_file["environments"]:
                self.vendor_name = str(self.json_file["environments"]["vendor"])
        return self.vendor_name

    def Board_Name(self):
        if "environments" in self.json_file:
            if "board" in self.json_file["environments"]:
                self.board_name = str(self.json_file["environments"]["board"])

        return self.board_name

