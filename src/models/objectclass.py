import json
from pathlib import Path
from dataclasses import dataclass, field

@dataclass
class User:
    username: str | None = None
    name: str | None = None



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

    def get_onenote_id(self) -> str|None:
        try:
            _onenote: dict = json.loads(self.onenote_section)
            return _onenote["section_id"]
        except:
            return
    
    @classmethod
    def dump_onenote_section(self, onenote_section: dict) -> str|None:
        try:
            return json.dumps(onenote_section)
        except:
            return
        
@dataclass
class DatabaseField:
    name: str
    index: int
    visible: bool

@dataclass
class Signage:
    refKey: str = ""
    title: str = ""
    status: str | int = ""
    type: str | int = ""
    owner: str = ""
    note: str = ""
    public_note: str = ""
    workspace_id: str = ""
    uid: str = ""
    link: str = ""


@dataclass
class OneNoteSection:
    id: str
    name: str