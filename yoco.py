"""This module contains all YOCO functions to load and save configurations.

YOCO is based on Python dictionaries and YAML files to provide a simple, yet powerful
way of configuring Python projects. YOCO supports specifying parameters through the
command line, YAML-files or directly from a Python dictionary.
"""
import argparse as _argparse
import copy
import os as _os
from typing import Optional
import sys
import re

from ruamel.yaml import YAML as _YAML

if sys.version_info < (3, 7):
    copy._deepcopy_dispatch[type(re.compile(""))] = lambda r, _: r

_yaml = _YAML()


def load_config_from_file(
    path: str, current_dict: Optional[dict] = None, parent: Optional[str] = None
) -> dict:
    """Load configuration from a file.

    Args:
        path: Path of YAML file to load.
        current_dict:
            Current configuration dictionary. Will not be modified.
            If None, an empty dictionary will be created.
        parent:
            Parent directory.
            If not None, path will be assumed to be relative to parent.

    Returns:
        Updated configuration dictionary.
    """
    if current_dict is None:
        current_dict = {}

    full_path = path if parent is None else _os.path.join(parent, path)

    parent = _os.path.dirname(full_path)

    with open(full_path) as f:
        config_dict = _yaml.load(f)
        current_dict = load_config(config_dict, current_dict, parent)

    return current_dict


def load_config(
    config_dict: dict,
    current_dict: Optional[dict] = None,
    parent: Optional[str] = None,
) -> dict:
    """Load a config dictionary.

    If a key is already in current_dict, config_dict will overwrite it.

    Note that default_dict and current_dict are not supported together.

    Args:
        config_dict: Configuration dictionary to be parsed.
        current_dict:
            Current configuration dictionary to be updated, will not be changed.
        parent: Path of parent config. Used to resolve relative paths.

    Returns:
        Loaded / updated configuration dictionary.
    """
    config_dict = copy.deepcopy(config_dict)
    if current_dict is None:
        current_dict = {}
    else:
        current_dict = copy.deepcopy(current_dict)

    if "config" in config_dict:
        current_dict = _resolve_config_key(config_dict, current_dict, parent)

    config_dict.pop("config", None)

    if parent is not None:
        _resolve_paths_recursively(config_dict, parent)

    current_dict = _merge_dictionaries(current_dict, config_dict)

    return current_dict


def save_config_to_file(path: str, config_dict: dict) -> None:
    """Save config dictionary as a yaml file."""
    with open(path, "w") as f:
        _yaml.dump(config_dict, f)


def load_config_from_args(
    parser: _argparse.ArgumentParser, args: Optional[list] = None
) -> dict:
    """Parse arguments and load configs into a config dictionary.

    Strings following -- will be used as key. Dots in that string are used to access
    nested dictionaries. YAML will be used for type conversion of the value.

    Args:
        parser:
            Parser used to parse known and unknown arguments.
            This function will handle both the known args that have been added before
            and it tries to parse all other args and integrate them into the config.
        args:
            List of arguments to parse. If None, sys.argv[1:] is used.

    Returns:
        Loaded configuration dictionary.
    """
    # parse arguments
    no_default_parser = copy.deepcopy(parser)
    for a in no_default_parser._actions:
        if a.dest != "config":
            a.default = None
    known, other_args = no_default_parser.parse_known_args(args)

    known_with_default, _ = parser.parse_known_args(args)

    config_dict = {k: v for k, v in vars(known).items() if v is not None}
    with_default_config_dict = {
        k: v for k, v in vars(known_with_default).items() if v is not None
    }
    with_default_config_dict.pop("config", None)

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
    # done parsing args, stored in arg_dict

    # integrate arg, value pairs into config_dict loaded before, one by one
    # args can set nested values by using dots
    # i.e., a.b.c will result in the following add_dict: {"a": {"b": {"c": value}}}
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

        if hierarchy[0] == "config":
            # handle special "config" key by loading the nested dict as root dict
            # this will practically replace "config" key with the dict from
            # the specified file
            add_dict = load_config(add_dict)
            # config file -> lower priority than what is already there
            config_dict = load_config(config_dict, add_dict)
        else:
            # integrate nested dictionary into config_dict loaded before
            # normal argument -> higher priority than what is arleady there
            config_dict = load_config(add_dict, config_dict)

    # add default values last (lowest priority) if they weren't specified so far
    config_dict = _merge_dictionaries(with_default_config_dict, config_dict)

    return config_dict


def _resolve_config_key(config_dict: dict, current_dict: dict, parent: str) -> dict:
    # config can be string, list of strings, dict, or list of string / dict
    if isinstance(config_dict["config"], str):
        return load_config_from_file(config_dict["config"], current_dict, parent)
    elif isinstance(config_dict["config"], list):
        return _resolve_config_list(config_dict["config"], current_dict, parent)
    elif isinstance(config_dict["config"], dict):
        return _resolve_config_dict(config_dict["config"], current_dict, parent)
    else:
        raise TypeError("Can't parse element of type {type(config_dict['config'])}")


def _resolve_config_dict(config_dict: list, current_dict: dict, parent: str) -> None:
    for ns, element in config_dict.items():
        if ns not in current_dict:
            current_dict[ns] = {}
        if isinstance(element, str):
            current_dict[ns] = load_config_from_file(element, current_dict[ns], parent)
        elif isinstance(element, list):
            current_dict[ns] = _resolve_config_list(element, current_dict[ns], parent)
        elif isinstance(element, dict):
            current_dict[ns] = _resolve_config_dict(element, current_dict[ns], parent)
    return current_dict


def _resolve_config_list(config_list: list, current_dict: dict, parent: str) -> None:
    for element in config_list:
        if isinstance(element, str):
            current_dict = load_config_from_file(element, current_dict, parent)
        elif isinstance(element, list):
            current_dict = _resolve_config_list(element, current_dict, parent)
        elif isinstance(element, dict):
            current_dict = _resolve_config_dict(element, current_dict, parent)
    return current_dict


def _merge_dictionaries(start_dict: dict, added_dict: dict) -> dict:
    """Create a dictionary by merging one into another.

    Keys present in start_dict will be overwritten by added_dict.

    Args:
        start_dict: The starting dictionary.
        added_dict: The dictionary to merge into current_dictionary.

    Returns:
        The merged dictionary.
    """
    merged_dictionary = copy.deepcopy(start_dict)
    for key, value in added_dict.items():
        if (
            key in start_dict
            and isinstance(start_dict[key], dict)
            and isinstance(added_dict[key], dict)
        ):
            merged_dictionary[key] = _merge_dictionaries(
                start_dict[key], added_dict[key]
            )
        else:
            merged_dictionary[key] = value
    return merged_dictionary


def _resolve_paths_recursively(config_dict: dict, parent: str) -> None:
    for key, value in config_dict.items():
        if isinstance(config_dict[key], dict):
            _resolve_paths_recursively(config_dict[key], parent)
        elif isinstance(value, str) and (
            value.startswith("./") or value.startswith("../")
        ):
            config_dict[key] = _os.path.join(parent, value)
