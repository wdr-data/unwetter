from os.path import dirname
from pathlib import Path

ASSETS = Path(dirname(__file__))


def load_asset(name):
    with open(ASSETS / name, "r") as fp:
        return fp.read()
