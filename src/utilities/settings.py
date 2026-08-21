# settings.py

import os
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
from uuid import uuid4

from qtpy import QSettings
from utilities.loggin import LOGGIN


class Settings:

    ORG_NAME = "FAMHP"
    ORG_DOMAIN = "famhp.net"
    APP_NAME = "InspectorMate"
    APP_VERSION = "6.5.0rc.1"
    APP_AUTHOR = "Debruycker Vincent"
    APP_DATA_PATH: Path = Path(os.getenv("LOCALAPPDATA")).joinpath("Programs/InspectorMate")
    DB_PATH: Path = APP_DATA_PATH.joinpath("inspectormate.sqlite")
    LOG_PATH: Path = APP_DATA_PATH.joinpath("inspectormate.log")
    CONFIG_PATH: Path = APP_DATA_PATH.joinpath("logging.ini")
    DEFAULT_SIGNAGE_PATTERN = r"^(([a-zA-Z]{0,3})\d{1,3})"
    DEFAULT_APP_STYLE = ""
    APP_LOGO = ":mylogo"

    def __init__(self):
        self._settings = QSettings(self.ORG_NAME, self.APP_NAME)

    @property
    def qsettings(self) -> QSettings:
        return self._settings

    @contextmanager
    def group(self, name: str):
        self._settings.beginGroup(name)
        try:
            yield self._settings
        finally:
            self._settings.endGroup()

    def ensure_files(self) -> None:
        if not self.LOG_PATH.is_file():
            self.LOG_PATH.touch()
        if not self.CONFIG_PATH.is_file():
            self.CONFIG_PATH.write_text(LOGGIN)

    def instance_id(self) -> str:
        instance_id = self._settings.value("InstanceId")
        if instance_id is None:
            instance_id = str(uuid4())
            self._settings.setValue("InstanceId", instance_id)
        return instance_id

    def set_instance_id(self, instance_id):
        self._settings.setValue("InstanceId", instance_id)

    # Styling
    def set_app_style(self, style_name: str = ""):
        self._settings.setValue("AppStyle", style_name)

    def app_style(self) -> str:
        style_name = self._settings.value("AppStyle", "")
        return style_name

    def set_app_font_size(self, font_size: float):
        self._settings.setValue("app_fontsize", font_size)

    def get_app_font_size(self) -> float:
        return self._settings.value("app_fontsize", 12.0, float)

    def get_alternating_row_coloring(self) -> bool:
        return self._settings.value("ALTERNATING_TABLE_ROW_COLOR", False, bool)
    
    def set_alternating_row_coloring(self, coloring: bool = False):
        self._settings.setValue("ALTERNATING_TABLE_ROW_COLOR", coloring)

    # Signage
    def set_signage_pattern(self, pattern: str):
        self._settings.setValue("regex", pattern)

    def get_signage_pattern(self) -> str:
        return self._settings.value("regex", self.DEFAULT_SIGNAGE_PATTERN)

    # Evidence
    def get_file_open_option(self) -> bool:
        return self._settings.value("USE_DEFAULT_FILEOPENER", False, bool)

    def set_file_open_option(self, opt: bool):
        self._settings.setValue("USE_DEFAULT_FILEOPENER", opt)

    # Update
    def set_update_show_option(self, opt: bool = True):
        self._settings.setValue("UPDATE_SHOW_AGAIN", opt)
    
    def get_update_show_option(self) -> bool:
        return self._settings.value("UPDATE_SHOW_AGAIN", True, bool)

    # Owner
    def get_owners(self) -> list:
        return self._settings.value("owners", [], "QStringList")

    def set_owners(self, owners: list):
        self._settings.setValue("owners", owners)

    # Table column width
    def get_column_width(self, group: str, column: int, default: int = 100) -> int:
        with self.group(group) as qs:
            return qs.value(f"column-{column}", default, int)

    def set_column_width(self, group: str, column: int, width: int) -> None:
        with self.group(group) as qs:
            qs.setValue(f"column-{column}", width)
    

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()