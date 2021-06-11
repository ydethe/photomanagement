from configparser import ConfigParser


def loadConfig(fic: str) -> ConfigParser:
    config = ConfigParser()
    config.read(fic, encoding="utf-8")
    return config
