import pymupdf
import logging
import json

from enum import Enum

from qtpy import QtWidgets, QtGui, QtCore, Signal, Slot
from documentviewer.viewerwidget import ViewerWidget

from PyMuPDF4QT.QtPymuPdf import (OutlineModel, OutlineItem, PageNavigator, 
                                  ZoomSelector, SearchModel, SearchItem, MetaDataWidget, 
                                  TextSelection, RectItem, LinkBox)
from PyMuPDF4QT.annotation import AnnotationModel, AnnotationPane
from utilities.utils import copy_file_link_to_clipboard
from qt_theme_manager import theme_icon_manager


SUPPORTED_FORMART = (".pdf", ".epub")

logger = logging.getLogger(__name__)


class MouseInteraction:

    class InteractionType(Enum):
        NONE = 0
        TEXTSELECTION = 1
        SCREENCAPTURE = 2
        HIGHLIGHT = 3
        WRITESIMPLETEXT = 4 

    def __init__(self, i: InteractionType = InteractionType.NONE):
        self._interaction = i

    @property
    def interaction(self):
        return self._interaction

    @interaction.setter
    def interaction(self, i: InteractionType):
        self._interaction = i


class PdfView(QtWidgets.QGraphicsView):
    sig_mouse_position = Signal(QtCore.QPointF)
    sig_annotation_added = Signal(object)
    sigRemoveAnnotation = Signal('qint64')
    sig_annotation_selected = Signal(object)

    def __init__(self, parent=None):
        super(PdfView, self).__init__(parent)
        screen = self.window().windowHandle().screen()
        self.dpr = screen.devicePixelRatio() if screen else 1.0

        # Mouse coordinate
        self.mouse_interaction = MouseInteraction()
        self.a0 = QtCore.QPointF()
        self.b1 = QtCore.QPointF()

        self.graphic_items = {} # dict of QGraphicItem > {pno:{id(rectItem):rectItem}}
        self.link_boxes = {} # {pno:[RectItems]}
        self._current_graphic_item = None

        self.setMouseTracking(True)
        self.setDragMode(QtWidgets.QGraphicsView.DragMode.RubberBandDrag)
    
        self._page_navigator = PageNavigator(parent)
        self._zoom_selector = ZoomSelector(parent)

        self.page_count: int = 0
        self.page_dlist: pymupdf.DisplayList = None
 
        self.annotations = {} # document native annotations

        self.doc_scene = QtWidgets.QGraphicsScene(self)
        self.setScene(self.doc_scene)

        self.page_pixmap_item = self.createPixmapItem()
        self.doc_scene.addItem(self.page_pixmap_item)

        self.setBackgroundBrush(QtGui.QColor(242, 242, 242))
        self.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QtGui.QPainter.RenderHint.TextAntialiasing)

        self.doc_scene.setSceneRect(self.page_pixmap_item.boundingRect()) 
        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter | QtCore.Qt.AlignmentFlag.AlignHCenter)
    
    def showEvent(self, event: QtGui.QShowEvent | None) -> None:
        return super().showEvent(event)
    
    def setDocument(self, doc: pymupdf.Document):
        self.fitzdoc: pymupdf.Document = doc
        self._page_navigator.setDocument(self.fitzdoc)
        self.page_count = len(self.fitzdoc)
        self.dlist: list[pymupdf.DisplayList] = [None] * self.page_count
        self._page_navigator.setCurrentPno(0)

    def pageNavigator(self) -> PageNavigator:
        return self._page_navigator
    
    def zoomSelector(self) -> ZoomSelector:
        return self._zoom_selector
    
    @Slot(ZoomSelector.ZoomMode)
    def setZoomMode(self, mode: ZoomSelector.ZoomMode):
        view_width = self.width()
        view_height = self.height()

        content_margins = self.contentsMargins()

        page_width = self.dlist[self.pageNavigator().currentPno()].rect.width
        page_height = self.dlist[self.pageNavigator().currentPno()].rect.height
        
        if mode == ZoomSelector.ZoomMode.FitToWidth:
            self._zoom_selector.zoomFactor = (view_width - content_margins.left() - content_margins.right() - 20) / page_width
            self.renderPage(self.pageNavigator().currentPno())
        elif mode == ZoomSelector.ZoomMode.FitInView:
            self._zoom_selector.zoomFactor = (view_height - content_margins.bottom() - content_margins.top() - 20) / page_height
            self.renderPage(self.pageNavigator().currentPno())
    
    @Slot()
    def zoomIn(self):
        self._zoom_selector.zoomIn()
        self.renderPage(self.pageNavigator().currentPno())
    
    @Slot()
    def zoomOut(self):
        self._zoom_selector.zoomOut()
        self.renderPage(self.pageNavigator().currentPno())

    def toQPixmap(self, fitzpix:pymupdf.Pixmap) -> QtGui.QPixmap:
        """Convert pymupdf.Pixmap to QtGui.QPixmap"""
        fitzpix_bytes = fitzpix.tobytes()
        pixmap = QtGui.QPixmap()
        r = pixmap.loadFromData(fitzpix_bytes)
        pixmap.setDevicePixelRatio(self.dpr)
        if not r:
            logger.error(f"Cannot load pixmap from data")
        return pixmap
    
    def createPixmapItem(self, pixmap=None, position=None, matrix=None) -> QtWidgets.QGraphicsPixmapItem:
        item = QtWidgets.QGraphicsPixmapItem(pixmap)

        if position is not None:
            item.setPos(position)
        if matrix is not None:
            item.setTransform(matrix)
        return item
    
    def createFitzpix(self, page_dlist: pymupdf.DisplayList, zoom_factor=1) -> pymupdf.Pixmap:
        """Create pymupdf.Pixmap applying zoom factor"""
        zf = zoom_factor * self.dpr
        mat = pymupdf.Matrix(zf, zf)  # zoom matrix
        fitzpix: pymupdf.Pixmap = page_dlist.get_pixmap(alpha=0, matrix=mat)
        return fitzpix
    
    def setAnnotations(self, annotations: dict):
        self.annotations.clear()
        self.annotations.update(annotations)

    def renderLinks(self, pno: int):
        boxes: list = self.link_boxes.get(pno)

        if boxes is None:
            boxes: list = []
            page = self.fitzdoc[pno]
            # for link in page.links([pymupdf.LINK_GOTO, pymupdf.LINK_NAMED]):
            for link in page.links():
                linkbox = LinkBox(link, pno, self.zoomSelector().zoomFactor)
                linkbox.sigJumpTo.connect(self.onLinkClicked)
                linkbox.sigToUri.connect(self.onUriClicked)
                self.doc_scene.addItem(linkbox)
                boxes.append(linkbox)
            self.link_boxes[pno] = boxes
    
    def renderPage(self, pno: int = 0):
        """
            Render the image
            Convert the pymupdf Displaylist to QPixmap
        """
        page_dlist: pymupdf.DisplayList = self.dlist[pno]

        if not page_dlist :  # create if not yet there
            fitzpage = self.fitzdoc.load_page(pno)
            self.dlist[pno] = fitzpage.get_displaylist()
            page_dlist = self.dlist[pno]

        # Remove annotations
        page = self.fitzdoc.load_page(pno)
        self.fitzdoc.xref_set_key(page.xref, "Annots", "null")    

        add_annotations = self.annotations.get(pno)
        if add_annotations is not None:
            quads: pymupdf.Quad
            for quads in add_annotations:
                page.add_highlight_annot(quads)
            page_dlist = page.get_displaylist()

        fitzpix = self.createFitzpix(page_dlist, self._zoom_selector.zoomFactor)
        pixmap = self.toQPixmap(fitzpix)
        
        self.page_pixmap_item.setPixmap(pixmap)

        self.renderLinks(pno)

        # Show/Hide/Transform graphic annotation items
        items = self.doc_scene.items()
        for item in items:
            if isinstance(item, QtWidgets.QGraphicsPixmapItem):
                continue
            elif isinstance(item, QtWidgets.QGraphicsLineItem):
                continue
            elif item.pno == pno:
                item.setVisible(True)
                item.setScale(self.zoomSelector().zoomFactor / item.zfactor)
            else:
                item.setVisible(False)
                
        self.centerOn(self.page_pixmap_item)
        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignCenter)
        self.doc_scene.setSceneRect(self.page_pixmap_item.boundingRect()) 
        self.viewport().update()

    @Slot()
    def setRotation(self, degree):
        """Rotate current page"""
        self.rotate(degree)

    def next(self):
        self.pageNavigator().jump(self.pageNavigator().currentPno() + 1)

    def previous(self):
        self.pageNavigator().jump(self.pageNavigator().currentPno() - 1)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.key() == QtCore.Qt.Key.Key_Left:
            self.previous()
        elif event.key() == QtCore.Qt.Key.Key_Right:
            self.next()

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        #Zoom : CTRL + wheel
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.KeyboardModifier.ControlModifier:
            anchor = self.transformationAnchor()
            self.setTransformationAnchor(QtWidgets.QGraphicsView.ViewportAnchor.AnchorUnderMouse)
            if event.angleDelta().y() > 0:
                self._zoom_selector.zoomIn()
            else:
                self._zoom_selector.zoomOut()
            while self._zoom_selector.zoomFactor >= self._zoom_selector.max_zoom_factor:
                self._zoom_selector.zoomOut()
            while self._zoom_selector.zoomFactor < self._zoom_selector.min_zoom_factor:
                self._zoom_selector.zoomIn()
            self.renderPage(self.pageNavigator().currentPno())
            self.setTransformationAnchor(anchor)
        else:
            # Scroll Down
            if event.angleDelta().y() < 0 and self.verticalScrollBar().sliderPosition() == self.verticalScrollBar().maximum():
                if self.pageNavigator().currentPno() < self.fitzdoc.page_count - 1:
                    location = QtCore.QPointF()
                    location.setY(self.verticalScrollBar().minimum())
                    self.pageNavigator().jump(self.pageNavigator().currentPno() + 1, location)
            # Scroll Up
            elif  event.angleDelta().y() > 0 and self.verticalScrollBar().sliderPosition() == self.verticalScrollBar().minimum():
                if self.pageNavigator().currentPno() > 0:
                    location = QtCore.QPointF()
                    location.setY(self.verticalScrollBar().maximum())
                    self.pageNavigator().jump(self.pageNavigator().currentPno() - 1, location)
            else:
                self.verticalScrollBar().setValue(self.verticalScrollBar().sliderPosition() - event.angleDelta().y())

    def getPage(self) -> pymupdf.Page:
        """Return Pymupdf current Page"""
        return self.fitzdoc.load_page(self.pageNavigator().currentPno())

    #TODO
    def loadGraphicItems(self, cache: list):
        if len(cache) == 0:
            return 
        
        annot: dict
        for annot in cache:
            rect = RectItem(annot.get("uid"))
            rect.setPen(QtGui.QPen(QtCore.Qt.GlobalColor.red))
            rect.textSelection = annot.get("text")

            try:
                position: dict = json.loads(annot.get("position"))
            except:
                continue

            coord: list = position.get("rect")
            r = QtCore.QRectF(coord[0], coord[1], coord[2], coord[3])
            rect.setRect(r)
            rect.pno = position.get("pageIndex")
            rect.zfactor = position.get("zfactor")
            if rect.pno > self.pageNavigator().currentPno():
                rect.setVisible(False)
            self.doc_scene.addItem(rect)

    def getGraphicItems(self) -> dict:
        return self.graphic_items
    
    def getTextFromSelection(self, pno: int, a0: QtCore.QPointF, b1: QtCore.QPointF) -> TextSelection:
        """Return TextSelection from selection points"""
        page: pymupdf.Page = self.fitzdoc.load_page(pno)
        zf = self._zoom_selector.zoomFactor
        rect = pymupdf.Rect(a0.x() / zf, a0.y() / zf, b1.x() / zf, b1.y() / zf)
        text_selection = TextSelection()
        text_selection.text = page.get_textbox(rect)
        return text_selection
    
    @Slot(QtCore.QPointF)
    def scrollTo(self, location: QtCore.QPointF | int):
        if isinstance(location, QtCore.QPointF):
            location = location.toPoint().y()
        self.verticalScrollBar().setValue(location)

    @Slot(int, QtCore.QPointF)
    def onLinkClicked(self, pno: int, to: QtCore.QPointF):
        self._page_navigator.jump(page=pno, location=to)

    #TODO
    @Slot(str)
    def onUriClicked(self, uri: str):
        if "file://" in uri:
            pass
        elif "http" in uri:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl(uri))

    def mousePressEvent(self, event):
        self.a0 = self.mapToScene(event.position().toPoint())
        self.startMouseInteraction()
        self.update()
        return super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        self.cursor_position = event.position()

        if self._current_graphic_item is not None:
            r = QtCore.QRectF(self.a0, self.mapToScene(event.position().toPoint())).normalized()
            self._current_graphic_item.setRect(r)
            self.update()
        self.sig_mouse_position.emit(self.mapToScene(event.position().toPoint()))
        return super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        self.b1: QtCore.QPointF = self.mapToScene(self.cursor_position.toPoint())
        
        if self._current_graphic_item is not None:
            self.endMouseInteraction()
            self.update()
        return super().mouseReleaseEvent(event)
    
    def startMouseInteraction(self):
        if self.mouse_interaction.interaction == MouseInteraction.InteractionType.TEXTSELECTION:
            self._current_graphic_item = RectItem()
            self._current_graphic_item.setPen(QtGui.QPen(QtCore.Qt.GlobalColor.red))
            r = QtCore.QRectF(self.a0, self.a0)
            self._current_graphic_item.setRect(r)
            self._current_graphic_item.pno = self.pageNavigator().currentPno()
            self._current_graphic_item.zfactor = self.zoomSelector().zoomFactor
            self.doc_scene.addItem(self._current_graphic_item)

    def endMouseInteraction(self):
        self._current_graphic_item.textSelection = self.getTextFromSelection(self.pageNavigator().currentPno(), self.a0, self.b1)

        # Put text into clipboard
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(self._current_graphic_item.textSelection.text)
        
        self.sig_annotation_added.emit(self._current_graphic_item)

        self._current_graphic_item = None
        self.doc_scene.clearSelection()

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if event == QtGui.QKeySequence.StandardKey.Delete:
            items = self.doc_scene.selectedItems()
            item: RectItem
            for item in items:
                if isinstance(item, RectItem):
                    result = self.removeAnnotation(item.uid)
                    if result:
                        self.sigRemoveAnnotation.emit(item.uid)

    @Slot('qint64')
    def removeAnnotation(self, uid: int) -> bool:
        items = self.doc_scene.items()
        for item in items:
            if isinstance(item, RectItem):
                if item.uid == uid:
                    try:
                        self.doc_scene.removeItem(item)
                    except Exception as e:
                        logger.exception(e)
                        return False  
        return True


