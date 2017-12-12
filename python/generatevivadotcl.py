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
        self.json_file_path = json_file_path
        self.hls_ip_path = hls_ip_path.replace("\\","/")

        self.__analyzeJson()

    def __analyzeJson(self):

        f = open(self.json_file_path,'r')

        json_file = json.loads(f.read())

        # とりあえず1つ目の関数だけ
        i = 0
        self.func_name = str(json_file["hardware_tasks"][i]["name"])
        self.use_hw_interrupt_port = json_file["hardware_tasks"][i].get("mode") is not None
 
        parameters_list = json_file["hardware_tasks"][i]["arguments"]

        bundles_dic_list = json_file["hardware_tasks"][i]["bundles"]

        bundles_pair_dic = {}

        for bundles_dic in bundles_dic_list:
            bundles_pair_dic[str(bundles_dic["bundle"])] = str(bundles_dic["port"])
        print(parameters_list)
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
                    self.axis_bundles.append([str(parameter["bundle"]), str(bundles_pair_dic[parameter["bundle"]]), str(parameter["direction"])])

        '''
        for bundles_pair in self.m_axi_bundles: #使用するm_axiのポートを重複なく数える
            port = bundles_pair[1]
            if port == "ACP" or port == "HP0" or port == "HP1" or port == "HP2" or port == "HP3":
                if port not in self.use_m_axi_ports:
                    self.use_m_axi_ports.append(port)
        '''

        # ボードの指定
        if "environments" in json_file:
            self.board_name = str(json_file["environments"][0]["board"])
        else:
            self.board_name = "zedboard"

    def generateVivadoTcl(self):

        vivado_tcl = ""

        # ボード指定によるプロジェクト属性の設定
        if self.board_name == "zedboard":
            vivado_tcl += "create_project -force %s %s/%s_vivado -part xc7z020clg484-1\n" % (self.project_name, self.project_path, self.project_name)
            vivado_tcl += "set_property board_part em.avnet.com:zed:part0:1.3 [current_project]\n"
        elif self.board_name == "zc702":
            vivado_tcl += "create_project -force %s %s/%s_vivado -part xc7z020clg484-1\n" % (self.project_name, self.project_path, self.project_name)
            vivado_tcl += "set_property board_part xilinx.com:zc702:part0:1.2 [current_project]\n"
        #else:
        #    vivado_tcl += "create_project -force %s %s/%s_vivado -part xc7z020clg484-1\n" % (self.project_name, self.project_path, self.project_name)
        #    vivado_tcl += "set_property board_part em.avnet.com:zed:part0:1.3 [current_project]\n"

        vivado_tcl += "set_property  ip_repo_paths  %s [current_project]\n" % (self.hls_ip_path)

        vivado_tcl += "create_bd_design \"%s_system\"\n" % (self.func_name)

        vivado_tcl += "open_bd_design {%s/%s_vivado/%s.srcs/sources_1/bd/%s_system/%s_system.bd}\n" % (self.project_path, self.project_name, self.project_name, self.func_name, self.func_name)

        vivado_tcl += "update_ip_catalog\n"

        vivado_tcl += "startgroup\n"
        vivado_tcl += "create_bd_cell -type ip -vlnv xilinx.com:ip:processing_system7:5.5 processing_system7_0\n"
        vivado_tcl += "endgroup\n"

        vivado_tcl += "startgroup\n"
        vivado_tcl += "create_bd_cell -type ip -vlnv xilinx.com:hls:%s:1.0 %s_0\n" % (self.func_name, self.func_name)
        vivado_tcl += "endgroup\n"

        vivado_tcl += "startgroup\n"
        vivado_tcl += "apply_bd_automation -rule xilinx.com:bd_rule:processing_system7 -config {make_external \"FIXED_IO, DDR\" apply_board_preset \"1\" Master \"Disable\" Slave \"Disable\" }  [get_bd_cells processing_system7_0]\n"
        vivado_tcl += "endgroup\n"

        # 使用する割り込みピン名リスト
        interrupt_pins = []

        # HW関数がvoidでない場合はHW処理の終了検知用の割込みピンを割り込みピン名リストに追加,returnの値用のポートを接続
        if self.use_hw_interrupt_port:
            interrupt_pins.append(self.func_name + "_0/interrupt")
            # return用のポートを接続する
            vivado_tcl += "startgroup\n"
            vivado_tcl += "apply_bd_automation -rule xilinx.com:bd_rule:axi4 -config {Master \"/processing_system7_0/M_AXI_GP0\" Clk \"Auto\" }  [get_bd_intf_pins %s_0/s_axi_AXILiteS]\n" % (self.func_name)
            vivado_tcl += "endgroup\n"

        # s_axiliteを使用するbundleについて
        if len(self.s_axilite_bundles) == 0:
            pass
        else: # s_axiliteがあるとき
            for s_axilite_bundle in self.s_axilite_bundles:
                vivado_tcl += "startgroup\n"
                if s_axilite_bundle[1] == "GP1":
                    vivado_tcl += "set_property -dict [list CONFIG.PCW_USE_M_AXI_%s {1}] [get_bd_cells processing_system7_0]\n" % (s_axilite_bundle[1])
                    self.use_m_axi_GP1 = True
                vivado_tcl += "apply_bd_automation -rule xilinx.com:bd_rule:axi4 -config {Master \"/processing_system7_0/M_AXI_%s\" Clk \"Auto\" }  [get_bd_intf_pins %s_0/s_axi_%s]\n" % (s_axilite_bundle[1], self.func_name, s_axilite_bundle[0])
                vivado_tcl += "endgroup\n"

        # m_axiを使用するbundleについて
        if len(self.m_axi_bundles) == 0:
            pass
        else: # m_axiがあるとき
            for m_axi_bundle in self.m_axi_bundles:
                vivado_tcl += "startgroup\n"
                # 使用するポートを有効にしてbundleと接続する
                vivado_tcl += "set_property -dict [list CONFIG.PCW_USE_S_AXI_%s {1}] [get_bd_cells processing_system7_0]\n" % (m_axi_bundle[1])
                vivado_tcl += "apply_bd_automation -rule xilinx.com:bd_rule:axi4 -config {Master \"/%s_0/m_axi_%s\" Clk \"Auto\" }  [get_bd_intf_pins processing_system7_0/S_AXI_%s]\n" % (self.func_name, m_axi_bundle[0], m_axi_bundle[1])
                # address editorからInclude segmentする
                vivado_tcl += "include_bd_addr_seg [get_bd_addr_segs -excluded %s_0/Data_m_axi_%s/SEG_processing_system7_0_%s_IOP]\n" % (self.func_name, m_axi_bundle[0], m_axi_bundle[1])
                vivado_tcl += "include_bd_addr_seg [get_bd_addr_segs -excluded %s_0/Data_m_axi_%s/SEG_processing_system7_0_%s_M_AXI_GP0]\n" % (self.func_name, m_axi_bundle[0], m_axi_bundle[1])
                # M_AXI_GP1を使用している時はそのbd_addr_segもInclude
                if self.use_m_axi_GP1:
                    vivado_tcl += "include_bd_addr_seg [get_bd_addr_segs -excluded %s_0/Data_m_axi_%s/SEG_processing_system7_0_%s_M_AXI_GP1]\n" % (self.func_name, m_axi_bundle[0], m_axi_bundle[1])
                vivado_tcl += "endgroup\n"

        # axisを使用するbundleについて
        if len(self.axis_bundles) == 0:
            pass
        else:
            for axis_bundle in self.axis_bundles:
                vivado_tcl += "startgroup\n"
                # 使用するポートを有効にしてbundleと接続する
                vivado_tcl += "set_property -dict [list CONFIG.PCW_USE_S_AXI_%s {1}] [get_bd_cells processing_system7_0]\n" % (axis_bundle[1])
                # 2つめ以降のStreamポートの情報をあつめる
                Conn_strs = ""
                if len(self.axis_bundles) > 0:
                    Conn_strs = " ".join(map(lambda bundle:"Conn_"+bundle[0]+" \"1\"", self.axis_bundles[1:len(self.axis_bundles)]))
                # print(Conn_strs)
                # print(self.axis_bundles)
                vivado_tcl += "endgroup\n"
            if (self.axis_bundles[0][2] == "in"):
                vivado_tcl += "apply_bd_automation -rule xilinx.com:bd_rule:axi4_s2mm -config {Dest_Intf \"/processing_system7_0/S_AXI_%s\" Bridge_IP \"New AXI DMA (High/Medium frequency transfer)\" %s Clk_Stream \"Auto\" Clk_MM \"Auto\" }  [get_bd_intf_pins %s_0/%s]\n" % (self.axis_bundles[0][1], Conn_strs, self.func_name, self.axis_bundles[0][0])
            if (self.axis_bundles[0][2] == "out"):
                vivado_tcl += "apply_bd_automation -rule xilinx.com:bd_rule:axi4_mm2s -config {Dest_Intf \"/processing_system7_0/S_AXI_%s\" Bridge_IP \"New AXI DMA (High/Medium frequency transfer)\" %s Clk_Stream \"Auto\" Clk_MM \"Auto\" }  [get_bd_intf_pins %s_0/%s]\n" % (self.axis_bundles[0][1], Conn_strs, self.func_name, self.axis_bundles[0][0])
            #新規作成されたDMAをコントロールするためのS_AXI_LITEをzynqとつなぐ
            dma_name = "axi_dma"
            vivado_tcl += "apply_bd_automation -rule xilinx.com:bd_rule:axi4 -config {Master \"/processing_system7_0/M_AXI_GP0\" Clk \"Auto\" }  [get_bd_intf_pins %s/S_AXI_LITE]\n" % dma_name
            #DMAの割り込みを割り込みピンのリストに追加
            interrupt_pins.append(dma_name + "/mm2s_introut")
            interrupt_pins.append(dma_name + "/s2mm_introut")
            #HWコアのap_startに定数1をセット
            vivado_tcl += "startgroup\n"
            vivado_tcl += "create_bd_cell -type ip -vlnv xilinx.com:ip:xlconstant:1.1 xlconstant_0\n"
            vivado_tcl += "endgroup\n"
            vivado_tcl += "connect_bd_net [get_bd_pins %s_0/ap_start] [get_bd_pins xlconstant_0/dout]\n" % self.func_name

        #割り込みピンをconcatを用いて連結してからzynqの割り込み検知コアに接続
        if len(self.axis_bundles) == 0:
            pass
        else:
            vivado_tcl += "startgroup\n"
            vivado_tcl += "set_property -dict [list CONFIG.PCW_USE_FABRIC_INTERRUPT {1} CONFIG.PCW_IRQ_F2P_INTR {1}] [get_bd_cells processing_system7_0]\n"
            vivado_tcl += "create_bd_cell -type ip -vlnv xilinx.com:ip:xlconcat:2.1 xlconcat_0\n"
            vivado_tcl += "set_property -dict [list CONFIG.NUM_PORTS {%s}] [get_bd_cells xlconcat_0]\n" % len(interrupt_pins)
            vivado_tcl += "endgroup\n"
            for i, interrupt_pin in enumerate(interrupt_pins):
                vivado_tcl += "connect_bd_net [get_bd_pins %s] [get_bd_pins xlconcat_0/In%s]\n" % (interrupt_pin, i)
            vivado_tcl += "connect_bd_net [get_bd_pins xlconcat_0/dout] [get_bd_pins processing_system7_0/IRQ_F2P]\n"

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
