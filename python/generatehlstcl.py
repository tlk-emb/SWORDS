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
    config = TasksConfig.parse_config(json_file_name)
    if config is None:
        return 1
    function_name = config.hw_funcname(config)
    vendor_name = config.vendorname(config)
    board_name = config.boardname(config)


    tclfile_name = project_name + "_hls.tcl"

    tclfile = open(tclfile_name,"w")

    tclfile.write(generatehlstcl(cfile_name, project_name, function_name, vendor_name, board_name, toolchain_path))


def generatehlstcl(cfile_name, project_name, function_name, vendor_name, board_name, toolchain_path):
    env = Environment(loader=FileSystemLoader(toolchain_path+'template\\'+vendor_name+'\\'))
    template = env.get_template('hls.tcl')

    data = {'cfilename': cfile_name, 'projname': project_name, 'funcname': function_name, 'boardname': board_name}
    return template.render(data)


if __name__ == "__main__":
    sys.exit(main())
