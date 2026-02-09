import pymupdf
import re
from enum import Enum
from dataclasses import dataclass, InitVar

from qt_theme_manager import theme_icon_manager
from qtpy import QtCore, QtGui, QtWidgets, Slot, Signal
from utilities.utils import timeuuid



class ZoomSelector(QtWidgets.QWidget):

    class ZoomMode(Enum):
        Custom = 0
        FitToWidth = 1
        FitInView = 2

    zoomModeChanged = Signal(ZoomMode)
    zoomFactorChanged = Signal(float)
    zoom_levels = ["Fit Width", "Fit Page", "12%", "25%", "33%", "50%", "66%", "75%", "100%", "125%", "150%", "200%", "400%"]
    max_zoom_factor = 3.0
    min_zoom_factor = 0.5
    zoom_factor_step = 0.25

    def __init__(self, parent=None):
        super().__init__(parent)
        self._zoom_factor: float = 1.0

    def zoomWidgets(self):
        self._selector = QtWidgets.QComboBox()
        self._selector.setEditable(True)
        for zoom_level in self.zoom_levels:
            self._selector.addItem(zoom_level)
        self._selector.currentTextChanged.connect(self.onCurrentTextChanged)
        self._selector.lineEdit().editingFinished.connect(self._editingFinished)
        self.action_zoom_in = QtGui.QAction(theme_icon_manager.get_icon(":zoom-in"), "Zoom In", self)
        self.action_zoom_in.setToolTip("Zoom In")
        self.action_zoom_out = QtGui.QAction(theme_icon_manager.get_icon(":zoom-out"), "Zoom Out", self)
        self.action_zoom_out.setToolTip("Zoom Out")
        return self.action_zoom_in, self.action_zoom_out, self._selector

    @property
    def zoomFactor(self) -> float:
        return self._zoom_factor

    @zoomFactor.setter
    def zoomFactor(self, zoom_factor):
        self._zoom_factor = zoom_factor
        self.setZoomFactor(self._zoom_factor)

    @Slot()
    def zoomIn(self):
        if self.zoomFactor < ZoomSelector.max_zoom_factor:
            self.zoomFactor += self.zoom_factor_step

    @Slot()
    def zoomOut(self):
        if self.zoomFactor > ZoomSelector.min_zoom_factor:
            self.zoomFactor -= self.zoom_factor_step

    @Slot()
    def _editingFinished(self):
        self.onCurrentTextChanged(self._selector.lineEdit().text())

    @Slot(float)
    def setZoomFactor(self, zf):
        zoom_level = int(100 * zf)
        self._selector.setCurrentText(f"{zoom_level}%")

    @Slot()
    def reset(self):
        self._selector.setCurrentIndex(8)  # 100%

    @Slot(str)
    def onCurrentTextChanged(self, text: str):
        if text == "Fit Width":
            self.zoomModeChanged.emit(ZoomSelector.ZoomMode.FitToWidth)
        elif text == "Fit Page":
            self.zoomModeChanged.emit(ZoomSelector.ZoomMode.FitInView)
        else:
            factor = 1.0
            withoutPercent = text.replace('%', '')
            zoomLevel = int(withoutPercent)
            if zoomLevel:
                factor = zoomLevel / 100.0

            self.zoomModeChanged.emit(ZoomSelector.ZoomMode.Custom)
            self.zoomFactorChanged.emit(factor)


