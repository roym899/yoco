"""YOCO is a minimalistic YAML-based configuration manager."""
import argparse as _argparse
import os as _os
from typing import Optional

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
        elif isinstance(value, str) and (
            value.startswith("./") or value.startswith("../")
        ):
            config_dict[key] = _os.path.join(parent, value)


def save_config_to_file(path, config_dict):
    """Save config dictionary as a yaml file."""
    with open(path, "w") as f:
        _yaml.dump(config_dict, f)


def config_from_parser(
    parser: _argparse.ArgumentParser, args: Optional[list] = None
) -> dict:
    """Parse arguments and load configs into a config dictionary.

    Strings following -- will be used as key. Dots in that string are used to access
    nested dictionaries. Yaml will be used for type conversion of the value.

    Args:
        parser:
            Parser used to parse known and unknown arguments.
            This function will handle both the known args that have been added before
            and it tries to parse all other args and integrate them into the config.
        args:
            List of arguments to parse. If None, sys.argv[1:] is used.
    """
    known, other_args = parser.parse_known_args(args)
    config_dict = {k: v for k, v in vars(known).items() if v is not None}
    config_dict = load_config(config_dict)
    current_key = None

    # list of unknown args (all strings) to dictionary
    # [--arg_1, val_1, --arg_2, val_2_a, val_2_b, ...]
    # -> {arg_1: val_1, arg_2: "{val_2_a} {val_2_b}, ...}
    arg_dict = {}
    for arg in other_args:
        if arg.startswith("--"):
            current_key = arg.replace("--", "")
            arg_dict[current_key] = []
        else:
            if current_key is None:
                parser.error(
                    message="General args need to start with --name {values}\n"
                )
            arg_dict[current_key].append(arg)
    arg_dict = {key: " ".join(values) for key, values in arg_dict.items()}

    # integrate arg, value pairs into config_dict loaded before, one by one
    # args can set nested values by using dots
    # i.e., a.b.c will result in the following hierarchy: {"a": {"b": {"c": value}}}
    # "config" can still be used to load files
    for arg, value in arg_dict.items():
        add_dict = {}
        current_dict = add_dict
        hierarchy = arg.split(".")
        for a in hierarchy[:-1]:
            current_dict[a] = {}
            current_dict = current_dict[a]
        # parse value using yaml (this allows setting lists, dictionaries, etc.)
        current_dict[hierarchy[-1]] = _yaml.load(value)

        # handle special "config" key by loading the nested dict as root dict
        # this will practically replace "config" key with the dict from
        # the specified file
        load_config(current_dict, current_dict)

        # integrate nested dictionary into config_dict loaded before
        load_config(add_dict, config_dict)

    return config_dict
