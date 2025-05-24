import os
import yaml
import logging

logger = logging.getLogger(__name__)

def load_config(config_path):
    logger.info(f"Loading configuration from: {config_path}")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)
    logger.info(f"Configuration loaded: {config}")
    return config
