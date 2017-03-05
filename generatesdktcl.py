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

    build_tclfile_name = project_name + "_build_sdk.tcl"
    build_tclfile = open(build_tclfile_name,"w")
    build_tclfile.write(generatebuildtcl(cfile_path, project_name, extractFuncName(json_file_path)))

    exe_tclfile_name = project_name + "_execute_sdk.tcl"
    exe_tclfile = open(exe_tclfile_name,"w")
    exe_tclfile.write(generateexetcl(cfile_path, project_name, extractFuncName(json_file_path)))

    config_tclfile_name = project_name + "_config_sdk.tcl"
    config_tclfile = open(config_tclfile_name,"w")
    config_tclfile.write(generateconfigtcl(cfile_path, project_name, extractFuncName(json_file_path)))

def extractFuncName(json_file_path):

    f = open(json_file_path,'r')

    json_file = json.loads(f.read())

    func_name = str(json_file["hardware_tasks"][0]["name"])

    return func_name

def generatebuildtcl(cfile_apth, project_name, toplevel_function_name):

    system_wrapper = "%s_system_wrapper" % (toplevel_function_name)

    tclfile_content = ""

    tclfile_content += "sdk set_workspace %s_vivado/%s.sdk\n" % (project_name, project_name)
    tclfile_content += "sdk create_hw_project -name %s_hw_platform_0 -hwspec %s_vivado/%s.sdk/%s.hdf\n" % (system_wrapper, project_name, project_name, system_wrapper)
    tclfile_content += "sdk create_app_project -name %s -proc ps7_cortexa9_0 -os standalone -hwproject %s_hw_platform_0 -lang c\n" % (project_name, system_wrapper)
    tclfile_content += "sdk import_sources -name %s -path software -linker-script\n" % (project_name)
    tclfile_content += "sdk build_project -name %s\n" % (project_name)
    tclfile_content += "exit\n"

    return tclfile_content

def generateexetcl(cfile_apth, project_name, toplevel_function_name):

    system_wrapper = "%s_system_wrapper" % (toplevel_function_name)

    tclfile_content = ""

    tclfile_content += "sdk set_workspace %s_vivado/%s.sdk\n" % (project_name, project_name)
    tclfile_content += "connect\n"
    tclfile_content += "targets 2\n"
    tclfile_content += "rst -processor\n"
    tclfile_content += "source %s_vivado/%s.sdk/%s_hw_platform_0/ps7_init.tcl\n" % (project_name, project_name, system_wrapper)
    tclfile_content += "ps7_init\n"
    tclfile_content += "ps7_post_config\n"
    tclfile_content += "dow %s_vivado/%s.sdk/%s/Release/%s.elf\n" % (project_name, project_name, project_name, project_name)
    tclfile_content += "con\n"
    tclfile_content += "exit\n"

    return tclfile_content

def generateconfigtcl(cfile_apth, project_name, toplevel_function_name):

    system_wrapper = "%s_system_wrapper" % (toplevel_function_name)

    tclfile_content = ""

    tclfile_content += "sdk set_workspace %s_vivado/%s.sdk\n" % (project_name, project_name)
    tclfile_content += "connect\n"
    tclfile_content += "fpga %s_vivado/%s.sdk/%s_hw_platform_0/%s.bit\n" % (project_name, project_name, system_wrapper, system_wrapper)
    tclfile_content += "exit\n"

    return tclfile_content

if __name__ == "__main__":
    sys.exit(main())