from pathlib import Path

# local module
from utils.helpers import open_yaml_config


CONFIG_FP = Path(__file__).parent.parent.parent.joinpath("assets/global_config.yaml")
GLOBAL_CONFIG = open_yaml_config(str(CONFIG_FP))
