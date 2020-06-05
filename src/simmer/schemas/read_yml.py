import os

import cerberus
import custom_validator
import yaml


def read_yml(yml_filename):
    file = open(yml_filename)
    parsed_yaml_file = yaml.load(file, Loader=yaml.SafeLoader)
    file.close()
    return parsed_yaml_file


def validate_yml(schema_filename, yml_filename):
    parsed_schema = read_yml(schema_filename)
    parsed_yml = read_yml(yml_filename)
    s = custom_validator.SimmerValidator()
    try:
        s.validate(parsed_yml, parsed_schema)
        return True
    except cerberus.SchemaError:
        return False


def get_plotting_args(yml_filename):
    schema_filename = os.getcwd() + "/plotting.yml"

    if validate_yml(schema_filename, yml_filename):
        yml_file = read_yml(yml_filename)
    else:
        raise cerberus.SchemaError("parsing plotting yml failed")
