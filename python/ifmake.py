#!/usr/bin/env python
# -*- coding: utf-8 -*-
# python dump_tree.py test.m

import sys
import re
import argparse
import logging
import os

from analyzer.jsonparam import TasksConfig

args = sys.argv

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("hw_file")
    parser.add_argument("conf_file")
    parser.add_argument(
        "--logging", default="WARNING",
        choices=["debug", "info", "warning", "error", "critical"])
    parser.add_argument("--debug", required=False, action="store_true")

    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.logging.upper()))

    hw_file_name = args.hw_file
    json_file_name = args.conf_file
    hw_iffile_name = hw_file_name[0:len(hw_file_name)-5] + "_if.c"

    logging.debug("input C source file: %s", hw_file_name)
    logging.debug("input config file: %s", json_file_name)
    logging.debug("output iflayer source file: %s", hw_iffile_name)

    config = TasksConfig.parse_config(json_file_name)
    if config is None:
        return 1

    generate_if = generateIF(hw_file_name, json_file_name, config)

    iflayer = generate_if.generateIF()

    iflayerfile = open(hw_iffile_name,"w")

    iflayerfile.write(iflayer)

    iflayerfile.close()

class generateIF:
    def __init__(self, hw_file_name, json_file_name, config):
        self.hw_file_name = hw_file_name
        self.func_name = config.hw_funcname(config)
        self.func_name_u = self.func_name.upper()
        self.func_name_l = self.func_name.lower()
        self.func_name_ul = (self.func_name[0]).upper() + (self.func_name[1:]).lower()

        task = config.hardware_tasks[self.func_name]
        self.json_args = task.arguments
        self.json_bundles = task.bundles

        #self.vendorname = config.vendorname(config)

        self.parm_decls = []
        for args in self.json_args:
            self.parm_decls.append(str(args.name))

        self.parm_interfaces = []
        for args in self.json_args:
            self.parm_interfaces.append(str(args.mode))

        self.parm_directions = []
        for args in self.json_args:
            self.parm_directions.append(str(args.direction))

        self.parm_data_numbers = []
        for args in self.json_args:
            self.parm_data_numbers.append(str(args.num))

        self.parm_bundles = []
        for bundle in self.json_bundles:
            self.parm_bundles.append(str(bundle.bundle))

        self.use_hp_ports = False
        for bundle in self.json_bundles:
            if "HP" in bundle.port:
                self.use_hp_ports = True

        self.parm_slave_bundles_noduplication = []
        for i in range(0,len(self.parm_decls)):
            if self.parm_interfaces[i] == "s_axilite":
                if self.parm_bundles[i] in self.parm_slave_bundles_noduplication:
                    pass
                else:
                    self.parm_slave_bundles_noduplication.append(self.parm_bundles[i])

        (self.define_line, self.hwfunc_decl) = self._analyze_hwfunc_decl()

        if self.hwfunc_decl.startswith("void"):
            self.return_type = "void"
        elif self.hwfunc_decl.startswith("int"):
            self.return_type = "int"
        else:
            self.return_type = "int"

        self.if_template_path = os.path.realpath(os.path.dirname(os.path.abspath(__file__))+"/../utils/if_template").replace("\\","/")

    def _analyze_hwfunc_decl(self):

        p_func_decl_int = "^int(\s+)%s(\s*)\(" % self.func_name
        p_func_decl_void = "void(\s+)%s(\s*)\(" % self.func_name


        with open(self.hw_file_name,"r") as f:
            hw_source = f.readlines()

        l = 0
        define_line = ""
        while (l<len(hw_source)):
            line = hw_source[l]

            if "#define" in line:
                define_line += line

            if (re.match(p_func_decl_int,line) or re.match(p_func_decl_void,line)):
                func_decl_lines = []
                while True:
                    line = hw_source[l]
                    line = re.sub('^\s*', '', line)
                    line = re.sub('$\s*', '', line)
                    func_decl_lines.append(line)
                    l += 1
                    if "{" in line:
                        break
                func_decl_line = ""
                for line in func_decl_lines:
                    func_decl_line += line
                return (define_line, func_decl_line)
            l += 1

        return (None,None)

    def _replace_func_decl(self, line):
        st_line = ""
        for l in line:
            st_line += l[:-1]

        if self.vendorname == "xilinx":
            (replaced_line,self.args) = self._x_replace_func_decl(st_line)
            replaced_line += "\n"
            replaced_line += self._x_add_hwif_decl()
            replaced_line += self._x_add_ver_in(self.args)
            return replaced_line

        return st_line

    def _x_replace_func_decl(self, line):
        [func_decl_pre, func_decl_arg] = line.split('(')
        replaced_line = func_decl_pre + "("

        args = re.split('[,)]', func_decl_arg)
        #args = func_decl_arg.split(',')
        for (arg,jarg) in zip(args,self.json_args):
            if jarg.mode == "m_axi":
                replaced_line += arg.replace(jarg.name, 'p'+jarg.name);
            else:
                replaced_line += arg
            replaced_line += ','

        return (replaced_line[:-1]+"){",args)


    def __generateHeaders(self):

        headers = ""

        headers += "#include <stdio.h>\n"
        headers += "#include <stdlib.h>\n"
        headers += "#include \"platform.h\"\n"
        if "m_axi" in self.parm_interfaces or "s_axilite" in self.parm_interfaces:
            headers += "#include \"x%s.h\"\n" % (self.func_name)
        headers += "#include \"xil_cache.h\"\n"
        headers += "#include \"xparameters.h\"\n"

        headers += "#include \"xil_io.h\"\n"
        headers += "#include \"xil_exception.h\"\n"
        headers += "#include \"xscugic.h\"\n"
        if "axis" in self.parm_interfaces:
            headers += "#include \"xaxidma.h\"\n"

        headers += '\n'+self.define_line

        return headers

    def __generateGlobalvals(self):
        global_vals = ""

        global_vals += "volatile int %s_done = 0;\n" % (self.func_name_l)
        #使用用途不明の為コメントアウト
        #global_vals += "unsigned int *baseaddr = XPAR_%s_0_S_AXI_AXILITES_BASEADDR;\n\n" % (self.func_name_u)

        global_vals += "static int used = 0;\n"

        if "axis" in self.parm_interfaces:
            stream_global_val_file = open(self.if_template_path + '/stream_global_val.c')
            global_vals += stream_global_val_file.read()
            stream_global_val_file.close()
        return global_vals

    def __generateConfigs(self):

        configs = ""
        if "axis" not in self.parm_interfaces:
            configs += "static X%s %sx = {\n" % (self.func_name_ul, self.func_name_l)
            configs += "    XPAR_%s_0_S_AXI_AXILITES_BASEADDR,\n" % (self.func_name_u)
            for bundle in self.parm_slave_bundles_noduplication:
                configs += "    XPAR_%s_0_S_AXI_%s_BASEADDR,\n" % (self.func_name_u, bundle.upper())
            configs += "    1\n" #この辺Liteの状況に合わせて増やす必要がある portが増えるとダメになるよ
            configs += "};\n\n"

            configs += "static X%s_Config %sc = {\n" % (self.func_name_ul, self.func_name_l)
            configs += "    1,\n"
            configs += "    XPAR_%s_0_S_AXI_AXILITES_BASEADDR" % (self.func_name_u)
            for bundle in self.parm_slave_bundles_noduplication:
                configs += ",\n    XPAR_%s_0_S_AXI_%s_BASEADDR" % (self.func_name_u, bundle.upper())
            configs += "\n"
            configs += "};\n\n"

        return configs

    def __generateIfxststatus(self): # generateSystemInterruptsで何回か使用

        if_xst_status = ""

        if_xst_status += "  if (Status != XST_SUCCESS){\n"
        if_xst_status += "      return XST_FAILURE;\n"
        if_xst_status += "  }\n\n"

        return if_xst_status

    def __generateSystemInterrupts(self):

        system_interrupts = ""
        if "axis" in self.parm_interfaces:
            #DMA用の割り込みハンドラ設定用関数を定義
            stream_interrupt_setup_file = open(self.if_template_path + '/stream_interrupt_setup.c')
            system_interrupts += stream_interrupt_setup_file.read()
            stream_interrupt_setup_file.close()
        else:
            #関数のreturn用の割り込み設定用関数を定義
            system_interrupts += "void %s_InterruptHandler(){\n" % (self.func_name_ul)
            system_interrupts += "  %s_done = 1;\n" % (self.func_name_l)
            system_interrupts += "  X%s_InterruptClear(&%sx, 1);\n" % (self.func_name_ul, self.func_name_l)
            system_interrupts += "}\n\n"

            system_interrupts += "XScuGic InterruptController;\n"
            system_interrupts += "static XScuGic_Config *GicConfig;\n\n"

            system_interrupts += "int SetUpInterruptSystem(XScuGic *XScuGicInstancePtr){\n"
            system_interrupts += "  Xil_ExceptionRegisterHandler(XIL_EXCEPTION_ID_INT,(Xil_ExceptionHandler) XScuGic_InterruptHandler, XScuGicInstancePtr);\n"
            system_interrupts += "  Xil_ExceptionEnable();\n"
            system_interrupts += "  return XST_SUCCESS;\n"
            system_interrupts += "}\n\n"

            system_interrupts += "int ScuGicInterrupt_Init(u16 DeviceId, X%s *%sInstancePtr){\n" % (self.func_name_ul, self.func_name_ul)
            system_interrupts += "  int Status;\n\n"
            system_interrupts += "  GicConfig = XScuGic_LookupConfig(DeviceId);\n"
            system_interrupts += "  if (NULL == GicConfig){\n"
            system_interrupts += "      return XST_FAILURE;\n"
            system_interrupts += "  }\n\n"

            system_interrupts += "  Status = XScuGic_CfgInitialize(&InterruptController, GicConfig, GicConfig->CpuBaseAddress);\n"
            system_interrupts += self.__generateIfxststatus()

            system_interrupts += "  Status = SetUpInterruptSystem(&InterruptController);\n"
            system_interrupts += self.__generateIfxststatus()

            system_interrupts += "  Status = XScuGic_Connect(&InterruptController, XPAR_FABRIC_%s_0_INTERRUPT_INTR, (Xil_ExceptionHandler)%s_InterruptHandler, (void *)%sInstancePtr);\n" % (self.func_name_u, self.func_name_ul, self.func_name_ul)
            system_interrupts += self.__generateIfxststatus()

            system_interrupts += "  XScuGic_Enable(&InterruptController, XPAR_FABRIC_%s_0_INTERRUPT_INTR);\n" % (self.func_name_u)
            system_interrupts += "  return XST_SUCCESS;\n"
            system_interrupts += "}\n\n"

        return system_interrupts

    def __generateInitDma(self):

        init_dma = ""

        init_dma += "XAxiDma AxiDma;\n\n"

        init_dma += "int init_dma(){\n"

        init_dma += "   XAxiDma_Config *CfgPtr;\n"
        init_dma += "   int Status;\n\n"

        init_dma += "   CfgPtr = XAxiDma_LookupConfig( (XPAR_AXI_DMA_DEVICE_ID) );\n" #2個以上必要な場合もあるぞ
        init_dma += "   if(!CfgPtr){\n"
        init_dma += "       printf(\"Error looking for AXI DMA config\\n\\r\");\n"
        init_dma += "       return XST_FAILURE;\n"
        init_dma += "   }\n\n"

        init_dma += "   Status = XAxiDma_CfgInitialize(&AxiDma, CfgPtr);\n"
        init_dma += "   if(Status != XST_SUCCESS){\n"
        init_dma += "       printf(\"Error initializing DMA\\n\\r\");\n"
        init_dma += "       return XST_FAILURE;\n"
        init_dma += "   }\n\n"

        init_dma += "   if(XAxiDma_HasSg(&AxiDma)){\n"
        init_dma += "       printf(\"Error DMA configured in SG mode\\n\\r\");\n"
        init_dma += "       return XST_FAILURE;\n"
        init_dma += "   }\n\n"

        init_dma += "   XAxiDma_IntrDisable(&AxiDma, XAXIDMA_IRQ_ALL_MASK, XAXIDMA_DEVICE_TO_DMA);\n"
        init_dma += "   XAxiDma_IntrDisable(&AxiDma, XAXIDMA_IRQ_ALL_MASK, XAXIDMA_DMA_TO_DEVICE);\n\n"

        init_dma += "   XAxiDma_Reset(&AxiDma);\n\n"

        init_dma += "   while (!XAxiDma_ResetIsDone(&AxiDma)) {}\n\n"

        init_dma += "   return XST_SUCCESS;\n"
        init_dma += "}\n\n"

        return init_dma

    def __generateIFLIntersection(self):

        IFL_intersection = ""

        if "axis" in self.parm_interfaces: #streamがある場合に
            IFL_intersection += "  int Status = init_dma();\n"
        else:
            IFL_intersection += "\n"
            IFL_intersection += "  if(used == 0){\n"
            IFL_intersection += "      if(X%s_CfgInitialize(&%sx, &%sc) != 0){\n" % (self.func_name_ul, self.func_name_l, self.func_name_l)
            IFL_intersection += "          return 1;\n"
            IFL_intersection += "      }\n"
            IFL_intersection += "      used = 1;\n"
            IFL_intersection += "  }\n\n"

        return IFL_intersection
    
    def __generateEarlyParms(self): #GP入力引数/HP・ACPのアドレス指定

        parms_set_str = ""

        if self.use_hp_ports: #HPポートを使う場合キャッシュ無効化
            parms_set_str += "  Xil_DCacheDisable();\n\n"

        for i in range(0,len(self.parm_decls)):
            if self.parm_interfaces[i] == "s_axilite":
                if self.parm_directions[i] == "in":
                    if self.parm_data_numbers[i] == 0: # スカラーの場合
                        parms_set_str += "  X%s_Set_%s(&%sx, %s);\n" % (self.func_name_ul, self.parm_decls[i], self.func_name_l, self.parm_decls[i])
                    else: # スカラーじゃない場合
                        parms_set_str += "  X%s_Write_%s_Words(&%sx, 0, %s, sizeof(%s) * %s / 4);\n" % (self.func_name_ul, self.parm_decls[i], self.func_name_l, self.parm_decls[i], self.parm_decls[i], self.parm_data_numbers[i])
            elif self.parm_interfaces[i] == "m_axi": # masterの場合
                parms_set_str += "  X%s_Set_p%s(&%sx, %s);\n" % (self.func_name_ul, self.parm_decls[i], self.func_name_l, self.parm_decls[i])
            elif self.parm_interfaces[i] == "axis": #
                pass
        
        if "axis" not in self.parm_interfaces:
            parms_set_str += "  X%s_Start(&%sx);\n\n" % (self.func_name_ul, self.func_name_l)

        for i in range(0,len(self.parm_decls)):
            if self.parm_interfaces[i] == "axis":
                parms_set_str += "  Xil_DCacheFlushRange((unsigned int)%s, sizeof(%s) * %s);\n\n" % (self.parm_decls[i], self.parm_decls[i], self.parm_data_numbers[i])

        for i in range(0,len(self.parm_decls)):
            if self.parm_interfaces[i] == "axis":
                if self.parm_directions[i] == "in":
                    parms_set_str += "  Status = XAxiDma_SimpleTransfer(&AxiDma, (unsigned int)%s, sizeof(%s) * %s, XAXIDMA_DMA_TO_DEVICE);\n" % (self.parm_decls[i], self.parm_decls[i], self.parm_data_numbers[i])
                    parms_set_str += "  if (Status != XST_SUCCESS){\n"
                    parms_set_str += "      print(\"Error: DMA transfer to Vivado HLS block failed\\n\");\n"
                    parms_set_str += "      return XST_FAILURE;\n"
                    parms_set_str += "  }\n\n"
                    # parms_set_str += "  while (XAxiDma_Busy(&AxiDma, XAXIDMA_DMA_TO_DEVICE));\n\n"

        for i in range(0,len(self.parm_decls)):
            if self.parm_interfaces[i] == "axis":
                if self.parm_directions[i] == "out":
                    parms_set_str += "  Status = XAxiDma_SimpleTransfer(&AxiDma, (unsigned int)%s, sizeof(%s) * %s, XAXIDMA_DEVICE_TO_DMA);\n" % (self.parm_decls[i], self.parm_decls[i], self.parm_data_numbers[i])
                    parms_set_str += "  if (Status != XST_SUCCESS){\n"
                    parms_set_str += "      print(\"Error: DMA transfer to Vivado HLS block failed\\n\");\n"
                    parms_set_str += "      return XST_FAILURE;\n"
                    parms_set_str += "  }\n\n"
                    # parms_set_str += "  while (XAxiDma_Busy(&AxiDma, XAXIDMA_DEVICE_TO_DMA));\n\n"        

        return parms_set_str

    def __generateLatterParms(self): #GP出力引数

        parms_get_str = ""

        for i in range(0,len(self.parm_decls)):
            if self.parm_interfaces[i] == "s_axilite":
                if self.parm_directions[i] == "out":
                    if self.parm_data_numbers[i] == 0: # スカラーの場合
                        parms_get_str += "  %s = X%s_Get_%s(&%sx);\n" % (self.parm_decls[i], self.func_name_ul, self.parm_decls[i], self.func_name_l)
                    else: # スカラーじゃない場合
                        parms_get_str += "  X%s_Read_%s_Words(&%sx, 0, %s, sizeof(%s) * %s / 4);\n" % (self.func_name_ul, self.parm_decls[i], self.func_name_l, self.parm_decls[i], self.parm_decls[i], self.parm_data_numbers[i])

        if self.use_hp_ports: #HPポートを使う場合キャッシュ無効化にしたのを戻す
            parms_get_str += "  Xil_DCacheEnable();\n\n"

        if self.return_type == "void":
            parms_get_str += "  return 0;\n\n"
        elif self.return_type == "int":
            parms_get_str += "  return X%s_Get_return(&%sx);\n\n" % (self.func_name_ul, self.func_name_l)
        else:
            parms_get_str += "  return X%s_Get_return(&%sx);\n\n" % (self.func_name_ul, self.func_name_l)

        return parms_get_str

    def __generateIFLInterrupt(self):

        IFL_interrupt = ""

        IFL_interrupt += re.sub(self.func_name, self.func_name+"_interrupt", self.hwfunc_decl)

        IFL_interrupt += self.__generateIFLIntersection()
        if "axis" in self.parm_interfaces:
            #DMA用の割り込みハンドラ設定用関数を呼び出し
            IFL_interrupt += " Status = SetupDMAInterruptSystem(&Intc, &AxiDma, TX_INTR_ID, RX_INTR_ID);\n"
            IFL_interrupt += " if (Status != XST_SUCCESS) {\n"

            IFL_interrupt += "     xil_printf(\"Failed intr setup\\r\\n\");\n"
            IFL_interrupt += "     return XST_FAILURE;\n"
            IFL_interrupt += " }\n\n"

            #DMA用の割り込み設定をON
            IFL_interrupt += " XAxiDma_IntrEnable(&AxiDma, XAXIDMA_IRQ_ALL_MASK,XAXIDMA_DMA_TO_DEVICE);\n"
            IFL_interrupt += " XAxiDma_IntrEnable(&AxiDma, XAXIDMA_IRQ_ALL_MASK,XAXIDMA_DEVICE_TO_DMA);\n"
        else:
            #関数のreturn用の割り込み設定用関数を呼び出し
            IFL_interrupt += "  if(ScuGicInterrupt_Init(XPAR_X%s_0_DEVICE_ID, &%sx) != 0){\n" % (self.func_name_u, self.func_name_l)
            IFL_interrupt += "      printf(\"Interrupt Initialization Error\\n\");\n"
            IFL_interrupt += "      return 1;\n"
            IFL_interrupt += "  }\n\n"

            IFL_interrupt += "  X%s_InterruptGlobalEnable(&%sx);\n" % (self.func_name_ul, self.func_name_l)
            IFL_interrupt += "  X%s_InterruptEnable(&%sx, 1);\n\n" % (self.func_name_ul, self.func_name_l)
        #キャッシュフラッシュ/スタート/DMA転送とか
        IFL_interrupt += self.__generateEarlyParms()

        if "axis" in self.parm_interfaces:
            IFL_interrupt += "  while (!TxDone && !RxDone && !Error) {}\n"
        else:
            IFL_interrupt += "  while(%s_done == 0);\n\n" % (self.func_name_l)

        IFL_interrupt += self.__generateLatterParms()

        IFL_interrupt += "}\n\n"

        return IFL_interrupt
    
    def __generateIFLPolingIdle(self):

        IFL_poling_Idle = ""

        if "axis" in self.parm_interfaces:
            IFL_poling_Idle += "  while (XAxiDma_Busy(&AxiDma, XAXIDMA_DMA_TO_DEVICE)||XAxiDma_Busy(&AxiDma, XAXIDMA_DEVICE_TO_DMA)){}\n"
        else:
            IFL_poling_Idle += "  while(1){\n"
            IFL_poling_Idle += "     if (X%s_IsIdle(&%sx) == 1){\n" % (self.func_name_ul, self.func_name_l)
            IFL_poling_Idle += "         break;\n"
            IFL_poling_Idle += "     }\n"
            IFL_poling_Idle += "  }\n"
            IFL_poling_Idle += " \n"

        return IFL_poling_Idle

    def __generateIFLPoling(self):

        IFL_poling = ""

        IFL_poling += self.hwfunc_decl

        IFL_poling += self.__generateIFLIntersection()

        if "axis" not in self.parm_interfaces:
            IFL_poling += self.__generateIFLPolingIdle() #DMA使用の場合はHWデータ転送前にDMAのアイドルを確認しない

        #キャッシュフラッシュ/スタート/DMA転送とか
        IFL_poling += self.__generateEarlyParms()

        IFL_poling += self.__generateIFLPolingIdle()

        IFL_poling += self.__generateLatterParms()

        IFL_poling += "}\n\n"

        return IFL_poling

    def generateIF(self):

        iflayer = ""

        iflayer += self.__generateHeaders()
        iflayer += "\n"
        iflayer += self.__generateGlobalvals()
        iflayer += "\n"
        iflayer += self.__generateConfigs()
        iflayer += "\n"
        iflayer += self.__generateSystemInterrupts()
        iflayer += "\n"

        if "axis" in self.parm_interfaces: #streamがある場合
            iflayer += self.__generateInitDma()
            iflayer += "\n"

        iflayer += self.__generateIFLInterrupt()
        iflayer += "\n"
        iflayer += self.__generateIFLPoling()

        return iflayer

if __name__ == "__main__":
    sys.exit(main())
