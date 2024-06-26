"""Test functions for YOCO."""

import argparse
import copy
import os

import pytest

import yoco


def test_config_from_file() -> None:
    """Test loading a simple config from a file."""
    loaded_dict = yoco.load_config_from_file("tests/test_files/config_1.yaml")

    expected_dict = {
        "test_param_1": 2,
        "test_param_2": "Test string",
        "test_list": [1, 2, 3],
    }

    assert loaded_dict == expected_dict

    # ensure current dictionary is not modified
    d1 = {"test": 10}
    d1_copy = copy.deepcopy(d1)
    loaded_dict = yoco.load_config_from_file("tests/test_files/config_1.yaml", d1)
    expected_dict = {
        "test_param_1": 2,
        "test_param_2": "Test string",
        "test_list": [1, 2, 3],
        "test": 10,
    }
    assert d1 == d1_copy
    assert loaded_dict == expected_dict


def test_load_config() -> None:
    """Test loading a config through a predefined config dictionary.

    YOCO should interpret "config" key as a path and follow such paths recursively.
    When parameters are repeated the one earlier in this chain "wins".
    """
    config_dict = {
        "config": "tests/test_files/config_1.yaml",
        "test_param_1": 3,  # final param should be 3, not 2 from the file
        "test_param_3": "Param not in file",
    }
    config_dict = yoco.load_config(config_dict)

    # Merged dictionary from config_1.yaml and the provided params
    expected_dict = {
        "test_param_1": 3,
        "test_param_2": "Test string",
        "test_list": [1, 2, 3],
        "test_param_3": "Param not in file",
    }
    assert config_dict == expected_dict

    # Default dictionary (i.e., merging without overwriting
    default_dict = {
        "config": "tests/test_files/config_1.yaml",
    }
    config_dict = {
        "test_param_1": 5,
        "test_param_3": 5,
    }
    expected_default_dict = copy.deepcopy(default_dict)
    current_dict = yoco.load_config(default_dict)
    final_config = yoco.load_config(config_dict, current_dict=current_dict)

    # Default dictionary should not change
    assert default_dict == expected_default_dict
    expected_dict = {
        "test_param_1": 5,
        "test_param_2": "Test string",
        "test_param_3": 5,
        "test_list": [1, 2, 3],
    }
    assert expected_dict == final_config

    # Ensure config_dict and current_dict are not modified
    d1 = {
        "config": "tests/test_files/config_1.yaml",
        "test_param_1": 3,  # final param should be 3, not 2 from the file
        "test_param_3": "Param not in file",
    }
    d2 = {"test_param_1": 1, "test_param_4": 1}
    expected_dict = {
        "test_param_1": 3,
        "test_param_2": "Test string",
        "test_list": [1, 2, 3],
        "test_param_3": "Param not in file",
        "test_param_4": 1,
    }
    d1_copy = copy.deepcopy(d1)
    d2_copy = copy.deepcopy(d2)
    d3 = yoco.load_config(d1, d2)
    assert d1_copy == d1
    assert d2_copy == d2
    assert d3 == expected_dict


def test_save_config(tmp_path: str) -> None:
    """Test saving the config to file.

    Loading a config, saving it to a file and loading it again should yield the same
    dictionary.
    """
    file_path = tmp_path / "test.yaml"
    original_dict = yoco.load_config_from_file("tests/test_files/config_1.yaml")
    yoco.save_config_to_file(file_path, original_dict)
    new_dict = yoco.load_config_from_file(file_path)
    assert original_dict == new_dict


def test_include() -> None:
    """Test loading a config file with various !include tags."""
    loaded_dict = yoco.load_config_from_file("tests/test_files/config_w_include.yaml")

    expected_dict = {
        "as_value": {"test": 1},
        "in_list": [{"test": 1}, {"test": 2}, 5, {"test": 2}],
        "test_param_1": 5,
        "test_param_2": "Test string",
        "test_list": [1, 2, 3]
    }

    assert loaded_dict == expected_dict


def test_nested_config() -> None:
    """Test loading with multiple nested config files.

    Loads a config file that contains two parent configs.
    One of which has another parent:

    start -> 1
            / \
           2   3
           |
           4 <- "parent" of 2

    The higher up in the chain, the higher the priority.
    If there are multiple parents, the last one wins.
    """
    original_dict = yoco.load_config_from_file("tests/test_files/1.yaml")
    expected_dict = {
        "2_and_4": 2,  # 2.yaml is higher up in the chain
        "4_only": 4,
        "2_and_3": 3,  # 3.yaml is the the last parent of 1
        "3_only": 3,
        "1_only": 1,
        "2_only": 2,
        "all": 1,
        "test_path": "tests/test_files/1.yaml",
        "rel_path": "tests/test_files/subdir/subdir.yaml",
    }
    assert original_dict == expected_dict


