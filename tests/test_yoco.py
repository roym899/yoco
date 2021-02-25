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
