import json
from dataclasses import dataclass
from pathlib import Path
from utilities.utils import (queryFileID, queryFileNameByID)

@dataclass
class Document:
    note: str = ""
    status_id: int = 1
    refKey: str = ""
    title: str = ""
    subtitle: str = ""
    reference: str = ""
    type_id: int = 0
    id: int = 0
    filename: str = ""
    _filepath: Path = ""
    modification_datetime: str = ""
    creation_datetime: str = ""
    workspace_id: int = 0
    dirpath: Path = ""
    display: bool = True
    fileid: str = ""

    def exists(self) -> bool:
        return self.filepath.exists()
    
    def extension(self) -> str:
        ext = Path(self.filepath).suffix
        return ext.lower()
    
    def folderpath(self) -> Path:
        return self.filepath.parent
    
    @property
    def filepath(self) -> Path:
        if self._filepath.exists():
            return self._filepath
        else:
            p = Path(queryFileNameByID(self.fileid))
            self._filepath = p
            return p
    
    @filepath.setter
    def filepath(self, fpath: Path | str) -> None:
        self._filepath = Path(fpath)

    
@dataclass
class Signage:
    note: str = ""
    status_id: str | int = ""
    owner: str = ""
    type_id: str | int = ""
    refKey: str = ""
    title: str = ""
    creation_datetime: str = ""
    modification_datetime: str = ""
    link: str = ""
    signage_id: int = 0
    workspace_id: int = 0
    uid: str = ""

@dataclass
class Workspace:
    id: int = 0
    name: str = ""
    rootpath: str = ""
    evidence_path: str = ""
    notebook_path: str = ""
    onenote_section: str = "" # json {section_id:{...}, section_name:{...}}
    state: bool = True

    def OESectionID(self) -> str | None:
        try:
            _onenote: dict = json.loads(self.onenote_section)
            return _onenote["section_id"]
        except:
            return
        
    def OESectionName(self) -> str | None:
        try:
            _onenote: dict = json.loads(self.onenote_section)
            return _onenote["section_name"]
        except:
            return
        
@dataclass
class SignageType:
    type_id: int
    type: str
    color: str
    icon: str
