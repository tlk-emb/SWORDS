#!/usr/bin/env python
# -*- coding: utf-8 -*-
# python dump_tree.py test.m

import sys
import argparse
import json
from jinja2 import Template,Environment,FileSystemLoader

args = sys.argv

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("cfile_path")
    parser.add_argument("json_file_path")
    parser.add_argument("project_name")
    parser.add_argument("toolchain_path")

    args = parser.parse_args()

    cfile_path = args.cfile_path
    json_file_path = args.json_file_path
    project_name = args.project_name
    toolchain_path = args.toolchain_path

    func_name = extractFuncName(json_file_path)
    vendor_name = extractVendorName(json_file_path)

    build_tclfile_name = project_name + "_build_sdk.tcl"
    build_tclfile = open(build_tclfile_name,"w")
    build_tclfile.write(generatetcl("build", project_name, func_name, vendor_name, toolchain_path))

    exe_tclfile_name = project_name + "_execute_sdk.tcl"
    exe_tclfile = open(exe_tclfile_name,"w")
    exe_tclfile.write(generatetcl("execute", project_name, func_name, vendor_name, toolchain_path))

    config_tclfile_name = project_name + "_config_sdk.tcl"
    config_tclfile = open(config_tclfile_name,"w")
    config_tclfile.write(generatetcl("config", project_name, func_name, vendor_name, toolchain_path))

def extractFuncName(json_file_path):
    f = open(json_file_path,'r')
    json_file = json.loads(f.read())
    func_name = str(json_file["hardware_tasks"][0]["name"])

    return func_name

def extractVendorName(json_file_path):
    f = open(json_file_path,'r')
    json_file = json.loads(f.read())
        
    vendor_name = "xilinx"
    if "environments" in json_file:
        if "vendor" in json_file["environments"]:
            vendor_name = str(json_file["environments"]["vendor"])

    return vendor_name

def generatetcl(mode, project_name, function_name, vendor_name, toolchain_path):
    env = Environment(loader=FileSystemLoader(toolchain_path+'template\\'+vendor_name+'\\'))
    template = env.get_template(mode+'_sdk.tcl')

    data = {'projname': project_name, 'funcname': function_name}
    return template.render(data)

if __name__ == "__main__":
    sys.exit(main())
