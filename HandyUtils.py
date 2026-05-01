"""A collection of utilities used across Handy Helpers"""

from pathlib import Path
import importlib.util
import sys

def ModuleExists(name):
    """Checks if Python module is available"""
    if name in sys.modules:
        return True
    elif (spec := importlib.util.find_spec(name)) is not None:
        return True
    else:
        return False


class ConfigNotFoundError(Exception):
    pass

def ReadConfigFile(confName, confDir: str = "./config/"):
    """Reads a configuration file of provided name. If it doesn't exist or is not a file, throws"""
    path = Path(confDir + "/" + confName).expanduser()
    if not path.exists() or not path.is_file():
        raise ConfigNotFoundError("Configuration file {0} does not exist".format(confName))

    value = path.read_text().strip()
    if not value:
        raise ConfigNotFoundError("Configuration file {0} is empty".format(confName))

    return value
