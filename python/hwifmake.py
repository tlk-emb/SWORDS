# -*- coding: utf-8 -*-

import sys
import re
import commands
import argparse
import logging

from jinja2 import Template,Environment,FileSystemLoader

from analyzer.jsonparam import TasksConfig

args = sys.argv

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("c_file")
    parser.add_argument("conf_file")
    parser.add_argument("toolchain_path")
    parser.add_argument(
        "--logging", default="WARNING",
        choices=["debug", "info", "warning", "error", "critical"])
    parser.add_argument("--debug", required=False, action="store_true")

    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.logging.upper()))

    hw_file_name = args.c_file
    json_file_name = args.conf_file
    toolchain_path = args.toolchain_path
    hwif_file_name = hw_file_name[0:len(hw_file_name)-2] + "if.c"

    logging.debug("input C source file: %s", hw_file_name)
    logging.debug("input config file: %s", json_file_name)
    logging.debug("output renamed C source file: %s", hwif_file_name)

    # JSONから設定を読み込み
    config = TasksConfig.get_config(json_file_name)
    if config is None:
        return 1

    hwif = Hwif_Generate(hw_file_name,config,toolchain_path)
    hwif_file = hwif.generate()

    hwif_source = open(hwif_file_name,"w")
    hwif_source.write(hwif_file)
    hwif_source.close()


class Hwif_Generate:
    def __init__(self, hw_file_name, config, toolchain_path):
        self.hw_file_name = hw_file_name
        self.toolchain_path = toolchain_path
        self.func_name = config.hw_funcname(config)
        self.func_return_mode = config.hardware_tasks[self.func_name].mode

        task = config.hardware_tasks[self.func_name]
        self.json_args = task.arguments

        self.vendorname = config.vendorname(config)

        self.args = ""

    def generate(self):
        generated_line = ""

        if self.vendorname == "xilinx":
            generated_line += "#include <string.h>\n"

        p_func_decl_int = "^int(\s+)%s(\s*)\(" % self.func_name
        p_func_decl_void = "void(\s+)%s(\s*)\(" % self.func_name

        with open(self.hw_file_name,"r") as f:
            hw_source = f.readlines()

        l = 0
        while (l<len(hw_source)):
            line = hw_source[l]

            if (re.match(p_func_decl_int,line) or re.match(p_func_decl_void,line)):
                func_decl_lines = []
                while True:#"{" not in line:
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
                generated_line += self._replace_func_decl(func_decl_line)
            elif "return" in line:
                generated_line += self._replace_return(line, self.args)
            else:
                generated_line += line
            l += 1
       
        return generated_line

    def _replace_func_decl(self, line):

        if self.vendorname == "xilinx":
            (replaced_line,self.args) = self._x_replace_func_decl(line)
            replaced_line += "\n"
            replaced_line += self._x_add_hwif_decl()
            replaced_line += self._x_add_ver_in(self.args)
            return replaced_line

        return line

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

    def _x_add_hwif_decl(self):
        env = Environment(loader=FileSystemLoader(self.toolchain_path+'template\\'+self.vendorname+'\\'))
        env.globals.update(zip=zip)
        template = env.get_template('hwif.c')

        name = []
        mode = []
        offset = []
        bundle = []
        for jarg in self.json_args:
            if jarg.mode == "m_axi":
                name.append('p'+jarg.name)
            else:
                name.append(jarg.name)
            mode.append(jarg.mode)
            offset.append(jarg.offset)
            bundle.append(jarg.bundle)
        
        data = {'return_mode': self.func_return_mode, 'name': name, 'mode': mode, 'offset': offset, 'bundle': bundle}
        return template.render(data)+'\n'

    def _x_add_ver_in(self, args):
        line = ""
        for (arg,jarg) in zip(args,self.json_args):
            if jarg.mode == "m_axi":
                line += re.sub('^\s*', '\t', arg)+";\n"

        for (arg,jarg) in zip(args,self.json_args):
            if jarg.mode == "m_axi" and jarg.direction == "in":
                arg = re.sub('^\s*', '', arg)
                arg_type = re.split('\s*', arg)[0]
                line += "\tmemcpy(%s, p%s, sizeof(%s) * %s);\n" % (jarg.name,jarg.name,arg_type,jarg.num)

        return line

    def _replace_return(self, line, args):
        if self.vendorname == "xilinx":
            replaced_line = self._x_add_ver_out(args)
            return replaced_line+line

        return line

    def _x_add_ver_out(self, args):
        line = ""

        for (arg,jarg) in zip(args,self.json_args):
            if jarg.mode == "m_axi" and jarg.direction == "out":
                arg = re.sub('^\s*', '', arg)
                arg_type = re.split('\s*', arg)[0]
                line += "\tmemcpy(p%s, %s, sizeof(%s) * %s);\n" % (jarg.name,jarg.name,arg_type,jarg.num)

        return line


if __name__ == "__main__":
    sys.exit(main())
