import os
from pathlib import Path, WindowsPath
import io
import re
import typing
import re
import json
import uuid
import pandas as pd
import fitz
from zipfile import ZipFile

from os import scandir, popen
from pathlib import Path, PureWindowsPath
from base64 import (b64decode, b64encode)

from qtpy import (QtWidgets, QtCore, QtGui)


def walkFolder(path: str | Path) -> set[Path]:
    """
    Scan the directory tree and return a list of file
    Ignore files that starts with a dot
    """
    
    file_list = set()

    for entry in Path(path).iterdir():
        if not entry.name.startswith('.') and entry.is_file():
            file_list.add(WindowsPath(entry))
        elif entry.is_dir():
            file_list.update(walkFolder(entry))

    return file_list

def hexuuid():
    return uuid.uuid4().hex

def createFolder(fpath: str):
    _path = Path(fpath)
    if not _path.exists() and _path.parent.exists():
        _path.mkdir()
            
def open_file(filepath: Path|str) -> None:
    """Open file using the operating system default app"""
    
    filepath = Path(filepath)

    if filepath.exists():

        fileCanBeOpened = QtGui.QDesktopServices.openUrl(QtCore.QUrl(f"file:///{filepath.as_posix()}", QtCore.QUrl.ParsingMode.TolerantMode))

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

def increment_refKey(current_refKey:str) -> str:
    """Increment a string id"""
    for char in current_refKey:
        if char.isnumeric():
            n = int(current_refKey[current_refKey.index(char):])
            n = n+1
            prefix = current_refKey[:current_refKey.index(char)]
            new_refKey = f'{prefix}{n:03d}'
            return new_refKey
        
def find_match(text: str, pattern: str = r"^(([a-zA-Z]{0,3})\d{1,3})") -> str:
    """
    Find pattern in the 10 first char of a string and return the match
    
    Note: Mainly used to infer the refKey from the title of a document request and document title
    """
    try:
        match = re.search(pattern, text[:10])
    except Exception as e:
        return ""
    else:
        return match.group(0) if match else ""

def mergeExcelFiles(files: list, drop_duplicate: str | bool = 'first', outfile: str = "") -> None | pd.DataFrame:
    """
    Merge the first worksheet of several excel files into one.
    """

    if len(files) > 0:
        dfs = []
        for file in files:
            dfs.append(pd.read_excel(file))
            
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

    fileid = popen(fr'fsutil file queryfileid "{path}"').read()
    return fileid[11:].strip()

def queryFileNameByID(fileid: str) -> str:
    """Return the path as string from a windows file id"""
    
    path = popen(fr'fsutil file queryfilenamebyid C:\ {fileid}').read()
    return path[39:].strip()

def extractAll(archive: str, dest: str = ""):
    
    err = False

    with ZipFile(archive, "r") as zip:
        try: 
            zip.extractall(dest)
        except:
            err = True

    return err

def unpackZip(zippedFile: str, dest: str = "") -> None | Exception:
    """ Extract a zip file including any nested zip files
        Delete the zip file(s) after extraction
    """
    err = None

    zpath = Path(zippedFile)

    x = re.search("^eudralink", zpath.stem.lower())

    if x is None and dest != "":
        dest = f"{dest}/{zpath.stem}"  

    with ZipFile(zippedFile, 'r') as zfile:
        try:
            zfile.extractall(path=dest)
        except Exception as err:
            return err
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




