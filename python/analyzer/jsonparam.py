# -*- coding: utf-8 -*-

import json
import logging

from jsonschema import validate
from jsonschema.exceptions import ValidationError


SCHEMA = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "definitions": {
        "software_task": {
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            },
            "required": ["name"]
        },
        "hardware_task_argument": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "type": {"type": "string"},
                "offset": {"type": "string"},
                "bundle": {"type": "string"},
                "direction": {"type": "string"},
                "num": {"type": "integer"}
            },
            "required": ["name", "num"]
        },
        "hardware_task_bundle": {
            "type": "object",
            "properties": {
                "bundle": {"type": "string"},
                "port": {"type": "string"}
            },
        },
        "hardware_task": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "return_type": {"type": "string"},
                "mode": {"type": "string"},
                "arguments": {
                    "type": "array",
                    "items": {"$ref": "#/definitions/hardware_task_argument"}
                },
                "bundles": {
                    "type": "array",
                    "items": {"$ref": "#/definitions/hardware_task_bundle"}
                },
                "use_stream": {"type": "boolean"},
                "auto_interface_select" : {"type": "boolean"}
            },
            "required": ["name", "return_type", "arguments"]
        },
        "environments": {
            "type": "object",
            "properties": {
                "vendor": {"type": "string"},
                "board": {"type": "string"},
                "ostype": {"type": "string"}
            },
        },
    },
    "type": "object",
    "properties": {
        "software_tasks": {
            "type": "array",
            "items": {"$ref": "#/definitions/software_task"}
        },
        "hardware_tasks": {
            "type": "array",
            "items": {"$ref": "#/definitions/hardware_task"}
        },
        "environments": {
            "type": "object",
            "items": {"$ref": "#/definitions/environments"}
        }
    },
    "required": ["software_tasks", "hardware_tasks"]
}


class Task(object):
    def __init__(self, name):
        self.name = name

class SoftwareTask(Task):
    @staticmethod
    def parse_config(node):
        return SoftwareTask(node["name"])

class HardwareTask(Task):
    def __init__(self, mode, name, auto_interface_select, return_type, arguments, bundles, use_stream):
        super(HardwareTask, self).__init__(name)
        self.mode = mode
        self.return_type = return_type
        self.arguments = arguments
        self.bundles = bundles
        self.use_stream = use_stream
        self.auto_interface_select = auto_interface_select

    @staticmethod
    def parse_config(node):
        name = node["name"]
        return_type = node["return_type"]
        arguments = [HardwareTaskArgument.parse_config(n)
                     for n in node["arguments"]]
        #ストリームはデフォルトでオフ
        use_stream = False
        if node.get("use_stream") is not None: use_stream = node["use_stream"]
        #バンドル指定ならバンドルよみこみ
        bundles = []
        if node.get("bundles") is not None:
            bundles = [HardwareTaskBundle.parse_config(n)
                        for n in node["bundles"]]
        #mode指定ならmodeよみこみ
        mode = None
        if node.get("mode") is not None:
            mode = node["mode"]
        #自動インタフェース選択はデフォルトでオン
        auto_interface_select = True
        if node.get("auto_interface_select") is not None:
            auto_interface_select = node["auto_interface_select"]

        return HardwareTask(mode, name, auto_interface_select, return_type, arguments, bundles, use_stream)
class HardwareTaskArgument(object):
    def __init__(self, name, arg_type, bundle, mode, offset=None, direction=None, num=None):
        self.name = name
        self.mode = mode
        self.arg_type = arg_type
        self.offset = offset
        self.bundle = bundle
        self.direction = direction
        self.num = num

    @staticmethod
    def parse_config(node):
        name = node["name"]
        arg_type = node["type"]
        offset = node.get("offset")
        direction = node.get("direction")
        num = node["num"]
        bundle = ""
        if node.get("bundle") is not None: bundle = node["bundle"]
        mode = ""
        if node.get("mode") is not None: mode = node["mode"]
        return HardwareTaskArgument(name, arg_type, bundle, mode, offset, direction, num)


class HardwareTaskBundle(object):
    def __init__(self, bundle=None, port=None):
        self.bundle = bundle
        self.port = port

    @staticmethod
    def parse_config(node):
        bundle = node.get("bundle")
        port = node.get("port")
        return HardwareTaskBundle(bundle, port)


