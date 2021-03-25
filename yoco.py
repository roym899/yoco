"""YOCO is a minimalistic YAML-based configuration manager."""
import os as _os

from ruamel.yaml import YAML as _YAML


_yaml = _YAML()


def load_config_from_file(path, current_dict=None, parent=None, ns=None):
    """Load configuration from a file."""
    if current_dict is None:
        current_dict = {}

    full_path = path if parent is None else _os.path.join(parent, path)

    parent = _os.path.dirname(full_path)

    with open(full_path) as f:
        config_dict = _yaml.load(f)
        if ns is not None:
            if ns not in current_dict:
                current_dict[ns] = {}
            load_config(config_dict, current_dict[ns], parent)
            current_dict[f"__path_{ns}__"] = parent
        else:
            load_config(config_dict, current_dict, parent)

    return current_dict


def load_config(config_dict, current_dict=None, parent=None):
    """Load a config specified as a dictionary."""
    if current_dict is None:
        current_dict = {}
    if "config" in config_dict:
        # config can be string, list of strings, dict, or list of string / dict
        if isinstance(config_dict["config"], str):
            load_config_from_file(config_dict["config"], current_dict, parent)
        elif isinstance(config_dict["config"], dict):
            for ns, config_path in config_dict["config"].items():
                load_config_from_file(config_path, current_dict, parent, ns)
        elif isinstance(config_dict["config"], list):
            for element in config_dict["config"]:
                if isinstance(element, str):
                    load_config_from_file(element, current_dict, parent)
                elif isinstance(element, dict):
                    for ns, config_path in element.items():
                        load_config_from_file(config_path, current_dict, parent, ns)

    config_dict.pop("config", None)

    if parent is not None:
        resolve_paths_recursively(config_dict, parent)

    update_recursively(current_dict, config_dict)

    return current_dict


def update_recursively(current_dict: dict, added_dict: dict):
    for key, value in added_dict.items():
        if (
            key in current_dict
            and isinstance(current_dict[key], dict)
            and isinstance(added_dict[key], dict)
        ):
            update_recursively(current_dict[key], added_dict[key])
        else:
            current_dict[key] = value


def resolve_paths_recursively(config_dict, parent):
    for key, value in config_dict.items():
        if isinstance(config_dict[key], dict):
            resolve_paths_recursively(config_dict[key], parent)
        elif (
            isinstance(value, str)
            and (value.startswith("./") or value.startswith("../"))
        ):
            config_dict[key] = _os.path.join(parent, value)


def save_config_to_file(path, config_dict):
    """Save config dictionary as a yaml file."""
    with open(path, "w") as f:
        _yaml.dump(config_dict, f)
