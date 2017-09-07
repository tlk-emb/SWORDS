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
                "mode": {
                    "type": "string",
                    "enum": ["axis", "m_axi", "s_axilite"]
                },
                "offset": {"type": "string"},
                "bundle": {"type": "string"}
            },
            "required": ["name", "mode"]
        },
        "hardware_task": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "mode": {
                    "type": "string",
                    "enum": ["s_axilite"]
                },
                "arguments": {
                    "type": "array",
                    "items": {"$ref": "#/definitions/hardware_task_argument"}
                }
            },
            "required": ["name", "mode", "arguments"]
        },
        "environments": {
            "type": "object",
            "properties": {
                "board": {"type": "string"}
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
            "type": "array",
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
    def __init__(self, name, mode, arguments):
        super(HardwareTask, self).__init__(name)
        self.mode = mode
        self.arguments = arguments

    @staticmethod
    def parse_config(node):
        name = node["name"]
        mode = node["mode"]
        arguments = [HardwareTaskArgument.parse_config(n)
                     for n in node["arguments"]]

        return HardwareTask(name, mode, arguments)

    def get_directive_pragmas(self):
        template = "#pragma HLS INTERFACE {mode} port=return"
        pragma = template.format(mode=self.mode)
        pragmas = [a.get_directive_pragma() for a in self.arguments]
        return [pragma] + pragmas


class HardwareTaskArgument(object):
    def __init__(self, name, mode, offset=None, bundle=None):
        self.name = name
        self.mode = mode
        self.offset = offset
        self.bundle = bundle

    @staticmethod
    def parse_config(node):
        name = node["name"]
        mode = node["mode"]
        offset = node.get("offset")
        bundle = node.get("bundle")
        return HardwareTaskArgument(name, mode, offset, bundle)

    def get_directive_pragma(self):
        template = "#pragma HLS INTERFACE {mode} port={name}"
        if self.offset is not None:
            template += " offset={offset}"
        if self.bundle is not None:
            template += " bundle={bundle}"

        return template.format(name=self.name, mode=self.mode,
                               offset=self.offset, bundle=self.bundle)


class TasksConfig(object):
    def __init__(self, hardware_tasks, software_tasks):
        self.hardware_tasks = hardware_tasks
        self.software_tasks = software_tasks

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

        for node in root["hardware_tasks"]:
            task = HardwareTask.parse_config(node)
            hw_tasks[task.name] = task

        for node in root["software_tasks"]:
            task = SoftwareTask.parse_config(node)
            sw_tasks[task.name] = task

        return TasksConfig(hw_tasks, sw_tasks)