class PageNavigator(QtWidgets.QWidget):
    currentPnoChanged = Signal(int)
    currentLocationChanged = Signal(QtCore.QPointF)

    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__()
        self._current_pno: int = None  # pno : page number
        self._current_page_label: str = ""
        self._current_location: QtCore.QPointF = QtCore.QPointF()
        self._page_index:  dict[str, int] = {}

        if parent is not None:
            parent = parent.toolbar()
            icon_size = parent.iconSize()
        else:
            icon_size = QtCore.QSize(24, 24)

        hbox = QtWidgets.QHBoxLayout()
        hbox.setSizeConstraint(QtWidgets.QLayout.SizeConstraint.SetFixedSize)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Minimum)
        self.setLayout(hbox)
        self.setContentsMargins(0, 0, 0, 0)
        hbox.setContentsMargins(5, 0, 5, 0)
        
        self.currentpage_lineedit = QtWidgets.QLineEdit()
        self.currentpage_lineedit.setFixedWidth(40)
        self.currentpage_lineedit.editingFinished.connect(self.onPageLineEditChanged)
        self.pagecount_label = QtWidgets.QLabel()
        # self.pagecount_label.setFixedWidth(40)

        self.previous_btn = QtWidgets.QToolButton(parent)
        self.previous_btn.setIcon(theme_icon_manager.get_icon(':arrow-up-s-line'))
        self.previous_btn.setIconSize(icon_size)
        self.previous_btn.clicked.connect(self.previous)

        self.next_btn = QtWidgets.QToolButton(parent)
        self.next_btn.setIcon(theme_icon_manager.get_icon(':arrow-down-s-line'))
        self.next_btn.setIconSize(icon_size)
        self.next_btn.clicked.connect(self.next)

        hbox.addWidget(self.previous_btn)
        hbox.addWidget(self.next_btn)
        hbox.addWidget(self.currentpage_lineedit)
        hbox.addWidget(self.pagecount_label)

    def setDocument(self, document: pymupdf.Document):
        self._document: pymupdf.Document = document
        self.indexPages()

    def indexPages(self):
        page: pymupdf.Page
        for page in self._document:
            self._page_index.update({page.get_label() : page.number})
    
    def _pageNumberFromLabel(self, label) -> int | None:
        return self._page_index.get(label)

    def _updatePageLineEdit(self):
        page_label = self._getCurrentPageLabel()

        if page_label != "":
            self.currentpage_lineedit.setText(page_label)
        else:
            self.currentpage_lineedit.setText(f"{self.currentPno() + 1}")
        
        self.pagecount_label.setText(f"{self.currentPno() + 1} of {self._document.page_count}")
    
    def document(self):
        return self._document
    
    def setCurrentPno(self, index: int):
        old_index = self._current_pno

        if 0<= index < self._document.page_count:
            self._current_pno = index
            self._updatePageLineEdit()

            if old_index != self._current_pno:
                self.currentPnoChanged.emit(self._current_pno)

    def _getCurrentPageLabel(self) -> str:
        page: pymupdf.Page = self._document[self.currentPno()]
        return page.get_label()

    def currentPno(self) -> int:
        return self._current_pno
    
    def currentPageLabel(self) -> str:
        return self.currentpage_lineedit.text()
    
    def jump(self, page: int, location = QtCore.QPointF()):
        self.setCurrentPno(page)
        self._current_location = location
        self.currentLocationChanged.emit(location)  

    @Slot()
    def onPageLineEditChanged(self):
        p = self.currentpage_lineedit.text()  #  page requested by user
        pno = self._pageNumberFromLabel(p)
 
        if pno is None:
            try:
                pno = int(p) - 1
            except:
                pass
        
        if isinstance(pno, int):
            self.jump(pno)
  
    @Slot()
    def next(self):
        self.jump(self.currentPno() + 1, QtCore.QPointF())

    @Slot()
    def previous(self):
        self.jump(self.currentPno() - 1, QtCore.QPointF())

class Kind(Enum):
    LINK_NONE = 0
    LINK_GOTO = 1
    LINK_URI = 2
    LINK_LAUNCH = 3
    LINK_NAMED = 4
    LINK_GOTOR = 5

class OutlineItem(QtGui.QStandardItem):
    def __init__(self, data: list):
        super().__init__()
        self.lvl: int = data[0]
        self.title: str = data[1]
        self.page: int = int(data[2]) - 1

        try:
            self.details: dict = data[3]
        except IndexError as e:
            # data[2] is 1-based source page number
            pass

        self.setData(self.title, role=QtCore.Qt.ItemDataRole.DisplayRole)

    def getDetails(self):
        return self.details


class OutlineModel(QtGui.QStandardItemModel):
    def __init__(self, parent=None):
        super().__init__(parent)

    def setupModelData(self, outline: list[list]):    
        parents: list[OutlineItem] = []

        prev_child = OutlineItem([0, "", 0, {}])
        parents.append(prev_child)

        for item in outline:
            child = OutlineItem(item)

            if child.lvl == 1:
                parent = self.invisibleRootItem()
            elif child.lvl > prev_child.lvl:
                parents.append(prev_child)
                parent = parents[-1]
            elif child.lvl < prev_child.lvl:
                parents.pop()
                parent = parents[-1]

            parent.appendRow(child)

            prev_child = child

    def setDocument(self, doc: pymupdf.Document):
        self._document = doc
        self.setupModelData(self.getToc())

    def getToc(self):
        toc = self._document.get_toc(simple=False)
        return toc

