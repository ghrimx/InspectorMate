import os
import re
import json
import uuid
import fitz
import pandas as pd
from hashlib import sha1
from pathlib import Path
from zipfile import ZipFile
from mammoth import extract_raw_text
from typing import Literal
from base64 import (b64decode, b64encode)

from qtpy import (QtWidgets, QtCore, QtGui)



def walkFolder(path: str | Path) -> set[Path]:
    """
    Scan the directory tree and return a list of file
    Ignore files that starts with a dot or tilt char
    """
    
    file_list = set()

    for entry in Path(path).iterdir():
        if not entry.name.startswith('.') and not entry.name.startswith('~') and entry.is_file():
            file_list.add(Path(entry))
        elif entry.is_dir():
            file_list.update(walkFolder(entry))

    return file_list

def hexuuid():
    return uuid.uuid4().hex

def timeuuid():
    return uuid.uuid1().time

def createFolder(fpath: str):
    _path = Path(fpath)
    if not _path.exists() and _path.parent.exists():
        _path.mkdir()
            
def open_file(filepath: Path|str, pathtype: Literal["file", "folder"] = "file") -> None:
    """Open file/folder using the operating system default app"""
    filepath = Path(filepath)

    if pathtype == "folder" and filepath.is_file():
        filepath = filepath.parent

    if filepath.exists():

        fileCanBeOpened = QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(filepath.as_posix()))

        if not fileCanBeOpened:
            q = QtWidgets.QMessageBox()
            q.setWindowTitle('File cannot be opened')
            q.setIcon(QtWidgets.QMessageBox.Icon.Warning)
            q.setText(f'File {filepath} cannot be opened')
            q.exec()
    else:
        msg = f"The file could not be found at the following path:\n\n{filepath}\n\nIt may have been moved or deleted."
        q = QtWidgets.QMessageBox()
        q.setWindowTitle('File not found')
        q.setIcon(QtWidgets.QMessageBox.Icon.Warning)
        q.setText(msg)
        q.exec()

def increment_refKey(refKey: str|int) -> str:
    """
        Increment a string id
        
        Return a string with suffix numeric part incremented
    """

    current_refKey = str(refKey).strip()

    if current_refKey[-1].isalpha():
        return current_refKey

    for char in current_refKey:
        if char.isnumeric():
            n = int(current_refKey[current_refKey.index(char):])
            n = n+1
            prefix = current_refKey[:current_refKey.index(char)]
            new_refKey = f'{prefix}{n:03d}'
            return new_refKey
        
def find_match(text: str, pattern: str = r"^(([a-zA-Z]{0,3})\d{1,3})") -> str:
    """
    Find pattern in a string and return the match
    
    Note: Mainly used to infer the refKey from the title of a document request and document title
    """
    try:
        match = re.search(pattern, text)
    except Exception as e:
        return ""
    else:
        return match.group(0) if match else ""
    
def findRefKeyFromPath(filepath: str, pattern: str = "", parent_segment: str = "") -> str:
    segments = filepath.replace(parent_segment, "")

    refkey = ""
    if pattern != "":
        # find refKey only in segments up to the evidence folder
        for item in segments.split('/'):
            refkey = find_match(item, pattern)
            if refkey != "":
                break
    
    return refkey

def mergeExcelFiles(files: list, drop_duplicate: str | bool = 'first', outfile: str = "") -> None | pd.DataFrame:
    """
    Merge the first worksheet of several excel files into one.
    """

    if len(files) > 0:
        dfs = []
        for file in files:
            dfs.append(pd.read_excel(file, dtype=str))
            
        df = pd.concat(dfs)

        df.drop_duplicates(keep=drop_duplicate, inplace=True)
        
        if outfile != "":
            try:
                df.to_excel(outfile, index=False)
            except:
                return
        else:
            return df
        
def image2hex(path: str) -> tuple:
    """Convert an image file to base64 string"""
    try:
        with open(path, "rb") as f:
            img_bytes = f.read()
            img_str = b64encode(img_bytes).decode('utf-8')
        return img_str, None
    except Exception as e:
        return None, e

def hex2image(img_str: str) -> tuple:
    """Convert a base64 string to QImage"""
    try:
        img = QtGui.QImage()
        img.loadFromData(b64decode(img_str))
        return img, None
    except Exception as e:
        return None, e
    
