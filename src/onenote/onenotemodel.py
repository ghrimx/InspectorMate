from qtpy import Qt, QtGui
from onenote import onenote_api

class TreeStandardItem(QtGui.QStandardItem):
    def __init__(self, onenote_node: onenote_api.HierarchyNode):
        super().__init__()
        self.name = ""
        self.id = ""

        if not onenote_node is None:
            self._deserialize(onenote_node=onenote_node)
            self.setData(onenote_node.name, role=Qt.ItemDataRole.DisplayRole)

    def _deserialize(self, onenote_node: onenote_api.HierarchyNode):
        self.name = onenote_node.name
        self.id = onenote_node.id

class OnenoteModel(QtGui.QStandardItemModel):
    def __init__(self):
        super().__init__()
        self.connection = None
        self.hierarchy = None

    def initConnection(self):
        self.connection, err = onenote_api.OneNote.connect()
        return self.connection, err

    def get_hierarchy(self):
        xml_hierarchy, err = self.connection.get_hierarchy("",4)
        if err != None:
            return
        return xml_hierarchy

    def buildModel(self):
        self.setHorizontalHeaderLabels(['Name'])

        xml, err = self.connection.get_hierarchy("",4)

        if err != None:
            return

        if isinstance(xml, Exception):
            return xml

        element_tree = onenote_api.ET.fromstring(xml)
        hierarchy = onenote_api.Hierarchy(element_tree)

        for notebook in hierarchy:
            notebook_node = TreeStandardItem(notebook)
            notebook_node.setSelectable(False)
            for section in notebook:
                section_node = TreeStandardItem(section)
                if isinstance(section, onenote_api.SectionGroup):
                    section_node.setSelectable(False)
                    for subsection in section:
                        subsection_node = TreeStandardItem(subsection)
                        section_node.appendRow(subsection_node)
                notebook_node.appendRow(section_node)
            self.appendRow(notebook_node)

    def refresh(self):
        self.clear()
        self.buildModel()
