import json
from dataclasses import dataclass
from pathlib import Path
from utilities.utils import (queryFileID, queryFileNameByID)

@dataclass
class Document:
    refkey: str = ""
    title: str = ""
    subtitle: str = ""
    reference: str = ""
    status: int = 1
    type: int = 0
    note: str = ""
    _filepath: Path = ""
    creation_datetime: str = ""
    modification_datetime: str = ""
    fileid: str = ""
    id: int = 0
    signage_id: int = 0
    workspace_id: int = 0

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
    """Interface with database"""
    refkey: str = ""
    title: str = ""
    owner: str = ""
    type: int = 0
    status: int = 0
    source: str = ""
    note: str = ""
    public_note: str = ""
    evidence: int = 0
    evidence_eol: int = 0
    creation_datetime: str = ""
    modification_datetime: str = ""
    signage_id: int = None
    parentID: int = None
    workspace_id: int = 0

@dataclass
class Workspace:
    id: int = 0
    name: str = ""
    reference: str = ""
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
    uid: int
    name: str
    color: str
    icon: str


@dataclass
class SignageStatus:
    uid: int
    name: str
    color: str
    icon: str = ""

@dataclass
class DocumentStatus:
    uid: int
    name: str
    color: str
    icon: str = ""  
    eol: int = 0

@dataclass
class DocumentType:
    type_id: int
    type: str
    color: str
    extenstion: str 
    icon: str = ""
