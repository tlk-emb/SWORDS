#!/usr/bin/env python
# -*- coding: utf-8 -*-
# python dump_tree.py test.m

import sys
import re
import commands
import argparse
import os
from jinja2 import Template,Environment,FileSystemLoader

from analyzer.jsonparam import TasksConfig

args = sys.argv

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("json_file_name")
    parser.add_argument("project_name")
    parser.add_argument("project_path")
    parser.add_argument("hls_ip_path")
    parser.add_argument("toolchain_path")

    args = parser.parse_args()

    json_file_name = args.json_file_name
    project_name = args.project_name
    project_path = args.project_path
    hls_ip_path = args.hls_ip_path
    toolchain_path = args.toolchain_path

    tclfile_name = "%s_vivado.tcl" % (project_name)

    gvt = generateVivadoTcl(json_file_name, project_name, project_path, hls_ip_path, toolchain_path)

    f = open(tclfile_name,'w')

    f.write(gvt.generateVivadoTcl())

    f.close()

class generateVivadoTcl:
    def __init__(self, json_file_name, project_name, project_path, hls_ip_path, toolchain_path):

        self.func_name = ""
        # HW関数の終了検知割り込みポートを使用するか
        self.use_hw_interrupt_port = False
        self.s_axilite_bundles = []
        self.m_axi_bundles = []
        self.axis_bundles = []
        # 不使用？？
        self.use_m_axi_ports = []
        # Include segment用
        self.use_m_axi_GP1 = False

        self.project_path = project_path.replace("\\","/")
        self.project_name = project_name
        self.json_file_name = json_file_name
        self.hls_ip_path = hls_ip_path.replace("\\","/")
        self.toolchain_path = toolchain_path
        self.lib_path = (toolchain_path+"utils/lib").replace("\\","/")

        config = TasksConfig.parse_config(json_file_name)
        if config is None:
            return 1

        self.func_name = config.hw_funcname(config)

        task = config.hardware_tasks[self.func_name]
        self.vendor_name = config.vendorname(config)
        self.board_name = config.boardname(config)

        self.use_hw_interrupt_port = task.mode is not None

        json_args = task.arguments
        json_bundles = task.bundles

        parm_modes = []
        for args in json_args:
            parm_modes.append(str(args.mode))

        parm_directions = []
        for args in json_args:
            parm_directions.append(str(args.direction))

        parm_arg_bundles = []
        for args in json_args:
            parm_arg_bundles.append(str(args.bundle))

        parm_bundles = []
        for bundle in json_bundles:
            parm_bundles.append(str(bundle.bundle))

        parm_ports = []
        for bundle in json_bundles:
            parm_ports.append(str(bundle.port))

        bundles_pair_dic = {}

        for (bundle,port) in zip(parm_bundles,parm_ports):
            bundles_pair_dic[bundle] = str(port)

        for i in range(len(parm_modes)):
            if (str(parm_modes[i])) == "s_axilite":
                if [str(parm_arg_bundles[i]) , str(bundles_pair_dic[parm_arg_bundles[i]])] not in self.s_axilite_bundles:
                    if parm_arg_bundles[i] in bundles_pair_dic :
                        self.s_axilite_bundles.append([str(parm_arg_bundles[i]), str(bundles_pair_dic[parm_arg_bundles[i]])])
                    else:
                        self.s_axilite_bundles.append([str(parm_arg_bundles[i]), "GP0"])

            elif (str(parm_modes[i])) == "m_axi":
                if [str(parm_arg_bundles[i]) , str(bundles_pair_dic[parm_arg_bundles[i]])] not in self.m_axi_bundles:
                    if parm_arg_bundles[i] in bundles_pair_dic :
                        self.m_axi_bundles.append([str(parm_arg_bundles[i]),  str(bundles_pair_dic[parm_arg_bundles[i]])])
                    else:
                        self.m_axi_bundles.append([str(parm_arg_bundles[i]), "ACP"])

            elif (str(parm_modes[i])) == "axis":
                if [str(parm_arg_bundles[i]), str(bundles_pair_dic[parm_arg_bundles[i]]), str(parm_directions[i])] not in self.axis_bundles:
                    self.axis_bundles.append([str(parm_arg_bundles[i]), str(bundles_pair_dic[parm_arg_bundles[i]]), str(parm_directions[i])])

        '''
        for bundles_pair in self.m_axi_bundles: #使用するm_axiのポートを重複なく数える
            port = bundles_pair[1]
            if port == "ACP" or port == "HP0" or port == "HP1" or port == "HP2" or port == "HP3":
                if port not in self.use_m_axi_p2orts:
                    self.use_m_axi_ports.append(port)
        '''

    '''
    def __analyzeJson(self):


        f = open(self.json_file_name,'r')

        json_file = json.loads(f.read())

        # とりあえず1つ目の関数だけ
        i = 0
        parameters_list = json_file["hardware_tasks"][i]["arguments"]

        bundles_dic_list = json_file["hardware_tasks"][i]["bundles"]

        bundles_pair_dic = {}

        for bundles_dic in bundles_dic_list:
            bundles_pair_dic[str(bundles_dic["bundle"])] = str(bundles_dic["port"])

        for parameter in parameters_list:
            if (str(parameter["mode"])) == "s_axilite":
                if [str(parameter["bundle"]) , str(bundles_pair_dic[parameter["bundle"]])] not in self.s_axilite_bundles:
                    if parameter["bundle"] in bundles_pair_dic :
                        self.s_axilite_bundles.append([str(parameter["bundle"]), str(bundles_pair_dic[parameter["bundle"]])])
                    else:
                        self.s_axilite_bundles.append([str(parameter["bundle"]), "GP0"])

            elif (str(parameter["mode"])) == "m_axi":
                if [str(parameter["bundle"]) , str(bundles_pair_dic[parameter["bundle"]])] not in self.m_axi_bundles:
                    if parameter["bundle"] in bundles_pair_dic :
                        self.m_axi_bundles.append([str(parameter["bundle"]),  str(bundles_pair_dic[parameter["bundle"]])])
                    else:
                        self.m_axi_bundles.append([str(parameter["bundle"]), "ACP"])

            elif (str(parameter["mode"])) == "axis":
                if [str(parameter["bundle"]), str(bundles_pair_dic[parameter["bundle"]]), str(parameter["direction"])] not in self.axis_bundles:
                    self.axis_bundles.append([str(parameter["bundle"]), str(bundles_pair_dic[parameter["bundle"]]), str(parameter["direction"])])

        for bundles_pair in self.m_axi_bundles: #使用するm_axiのポートを重複なく数える
            port = bundles_pair[1]
            if port == "ACP" or port == "HP0" or port == "HP1" or port == "HP2" or port == "HP3":
                if port not in self.use_m_axi_p2orts:
                    self.use_m_axi_ports.append(port)
    '''



    def generateVivadoTcl(self):
        # テンプレートにわたすパラメータの情報を作成

        #割り込みピンのリストを作成
        interrupt_pins = []
        if self.use_hw_interrupt_port:
            interrupt_pins.append(self.func_name + "_0/interrupt")
        if len(self.axis_bundles) > 0:
            interrupt_pins.append("axi_dma/mm2s_introut")
            interrupt_pins.append("axi_dma/s2mm_introut")

        #n_axi_GP1を使用するか
        for s_axilite_bundle in self.s_axilite_bundles:
            if s_axilite_bundle[1] == "GP1":    
                self.use_m_axi_GP1 = True

        #DMAを介してzynqとHWコアをつなぐ際にHWコアの他のピンの接続を同時に行うための文字列を作成する
        axis_conn_strs = ""
        if len(self.axis_bundles) > 0:
            axis_conn_strs = " ".join(map(lambda bundle:"Conn_"+bundle[0]+" \"1\"", self.axis_bundles[1:len(self.axis_bundles)]))

        #tlast_genの数=HWコアの出力ピンの数を数える
        tlast_gen_num = len(filter(lambda bundle:bundle[2] == "out", self.axis_bundles))

        env = Environment(loader=FileSystemLoader(self.toolchain_path+'template\\'+self.vendor_name+'\\'))
        template = env.get_template('vivado.tcl')
        self.use_m_axi_GP1 = True
        data = {
            'boardname' : self.board_name,
            'projname': self.project_name,
            'projpath' : self.project_path,#os.path.realpath(self.project_path).replace("\\","/"), 
            'hlsippath' : self.hls_ip_path, 
            'funcname': self.func_name,
            'libpath' : self.lib_path,
            'use_hw_interrupt_port'  : self.use_hw_interrupt_port,
            'use_m_axi_GP1' : self.use_m_axi_GP1,
            's_axilite_bundles' : self.s_axilite_bundles,
            'm_axi_bundles' : self.m_axi_bundles,
            'axis_bundles' : self.axis_bundles,
            'interrupt_pins' : interrupt_pins,
            'Conn_strs' : axis_conn_strs,
            'tlast_gen_num' : tlast_gen_num
            }
        
        return template.render(data)
        
if __name__ == "__main__":
    sys.exit(main())
