import logging
import enum
from functools import partial
from base64 import (b64decode, b64encode)

from qtpy import QtWidgets, QtCore, QtGui, Slot

from db.database import AppDatabase
from utilities.config import settings
from utilities.utils import (hexuuid, createFolder, queryFileID)
from utilities import config as mconf

logger = logging.getLogger(__name__)


class TextEdit(QtWidgets.QTextEdit):

    def __init__(self, filename=str, text=str, parent=None):
        super(TextEdit, self).__init__(parent)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        self.filename: str = filename
        base_url = QtCore.QUrl(f"file:///{AppDatabase.active_workspace.notebook_path}/")
        self.document().setBaseUrl(base_url)

        self.setHtml(text)

        self._cursor = self.textCursor()

        self.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.LinksAccessibleByMouse | QtCore.Qt.TextInteractionFlag.TextEditorInteraction)
        self.document().setModified(False)
        self.setWindowTitle(QtCore.QFileInfo(self.filename).fileName())
        self.setObjectName(self.userFriendlyFilename())

        self.connectSignals()

    def userFriendlyFilename(self):
        return QtCore.QFileInfo(self.filename).fileName()
    
    def cursor_position_changed(self):
        self._cursor: QtGui.QTextCursor = self.textCursor()

    def connectSignals(self):
        # self.currentCharFormatChanged.connect(self.current_char_format_changed)
        self.cursorPositionChanged.connect(self.cursor_position_changed)
    
    def canInsertFromMimeData(self, source: QtCore.QMimeData):
        if source.hasImage():
            return source.hasImage()
        else:
            return super(TextEdit, self).canInsertFromMimeData(source)
        
    def insertFromMimeData(self, source: QtCore.QMimeData):
        cursor = self.textCursor()
        document = self.document()

        if source.hasUrls():
            for url in source.urls():
                file_info = QtCore.QFileInfo(url.toLocalFile())
                if file_info.suffix().lower() in QtGui.QImageReader.supportedImageFormats():
                    image = QtGui.QImage(url.toLocalFile())
                    if not image.isNull():
                        document.addResource(QtGui.QTextDocument.ResourceType.ImageResource, url, image)
                        cursor.insertImage(url.toLocalFile())
                else:
                    # If we hit a non-image or non-local URL break the loop and fall out
                    # to the super call & let Qt handle it
                    break
        elif source.hasImage():
            image = source.imageData()
            uuid = hexuuid()

            image_dir = f"{AppDatabase.active_workspace.notebook_path}/.images"
            createFolder(image_dir)
            image_path = f'{image_dir}/{uuid}.png'

            image_saved = QtGui.QImage(image).save(image_path, "PNG", 100)
            if not image_saved:
                logger.error(f"Error saving image saved: {image_path}")
            
            img_url = QtCore.QUrl.fromLocalFile(f'.images/{uuid}.png')
            resolved_url = document.baseUrl().resolved(img_url)

            document.addResource(QtGui.QTextDocument.ResourceType.ImageResource, resolved_url, image)

            # insert image with relative path for web browser
            cursor.insertImage(QtGui.QImage(image), img_url.toString())


            # insert image as base64 string
            # img = QtGui.QImage(image)
            # buffer = QtCore.QBuffer()
            # buffer.open(QtCore.QIODevice.OpenModeFlag.WriteOnly)
            # img.save(buffer, 'PNG')
            # img_str = b64encode(buffer.data()).decode("utf8")

            # cursor.insertHtml(f'<p><img alt="" src="data:image/png;base64,{img_str}"/></p>')

            # Add citation below the image
            # Get the Pixmap cacheKey from the Qsettings if cachekeys match then insert the citation along with the image
            image_cachekey = QtWidgets.QApplication.clipboard().image().cacheKey()
            capture = mconf.settings.value("capture", [], "QStringList")
            if len(capture) > 0:
                if str(image_cachekey) == capture[0]:
                    citation = capture[1]
                    cursor.insertBlock()
                    cursor.insertText(citation)
                    
                    # set a blue color to the foreground of the citation
                    cursor.select(QtGui.QTextCursor.SelectionType.LineUnderCursor)
                    fmt = QtGui.QTextCharFormat()
                    fmt.setForeground(QtGui.QColor(85, 0, 255))
                    cursor.mergeCharFormat(fmt)
                    self.mergeCurrentCharFormat(fmt)

        elif source.hasText():
            hyperlink = QtCore.QUrl(source.text())
            if not hyperlink.isRelative():
                link = QtGui.QTextCharFormat()
                link.setAnchor(True)
                link.setAnchorHref(f"{source.text()}")
                link.setAnchorNames([f"{source.text()}"])
                link.setForeground(QtCore.Qt.GlobalColor.blue)
                link.setFontUnderline(True)
                cursor.insertText(source.text(), link)
            else:
                super(TextEdit, self).insertFromMimeData(source)
        else:
            super(TextEdit, self).insertFromMimeData(source)
    
    def closeEvent(self, event):
        if self.document().isModified():
            err = self.save()

            if err is not None:
                QtWidgets.QMessageBox.warning(self,
                                              "RichTextEditor -- Save Error",
                                              f"Failed to save {self.filename}: {err}")

    def isModified(self):
        return self.document().isModified()

    def save(self) -> Exception | bool:
        try:
            fh = QtCore.QFile(self.filename)
            if not fh.open(QtCore.QIODevice.OpenModeFlag.WriteOnly):
                logger.error(IOError(fh.errorString()))
            stream = QtCore.QTextStream(fh)
            stream.setEncoding(QtCore.QStringConverter.Encoding.Utf8)
            stream << self.toHtml()
        except EnvironmentError as e:
            logger.error(f"RichTextEditor -- Save Error:\nFailed to save {self.filename}: {e}")
            return e
        finally:
            self.document().setModified(False)
            return None

    def merge_format_on_word_or_selection(self, fmt: QtGui.QTextCharFormat):
        if not self._cursor.hasSelection():
            self._cursor.select(QtGui.QTextCursor.SelectionType.WordUnderCursor)

        self._cursor.mergeCharFormat(fmt)
        self.mergeCurrentCharFormat(fmt)

    @classmethod
    def load(cls, filename: str):
        fh = None
        try:
            fh = QtCore.QFile(filename)
            if not fh.open(QtCore.QIODevice.OpenModeFlag.ReadOnly):
                logger.error(f"RichTextEditor -- Open Error:\nFailed to open {filename}: {IOError(fh.errorString())}")
                QtWidgets.QMessageBox.warning(cls,
                                              "RichTextEditor -- Open Error",
                                              f"Failed to open {cls.filename}: {IOError(fh.errorString())}")
                return
            stream = QtCore.QTextStream(fh)
            stream.setEncoding(QtCore.QStringConverter.Encoding.Utf8)
            text = stream.readAll()
        except EnvironmentError as e:
            QtWidgets.QMessageBox.warning(cls,
                                          "RichTextEditor -- Load Error",
                                          f"Failed to load {filename}: {e}")
            return
        finally:
            if fh is not None:
                fh.close()
            return cls(filename, text)
    
    @Slot()
    def textBold(self):
        cursor = self._cursor

        fmt = QtGui.QTextCharFormat()
        weight = QtGui.QFont.Weight.Bold if cursor.charFormat().fontWeight() == QtGui.QFont.Weight.Normal else QtGui.QFont.Weight.Normal
        fmt.setFontWeight(weight)
        self.merge_format_on_word_or_selection(fmt)
    
    @Slot()
    def textItalic(self):
        cursor = self._cursor

        fmt = QtGui.QTextCharFormat()
        style = False if cursor.charFormat().fontItalic() else True
        fmt.setFontItalic(style)
        self.merge_format_on_word_or_selection(fmt)

    @Slot()
    def textUnderline(self):
        cursor = self._cursor

        fmt = QtGui.QTextCharFormat()
        style = False if cursor.charFormat().fontUnderline() else True
        fmt.setFontUnderline(style)
        self.merge_format_on_word_or_selection(fmt)

    @Slot()
    def textStrikeout(self):
        cursor = self._cursor

        fmt = QtGui.QTextCharFormat()
        style = False if cursor.charFormat().fontStrikeOut() else True
        fmt.setFontStrikeOut(style)
        self.merge_format_on_word_or_selection(fmt)
    