def test_namespaces() -> None:
    """Test loading config with namespaces.

    If "config" key contains a dictionary, the key will be the param name under which
    the config file will be added.

    The config value can also be a list of dictionaries / strings, adding namespaces if
    it is a dictionary.
    """
    config_dict = yoco.load_config_from_file("tests/test_files/namespace_1.yaml")
    expected_dict = {
        "ns_1": {
            "test_param_1": 2,
            "test_param_2": "Test string",
            "test_list": [1, 2, 3],
            "ns_2_param": 1,
            "ns_nested": {
                "test_param_1": 2,
                "test_param_2": "Test string",
                "test_list": [1, 2, 3],
            },
        },
        "test_param_1": 5,
    }
    assert config_dict == expected_dict

    config_dict = yoco.load_config_from_file("tests/test_files/nested_namespace.yaml")
    expected_dict = {
        "a": {
            "b": {
                "test_param_1": 2,
                "test_param_2": "Test string",
                "test_list": [1, 2, 3],
            },
            "b2": {
                "test_param_1": 2,
                "test_param_2": "Test string",
                "test_list": [1, 2, 3],
            },
        },
    }
    assert config_dict == expected_dict


def test_config_from_parser() -> None:
    """Test loading config using argparse."""
    parser = argparse.ArgumentParser()
    config_dict = yoco.load_config_from_args(parser, args=["--a", "1"])
    expected_dict = {"a": 1}
    assert config_dict == expected_dict

    # simple hierarchy
    parser = argparse.ArgumentParser()
    config_dict = yoco.load_config_from_args(parser, args=["--a.b.c", "1"])
    expected_dict = {"a": {"b": {"c": 1}}}
    assert config_dict == expected_dict

    # nested config
    parser = argparse.ArgumentParser()
    config_dict = yoco.load_config_from_args(
        parser,
        args=[
            "--a.test_param_1",
            "Overwrite",
            "file",
            "--config.a",
            "tests/test_files/config_1.yaml",
        ],
    )
    expected_dict = {
        "a": {
            "test_param_1": "Overwrite file",
            "test_param_2": "Test string",
            "test_list": [1, 2, 3],
        }
    }
    assert config_dict == expected_dict

    # trying wrong arg order
    parser = argparse.ArgumentParser()
    with pytest.raises(SystemExit):
        config_dict = yoco.load_config_from_args(
            parser, args=["1", "--a"]
        )  # wrong order

    # test default args (priority: default < from config < argument)
    # first case: with default config
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", type=int, default=3)
    parser.add_argument("--config", default="tests/test_files/test_1.yaml")
    config_dict = yoco.load_config_from_args(
        parser,
        args=[
            "--config",
            "tests/test_files/test_2.yaml",
        ],
    )
    expected_dict = {
        "test": 2,  # provided config has highest priority
    }
    assert config_dict == expected_dict

    config_dict = yoco.load_config_from_args(
        parser,
        args=["--config", "tests/test_files/test_2.yaml", "--test", "4"],
    )
    expected_dict = {
        "test": 4,  # argument has highest priority
    }
    assert config_dict == expected_dict

    config_dict = yoco.load_config_from_args(
        parser,
        args=[],
    )
    expected_dict = {
        "test": 1,  # default config has highest priority
    }
    assert config_dict == expected_dict

    # second case: without default config
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", type=int, default=3)
    parser.add_argument("--config")
    config_dict = yoco.load_config_from_args(
        parser,
        args=[
            "--config",
            "tests/test_files/test_2.yaml",
        ],
    )
    expected_dict = {
        "test": 2,  # provided config has highest priority
    }
    assert config_dict == expected_dict

    config_dict = yoco.load_config_from_args(
        parser,
        args=[
            "--config",
            "tests/test_files/test_2.yaml",
            "--test",
            "4",
        ],
    )
    expected_dict = {
        "test": 4,  # provided argument has highest priority
    }
    assert config_dict == expected_dict

    config_dict = yoco.load_config_from_args(
        parser,
        args=[],
    )
    expected_dict = {
        "test": 3,  # default value has highest priority
    }
    assert config_dict == expected_dict

    # third case: without config in argument list
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", type=int, default=3)
    config_dict = yoco.load_config_from_args(
        parser,
        args=[
            "--config",
            "tests/test_files/test_2.yaml",
        ],
    )
    expected_dict = {
        "test": 2,  # provided config has highest priority
    }
    assert config_dict == expected_dict

    config_dict = yoco.load_config_from_args(
        parser,
        args=[
            "--config",
            "tests/test_files/test_2.yaml",
            "--test",
            "4",
        ],
    )
    expected_dict = {
        "test": 4,  # provided argument has highest priority
    }
    assert config_dict == expected_dict

    config_dict = yoco.load_config_from_args(
        parser,
        args=[],
    )
    expected_dict = {
        "test": 3,  # default value has highest priority
    }
    assert config_dict == expected_dict

    # search path when loading from args
    config_dict = yoco.load_config_from_args(
        parser,
        args=["--config", "file_in_other_folder.yaml"],
        search_paths=["tests/other_folder/"],
    )
    expected_dict = {
        "my_var": 2.3,  # from file_in_other_folder
        "test": 3,  # from default arg
    }
    assert config_dict == expected_dict


def test_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test resolving of paths with searchpaths and homefolder."""

    # expand home dir
    def mock_expanduser(path: str) -> str:
        return path.replace("~", "tests/home_dir")

    monkeypatch.setattr(os.path, "expanduser", mock_expanduser)

    config_dict = yoco.load_config_from_file(
        "tests/test_files/paths.yaml", search_paths=[".", "", "tests/other_folder/"]
    )
    expected_dict = {
        "file_in_home": "tests/home_dir/123.dat",  # default value has highest priority
        "my_number": 1,
        "my_var": 2.3,
    }
    assert config_dict == expected_dict
