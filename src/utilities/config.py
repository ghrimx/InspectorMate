import os
import sys
import logging
from pathlib import Path
from dataclasses import dataclass

from qtpy import QSettings

from utilities.loggin import LOGGIN

logger = logging.getLogger(__name__)

@dataclass
class Config():
    organization_name: str = "FAMHP"
    app_name: str = "InspectorMate"
    app_version: str = "3.2.0-alpha"
    db_version: str = ""
    app_data_path: Path = Path(os.getenv('APPDATA')).joinpath(".inspectormate")
    db_path: Path = Path(os.getenv('APPDATA')).joinpath(f".inspectormate/inspectormate.sqlite")
    log_path: Path = Path(os.getenv('APPDATA')).joinpath(".inspectormate/inspectormate.log")
    config_path: Path = Path(os.getenv('APPDATA')).joinpath(".inspectormate/logging.ini")

    def __post_init__(cls):
        """
        Create/Move/Copy/Unzip the necessary files/folders after the init of the Config class
        """
        if not cls.app_data_path.exists():
            cls.app_data_path.mkdir(parents=True, exist_ok=True)

        if not cls.log_path.exists():
            f = open(cls.log_path, 'w')

        if not cls.config_path.exists():
            p = Path(cls.config_path)
            p.write_text(LOGGIN)

        if not cls.db_path.exists():
            from shutil import copyfile
            bundle_dir = Path(getattr(sys, '_MEIPASS', Path.cwd()))
            try:
                copyfile(Path.joinpath(bundle_dir,"data","inspectormate_template.sqlite").as_posix(), cls.db_path.as_posix())
            except Exception as e:
                f = open(os.path.join(cls.app_data_path,"err_db_location.txt"), "w")
                f.write(f"{Path.joinpath(bundle_dir,"data","inspectormate_template.sqlite").as_posix()}")
                f.write(f"{e}")
                f.close()
        
config = Config()
settings = QSettings(config.organization_name, config.app_name)
default_regex = r"^(([a-zA-Z]{0,3})\d{1,3})"
