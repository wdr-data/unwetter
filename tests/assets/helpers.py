from os.path import dirname
from pathlib import Path

ASSETS = Path(dirname(__file__))


def load_asset(name, **kwargs):
    kwargs["encoding"] = kwargs.get("encoding", "utf-8")

    with open(ASSETS / name, "r", **kwargs) as fp:
        return fp.read()
