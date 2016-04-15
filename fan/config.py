import os 
import yaml

CONFIG = {}
if os.path.isfile("config.yaml"):
    with open("config.yaml") as f:
        CONFIG = yaml.safe_load(f)

if os.path.isfile("config-dev.yaml"):
    with open("config-dev.yaml") as f:
        devConfig = yaml.safe_load(f)
        for key in devConfig:
            CONFIG[key] = devConfig[key]