import yaml
import unittest
import sys

sys.path.append(os.getcwd()[:-6])
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


parent_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))

import schemas.custom_validator as validator


class TestYml(unittest.TestCase):
    def test_validator_instantiate(self):
        try:
            validator.SimmerValidator()
            instantiated = True
        except:
            instantiated = False
        self.assertTrue(instantiated)

    def test_validate(self):
        s = validator.SimmerValidator()

        file = open("../src/simmer/schemas/plotting.yml")
        parsed_yaml_file = yaml.load(file, Loader=yaml.SafeLoader)

        document = {"all_colorbars": True}
        try:
            s.validate(document, parsed_yaml_file)
            validated = True
        except:
            validated = False
        file.close()
        self.assertTrue(validated)
