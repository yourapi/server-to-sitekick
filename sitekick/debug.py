import random
from importlib import import_module
from pathlib import Path
from pprint import pprint

def debug(*args):
    """Get the command from the endpoint, execute it and POST the result."""
    from sitekick import get_command
    command = get_command()
    print(f"Executing command: {command}")
    result = command()
    print(f"Result: {result}")
