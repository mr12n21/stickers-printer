import yaml
import os

CONFIG_PATH = "config.yaml"
PRINTER_MODEL = "QL-1050"
USB_PATH = "/dev/usb/lp0"

def load_config(config_path=CONFIG_PATH):
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Konfigurační soubor nenalezen: {config_path}")
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)
    return config