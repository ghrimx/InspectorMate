import logging
import subprocess
from qtpy import QtGui, QtCore, Signal
from onenote import onenote_api as OE
from xml.etree import ElementTree as ET

from utilities.utils import get_safe_temp_path, json
from common import OETag


logger = logging.getLogger(__name__)

class WorkerSignals(QtCore.QObject):
    finished = Signal()
    error = Signal(Exception)
    result = Signal(object)
    progress = Signal(int)


class Worker(QtCore.QRunnable):
    def __init__(self, func: callable):
        super().__init__()
        self.signals = WorkerSignals()
        self.func = func

    def run(self):
        try:
            output = self.func()
        except Exception as e:
            self.signals.error.emit(e)
        else:
            self.signals.result.emit(output)
        finally:
            self.signals.finished.emit()


def getTags(ps_script: str, section_id: str) -> list[OETag]:
    outfile = ""

    if logging.root.level == logging.DEBUG:
        outfile = get_safe_temp_path().joinpath(f"output_{section_id}.json").as_posix()
        logger.debug(f"Output powershell will written to '{outfile}'")

    try:
        process = subprocess.run(
            ["powershell", "-NoProfile",
            "-File", ps_script, 
            "-SectionId", section_id, 
            "-OutputJson", outfile],
            shell=True,
            check=True,
            capture_output=True,
            encoding="utf-8"
            )
    except subprocess.CalledProcessError as e:
        logger.error(f"CalledProcessError={e}")
        logger.error(f"Command: {e.cmd}")
        logger.error(f"Return Code: {e.returncode}")
        logger.error(f"Output: {e.output}")
        logger.error(f"Error Output: {e.stderr}")
        return []
    except Exception as e:
        logger.error(f"Unexepected error occured. Error: {e}")
        return []
        
    try:
        json_text = process.stdout.strip()
    except Exception as e:
        logger.error(f"Cannot read Powershell script output. Error={e}")
        return []
    
    try:
        raw: list[dict] = json.loads(json_text) 
    except Exception as e:
        logger.error(f"Cannot parse data into dict using json. Error={e}")
        return []
    
    # normalize
    if raw is None:
        data: list[dict] = []
    elif isinstance(raw, dict):
        data = [raw]
    elif isinstance(raw, list):
        if not all(isinstance(t, dict) for t in raw):
            logger.error("JSON list contains non-dict items")
            return []
        data = raw
    
    try:
        tags = [OETag.from_dict(t) for t in data]
    except Exception as e:
        logger.error(f"Cannot decrompress dict into dataclass. Error={e}\n\tData:{data}")
        return []
      
    return tags


class TreeStandardItem(QtGui.QStandardItem):
    def __init__(self, onenote_node: OE.HierarchyNode):
        super().__init__()       
        if isinstance(onenote_node, OE.Notebook):
            self.name = onenote_node.nickname if onenote_node.nickname else "Other"
        else:
            self.name = onenote_node.name 
        self.object_id = onenote_node.id
        
        self.setData(self.name, role=QtCore.Qt.ItemDataRole.DisplayRole)


class OnenoteModel(QtGui.QStandardItemModel):
    cache_pages: dict[OE.Page] = {}

    def __init__(self):
        super().__init__()

    def buildModel(self, hierarchy: OE.Hierarchy):
        self.clear()
        self.setHorizontalHeaderLabels(['Name'])
      
        for notebook in hierarchy:
            notebook_node = TreeStandardItem(notebook)
            notebook_node.setSelectable(False)
            for section in notebook:
                section_node = TreeStandardItem(section)
                if isinstance(section, OE.SectionGroup):
                    section_node.setSelectable(False)
                    for subsection in section:
                        subsection_node = TreeStandardItem(subsection)
                        section_node.appendRow(subsection_node)
                notebook_node.appendRow(section_node)
            self.appendRow(notebook_node)

    def getHierarchy(self,
                     on_finished: callable,
                     node_id: str = "",
                     scope: int = 4):
        
        def func() -> OE.Hierarchy:
            ps_script = f"""
                            $OutputEncoding = [Console]::InputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
                            $OneNote = New-Object -ComObject OneNote.Application
                            [xml]$Hierarchy = ""
                            $OneNote.GetHierarchy("{node_id}", {scope}, [ref]$Hierarchy)
                            $Hierarchy.outerXml
                        """
            process = subprocess.run(["powershell", "-Command", ps_script],
                                    check=True,
                                    capture_output=True)
            output = process.stdout.decode("UTF-8").strip()
            xml = ET.fromstring(output)
            hierarchy = OE.Hierarchy(xml) if xml else []
            return hierarchy
        
        pool = QtCore.QThreadPool().globalInstance()
        worker = Worker(func)
        worker.signals.result.connect(self.buildModel)
        worker.signals.finished.connect(on_finished)
        worker.signals.error.connect(lambda e: logger.error(e))

        pool.start(worker)

