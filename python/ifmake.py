#!/usr/bin/env python
# -*- coding: utf-8 -*-
# python dump_tree.py test.m

import sys
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
    hw_iffile_name = hw_file_name[0:len(hw_file_name)-2] + "_if.c"

    logging.debug("input C source file: %s", hw_file_name)
    logging.debug("input config file: %s", json_file_name)
    logging.debug("output iflayer source file: %s", hw_iffile_name)

    llvm_libdir = None
    llvm_libfile = None

    if args.llvm_libdir != None:
        llvm_libdir = args.llvm_libdir

    if args.llvm_libfile != None:
        llvm_libfile = args.llvm_libfile

    generate_if = generateIF(hw_file_name, json_file_name, llvm_libdir, llvm_libfile)

    iflayer = generate_if.generateIF()

    iflayerfile = open(hw_iffile_name,"w")

    iflayerfile.write(iflayer)

    iflayerfile.close()

class generateIF:
    def __init__(self, hw_file_name, json_file_name, llvm_libdir, llvm_libfile):
        self.EP = ExtractParameter(hw_file_name, json_file_name, llvm_libdir, llvm_libfile)

    def __generateHeaders(self):

        headers = ""

        headers += "#include <stdio.h>\n"
        headers += "#include <stdlib.h>\n"
        headers += "#include \"platform.h\"\n"
        headers += "#include \"x%s.h\"\n" % (self.EP.func_name)
        headers += "#include \"xil_cache.h\"\n"
        headers += "#include \"xparameters.h\"\n"

        headers += "#include \"xil_io.h\"\n"
        headers += "#include \"xil_exception.h\"\n"
        headers += "#include \"xscugic.h\"\n"
        if "axis" in self.EP.parm_interfaces:
            headers += "#include \"xaxidma.h\"\n"

        return headers

    def __generateGlobalvals(self):
        global_vals = ""

        global_vals += "volatile int %s_done = 0;\n" % (self.EP.func_name_l)
        global_vals += "unsigned int *baseaddr = XPAR_%s_0_S_AXI_AXILITES_BASEADDR;\n\n" % (self.EP.func_name_u)

        global_vals += "static int used = 0;\n"

        """
        streamの場合，DMAサイズを定義
        """

        return global_vals

    def __generateConfigs(self):

        configs = ""

        configs += "static X%s %sx = {\n" % (self.EP.func_name_ul, self.EP.func_name_l)
        configs += "    XPAR_%s_0_S_AXI_AXILITES_BASEADDR,\n" % (self.EP.func_name_u)
        for bundle in self.EP.parm_slave_bundles_noduplication:
            configs += "    XPAR_%s_0_S_AXI_%s_BASEADDR,\n" % (self.EP.func_name_u, bundle.upper())
        configs += "    1\n" #この辺Liteの状況に合わせて増やす必要がある portが増えるとダメになるよ
        configs += "};\n\n"

        configs += "static X%s_Config %sc = {\n" % (self.EP.func_name_ul, self.EP.func_name_l)
        configs += "    1,\n"
        configs += "    XPAR_%s_0_S_AXI_AXILITES_BASEADDR" % (self.EP.func_name_u)
        for bundle in self.EP.parm_slave_bundles_noduplication:
            configs += ",\n    XPAR_%s_0_S_AXI_%s_BASEADDR" % (self.EP.func_name_u, bundle.upper())
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

        system_interrupts += "void %s_InterruptHandler(){\n" % (self.EP.func_name_ul)
        system_interrupts += "  %s_done = 1;\n" % (self.EP.func_name_l)
        system_interrupts += "  X%s_InterruptClear(&%sx, 1);\n" % (self.EP.func_name_ul, self.EP.func_name_l)
        system_interrupts += "}\n\n"

        system_interrupts += "XScuGic InterruptController;\n"
        system_interrupts += "static XScuGic_Config *GicConfig;\n\n"

        system_interrupts += "int SetUpInterruptSystem(XScuGic *XScuGicInstancePtr){\n"
        system_interrupts += "  Xil_ExceptionRegisterHandler(XIL_EXCEPTION_ID_INT,(Xil_ExceptionHandler) XScuGic_InterruptHandler, XScuGicInstancePtr);\n"
        system_interrupts += "  Xil_ExceptionEnable();\n"
        system_interrupts += "  return XST_SUCCESS;\n"
        system_interrupts += "}\n\n"

        system_interrupts += "int ScuGicInterrupt_Init(u16 DeviceId, X%s *%sInstancePtr){\n" % (self.EP.func_name_ul, self.EP.func_name_ul)
        system_interrupts += "  int Status;\n\n"
        system_interrupts += "  GicConfig = XScuGic_LookupConfig(DeviceId);\n"
        system_interrupts += "  if (NULL == GicConfig){\n"
        system_interrupts += "      return XST_FAILURE;\n"
        system_interrupts += "  }\n\n"

        system_interrupts += "  Status = XScuGic_CfgInitialize(&InterruptController, GicConfig, GicConfig->CpuBaseAddress);\n"
        system_interrupts += self.__generateIfxststatus()

        system_interrupts += "  Status = SetUpInterruptSystem(&InterruptController);\n"
        system_interrupts += self.__generateIfxststatus()

        system_interrupts += "  Status = XScuGic_Connect(&InterruptController, XPAR_FABRIC_%s_0_INTERRUPT_INTR, (Xil_ExceptionHandler)%s_InterruptHandler, (void *)%sInstancePtr);\n" % (self.EP.func_name_u, self.EP.func_name_ul, self.EP.func_name_ul)
        system_interrupts += self.__generateIfxststatus()

        system_interrupts += "  XScuGic_Enable(&InterruptController, XPAR_FABRIC_%s_0_INTERRUPT_INTR);\n" % (self.EP.func_name_u)
        system_interrupts += "  return XST_SUCCESS;\n"
        system_interrupts += "}\n\n"       

        return system_interrupts

    def __generateInitDma(self):

        init_dma = ""

        init_dma += "XAxiDma AxiDma;\n\n"

        init_dma += "int init_dma(){\n"

        init_dma += "   XAxiDma_Config *CfgPtr;\n"
        init_dma += "   int Status;\n\n"

        init_dma += "   CfgPtr = XAxiDma_LookupConfig( (XPAR_AXI_DMA_0_DEVICE_ID) );\n" #2個以上必要な場合もあるぞ
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

        if "axis" in self.EP.parm_interfaces: #streamがある場合に
            IFL_intersection += "  int Status = init_dma();\n"

        IFL_intersection += "\n"
        IFL_intersection += "  if(used == 0){\n"
        IFL_intersection += "      if(X%s_CfgInitialize(&%sx, &%sc) != 0){\n" % (self.EP.func_name_ul, self.EP.func_name_l, self.EP.func_name_l)
        IFL_intersection += "          return 1;\n"
        IFL_intersection += "      }\n"
        IFL_intersection += "      used = 1;\n"
        IFL_intersection += "  }\n\n"

        return IFL_intersection
    
    def __generateEarlyParms(self): #GP入力引数/HP・ACPのアドレス指定

        parms_set_str = ""

        if self.EP.use_hp_ports: #HPポートを使う場合キャッシュ無効化
            parms_set_str += "  Xil_DCacheDisable();\n\n"

        for i in range(0,len(self.EP.parm_decls)):
            if self.EP.parm_interfaces[i] == "s_axilite":
                if self.EP.parm_directions[i] == "in":
                    if self.EP.parm_data_numbers[i] == 0: # スカラーの場合
                        parms_set_str += "  X%s_Set_%s(&%sx, %s);\n" % (self.EP.func_name_ul, self.EP.parm_decls[i], self.EP.func_name_l, self.EP.parm_decls[i])
                    else: # スカラーじゃない場合
                        parms_set_str += "  X%s_Write_%s_Words(&%sx, 0, %s, sizeof(%s) * %s / 4);\n" % (self.EP.func_name_ul, self.EP.parm_decls[i], self.EP.func_name_l, self.EP.parm_decls[i], self.EP.parm_decls[i], self.EP.parm_data_numbers[i])
            elif self.EP.parm_interfaces[i] == "m_axi": # masterの場合
                parms_set_str += "  X%s_Set_p%s(&%sx, %s);\n" % (self.EP.func_name_ul, self.EP.parm_decls[i], self.EP.func_name_l, self.EP.parm_decls[i])
            elif self.EP.parm_interfaces[i] == "axis": #
                pass

        parms_set_str += "  X%s_Start(&%sx);\n\n" % (self.EP.func_name_ul, self.EP.func_name_l)

        for i in range(0,len(self.EP.parm_decls)):
            if self.EP.parm_interfaces[i] == "axis":
                parms_set_str += "  Xil_DCacheFlushRange((unsigned int)%s, sizeof(%s) * %s / 8);\n\n" % (self.EP.parm_decls[i], self.EP.parm_decls[i], self.EP.parm_data_numbers[i])

        for i in range(0,len(self.EP.parm_decls)):
            if self.EP.parm_interfaces[i] == "axis":
                if self.EP.parm_directions[i] == "in":
                    parms_set_str += "  Status = XAxiDma_SimpleTransfer(&AxiDma, (unsigned int)%s, sizeof(%s) * %s / 8, XAXIDMA_DMA_TO_DEVICE);\n" % (self.EP.parm_decls[i], self.EP.parm_decls[i], self.EP.parm_data_numbers[i])
                    parms_set_str += "  if (Status != XST_SUCCESS){\n"
                    parms_set_str += "      print(\"Error: DMA transfer to Vivado HLS block failed\\n\");\n"
                    parms_set_str += "      return XST_FAILURE;\n"
                    parms_set_str += "  }\n\n"
                    parms_set_str += "  while (XAxiDma_Busy(&AxiDma, XAXIDMA_DMA_TO_DEVICE));\n\n"

        for i in range(0,len(self.EP.parm_decls)):
            if self.EP.parm_interfaces[i] == "axis":
                if self.EP.parm_directions[i] == "out":
                    parms_set_str += "  Status = XAxiDma_SimpleTransfer(&AxiDma, (unsigned int)%s, sizeof(%s) * %s / 8, XAXIDMA_DEVICE_TO_DMA);\n" % (self.EP.parm_decls[i], self.EP.parm_decls[i], self.EP.parm_data_numbers[i])
                    parms_set_str += "  if (Status != XST_SUCCESS){\n"
                    parms_set_str += "      print(\"Error: DMA transfer to Vivado HLS block failed\\n\");\n"
                    parms_set_str += "      return XST_FAILURE;\n"
                    parms_set_str += "  }\n\n"
                    parms_set_str += "  while (XAxiDma_Busy(&AxiDma, XAXIDMA_DEVICE_TO_DMA));\n\n"        

        return parms_set_str

    def __generateLatterParms(self): #GP出力引数

        parms_get_str = ""

        for i in range(0,len(self.EP.parm_decls)):
            if self.EP.parm_interfaces[i] == "s_axilite":
                if self.EP.parm_directions[i] == "out":
                    if self.EP.parm_data_numbers[i] == 0: # スカラーの場合
                        parms_get_str += "  %s = X%s_Get_%s(&%sx);\n" % (self.EP.parm_decls[i], self.EP.func_name_ul, self.EP.parm_decls[i], self.EP.func_name_l)
                    else: # スカラーじゃない場合
                        parms_get_str += "  X%s_Read_%s_Words(&%sx, 0, %s, sizeof(%s) * %s / 4);\n" % (self.EP.func_name_ul, self.EP.parm_decls[i], self.EP.func_name_l, self.EP.parm_decls[i], self.EP.parm_decls[i], self.EP.parm_data_numbers[i])

        if self.EP.use_hp_ports: #HPポートを使う場合キャッシュ無効化にしたのを戻す
            parms_get_str += "  Xil_DCacheEnable();\n\n"

        if self.EP.return_type == "void":
            parms_get_str += "  return 0;\n\n"
        else:
            parms_get_str += "  return X%s_Get_return(&%sx);\n\n" % (self.EP.func_name_ul, self.EP.func_name_l)

        return parms_get_str


    def __generateFuncParms(self):

        parms_str = ""

        for i in range(0,len(self.EP.parm_decls)):
            if (i != 0):
                parms_str += ", "
            parms_str += self.EP.parm_types[i] + " " + self.EP.parm_decls[i]
            if (len(self.EP.parm_suffixs[i]) != 0):
                for j in range(0,len(self.EP.parm_suffixs[i])):
                    parms_str += "[%s]" % (self.EP.parm_suffixs[i][j])

        return parms_str

    def __generateIFLInterrupt(self):

        IFL_interrupt = ""

        IFL_interrupt += "int %s_interrupt(%s){\n" % (self.EP.func_name, self.__generateFuncParms()) #引数をどうするの?

        IFL_interrupt += self.__generateIFLIntersection()

        IFL_interrupt += "  if(ScuGicInterrupt_Init(XPAR_X%s_0_DEVICE_ID, &%sx) != 0){\n" % (self.EP.func_name_u, self.EP.func_name_l)
        IFL_interrupt += "      printf(\"Interrupt Initialization Error\\n\");\n"
        IFL_interrupt += "      return 1;\n"
        IFL_interrupt += "  }\n\n"

        IFL_interrupt += "  X%s_InterruptGlobalEnable(&%sx);\n" % (self.EP.func_name_ul, self.EP.func_name_l)
        IFL_interrupt += "  X%s_InterruptEnable(&%sx, 1);\n\n" % (self.EP.func_name_ul, self.EP.func_name_l)

        #キャッシュフラッシュ/スタート/DMA転送とか
        IFL_interrupt += self.__generateEarlyParms()

        IFL_interrupt += "  while(%s_done == 0);\n\n" % (self.EP.func_name_l)

        IFL_interrupt += self.__generateLatterParms()

        IFL_interrupt += "}\n\n"

        return IFL_interrupt
    
    def __generateIFLPolingIdle(self):

        IFL_poling_Idle = ""

        IFL_poling_Idle += "  while(1){\n"
        IFL_poling_Idle += "     if (X%s_IsIdle(&%sx) == 1){\n" % (self.EP.func_name_ul, self.EP.func_name_l)
        IFL_poling_Idle += "         break;\n"
        IFL_poling_Idle += "     }\n"
        IFL_poling_Idle += "  }\n"
        IFL_poling_Idle += " \n"

        return IFL_poling_Idle

    def __generateIFLPoling(self):

        IFL_poling = ""

        IFL_poling += "int %s(%s){\n" % (self.EP.func_name, self.__generateFuncParms())
#        IFL_poling += "int %s_poling(%s){\n" % (self.EP.func_name, self.__generateFuncParms()) #_polingはつけないようにする

        IFL_poling += self.__generateIFLIntersection()

        IFL_poling += self.__generateIFLPolingIdle()

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

        if "axis" in self.EP.parm_interfaces: #streamがある場合
            iflayer += self.__generateInitDma()
            iflayer += "\n"

        iflayer += self.__generateIFLInterrupt()
        iflayer += "\n"
        iflayer += self.__generateIFLPoling()

        return iflayer

if __name__ == "__main__":
    sys.exit(main())
