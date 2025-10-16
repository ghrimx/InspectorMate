import logging
from qtpy import QtGui, QtCore, QtWidgets, Slot, Signal
from onenote import onenote_api as OE
from pyqtspinner import WaitingSpinner

logger = logging.getLogger(__name__)

class WorkerSignals(QtCore.QObject):
    finished = Signal()
    error = Signal(Exception)
    result = Signal(object)
    progress = Signal(int)


class Worker(QtCore.QRunnable):
    def __init__(self):
        super().__init__()
        self.signals = WorkerSignals()

    def run(self):
        try:
            xml = OE.getHierarchy()
            hierarchy = OE.Hierarchy(xml) if xml else []
        except Exception as e:
            self.signals.error.emit(e)
        else:
            self.signals.result.emit(hierarchy)
        finally:
            self.signals.finished.emit()


class TreeStandardItem(QtGui.QStandardItem):
    def __init__(self, onenote_node: OE.HierarchyNode):
        super().__init__()
        self.name = ""
        self.id = ""

        if not onenote_node is None:
            self._deserialize(onenote_node=onenote_node)
            self.setData(onenote_node.name, role=QtCore.Qt.ItemDataRole.DisplayRole)

    def _deserialize(self, onenote_node: OE.HierarchyNode):
        self.name = onenote_node.name
        self.id = onenote_node.id


class OnenoteModel(QtGui.QStandardItemModel):
    cache_pages: dict[OE.Page] = {}

    def __init__(self):
        super().__init__()

    def buildModel(self, hierarchy):
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

    @classmethod
    def fetch_onenote(cls, section_id: str):
        """Fetch OE:Tag from Microsoft OneNote and return a list of Tag dataclass"""       
        data: dict = OE.executeScript(section_id)

        if data is None:
            return []
        
        tags: list[OE.Tag] = []

        spage: dict
        for spage in data.values():
            page: OE.Page = OE.Page()
            page.name = spage.get("Name")
            page.id = spage.get("ID")
            page.last_modified_time = spage.get("lastModifiedTime")
            page.date_time = spage.get("dateTime")

            if cls.cache_pages.get(page.id) is not None:
                if page.last_modified_time == cls.cache_pages.get(page.id).last_modified_time:
                    continue
            else:
                cls.cache_pages.update({page.id:page})
                       
            item: dict
            for item in spage.get("tags"):
                tag: OE.Tag = OE.Tag()
                tag.object_id = item.get("ID")
                tag.lastModifiedTime = item.get("lastModifiedTime")
                tag.index = item.get("index")
                tag.text = item.get("Cdata")
                tag.type = item.get("Name")
                tag.link = item.get("Link")
                tag.page_name = item.get("PageName")
                tag.creationTime = item.get("creationTime")

                tags.append(tag)

        return tags
    
    #TODO
    @classmethod
    def _fetch_onenote(cls, section_id: str):
        """Fetch OE:Tag from Microsoft OneNote and return a list of Tag dataclass"""       

        section_xml = OE.getHierarchy(section_id)

        if section_xml is None:
            return
                
        section_hierarchy = OE.Hierarchy(section_xml)
        tags: list[OE.Tag] = []

        page: OE.Page
        for page in section_hierarchy:

            if cls.cache_pages.get(page.id) is not None:
                if page.last_modified_time == cls.cache_pages.get(page.id).last_modified_time:
                    continue
            else:
                cls.cache_pages.update({page.id:page})

            page_content = OE.getPageContent(page.id)

            if page_content is None:
                return
            
            tags.extend(OE.get_tags(page, page_content))

        return tags

    def refresh(self):
        self.clear()
        self.buildModel()

class OnenotePickerDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.model = OnenoteModel()
        self.onenote_section = ""
        self.selected_item = None

        self.setWindowTitle("OneNote Picker")
        vbox = QtWidgets.QVBoxLayout(self)

        buttons = (QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox = QtWidgets.QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.oe_treeview = QtWidgets.QTreeView()
        self.oe_treeview.resizeColumnToContents(0)
        self.oe_treeview.setModel(self.model)
        
        self.oe_treeview.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

        vbox.addWidget(self.oe_treeview)
        vbox.addWidget(self.buttonBox)
        self.spinner = WaitingSpinner(self.oe_treeview)

    def on_hierarchy_ready(self, hierarchy):
        self.model.buildModel(hierarchy)
        self.oe_treeview.selectionModel().selectionChanged.connect(self.onRowSelected)

    def connect(self):
        self.spinner.start()
        QtWidgets.QApplication.processEvents()
        
        worker = Worker()
        pool = QtCore.QThreadPool().globalInstance()
        worker.signals.result.connect(self.on_hierarchy_ready)
        worker.signals.error.connect(lambda e: logger.error(e))
        worker.signals.finished.connect(self.spinner.stop)
        pool.start(worker)
      
    @Slot()
    def onRowSelected(self):
        selected_index = self.oe_treeview.selectionModel().currentIndex()
        self.selected_item = self.model.itemFromIndex(selected_index)

    def accept(self):
        if self.selected_item is not None:
            self.onenote_section = f'{{"section_name":"{self.selected_item.name}", "section_id":"{self.selected_item.id}"}}'
        super().accept()

    def oeSection(self):
        return self.onenote_section