class Notepad(QtWidgets.QWidget):

    class LayoutStrategy(enum.Enum):
        Cascade = 0
        Tile = 1
        Tabbed = 2

    layout_strategy: LayoutStrategy = LayoutStrategy.Cascade

    def __init__(self, parent=None):
        super().__init__(parent)

        vbox = QtWidgets.QVBoxLayout(self)
        self.setLayout(vbox)

        # MdiArea
        self.mdi = QtWidgets.QMdiArea()
        self.mdi.setTabsMovable(True)
        self.mdi.setTabsClosable(True)
        
        self.createActions()
        self.createToolbar()
        
        vbox.addWidget(self.toolbar)
        vbox.addWidget(self.mdi)

        QtCore.QTimer.singleShot(0, self.loadFiles)
        self.loadSettings()

    def createActions(self):
        self.action_addnote = QtGui.QAction(QtGui.QIcon(':file_add'), "add note", self, triggered=self.addNote)
        self.action_editnote = QtGui.QAction(QtGui.QIcon(':file-edit-line'), "edit note", self, triggered=self.editNote)

        self.action_minimizeAll = QtGui.QAction(QtGui.QIcon(':folder-2-line'), "Minimize", self, triggered=self.minimizeAll)
        self.action_showNormalAll = QtGui.QAction(QtGui.QIcon(':folder-2-line'), "Normal", self, triggered=self.showNormalAll)
        self.action_showMaximizeAll = QtGui.QAction(QtGui.QIcon(':folder-2-line'), "Maximized", self, triggered=self.showMaximizeAll)
        self.action_setTileView = QtGui.QAction(QtGui.QIcon(':layout-grid-line'), "Tile", self, triggered=self.setTileView)
        self.action_setTabbedView = QtGui.QAction(QtGui.QIcon(':folder-2-line'), "Tabbed", self, triggered=self.setTabbedView)

        self.action_close = QtGui.QAction("Cl&ose", self, statusTip="Close the active window", triggered=self.close)
        self.action_closeall = QtGui.QAction("Close &All", self, statusTip="Close all the windows", triggered=self.close_all)

        # Text actions
        self.action_bold = QtGui.QAction(QtGui.QIcon(':bold'), "Bold (Ctrl+B)", self, checkable=True)
        self.action_italic =  QtGui.QAction(QtGui.QIcon(':italic'), "Italic (Ctrl+I)", self, checkable=True)
        self.action_underline = QtGui.QAction(QtGui.QIcon(':underline'), "Underline (Ctrl+U)", self, checkable=True)
        self.action_strikeout = QtGui.QAction(QtGui.QIcon(':strikeout'), "StrikeOut (Ctrl+-)", self, checkable=True)

    def createToolbar(self):
        self.toolbar = QtWidgets.QToolBar(self)

        viewmenu_toolbutton = QtWidgets.QToolButton(self)
        viewmenu_toolbutton.setIcon(QtGui.QIcon(':eye-line'))
        viewmenu_toolbutton.setText("Views")
        viewmenu_toolbutton.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)

        viewmenu = QtWidgets.QMenu("View", self)

        cascade_menu = QtWidgets.QMenu("Cascade", self)
        cascade_menu.setIcon(QtGui.QIcon(':stack-line'))
        cascade_menu.addAction(self.action_minimizeAll)
        cascade_menu.addAction(self.action_showNormalAll)
        cascade_menu.addAction(self.action_showMaximizeAll)
        viewmenu.addMenu(cascade_menu)

        viewmenu.addAction(self.action_setTileView)
        viewmenu.addAction(self.action_setTabbedView)
        viewmenu_toolbutton.setMenu(viewmenu)
        
        self.toolbar.addAction(self.action_addnote)
        self.toolbar.addAction(self.action_editnote)
        self.toolbar.addWidget(viewmenu_toolbutton)

        self.window_menu = QtWidgets.QMenu("Window", self)

        self.windowmenu_toolbutton = QtWidgets.QToolButton(self)
        self.windowmenu_toolbutton.setIcon(QtGui.QIcon(':window-2-line'))
        self.windowmenu_toolbutton.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
        self.windowmenu_toolbutton.setMenu(self.window_menu)
        self.update_window_menu()
        self.window_menu.aboutToShow.connect(self.update_window_menu)
        self.toolbar.addWidget(self.windowmenu_toolbutton)

        self.toolbar.addSeparator()

        # Text actions
        self.toolbar.addAction(self.action_bold)
        self.toolbar.addAction(self.action_italic)
        self.toolbar.addAction(self.action_underline)
        self.toolbar.addAction(self.action_strikeout)

    @Slot()
    def update_window_menu(self):
        self.window_menu.clear()
        self.window_menu.addAction(self.action_close)
        self.window_menu.addAction(self.action_closeall)
        self.window_menu.addSeparator()

        windows = self.mdi.subWindowList()
        
        for i, window in enumerate(windows):
            child: TextEdit = window.widget()

            f = child.userFriendlyFilename()
            text = f'{i + 1} {f}'
            if i < 9:
                text = '&' + text

            action = self.window_menu.addAction(text)
            action.setCheckable(True)
            action.setChecked(window is self.mdi.activeSubWindow())
            slot_func = partial(self.set_active_sub_window, window=window)
            action.triggered.connect(slot_func)

    def set_active_sub_window(self, window):
        if window:
            self.mdi.setActiveSubWindow(window)

    def close(self):
        active_sub_window = self.mdi.activeSubWindow()
        
        if active_sub_window is None:
            return
        
        current_textedit: TextEdit = active_sub_window.widget()

        err = current_textedit.save()
        if err:
            return

        self.mdi.closeActiveSubWindow()

    def close_all(self):
        err = self.saveAll()
        
        if err:
            return

        self.saveSettings()
        self.mdi.closeAllSubWindows()
    
    def saveSettings(self):
        # Save opened files
        files = []
        for subwindows in self.mdi.subWindowList():
            textedit: TextEdit = subwindows.widget()
            files.append(textedit.filename)

        settings.setValue("NotebookCurrentFiles", files)

        # Save layout strategy
        settings.setValue("NotebookLayoutStrategy", self.layout_strategy)
    
    def loadSettings(self):
        # Restore layout strategy
        layout_strategy = settings.value("NotebookLayoutStrategy", self.layout_strategy)

        if layout_strategy == self.LayoutStrategy.Cascade:
            self.setCascadeView()
        elif layout_strategy == self.LayoutStrategy.Tile:
            self.setTileView()
        elif layout_strategy == self.LayoutStrategy.Tabbed:
            self.setTabbedView()

    def loadfile(self, filename):
        textedit = TextEdit.load(filename)
        if textedit is not None:
            # Connect action
            self.action_bold.triggered.connect(textedit.textBold)
            self.action_italic.triggered.connect(textedit.textItalic)
            self.action_strikeout.triggered.connect(textedit.textStrikeout)
            self.action_underline.triggered.connect(textedit.textUnderline)

            subwindow = self.mdi.addSubWindow(textedit)
            subwindow.show()

    @Slot()
    def loadFiles(self):
        files = settings.value("NotebookCurrentFiles", [], "QStringList")
        for filename in files:
            if QtCore.QFile.exists(filename):
                self.loadfile(filename)
                QtWidgets.QApplication.processEvents()

    def saveAll(self):
        errors = []
        for subwindows in self.mdi.subWindowList():
            textedit: TextEdit = subwindows.widget()
            if textedit.isModified():
                err = textedit.save()
                if err is not None:
                    errors.append(f"{textedit.filename}: {err}")
        
        if errors:
            QtWidgets.QMessageBox.warning(self, "RichTextEditor -- Save All Error", f"Failed to save\n {"\n".join(errors)}")
        
        return errors

    def addNote(self):
        filename = f"Untitled.html"
        fname = QtWidgets.QFileDialog.getSaveFileName(parent=None,
                                                          caption="RichTextEditor -- Save File As",
                                                          directory=f"{AppDatabase.active_workspace.notebook_path}/{filename}",
                                                          filter="Text files (*.html *.*)")
        if fname[0] == "":
            return
        
        with open(fname[0], "w") as f:
            text = ""
            f.write(text)
            f.close()

        self.loadfile(fname[0])

    def editNote(self):
        fname = QtWidgets.QFileDialog.getOpenFileName(parent=None,
                                                      caption="RichTextEditor -- Select file",
                                                      directory=f"{AppDatabase.active_workspace.notebook_path}",
                                                      filter="Text files (*.html *.*)")
        
        if fname[0] == "":
            return

        for subwindow in self.mdi.subWindowList():
            textedit: TextEdit = subwindow.widget()
            if textedit.filename == fname[0]:
                self.mdi.setActiveSubWindow(subwindow)
                break
        else:
            self.loadfile(fname[0])

    def setTabbedView(self):
        self.mdi.setViewMode(QtWidgets.QMdiArea.ViewMode.TabbedView)
        self.layout_strategy = self.LayoutStrategy.Tabbed

    def setCascadeView(self):
        self.mdi.setViewMode(QtWidgets.QMdiArea.ViewMode.SubWindowView)
        self.mdi.cascadeSubWindows()
        self.layout_strategy = self.LayoutStrategy.Cascade
    
    def setTileView(self):
        self.mdi.setViewMode(QtWidgets.QMdiArea.ViewMode.SubWindowView)
        for subwindow in self.mdi.subWindowList():
            subwindow.showMaximized()
        self.mdi.tileSubWindows()
        self.layout_strategy = self.LayoutStrategy.Tile

    def minimizeAll(self):
        self.setCascadeView()
        for subwindow in self.mdi.subWindowList():
            subwindow.showMinimized()
    
    def showNormalAll(self):
        self.setCascadeView()
        for subwindow in self.mdi.subWindowList():
            subwindow.showNormal()

    def showMaximizeAll(self):
        self.setCascadeView()
        for subwindow in self.mdi.subWindowList():
            subwindow.showMaximized()

    
