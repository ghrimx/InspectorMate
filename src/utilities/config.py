import os
from pathlib import Path
from dataclasses import dataclass

from qtpy import QSettings

from utilities.loggin import LOGGIN


@dataclass
class Config():
    organization_name: str = "FAMHP"
    app_name: str = "InspectorMate"
    app_version: str = "2.0.0a"
    db_version: str = ""
    app_data_path: Path = Path(os.getenv('LOCALAPPDATA')).joinpath("Programs/InspectorMate")
    db_path: Path = app_data_path.joinpath(f"inspectormate.sqlite")
    log_path: Path = app_data_path.joinpath("inspectormate.log")
    config_path: Path = app_data_path.joinpath("logging.ini")
    style_path: Path = app_data_path.joinpath("Style")

    def __post_init__(cls):
        """
        Create the necessary files/folders after the init of the Config class
        """
        if not cls.app_data_path.exists():
            cls.app_data_path.mkdir(parents=True, exist_ok=True)

        if not cls.log_path.exists():
            f = open(cls.log_path, 'w')

        if not cls.config_path.exists():
            p = Path(cls.config_path)
            p.write_text(LOGGIN)
        
config = Config()
settings = QSettings(config.organization_name, config.app_name)
default_regex = r"^(([a-zA-Z]{0,3})\d{1,3})"
