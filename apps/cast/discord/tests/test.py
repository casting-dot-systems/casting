import pytest


def test_basic_assertion():
    """Test basic assertion to verify pytest is working."""
    assert 1 == 1


def test_string_equality():
    """Test string equality assertion."""
    assert "hello" == "hello"


def test_boolean_values():
    """Test boolean assertions."""
    assert True is True
    assert False is False
    assert not False


def test_list_operations():
    """Test basic list operations."""
    test_list = [1, 2, 3]
    assert len(test_list) == 3
    assert 2 in test_list


def test_math_operations():
    """Test basic math operations."""
    assert 2 + 2 == 4
    assert 10 - 5 == 5
    assert 3 * 4 == 12
    assert 8 / 2 == 4


def test_none_values():
    """Test None value assertions."""
    assert None is None
    test_var = None
    assert test_var is None


class TestBasicClass:
    """Test class to verify class-based tests work."""
    
    def test_class_method(self):
        """Test method within a class."""
        assert "test" == "test"
    
    def test_class_setup(self):
        """Test class setup functionality."""
        self.value = 42
        assert self.value == 42


@pytest.mark.parametrize("input_val,expected", [
    (1, 1),
    (2, 2),
    ("hello", "hello"),
])
def test_parametrized(input_val, expected):
    """Test parametrized test functionality."""
    assert input_val == expected