def queryFileID(path: str) -> str:
    """Return the windows fileid from the filepath"""
    fileid = os.popen(fr'fsutil file queryfileid "{path}"').read()
    return fileid.split(' ')[-1].strip()

def queryFileNameByID(fileid: str) -> str:
    """Return the path as string from a windows file id"""  
    path = os.popen(fr'fsutil file queryfilenamebyid C:\ {fileid}').read()
    return path.split('?')[-1][1:].strip()

def extractAll(archive: str, dest: str = ""):
    
    err = False

    with ZipFile(archive, "r") as zip:
        try: 
            zip.extractall(dest)
        except:
            err = True

    return err

def unpackZip(zippedFile: str, dest: str = "", max_name_length: int | None = None) -> None | Exception:
    """ Extract a zip file including any nested zip files
        Delete the zip file(s) after extraction
    """
    err = None

    zpath = Path(zippedFile)

    x = re.search("^eudralink", zpath.stem.lower())

    if x is None and dest != "":
        dest = f"{dest}/{zpath.stem}"  

    try:
        with ZipFile(zippedFile, 'r') as zfile:
            try:
                zfile.extractall(path=dest)
            except Exception as err:
                return err
    except Exception as e:
        return e
    
    os.remove(zippedFile)
    for root, dirs, files in os.walk(dest):
        for filename in files:
            if re.search(r'\.zip$', filename):
                fileSpec = os.path.join(root, filename)
                unpackZip(fileSpec, root)
    
    zfile.close()
    return err

def unpackPDF(filepath: str):
    fpath = Path(filepath)

    try:
        doc = fitz.open(fpath.as_posix())
    except Exception as e:
        return e
    else:
        with doc:
            if len(doc.embfile_names()) > 0:
                folderpath = fpath.with_suffix("")
                createFolder(folderpath.as_posix())

                for item in doc.embfile_names():
                    fbytes = doc.embfile_get(item)
                    outpath = folderpath.joinpath(item)

                    try:
                        outfile = open(outpath.as_posix(), "wb")
                    except Exception as e:
                        return e
                    else:
                        with outfile:
                            outfile.write(fbytes)
            else:
                return
        try:
            os.remove(fpath.as_posix())
        except Exception as e:
            return e
        else:
            return True

def writeJson(json_path: str, data: dict) -> tuple[bool, str]:
    """Write JSON file"""
    jsonfile = QtCore.QFile(json_path)
    err = None

    if not jsonfile.open(QtCore.QIODeviceBase.OpenModeFlag.WriteOnly):
        err = f"Opening Error: {IOError(jsonfile.errorString())}"
        return False, err
    
    json_document = QtCore.QJsonDocument.fromVariant(data)

    if json_document.isNull():
        err = f"Failed to map JSON data structure"
        return False, err

    jsonfile.write(json_document.toJson(QtCore.QJsonDocument.JsonFormat.Indented))
    jsonfile.close()

    return True, err

def readJson(json_file: str) -> tuple[dict, str]:
        try:
            with open(json_file, mode='r', encoding='utf8') as file:
                return json.load(file), ""
        except json.JSONDecodeError:
            err = f"Warning: {json_file} is empty or contains invalid JSON."
            return {}, err
        except FileNotFoundError:
                err = f"Error: {json_file} not found."
                return {}, err
        
def contextual_line_id(line: str, context: str = "") -> str:
    normalized = f"{context.strip()}::{line.strip()}"
    return sha1(normalized.encode()).hexdigest()[:10]

def line_id(line: str) -> str:
    normalized = " ".join(line.strip().split())
    return sha1(normalized.encode()).hexdigest()[:10]

def extract_hash_lines(docx_path) -> dict:
    """
    Extract all lines starting with '#' or '! from a Word (.docx) document using mammoth.
    """
    try:
        with open(docx_path, "rb") as docx_file:
            result = extract_raw_text(docx_file)
            text: str = result.value  # The raw text extracted

    except Exception as e:
        return False, str(e)

    lines = {}
    for line in text.splitlines():
        if line.strip().startswith(("#", "!")):
            lid = line_id(line)
            lines[lid] = line.strip()
    return lines

def trim_file(filepath, keep_lines=10000):
    """Trim a text file to keep only the last n lines"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        return e
    
    if len(lines) > keep_lines:
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.writelines(lines[-keep_lines])
        except Exception as e:
            return e
