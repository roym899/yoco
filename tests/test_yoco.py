"""Test functions for YOCO."""
import yoco


def test_config_from_file():
    """Test loading a simple config from a file."""
    loaded_dict = yoco.load_config_from_file("tests/test_files/config_1.yaml")

    expected_dict = {
        "test_param_1": 2,
        "test_param_2": "Test string",
        "test_list": [1, 2, 3]
    }

    assert loaded_dict == expected_dict