class TasksConfig(object):
    def __init__(self, hardware_tasks, software_tasks, environments):
        self.hardware_tasks = hardware_tasks
        self.software_tasks = software_tasks
        self.environments = environments

    def hw_funcname(self, config):
        # TODO: Currently we support only 1 HWtask
        functions = config.hardware_tasks.keys()
        if len(functions):
            return str(functions[0])
        else:
            return None

    def vendorname(self, config):
        vendor_name = "xilinx"
        if "vendor" in config.environments:
            return config.environments["vendor"]
        else:
            return vendor_name

    def boardname(self, config):
        board_name = "zedboard"
        if "board" in config.environments:
            return config.environments["board"]
        else:
            return board_name


    @staticmethod
    def get_config(filename):
        config = TasksConfig.parse_config(filename)
        config_connection_selected = TasksConfig.select_connection(config)
        return config_connection_selected
    
    @staticmethod
    def parse_config(filename):
        with open(filename) as f:
            root = json.load(f)
            try:
                validate(root, SCHEMA)
            except ValidationError as e:
                logging.error("config validation error: %s", e)
                return None

        hw_tasks = {}
        sw_tasks = {}
        environments = {}

        for node in root["hardware_tasks"]:
            task = HardwareTask.parse_config(node)
            hw_tasks[task.name] = task

        for node in root["software_tasks"]:
            task = SoftwareTask.parse_config(node)
            sw_tasks[task.name] = task

        environments.update(root["environments"])

        return TasksConfig(hw_tasks, sw_tasks, environments)

    #通信プロトコル・ポートの選択を行う
    @staticmethod
    def select_connection(config):
        intBytesize = 32/8
        #各HWタスクについて
        for hwtask_name in config.hardware_tasks.keys():
            hwtask = config.hardware_tasks[hwtask_name]
            ####################################################
            ##### インタフェースが手動指定の場合はスキップ #####
            ####################################################
            if hwtask.auto_interface_select == False: continue

            bundle_dic = {} #key: bundle_name value: [protocol, data_byte_size]

            #引数の通信プロトコルおよびバンドルを決定する
            if hwtask.use_stream:
                #ストリームを使用する場合
                hwtask.mode = None
                for i in range(len(hwtask.arguments)):
                    hwtask.arguments[i].mode = "axis"
                    #現時点では1入力1出力のみ対応のためinとoutでbundleを決める
                    if hwtask.arguments[i].direction == "in":
                        hwtask.arguments[i].bundle = "bundle_in"
                        bundle_dic["bundle_in"] = ["axis", hwtask.arguments[i].num * intBytesize]
                    else:
                        hwtask.arguments[i].bundle = "bundle_out"
                        bundle_dic["bundle_out"] = ["axis", hwtask.arguments[i].num * intBytesize]
            else:
                #ストリームを使用しない場合
                hwtask.mode = "s_axilite"
                protocol_dic = {} #key: m_axi, s_axilite, value: bundle_name
                for i,argument in enumerate(hwtask.arguments):
                    if argument.num * intBytesize < 400:
                        hwtask.arguments[i].mode = "s_axilite"
                    else:
                        hwtask.arguments[i].mode = "m_axi"
                        hwtask.arguments[i].offset = "slave"

                #定まった通信プロトコルについてbundleでまとめる
                #通信プロトコルの集合を求める
                for i,argument in enumerate(hwtask.arguments):
                    bundle_name = ""
                    if argument.mode not in protocol_dic:
                        bundle_name = "bundle_" + chr(ord('a') + len(bundle_dic))
                        bundle_dic[bundle_name] = [argument.mode, argument.num * intBytesize]
                        protocol_dic[argument.mode] = bundle_name
                    else:
                        bundle_name = protocol_dic[argument.mode]
                        bundle_dic[bundle_name][1] += argument.num * intBytesize
                    hwtask.arguments[i].bundle = bundle_name

            #[bundle_name, data_byte_size]のリスト
            GP_port_list = []
            ACP_port_list = []
            HP_port_list = []
            #各バンドルの通信データ量から使用する通信ポートを決定する
            for bundle_name in bundle_dic.keys():
                data_byte_size = bundle_dic[bundle_name][1]
                port_name = ""
                if data_byte_size < 64 or bundle_dic[bundle_name][0] == "s_axilite":
                    port_name = "GP"
                    GP_port_list.append([bundle_name, data_byte_size])
                elif data_byte_size < 64 * 1000:
                    port_name = "ACP"
                    ACP_port_list.append([bundle_name, data_byte_size])
                else:
                    port_name = "HP"
                    HP_port_list.append([bundle_name, data_byte_size])
                print(bundle_name, port_name)
            #決定した通信ポートをconfigに設定する
            for i, ACP_port in enumerate(ACP_port_list):
                hwtask.bundles.append(HardwareTaskBundle(ACP_port[0], "ACP"))
            for i, GP_port in enumerate(GP_port_list):
                hwtask.bundles.append(HardwareTaskBundle(GP_port[0], "GP" + str(i)))
            for i, HP_port in enumerate(HP_port_list):
                hwtask.bundles.append(HardwareTaskBundle(HP_port[0], "HP" + str(i)))

        return config

