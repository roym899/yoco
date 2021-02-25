"""Test functions for YOCO."""
import yoco


def test_config_from_file():
    """Test loading a simple config from a file."""
    loaded_dict = yoco.load_config_from_file("tests/test_files/config_1.yaml")

    expected_dict = {
        "test_param_1": 2,
        "test_param_2": "Test string",
        "test_list": [1, 2, 3],
    }

    assert loaded_dict == expected_dict


def test_load_config():
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


def test_save_config(tmp_path):
    """Test saving the config to file.

    Loading a config, saving it to a file and loading it again should yield the same
    dictionary.
    """
    file_path = tmp_path / "test.yaml"
    original_dict = yoco.load_config_from_file("tests/test_files/config_1.yaml")
    yoco.save_config_to_file(file_path, original_dict)
    new_dict = yoco.load_config_from_file(file_path)
    assert original_dict == new_dict


def test_nested_config():
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
    }
    assert original_dict == expected_dict
