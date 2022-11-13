"""Generic helper functions."""

def is_var_number(var) -> bool:
    """Checks if the provided variable is a number type.

    Args:
        var (any): The variable to check.

    Returns:
        bool: True if the provide variable is a number type, False otherwise.
    """
    try:
        return type(var) == int or type(var) == float #pylint: disable=unidiomatic-typecheck
    except Exception:
        pass
    return False

def is_var_function(var) -> bool:
    """Checks if the provided variable is a function.

    Args:
        var (any): The variable to check.

    Returns:
        bool: True if the provided variable is a function, False otherwise.
    """
    try:
        return callable(var)
    except Exception:
        pass
    return False
