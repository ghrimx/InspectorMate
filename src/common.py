import json
from enum import Enum
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, fields
from typing import TypeVar, Generic, Dict, Optional, Iterable, Tuple


@dataclass
class DatabaseField:
    name: str
    index: int
    visible: bool


@dataclass
class Workspace:
    id: int = 0
    name: str = ""
    reference: str = ""
    rootpath: str = ""
    evidence_path: str = ""
    notebook_path: str = ""
    state: bool = True


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
        # else:
        #     p = Path(queryFileNameByID(self.fileid))
        #     self._filepath = p
        #     return p
    
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

    def __post_init__(self):
        if self.creation_datetime == "":
            self.creation_datetime = datetime.now().strftime("%Y-%m-%d")


@dataclass
class OETag:
    TypeName: str
    Text: str
    Link: str  
    ID: str
    PageID: str
    PageName: str
    CreationTime: str
    LastModifiedTime: str
    TypeIndex:  int
    extra: dict = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, d: dict):
        known = {f.name for f in fields(cls) if f.name != "extra"}
        known_data = {k: v for k, v in d.items() if k in known}
        extra = {k: v for k, v in d.items() if k not in known}

        return cls(**known_data, extra=extra)


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


class ConnectorType(Enum):
    ONENOTE = 'onenote'
    DOCX = 'docx'


@dataclass
class Connector:
    uid: int = -1
    type: str = ""
    name: str= ""
    value: str = ""
    last_modified: str = ""

    @classmethod
    def from_json(cls, value):
        try:
            return json.loads(value)
        except:
            return

# For Excel QRunnable
@dataclass
class UpdateItem:
    signage_id: int
    title: str


K_int = TypeVar("K_int", bound=int)
K_str = TypeVar("K_str", bound=str)
V = TypeVar("V")

class Cache(Generic[K_int, K_str, V]):
    """Two-way cache mapping between integer keys and string aliases.

    Features:
    - Retrieve by int or str key.
    - Prevent duplicate key registration.
    - Supports reverse lookup (int to str, str to int).
    - Fully type-safe for IDE completion.
    """

    def __init__(self):
        self._int_to_value: Dict[K_int, V] = {}
        self._str_to_int: Dict[K_str, K_int] = {}

    # -----------------------------
    # Core API
    # -----------------------------
    def add(self, int_key: K_int, str_key: K_str, value: V) -> None:
        """Add a new entry. Raises ValueError if key already exists."""
        if int_key in self._int_to_value:
            raise ValueError(f"Integer key {int_key!r} already exists.")
        if str_key in self._str_to_int:
            raise ValueError(f"String key {str_key!r} already exists.")

        self._int_to_value[int_key] = value
        self._str_to_int[str_key] = int_key

    def get(self, key: K_int | K_str, default: Optional[V] = None) -> Optional[V]:
        """Retrieve value by either int or str key."""
        if isinstance(key, int):
            return self._int_to_value.get(key, default)
        elif isinstance(key, str):
            int_key = self._str_to_int.get(key)
            return self._int_to_value.get(int_key, default) if int_key is not None else default
        raise TypeError(f"Unsupported key type: {type(key).__name__}")

    def remove(self, key: K_int | K_str) -> bool:
        """Remove entry by int or str key."""
        if isinstance(key, str):
            int_key = self._str_to_int.pop(key, None)
            if int_key is not None:
                self._int_to_value.pop(int_key, None)
                return True
        elif isinstance(key, int):
            if key in self._int_to_value:
                self._int_to_value.pop(key)
                for s, i in list(self._str_to_int.items()):
                    if i == key:
                        del self._str_to_int[s]
                        break
                return True
        return False

    def clear(self) -> None:
        """Clear the entire cache."""
        self._int_to_value.clear()
        self._str_to_int.clear()

    # -----------------------------
    # Reverse lookups
    # -----------------------------
    def get_str_key(self, int_key: K_int) -> Optional[K_str]:
        """Get the string alias corresponding to an integer key."""
        for s, i in self._str_to_int.items():
            if i == int_key:
                return s
        return None

    def get_int_key(self, str_key: K_str) -> Optional[K_int]:
        """Get the integer key corresponding to a string alias."""
        return self._str_to_int.get(str_key)

    # -----------------------------
    # Dict-like and view methods
    # -----------------------------
    def keys(self) -> Iterable[K_int]:
        return self._int_to_value.keys()

    def strkeys(self) -> Iterable[K_str]:
        return self._str_to_int.keys()

    def intkeys(self) -> Iterable[K_int]:
        return self._str_to_int.values()

    def items(self) -> Iterable[Tuple[K_int, V]]:
        return self._int_to_value.items()

    def values(self) -> Iterable[V]:
        return self._int_to_value.values()

    def __len__(self) -> int:
        return len(self._int_to_value)

    def __contains__(self, key: K_int | K_str) -> bool:
        if isinstance(key, int):
            return key in self._int_to_value
        if isinstance(key, str):
            return key in self._str_to_int
        return False

    def __getitem__(self, key: K_int | K_str) -> V:
        result = self.get(key)
        if result is None:
            raise KeyError(key)
        return result

    def __setitem__(self, key: K_int | K_str, value: V) -> None:
        if isinstance(key, int):
            if key not in self._int_to_value:
                raise KeyError(f"Integer key {key!r} not found. Use add() to insert new items.")
            self._int_to_value[key] = value
        else:
            raise ValueError("Cannot set value with string key alone (requires both keys).")

    def __repr__(self) -> str:
        return f"<Cache size={len(self)}>"

