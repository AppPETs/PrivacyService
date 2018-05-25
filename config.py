"""PrivacyService configuration module
Attemps to read a conf.json file that exists locally and uses this file
to populate an options dictionary. If no such file exists, default conf-
iguration values are used."""

import json
import os

CONFIG_FILE_NAME = os.path.join(os.path.dirname(__file__), "conf.json")

CONFIG_DEFAULT = {
    "DATABASE_FILE": os.path.join(os.path.dirname(__file__), "data.db"),
# General configuration
    "KEY_SIZE_IN_BITS": 256,
    "SUPERFLUOUS_HEADERS_ALLOWED": True,
# Server configuration
    "SERVER_ADDRESS": "127.0.0.1",
    "SERVER_PORT": 8080,
# Other settings
    "REQUEST_LOGGING": True
}


def store_config(config, to_file=CONFIG_FILE_NAME):
    """Store server configuration to disk"""
    with open(to_file, "w") as outfile:
        json.dump(config, outfile, indent=4)


def load_config(from_file=CONFIG_FILE_NAME):
    """Loads server configuration"""
    global _config

    # Use existing configuration, if it was already loaded during this
    # execution
    if '_config' in globals():
        return _config

    # Use default configuration as baseline. The loaded file replaces
    # the keys it re-defines. This means local configuration files can
    # focus on re-defining only the keys they want to change.
    config = CONFIG_DEFAULT.copy()

    if os.path.exists(from_file):
        try:
            with open(from_file) as input:
                config.update(json.load(input))
        except:
            pass
    else:
        store_config(config)

    _config = config

    return _config
    