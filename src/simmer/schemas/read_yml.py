import os

import cerberus
import yaml

from .custom_validator import SimmerValidator


def normalize(yml_dict, validator, schema, plot_types):
    """
    Inputs:
        :yml_dict: (dictionary) the dictionary to be normalized against a schema
        :validator: (SimmerValidator) the validator object used.
        :schema: the schema against which the yml_dict is normalized.
        :plot_types: (list of strings) the basic plot_types that must be in
            the uppermost keys.

    Outputs:
        :normalized: normalized dictionary.
    """
    validator.schema = schema
    for plot_type in plot_types:
        if plot_type not in yml_dict.keys():
            yml_dict[plot_type] = {}
    normalized = validator.normalized(yml_dict)
    return normalized


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
            See the `plotting_schema.yml` schema for documentation of keys and values.

    """
    my_path = os.path.abspath(os.path.dirname(__file__))
    schema_filename = os.path.join(my_path, "plotting_schema.yml")
    plot_types = ["intermediate", "final_im", "rots"]

    if not yml_filename:
        # the normalizer fills in all empty fields later on
        yml_dict = {plot_type: {} for plot_type in plot_types}
    else:
        if validate_yml(schema_filename, yml_filename):
            yml_dict = read_yml(yml_filename)
        else:
            raise cerberus.SchemaError("parsing plotting yml failed")

    s = SimmerValidator()
    schema = read_yml(schema_filename)
    plotting_args = normalize(yml_dict, s, schema, plot_types)
    return plotting_args