@dataclass
class GoToLink:
    kind: Kind = Kind.LINK_GOTO
    xref: int = 0
    hotspot: pymupdf.Rect = None
    page_to: int = 0
    to: pymupdf.Point = None
    zoom: float = 1.0
    id: str = ""
    page: InitVar[pymupdf.Page | None] = None
    page_from: int = 0
    label: str = ""

    def __post_init__(self, page: pymupdf.Page):
        self.page_from = page.number
        height_correction = self.hotspot.height * 0.1
        rect = self.hotspot + [0, height_correction, 0, -height_correction]
        label: str = page.get_textbox(rect)
        self.label = label.strip().replace("\n", " ")

@dataclass
class UriLink:
    kind: Kind = Kind.LINK_URI
    xref: int = 0
    hotspot: pymupdf.Rect = None
    uri: str = ""
    id: str = ""
    page: InitVar[pymupdf.Page | None] = None
    page_from: int = 0
    label: str = ""

    def __post_init__(self, page: pymupdf.Page):
        self.page_from = page.number
        height_correction = self.hotspot.height * 0.1
        rect = self.hotspot + [0, height_correction, 0, -height_correction]
        label: str = page.get_textbox(rect)
        self.label = label.strip().replace("\n", " ")

@dataclass
class NamedLink:
    kind: Kind = Kind.LINK_NAMED
    xref: int = 0
    hotspot: pymupdf.Rect = None
    page_to: int = 0
    to: pymupdf.Point = None
    zoom: float = 1.0
    nameddest: str = ""
    id: str = ""
    page: InitVar[pymupdf.Page | None] = None
    page_from: int = 0
    label: str = ""

    def __post_init__(self, page: pymupdf.Page):
        self.page_from = page.number
        height_correction = - self.hotspot.height * 0.1
        rect = self.hotspot + [0, height_correction, 0, -height_correction]
        label: str = page.get_textbox(rect)
        self.label = label.strip().replace("\n", " ")

class LinkFactory:
    def __init__(self):
        self.link_types = {}

        link_type: GoToLink | UriLink | NamedLink
        for link_type in [GoToLink, UriLink, NamedLink]:
            self.link_types[link_type.kind] = link_type

    def createLink(self, link: dict, page: pymupdf.Page) -> GoToLink | UriLink | NamedLink:
        val: GoToLink | UriLink | NamedLink
        # val = self.link_types.get(link['kind'])
        for key, val in self.link_types.items():
            if link['kind'] == key.value:
                return val(*link.values(), page)
            
class LinkItem(QtGui.QStandardItem):
    def __init__(self, link: GoToLink | UriLink | NamedLink):
        super().__init__()
        self._link = link

        self.setData(self._link.label, role=QtCore.Qt.ItemDataRole.DisplayRole)
    
    def link(self):
        return self._link

class LinkModel(QtGui.QStandardItemModel):
    def __init__(self, parent=None):
        super().__init__(parent)

    def setDocument(self, doc: pymupdf.Document):
        self._document = doc
        self.setupModelData()

    def setupModelData(self):    
        parent = self.invisibleRootItem()

        link_factory = LinkFactory()

        for page in self._document:
            for link in page.links([pymupdf.LINK_GOTO, pymupdf.LINK_NAMED]):
                link_object = link_factory.createLink(link, page)

                link_item = LinkItem(link_object)
                parent.appendRow(link_item)

class SearchItem(QtGui.QStandardItem):
    def __init__(self, result: dict):
        super().__init__()

        self.pno = result['pno']
        self.quads = result['quads']
        self.page_label = result['label']

        self.setData(f"index: {self.pno}\tlabel: {self.page_label}\tcount: {len(self.quads)}", role=QtCore.Qt.ItemDataRole.DisplayRole)
    
    def results(self):
        return self.pno, self.quads, self.page_label


class SearchModel(QtGui.QStandardItemModel):
    sigTextFound = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._search_results: dict[int, list] = {}

    def setDocument(self, doc: pymupdf.Document):
        self._document = doc

    def searchFor(self, text: str):
        self.clear()
        self._search_results.clear()
        
        self._found_count = 0

        if text != "":
            root_item = self.invisibleRootItem()
            page: pymupdf.Page
            for page in self._document:
                quads: list = page.search_for(text, quads=True)
                
                if len(quads) > 0:
                    self._found_count = self._found_count + len(quads)
                    page_result = {"pno" : page.number, "label": page.get_label(), "quads" : quads}
                    self._search_results.update({page.number: quads})
                    search_item = SearchItem(page_result)
                    root_item.appendRow(search_item)
        
        self.sigTextFound.emit(f"Hits: {self._found_count}")

    def foundCount(self):
        return self._found_count
    
    def getSearchResults(self):
        return self._search_results
    
class MetaDataWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._metadata = None
        self.metadata_label = QtWidgets.QLabel()
        self.metadata_label.setWordWrap(True)
        self.metadata_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        vbox = QtWidgets.QVBoxLayout()
        self.setLayout(vbox)

        vbox.addWidget(self.metadata_label)

        spacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Policy.Minimum, 
                                       QtWidgets.QSizePolicy.Policy.Expanding)
        vbox.addSpacerItem(spacer)
    
    def setMetadata(self, metadata: dict):
        self._metadata = '\n'.join(f"{key} : {val}" for key, val in metadata.items())
        self.metadata_label.setText(self._metadata.strip())


class TextSelection:
    """Class that holds the selected text as string and its corresponding quad.
        
    Quad represents a four-sided mathematical shape (also called quadrilateral or tetragon) in the plane,
    defined as a sequence of four Point objects.
    Quad is used to display the selected text.
    """
    def __init__(self, s: str = ""):
        self._text: str = s
        self._quads = []

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, s: str):
        s = re.sub(r"(\s\n){3,}", "\n", s.strip())
        self._text = s

    @property
    def quads(self):
        return self._quads

    @quads.setter
    def quads(self, q):
        self._quads = q


class BaseAnnotation:
    """Base class for annotation"""

    def __init__(self, dbid = None):
        self._pno: int = -1
        self._text_selection: TextSelection = None
        self._zfactor = 1.0
        self._uid: int = dbid if dbid else timeuuid()

    @property
    def textSelection(self):
        return self._text_selection
    
    @textSelection.setter
    def textSelection(self, t: TextSelection):
        self._text_selection = t

    @property
    def pno(self):
        return self._pno
    
    @pno.setter
    def pno(self, i: int):
        if isinstance(i, str):
            try:
                i = int(i)
            except:
                i = None
        self._pno = i 

    @property
    def zfactor(self):
        return self._zfactor
    
    @zfactor.setter
    def zfactor(self, z: float):
        self._zfactor = z

    @property
    def uid(self):
        return self._uid
    


class RectItem(QtWidgets.QGraphicsRectItem, BaseAnnotation):
    def __init__(self, dbid = None, parent = None):
        QtWidgets.QGraphicsRectItem.__init__(self, parent)
        BaseAnnotation.__init__(self, dbid)

        self.setFlags(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable | QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)


class LinkBox(QtWidgets.QGraphicsObject):
    sigJumpTo = Signal(int, QtCore.QPointF)
    sigToUri = Signal(str)

    def __init__(self, link: dict, pno: int, zfactor: float, parent=None):
        super(LinkBox, self).__init__(parent)
        self._link = link
        self.pno = pno
        self.zfactor = zfactor
        self.to_page: int|str = link.get("page")
        self.uri = link.get("uri")

        if isinstance(self.to_page, str):
            try:
                self.to_page = int(self.to_page) - 1 # assume the page label is the exact target
            except:
                pass

        rect: pymupdf.Rect = link["from"]
        a0 = QtCore.QPointF(rect.x0,rect.y0) * self.zfactor
        b1 = QtCore.QPointF(rect.x1,rect.y1) * self.zfactor
        self.rect = QtCore.QRectF(a0, b1)
        self.to: QtCore.QPointF = QtCore.QPointF()
        _to: pymupdf.Point = link.get("to")
        if _to:
            self.to.setX(_to.x)
            self.to.setY(_to.y)

        self.setAcceptedMouseButtons(QtCore.Qt.MouseButton.LeftButton)
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)

    def boundingRect(self):
        return self.rect

    def paint(self, painter, option, widget):
        painter.setPen(QtGui.QPen(QtCore.Qt.GlobalColor.cyan))
        painter.drawRect(self.rect)

    def mousePressEvent(self, event):
        if self.to_page is not None:
            self.sigJumpTo.emit(self.to_page, self.to)
        elif self.uri is not None:
            self.sigToUri.emit(self.uri)
        event.accept()
    

