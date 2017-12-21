# -*- coding: utf-8 -*-

import sys
import argparse
from jinja2 import Template,Environment,FileSystemLoader

from extractjsonparam import ExtractJsonParameter

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

    EJP = ExtractJsonParameter(json_file_path)
    function_name = EJP.Func_Name()
    vendor_name = EJP.Vendor_Name()

    build_tclfile_name = project_name + "_build_sdk.tcl"
    build_tclfile = open(build_tclfile_name,"w")
    build_tclfile.write(generatetcl("build", project_name, function_name, vendor_name, toolchain_path))

    exe_tclfile_name = project_name + "_execute_sdk.tcl"
    exe_tclfile = open(exe_tclfile_name,"w")
    exe_tclfile.write(generatetcl("execute", project_name, function_name, vendor_name, toolchain_path))

    config_tclfile_name = project_name + "_config_sdk.tcl"
    config_tclfile = open(config_tclfile_name,"w")
    config_tclfile.write(generatetcl("config", project_name, function_name, vendor_name, toolchain_path))


def generatetcl(mode, project_name, function_name, vendor_name, toolchain_path):
    env = Environment(loader=FileSystemLoader(toolchain_path+'template\\'+vendor_name+'\\'))
    template = env.get_template(mode+'_sdk.tcl')

    data = {'projname': project_name, 'funcname': function_name}
    return template.render(data)

if __name__ == "__main__":
    sys.exit(main())
