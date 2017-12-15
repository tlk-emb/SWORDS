#!/usr/bin/env python
# -*- coding: utf-8 -*-
# python dump_tree.py test.m

import sys
import argparse
import json

args = sys.argv

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("cfile_path")
    parser.add_argument("json_file_path")
    parser.add_argument("project_name")

    args = parser.parse_args()

    cfile_path = args.cfile_path
    json_file_path = args.json_file_path
    project_name = args.project_name

    tclfile_name = project_name + "_hls.tcl"

    tclfile = open(tclfile_name,"w")

    tclfile.write(generatehlstcl(cfile_path, project_name, extractFuncName(json_file_path), extractBoardName(json_file_path)))

def extractFuncName(json_file_path):

    f = open(json_file_path,'r')

    json_file = json.loads(f.read())

    #とりあえず1つ目のHW
    func_name = str(json_file["hardware_tasks"][0]["name"])

    return func_name

def extractBoardName(json_file_path):

    f = open(json_file_path,'r')

    json_file = json.loads(f.read())

    if "environments" in json_file:
        board_name = str(json_file["environments"][0]["board"])
    else:
        board_name = "zedboard"

    return board_name

def generatehlstcl(cfile_path, project_name, toplevel_function_name, board_name):

    tclfile_content = ""

    tclfile_content += "open_project %s_hls\n" % (project_name)
    tclfile_content += "set_top %s\n" % (toplevel_function_name)
    tclfile_content += "add_files %s\n" % (cfile_path)
    tclfile_content += "open_solution \"solution1\"\n" 
    if board_name == "zedboard":
        tclfile_content += "set_part {xc7z020clg484-1}\n"
    elif board_name == "zc702":
        tclfile_content += "set_part {xc7z020clg484-1}\n"
    elif board_name == "zc706":
        tclfile_content += "set_part {xc7z045ffg900-2}\n"
    elif board_name == "zybo":
        tclfile_content += "set_part {xc7z010clg400-1}\n"
    #else:
    #    tclfile_content += "set_part {xc7z020clg484-1}\n"
    tclfile_content += "create_clock -period 10 -name default\n"
    tclfile_content += "csynth_design\n"
    tclfile_content += "export_design -format ip_catalog\n"
    tclfile_content += "exit\n"

    return tclfile_content

if __name__ == "__main__":
    sys.exit(main())
