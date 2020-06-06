import os

import cerberus
import yaml

from .custom_validator import SimmerValidator

# TODO: refactor pretty much all of this


def read_yml(yml_filename):
    """
    Reads in a yaml file.

    Inputs:
        :yml_filename: (string) path to the yml.

    Outputs:
        :parsed_yml_file: (dictionary) key-value pairs as read from the yaml
            file.

    """
    file = open(yml_filename)
    parsed_yaml_file = yaml.load(file, Loader=yaml.SafeLoader)
    file.close()
    return parsed_yaml_file


def validate_yml(schema_filename, yml_filename):
    """
    Ensures that a given yml file is in accordance with the provided schema. In
    essence, this ensures that no odd keys or fields are provided to the yml.

    Inputs:
        :schema_filename: (string) path to schema yaml.
        :yml_filename: (string) path to yml yaml.

    Outputs:
        :validated: (bool) whether or not the yaml was successfully validated.

    """
    parsed_schema = read_yml(schema_filename)
    parsed_yml = read_yml(yml_filename)
    s = SimmerValidator()
    try:
        s.validate(parsed_yml, parsed_schema)
        validated = True
    except cerberus.SchemaError:
        validated = False
    return validated


def get_plotting_args(yml_filename=None):
    """
    Gets plotting args.

    Inputs:
        :yml_filename: (string) path of the plotting yml to be used.
                        Defaults to None.

    Outputs:
        :plotting_arg: (dictionary) all arguments that are related to plotting.
            See the `plotting.yml` schema for documentation of keys and values.

    """
    schema_filename = os.getcwd() + "/plotting.yml"
    if not yml_filename:
        yml_dict = {}  # the normalizer fills in all empty fields later on
    else:
        if validate_yml(schema_filename, yml_filename):
            yml_dict = read_yml(yml_filename)
        else:
            raise cerberus.SchemaError("parsing plotting yml failed")
    s = SimmerValidator()
    s.schema = read_yml(schema_filename)
    plotting_args = s.normalized(yml_dict)
    return plotting_args
