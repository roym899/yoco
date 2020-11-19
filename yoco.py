"""YOCO is a minimalistic YAML-based configuration manager."""
import os

from ruamel.yaml import YAML

yaml = YAML()


def load_config_from_file(path, current_dict=None, parent=None):
    """Load configuration from a file."""
    if current_dict is None:
        current_dict = {}

    full_path = path if parent is None else os.path.join(parent, path)

    if parent is None:
        parent = os.path.dirname(path)

    with open(full_path) as f:
        config_dict = yaml.load(f)
        load_config(config_dict, current_dict, parent)

    return current_dict


def load_config(config_dict, current_dict=None, parent=None):
    """Load a config specified as a dictionary."""
    if current_dict is None:
        current_dict = {}
    if "config" in config_dict:
        if isinstance(config_dict["config"], str):
            load_config_from_file(config_dict["config"], current_dict, parent)
        elif isinstance(config_dict["config"], list):
            for config_path in config_dict["config"]:
                load_config_from_file(config_path, current_dict, parent)

    config_dict.pop("config", None)
    current_dict.update(config_dict)

    return current_dict