class PdfViewer(ViewerWidget):
    def __init__(self, parent=None):
        super(PdfViewer, self).__init__(parent)
    
    @classmethod
    def supportedFormats(cls) -> list[str]:
        return SUPPORTED_FORMART

    def loadDocument(self, filepath: str = ""):
        if filepath == "":
            return
        
        try:
            self.fitzdoc: pymupdf.Document = pymupdf.Document(filepath)
        except Exception as e:
            logger.error(f"Cannot load document - Error: {e}")
            return
        
        try:
            self.pdfview.setDocument(self.fitzdoc)
        except Exception as e:
            logger.error(f"Cannot process document - Error: {e}")
            return

        self.outline_model.setDocument(self.fitzdoc)
        self.search_model.setDocument(self.fitzdoc)
        self.metadata_tab.setMetadata(self.fitzdoc.metadata)
        self.annotation_model.setFilter(f"document_id={self.document.id}")
        if self.annotation_model.initCache(self.document.id):
            self.pdfview.loadGraphicItems(self.annotation_model.cache())

    def initViewer(self):
        self.pdfview = PdfView(self)
        self.outline_model = OutlineModel()
        self.search_model = SearchModel()
        self.annotation_model = AnnotationModel()

        # Toolbar button
        self.mouse_action_group = QtGui.QActionGroup(self)
        self.mouse_action_group.setExclusionPolicy(QtGui.QActionGroup.ExclusionPolicy.ExclusiveOptional)
        self.mouse_action_group.triggered.connect(self.triggerMouseAction)

        # Text Selector
        self.text_selector = QtGui.QAction(theme_icon_manager.get_icon(':text-block'), "Text Selection", self)
        self.text_selector.setCheckable(True)
        self.text_selector.setShortcut(QtGui.QKeySequence("ctrl+alt+t"))
        self.text_selector.triggered.connect(self.triggerMouseAction)

        # Snipping tool
        self.capture_area.triggered.connect(lambda: self.capture(self.citation()))
        
        # MarkPen
        self.mark_pen = QtGui.QAction(theme_icon_manager.get_icon(':mark_pen'), "Mark Text", self)
        self.mark_pen.setCheckable(True)
        self.mark_pen.triggered.connect(lambda: self.triggerMouseAction)
        
        self.mouse_action_group.addAction(self.text_selector)
        self.mouse_action_group.addAction(self.capture_area)
        self.mouse_action_group.addAction(self.mark_pen)

        self.page_navigator = self.pdfview.pageNavigator()
        self.zoom_selector = self.pdfview.zoomSelector()
        
        # Zoom
        self.action_fitwidth = QtGui.QAction(theme_icon_manager.get_icon(':expand-width-fill'), "Fit Width", self)
        self.action_fitwidth.triggered.connect(self.fitwidth)

        self.action_fitheight = QtGui.QAction(theme_icon_manager.get_icon(':expand-height-line'), "Fit Height", self)
        self.action_fitheight.triggered.connect(self.fitheight)
        
        # Zoom In/Out
        zoom_in, zoom_out, _ = self.pdfview.zoomSelector().zoomWidgets()
        zoom_in.triggered.connect(self.pdfview.zoomIn)
        zoom_out.triggered.connect(self.pdfview.zoomOut)

        # Rotate
        self.rotate_anticlockwise = QtGui.QAction(theme_icon_manager.get_icon(":anticlockwise"), "Rotate left", self)
        self.rotate_anticlockwise.setToolTip("Rotate anticlockwise")
        self.rotate_anticlockwise.triggered.connect(lambda: self.pdfview.setRotation(-90))

        self.rotate_clockwise = QtGui.QAction(theme_icon_manager.get_icon(":clockwise"), "Rotate right", self)
        self.rotate_clockwise.setToolTip("Rotate clockwise")
        self.rotate_clockwise.triggered.connect(lambda: self.pdfview.setRotation(90))

        # Citation
        self.action_cite.triggered.connect(self.citationToClipboard)

        # Add Action/Widget to toolbar
        self._toolbar.insertWidget(self.toolbarFreeSpace(), self.page_navigator)
        self._toolbar.insertSeparator(self.toolbarFreeSpace())
        self._toolbar.insertAction(self.toolbarFreeSpace(), self.action_fitwidth)
        self._toolbar.insertAction(self.toolbarFreeSpace(), self.action_fitheight)
        self._toolbar.insertAction(self.toolbarFreeSpace(), zoom_in)
        self._toolbar.insertAction(self.toolbarFreeSpace(), zoom_out)
        self._toolbar.insertSeparator(self.toolbarFreeSpace())
        self._toolbar.insertAction(self.toolbarFreeSpace(), self.rotate_anticlockwise)
        self._toolbar.insertAction(self.toolbarFreeSpace(), self.rotate_clockwise)
        self._toolbar.insertSeparator(self.toolbarFreeSpace())
        self._toolbar.insertAction(self._toolbar_spacer, self.action_create_child_signage)
        self._toolbar.insertAction(self.toolbarFreeSpace(), self.action_cite)
        self._toolbar.insertAction(self.toolbarFreeSpace(), self.text_selector)
        self._toolbar.insertAction(self.toolbarFreeSpace(), self.capture_area)
        # self._toolbar.insertAction(self.toolbarFreeSpace(), self.mark_pen) #TODO

        # Outline Tab
        self.outline_tab = QtWidgets.QTreeView(self.left_pane)
        self.outline_tab.setModel(self.outline_model)
        self.outline_tab.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.outline_tab.setHeaderHidden(True)
        self.outline_tab.selectionModel().selectionChanged.connect(self.onOutlineSelected)
        self.left_pane.addTab(self.outline_tab, "Outline")

        # Search Tab
        search_tab = QtWidgets.QWidget(self.left_pane)
        search_tab_layout = QtWidgets.QVBoxLayout()
        search_tab.setLayout(search_tab_layout)

        self.search_LineEdit = QtWidgets.QLineEdit()
        self.search_LineEdit.setPlaceholderText("Find in document")
        self.search_LineEdit.editingFinished.connect(self.searchFor)
        
        self.search_count = QtWidgets.QLabel("Hits: ")

        self.search_results = QtWidgets.QTreeView(self.left_pane)
        self.search_results.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)  # Make ReadOnly
        self.search_results.setModel(self.search_model)
        self.search_results.setHeaderHidden(True)
        self.search_results.setRootIsDecorated(False)
        self.search_results.selectionModel().selectionChanged.connect(self.onSearchResultSelected)

        search_tab_layout.addWidget(self.search_LineEdit)
        search_tab_layout.addWidget(self.search_count)
        search_tab_layout.addWidget(self.search_results)
        self.left_pane.addTab(search_tab, "Search")

        # Metadata
        self.mouse_position = QtWidgets.QLabel()         # for debug
        self.mouse_position.setEnabled(False)
        self.pdfview.sig_mouse_position.connect(self.updateMousePositionLabel)
        self.metadata_tab = MetaDataWidget(self.left_pane)
        self.metadata_tab.layout().insertWidget(1, self.mouse_position)
        self.left_pane.addTab(self.metadata_tab, "Metadata")

        # Annotations pane
        self.annotation_pane = AnnotationPane(self.annotation_model)
        self.left_pane.addTab(self.annotation_pane, "Annotations")

        # Splitter
        self.splitter.replaceWidget(1, self.pdfview)
           
        # Signals
        self.page_navigator.currentPnoChanged.connect(self.pdfview.renderPage) # Render page at init time
        self.page_navigator.currentLocationChanged.connect(self.pdfview.scrollTo)
        self.search_model.sigTextFound.connect(self.onSearchFound)
        self.pdfview.sig_annotation_added.connect(self.onAnnotationAdded)
        self.pdfview.sigRemoveAnnotation.connect(self.annotation_model.removeById)
        self.annotation_pane.clicked.connect(self.onAnnotationListClicked)
        self.annotation_pane.sigRemoveAnnotation.connect(self.pdfview.removeAnnotation)

        self.installEventFilter(self.pdfview)

    # for debug
    @Slot(QtCore.QPointF)
    def updateMousePositionLabel(self, pos):
        self.mouse_position.setText(f"x: {pos.x()}, y: {pos.y()}")

    @Slot()
    def triggerMouseAction(self):
        if self.text_selector.isChecked():
            self.pdfview.mouse_interaction.interaction = MouseInteraction.InteractionType.TEXTSELECTION
        elif self.capture_area.isChecked():
            self.pdfview.mouse_interaction.interaction = MouseInteraction.InteractionType.SCREENCAPTURE
        elif self.mark_pen.isChecked():
            self.pdfview.mouse_interaction.interaction = MouseInteraction.InteractionType.HIGHLIGHT
        else:
            self.pdfview.mouse_interaction.interaction = MouseInteraction.InteractionType.NONE

    @Slot(str)
    def onSearchFound(self, count: str):
        self.search_count.setText(count)
        self.pdfview.setAnnotations(self.search_model.getSearchResults())
        self.pdfview.renderPage(self.page_navigator.currentPno())
        self.search_results.resizeColumnToContents(0)

    def pdfViewSize(self) -> QtCore.QSize:
        idx = self.splitter.indexOf(self.pdfview)
        return self.splitter.widget(idx).size()

    def toolbar(self):
        return self._toolbar

    def showEvent(self, event):
        super().showEvent(event)

    def eventFilter(self, object: QtCore.QObject, event: QtCore.QEvent):
        if object == self and event.type() == QtCore.QEvent.Type.Wheel:
            return True
        return False
    
    @Slot()
    def searchFor(self):
        self.search_model.searchFor(self.search_LineEdit.text())
    
    @Slot()
    def fitwidth(self):
        self.pdfview.setZoomMode(ZoomSelector.ZoomMode.FitToWidth)

    @Slot()
    def fitheight(self):
        self.pdfview.setZoomMode(ZoomSelector.ZoomMode.FitInView)
    
    @Slot(QtCore.QItemSelection, QtCore.QItemSelection)
    def onOutlineSelected(self, selected: QtCore.QItemSelection, deseleted: QtCore.QItemSelection):
        for idx in selected.indexes():
            item: OutlineItem = self.outline_tab.model().itemFromIndex(idx)
            if item.details is not None:
                self.page_navigator.jump(item.page)

    @Slot(QtCore.QItemSelection, QtCore.QItemSelection)
    def onSearchResultSelected(self, selected: QtCore.QItemSelection, deseleted: QtCore.QItemSelection):
        for idx in selected.indexes():
            item: SearchItem = self.search_results.model().itemFromIndex(idx)
            page, quads, page_label = item.results()
            self.page_navigator.jump(page)

    @Slot()
    def citation(self) -> str:
        refkey = "refkey=" + self.refKey.text() if self.refKey.text() != "" else None
        page = f"p. {self.page_navigator.currentPageLabel()}"
        title = f'"{self.title.toPlainText()}"'
        citation = "; ".join(x for x in [refkey, title, self.subtitle.text(), self.reference.text(), "PDF", page] if x)
        return f"[{citation}]"
    
    def citationToClipboard(self):
        target = f'{self._document.filepath.as_posix()}'
        suffix = f'#page={self.page_navigator.currentPageLabel()}'
        copy_file_link_to_clipboard(target, self.citation(), suffix)

    def source(self) -> str:
        title = self._document.title
        page = self.page_navigator.currentPageLabel()
        viewer = self.viewerName()
        source = f'{{"application":"InspectorMate", "module":"{viewer}", "item":"document", "item_title":"{title}", "page":"{page}"}}'
        return source
    
    @Slot(object)
    def onAnnotationAdded(self, annot: RectItem):
        if annot.rect().width() == 0 and annot.rect().height() == 0:
            return 

        record = self.annotation_model.record()
        record.setValue(self.annotation_model.Fields.DocumentID.index, self.document.id)
        record.setValue(self.annotation_model.Fields.PageNumber.index, annot.pno)
        # {"pageIndex":int,"rect":[ ax: float, ay: float, aaw: float, aah: float], "zfactor": float}
        position = {"pageIndex": annot.pno, "rect": annot.rect().getRect(), "zfactor": annot.zfactor}
        json_position = json.dumps(position)
        record.setValue(self.annotation_model.Fields.Position.index, json_position)
        record.setValue(self.annotation_model.Fields.Text.index, annot.textSelection.text)
        record.setValue(self.annotation_model.Fields.Uid.index, annot.uid)
        self.annotation_model.beginInsertRows(QtCore.QModelIndex(), self.annotation_model.rowCount(), self.annotation_model.rowCount() + 1)
        inserted = self.annotation_model.insertRecord(-1, record)
        self.annotation_model.endInsertRows()

        if not inserted:
            logger.error(f"Cannot insert annotation into the database - Error: {self.annotation_model.lastError().text()}")
            return
        
        self.annotation_model.select()
        self.annotation_model.setFilter(f"document_id={self.document.id}")
    
    @Slot(QtCore.QModelIndex)
    def onAnnotationListClicked(self, index: QtCore.QModelIndex):
        pno = index.sibling(index.row(), self.annotation_model.Fields.PageNumber.index).data(QtCore.Qt.ItemDataRole.DisplayRole)
        position = index.sibling(index.row(), self.annotation_model.Fields.Position.index).data(QtCore.Qt.ItemDataRole.DisplayRole)
        location = json.loads(position)

        to = QtCore.QPointF()
        rect: list = location.get("rect")
        if rect:
            ax, ay, aaw, aah = rect
            to.setX(ax)
            to.setY(ay)

        try:
            p = int(pno)
        except Exception as e:
            pass
        else:
            self.page_navigator.jump(p, to)
