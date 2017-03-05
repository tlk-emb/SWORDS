#!/usr/bin/env python
# -*- coding: utf-8 -*-
# python dump_tree.py test.m

import sys
import re
import commands
import argparse
import json
import os

args = sys.argv

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("json_file_path")
    parser.add_argument("project_name")
    parser.add_argument("project_path")
    parser.add_argument("hls_ip_path")

    args = parser.parse_args()

    json_file_path = args.json_file_path
    project_name = args.project_name
    project_path = args.project_path
    hls_ip_path = args.hls_ip_path

    tclfile_name = "%s_vivado.tcl" % (project_name)

    gvt = generateVivadoTcl(json_file_path, project_name, project_path, hls_ip_path)

    f = open(tclfile_name,'w')

    f.write(gvt.generateVivadoTcl())

    f.close()

class generateVivadoTcl:
    def __init__(self, json_file_path, project_name, project_path, hls_ip_path):

        self.func_name = ""
        self.s_axilite_bundles = []
        self.m_axi_bundles = []
        self.axis_bundles = []
        self.use_m_axi_ports = []

        self.project_path = project_path.replace("\\","/")
        self.project_name = project_name
        self.json_file_path = json_file_path
        self.hls_ip_path = hls_ip_path.replace("\\","/")

        self.__analyzeJson()

    def __analyzeJson(self):

        f = open(self.json_file_path,'r')

        json_file = json.loads(f.read())

        # とりあえず1つ目の関数だけ
        i = 0
        self.func_name = str(json_file["hardware_tasks"][i]["name"])

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
                if str(parameter["bundle"]) not in self.axis_bundles:
                    self.axis_bundles.append(str(parameter["bundle"]))
        
        for bundles_pair in self.m_axi_bundles: #使用するm_axiのポートを重複なく数える
            port = bundles_pair[1]
            if port == "ACP" or port == "HP0" or port == "HP1" or port == "HP2" or port == "HP3":
                if port not in self.use_m_axi_ports:
                    self.use_m_axi_ports.append(port)
        
    def generateVivadoTcl(self):

        vivado_tcl = ""

        vivado_tcl += "create_project -force %s %s/%s_vivado -part xc7z020clg484-1\n" % (self.project_name, self.project_path, self.project_name)

        vivado_tcl += "set_property board_part em.avnet.com:zed:part0:1.3 [current_project]\n"

        vivado_tcl += "set_property  ip_repo_paths  %s [current_project]\n" % (self.hls_ip_path)

        vivado_tcl += "create_bd_design \"%s_system\"\n" % (self.func_name)

        vivado_tcl += "open_bd_design {%s/%s_vivado/%s.srcs/sources_1/bd/%s_system/%s_system.bd}\n" % (self.project_path, self.project_name, self.project_name, self.func_name, self.func_name)

        vivado_tcl += "startgroup\n"
        vivado_tcl += "create_bd_cell -type ip -vlnv xilinx.com:ip:processing_system7:5.5 processing_system7_0\n"
        vivado_tcl += "endgroup\n"

        vivado_tcl += "startgroup\n"
        vivado_tcl += "create_bd_cell -type ip -vlnv xilinx.com:hls:%s:1.0 %s_0\n" % (self.func_name, self.func_name)
        vivado_tcl += "endgroup\n"

        vivado_tcl += "startgroup\n"
        vivado_tcl += "apply_bd_automation -rule xilinx.com:bd_rule:processing_system7 -config {make_external \"FIXED_IO, DDR\" apply_board_preset \"1\" Master \"Disable\" Slave \"Disable\" }  [get_bd_cells processing_system7_0]\n"
        vivado_tcl += "endgroup\n"

        vivado_tcl += "startgroup\n"
        vivado_tcl += "apply_bd_automation -rule xilinx.com:bd_rule:axi4 -config {Master \"/processing_system7_0/M_AXI_GP0\" Clk \"Auto\" }  [get_bd_intf_pins %s_0/s_axi_AXILiteS]\n" % (self.func_name)
        for s_axilite_bundle in self.s_axilite_bundles:
            vivado_tcl += "apply_bd_automation -rule xilinx.com:bd_rule:axi4 -config {Master \"/processing_system7_0/M_AXI_%s\" Clk \"Auto\" }  [get_bd_intf_pins %s_0/s_axi_%s]\n" % (s_axilite_bundle[1], self.func_name, s_axilite_bundle[0])
        vivado_tcl += "endgroup\n"

        vivado_tcl += "startgroup\n"

        vivado_tcl += "set_property -dict [list CONFIG.PCW_USE_FABRIC_INTERRUPT {1} CONFIG.PCW_IRQ_F2P_INTR {1}] [get_bd_cells processing_system7_0]\n"
        if len(self.m_axi_bundles) == 0:
            pass
        else: #m_axiがあるとき
            for m_axi_port in self.use_m_axi_ports: 
                vivado_tcl += "set_property -dict [list CONFIG.PCW_USE_S_AXI_%s {1}] [get_bd_cells processing_system7_0]\n" % (m_axi_port)
        vivado_tcl += "endgroup\n"

        for m_axi_bundle in self.m_axi_bundles:
            vivado_tcl += "apply_bd_automation -rule xilinx.com:bd_rule:axi4 -config {Master \"/%s_0/m_axi_%s\" Clk \"Auto\" }  [get_bd_intf_pins processing_system7_0/S_AXI_%s]\n" % (self.func_name, m_axi_bundle[0], m_axi_bundle[1])

        vivado_tcl += "connect_bd_net [get_bd_pins %s_0/interrupt] [get_bd_pins processing_system7_0/IRQ_F2P]\n" % (self.func_name)

        for m_axi_bundle in self.m_axi_bundles: #ACPを使うならアドレスエディタをいじる必要がある
            print m_axi_bundle
            if m_axi_bundle[1] == "ACP":
                vivado_tcl += "include_bd_addr_seg [get_bd_addr_segs -excluded %s_0/Data_m_axi_%s/SEG_processing_system7_0_ACP_IOP]\n" % (self.func_name, m_axi_bundle[0])
                vivado_tcl += "include_bd_addr_seg [get_bd_addr_segs -excluded %s_0/Data_m_axi_%s/SEG_processing_system7_0_ACP_M_AXI_GP0]\n" % (self.func_name, m_axi_bundle[0])

        vivado_tcl += "make_wrapper -files [get_files %s/%s_vivado/%s.srcs/sources_1/bd/%s_system/%s_system.bd] -top\n" % (self.project_path, self.project_name, self.project_name, self.func_name, self.func_name)

        vivado_tcl += "add_files -norecurse %s/%s_vivado/%s.srcs/sources_1/bd/%s_system/hdl/%s_system_wrapper.v\n" % (self.project_path, self.project_name, self.project_name, self.func_name, self.func_name)

        vivado_tcl += "update_compile_order -fileset sources_1\n"

        vivado_tcl += "update_compile_order -fileset sim_1\n"

        vivado_tcl += "launch_runs impl_1 -to_step write_bitstream\n"

        vivado_tcl += "wait_on_run impl_1\n"

        vivado_tcl += "open_bd_design {%s/%s_vivado/%s.srcs/sources_1/bd/%s_system/%s_system.bd}\n" % (self.project_path, self.project_name, self.project_name, self.func_name, self.func_name)

        vivado_tcl += "file mkdir %s/%s_vivado/%s.sdk\n" % (self.project_path, self.project_name, self.project_name)

        vivado_tcl += "file copy -force %s/%s_vivado/%s.runs/impl_1/%s_system_wrapper.sysdef %s/%s_vivado/%s.sdk/%s_system_wrapper.hdf\n" % (self.project_path, self.project_name, self.project_name, self.func_name, self.project_path, self.project_name, self.project_name, self.func_name)

        vivado_tcl += "open_run impl_1\n"

        vivado_tcl += "report_utilization -hierarchical -file %s/utilreport.txt\n" % (self.project_path)

        vivado_tcl += "exit\n"

        return vivado_tcl

if __name__ == "__main__":
    sys.exit(main())
