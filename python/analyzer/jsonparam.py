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
                "arguments": {
                    "type": "array",
                    "items": {"$ref": "#/definitions/hardware_task_argument"}
                },
                "use_stream": {"type": "boolean"}
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
    def __init__(self, name, return_type, arguments):
        super(HardwareTask, self).__init__(name)
        self.mode = None
        self.return_type = return_type
        self.arguments = arguments
        self.bundles = []

    @staticmethod
    def parse_config(node):
        name = node["name"]
        return_type = node["return_type"]
        arguments = [HardwareTaskArgument.parse_config(n)
                     for n in node["arguments"]]

        return HardwareTask(name, return_type, arguments)


class HardwareTaskArgument(object):
    def __init__(self, name, arg_type, offset=None, direction=None, num=None):
        self.name = name
        self.mode = ""
        self.arg_type = arg_type
        self.offset = offset
        self.bundle = ""
        self.direction = direction
        self.num = num

    @staticmethod
    def parse_config(node):
        name = node["name"]
        arg_type = node["type"]
        offset = node.get("offset")
        direction = node.get("direction")
        num = node["num"]
        return HardwareTaskArgument(name, arg_type, offset, direction, num)


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
            if config.hardware_tasks[hwtask_name].return_type is not "void":
                config.hardware_tasks[hwtask_name].mode = "s_axilite"
            # config.hardware_tasks[hwtask_name].arguments[0].mode = "m_axi"
            # config.hardware_tasks[hwtask_name].arguments[1].mode = "s_axilite"
            # config.hardware_tasks[hwtask_name].arguments[2].mode = "m_axi"
            # config.hardware_tasks[hwtask_name].arguments[0].bundle = "bundle_a"
            # config.hardware_tasks[hwtask_name].arguments[1].bundle = "bundle_b"
            # config.hardware_tasks[hwtask_name].arguments[2].bundle = "bundle_a"
            # config.hardware_tasks[hwtask_name].bundles = [HardwareTaskBundle("bundle_a", "ACP"), HardwareTaskBundle("bundle_b", "GP0")]

            #通信プロトコルを決定する
            for i,argument in enumerate(config.hardware_tasks[hwtask_name].arguments):
                if argument.num * intBytesize < 400:
                    config.hardware_tasks[hwtask_name].arguments[i].mode = "s_axilite"
                else:
                    config.hardware_tasks[hwtask_name].arguments[i].mode = "m_axi"
                    config.hardware_tasks[hwtask_name].arguments[i].offset = "slave"

            #定まった通信プロトコルについてbundleでまとめる
            #通信プロトコルの集合を求める
            protocol_dic = {} #key: m_axi, s_axilite, axis value: bundle_name
            bundle_dic = {} #key: bundle_name value: data_byte_size
            for i,argument in enumerate(config.hardware_tasks[hwtask_name].arguments):
                bundle_name = ""
                if argument.mode not in protocol_dic:
                    bundle_name = "bundle_" + chr(ord('a') + len(bundle_dic))
                    bundle_dic[bundle_name] = argument.num * intBytesize
                    protocol_dic[argument.mode] = bundle_name
                else:
                    bundle_name = protocol_dic[argument.mode]
                    bundle_dic[bundle_name] += argument.num * intBytesize
                config.hardware_tasks[hwtask_name].arguments[i].bundle = bundle_name
                print(i)
                print(bundle_name)

            #各バンドルの通信ポートをデータサイズが大きい順にソートする
            bundle_dic_sorted = sorted(bundle_dic.items(), key=lambda x: -x[1])
            #各ポートの使用可能最大数
            max_GP = 2
            max_ACP = 1
            max_HP = 4
            #[bundle_name, data_byte_size]のリスト
            GP_port_list = []
            ACP_port_list = []
            HP_port_list = []
            #各バンドルの通信データ量から使用する通信ポートを仮に決定する,各ポートの使用可能最大数は無視
            for bundle_name in bundle_dic.keys():
                data_byte_size = bundle_dic[bundle_name]
                print(data_byte_size)
                port_name = ""
                if data_byte_size < 64:
                    port_name = "GP"
                    GP_port_list.append([bundle_name, data_byte_size])
                elif data_byte_size < 64 * 1000:
                    port_name = "ACP"
                    ACP_port_list.append([bundle_name, data_byte_size])
                else:
                    port_name = "HP"
                    HP_port_list.append([bundle_name, data_byte_size])
            #各通信ポートについて使用可能最大数を超えているものについてデータサイズが一番小さなものを別の通信ポートに変更する
            while True:
                #ACPポート数超過
                if len(ACP_port_list) > max_ACP:
                    change_port = min(ACP_port_list, key=lambda x: x[1])
                    change_port_bundle_name = change_port[0]
                    change_port_data_byte_size = change_port[1]
                    if change_port_data_byte_size < 64 and len(GP_port_list) + 1 < max_GP:
                        new_port = "GP" + str(len(GP_port_list))
                        ACP_port_list.remove(change_port)
                        GP_port_list.append([change_port_bundle_name, change_port_data_byte_size])
                    elif len(HP_port_list) + 1 < max_HP:
                        new_port = "HP" + str(len(HP_port_list))
                        ACP_port_list.remove(change_port)
                        HP_port_list.append([change_port_bundle_name, change_port_data_byte_size])
                #GPポート超過
                if len(GP_port_list) > max_GP:
                    change_port = min(GP_port_list, key=lambda x: x[1])
                    change_port_bundle_name = change_port[0]
                    change_port_data_byte_size = change_port[1]
                    if change_port_data_byte_size < 64 * 10000 and len(ACP_port_list) + 1 < max_ACP:
                        new_port = "ACP"
                        GP_port_list.remove(change_port)
                        ACP_port_list.append([change_port_bundle_name, change_port_data_byte_size])
                    elif len(HP_port_list) + 1 < max_HP:
                        new_port = "HP" + str(len(HP_port_list))
                        GP_port_list.remove(change_port)
                        HP_port_list.append([change_port_bundle_name, change_port_data_byte_size])
                #HPポート超過
                if len(HP_port_list) > max_HP:
                    change_port = min(HP_port_list, key=lambda x: x[1])
                    change_port_bundle_name = change_port[0]
                    change_port_data_byte_size = change_port[1]
                    #HPポートが選ばれているということは大容量なのでACP優先
                    if len(ACP_port_list) + 1 < max_ACP:
                        new_port = "ACP"
                        HP_port_list.remove(change_port)
                        ACP_port_list.append([change_port_bundle_name, change_port_data_byte_size])
                    elif len(GP_port_list) + 1 < max_GP:
                        new_port = "GP" + str(len(GP_port_list))
                        HP_port_list.remove(change_port)
                        GP_port_list.append([change_port_bundle_name, change_port_data_byte_size])
                
                #すべての通信ポートが使用可能最大数以内におさまっていれば終了
                if (len(GP_port_list) <= max_GP and len(ACP_port_list) <= max_ACP and len(HP_port_list) <= max_HP): break
                
            #決定した通信ポートをconfigに設定する
            config.hardware_tasks[hwtask_name].bundles.append(HardwareTaskBundle(ACP_port_list[0][0], "ACP"))
            for i, GP_port in enumerate(GP_port_list):
                config.hardware_tasks[hwtask_name].bundles.append(HardwareTaskBundle(GP_port[0], "GP" + str(i)))
            for i, HP_port in enumerate(HP_port_list):
                config.hardware_tasks[hwtask_name].bundles.append(HardwareTaskBundle(HP_port[0], "HP" + str(i)))

        return config

