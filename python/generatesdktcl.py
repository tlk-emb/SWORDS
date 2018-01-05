# -*- coding: utf-8 -*-

import sys
import argparse
from jinja2 import Template,Environment,FileSystemLoader

from analyzer.jsonparam import TasksConfig

args = sys.argv

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("cfile_name")
    parser.add_argument("json_file_name")
    parser.add_argument("project_name")
    parser.add_argument("toolchain_path")

    args = parser.parse_args()

    cfile_name = args.cfile_name
    json_file_name = args.json_file_name
    project_name = args.project_name
    toolchain_path = args.toolchain_path

    # JSONÇ©ÇÁê›íËÇì«Ç›çûÇ›
    config = TasksConfig.get_config(json_file_name)
    if config is None:
        return 1
    function_name = config.hw_funcname(config)
    vendor_name = config.vendorname(config)


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
